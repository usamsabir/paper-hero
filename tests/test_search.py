import unittest
import json
from src.engine import SearchAPI
from src.interfaces import Paper


class TestSearchAPI(unittest.TestCase):

    def setUp(self):
        self.sample_papers_json = json.dumps([
            {"title": "Advances in NLP", "author": "Jane Doe, John Smith", "year": 2023, "month": 6, "venue": "ACL",
             "abstract": "This paper discusses recent advances in Natural Language Processing.",
             "url": "http://example.com/paper1", "doi": "10.1234/paper1"},
            {"title": "Deep Learning for Computer Vision", "author": "Alice Johnson", "year": 2022, "month": 12,
             "venue": "CVPR", "abstract": "An overview of deep learning techniques applied to computer vision tasks.",
             "url": "http://example.com/paper2", "doi": "10.1234/paper2"},
            {"title": "Transformer Architectures", "author": "Bob Brown, Charlie Chen", "year": 2023, "month": 9,
             "venue": "EMNLP", "abstract": "A comprehensive study of transformer architectures in various NLP tasks."}
            # Note: missing url and doi
        ])

    def test_build_paper_list(self):
        papers = SearchAPI.build_paper_list(self.sample_papers_json)

        self.assertEqual(len(papers), 3)
        self.assertIsInstance(papers[0], Paper)
        self.assertEqual(papers[0].title, "Advances in NLP")
        self.assertEqual(papers[1].author, "Alice Johnson")
        self.assertEqual(papers[0].url, "http://example.com/paper1")
        self.assertEqual(papers[0].doi, "10.1234/paper1")
        self.assertEqual(papers[2].url, "")  # Default value for missing url
        self.assertEqual(papers[2].doi, "")


    def test_build_and_search_with_sorting_and_pagination(self):
        results = SearchAPI.build_and_search(
            self.sample_papers_json,
            query={"year": (("2022", "2023"),)},
            sort_by='year',
            sort_order='asc',
            page=1,
            page_size=2
        )
        self.assertEqual(len(results['papers']), 2)
        self.assertEqual(results['papers'][0].year, 2022)  # First paper should be from 2022
        self.assertEqual(results['papers'][1].year, 2023)

if __name__ == '__main__':
    unittest.main()