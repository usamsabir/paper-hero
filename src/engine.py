import json
from collections import defaultdict
from typing import Dict, Any

import spacy
from tqdm import tqdm

from src.interfaces import Paper


class SearchAPI:
    SEARCH_PRIORITY = ["year", "month", "venue", "author", "title", "abstract"]

    def __init__(self) -> None:
        self.papers: list[Paper] = []

    def exhausted_search(self, query: dict[str, tuple[tuple[str]]]) -> list[Paper]:
        """Exhausted search papers by matching query"""
        def _in_string(statement, string):
            stmt_in_string = False
            if " " in statement and statement.lower() in string.lower():
                stmt_in_string = True
            else:
                tokens = self.tokenize(string.lower())
                if statement.lower() in tokens:
                    stmt_in_string = True
            return stmt_in_string

        papers = self.papers
        for field in self.SEARCH_PRIORITY:
            if field in query:
                req = query[field]
                time_spans = []
                if field in ["year", "month"]:
                    for span in req:
                        assert len(span) == 2
                        assert all(num.isdigit() for num in span)
                        time_spans.append((int(span[0]), int(span[1])))

                paper_indices = []
                for i, p in enumerate(papers):
                    matched = False
                    if time_spans:
                        if any(s <= p[field] <= e for s, e in time_spans):
                            matched = True
                    else:
                        if any(
                            all(
                                _in_string(stmt, p[field])
                                for stmt in and_statements
                            )
                            for and_statements in req
                        ):
                            matched = True

                    if matched:
                        paper_indices.append(i)
                papers = [papers[i] for i in paper_indices]

        return papers

    def search(
        self, query: dict[str, tuple[tuple[str]]], method: str = "exhausted"
    ) -> list[Paper]:
        """Search papers

        Args:
            query: A dict of queries on different field.
                A query in a field is a tuple of strings, where strings are AND
                and tuple means OR. Strings are case-insensitive.
                e.g. {
                    "venue": (("EMNLP", ), ("ACL",)),
                    "title": (("parsing", "tree-crf"), ("event extraction",))
                }
                This query means we want to find papers in EMNLP or ACL,
                AND the title either contains ("parsing" AND "tree-crf") OR "event extraction"
            method: choice from:
                - `exhausted`: brute force mathing

        Returns:
            a list of `Paper`
        """
        papers = []
        if method == "exhausted":
            papers = self.exhausted_search(query)
        else:
            raise NotImplementedError

        if papers:
            papers = sorted(set(papers), key=lambda p: (p.year, p.month), reverse=True)
        return papers

    def tokenize(self, string: str) -> list[str]:
        return string.lower().split()


    @staticmethod
    def build_paper_list(json_string: str) -> list[Paper]:
        """Build a paper list from a JSON string"""
        paper_data = json.loads(json_string)
        papers = []
        for paper in paper_data:
            # Ensure all required fields are present
            paper_dict = {
                'title': paper.get('title', ''),
                'author': paper.get('author', ''),
                'abstract': paper.get('abstract', ''),
                'url': paper.get('url', ''),
                'doi': paper.get('doi', ''),
                'venue': paper.get('venue', ''),
                'year': paper.get('year', 0),
                'month': paper.get('month', 0)
            }
            papers.append(Paper(**paper_dict))
        return papers

    def advanced_search(
            self,
            query: Dict[str, tuple[tuple[str]]],
            sort_by: str = None,
            sort_order: str = 'desc',
            page: int = 1,
            page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Advanced search with sorting and pagination

        Args:
            query: A dict of queries on different fields
            sort_by: Field to sort by (e.g., 'year', 'month', 'venue')
            sort_order: 'asc' for ascending, 'desc' for descending
            page: The page number to return (starting from 1)
            page_size: Number of results per page

        Returns:
            A dict containing:
                - 'papers': A list of `Paper` objects for the current page
                - 'total_results': Total number of papers matching the query
                - 'page': Current page number
                - 'total_pages': Total number of pages
        """
        results = self.search(query)

        if sort_by:
            reverse = sort_order.lower() == 'desc'
            results.sort(key=lambda p: getattr(p, sort_by), reverse=reverse)

        total_results = len(results)
        total_pages = (total_results + page_size - 1) // page_size

        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        return {
            'papers': results[start_index:end_index],
            'total_results': total_results,
            'page': page,
            'total_pages': total_pages
        }
    @classmethod
    def build_and_search(
            cls,
            json_string: str,
            query: Dict[str, tuple[tuple[str]]],
            sort_by: str = None,
            sort_order: str = 'desc',
            page: int = 1,
            page_size: int = 10
    ) -> Dict[str, Any]:
        """Build a paper list from a JSON string and immediately search it with sorting and pagination"""
        papers = cls.build_paper_list(json_string)
        api = cls()
        api.papers = papers
        return api.advanced_search(query, sort_by, sort_order, page, page_size)
