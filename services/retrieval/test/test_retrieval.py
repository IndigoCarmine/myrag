
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from services.retrieval.main import app, QdrantClient, models

class TestRetrievalService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('services.retrieval.main.client')  # Mock Qdrant Client
    @patch('services.retrieval.main.requests.post')  # Mock Embedding Service
    def test_search_success(self, mock_post, mock_qdrant):
        # 1. Mock Embedding Service Response
        mock_embedding_response = MagicMock()
        mock_embedding_response.status_code = 200
        # Mocking a 4-dimensional vector for simplicity
        mock_embedding_response.json.return_value = {"vectors": [[0.1, 0.2, 0.3, 0.4]], "dimension": 4}
        mock_post.return_value = mock_embedding_response

        # 2. Mock Qdrant Vector Search Response
        # Qdrant returns ScoredPoint objects
        mock_vector_result = [
            models.ScoredPoint(
                id=1, 
                version=1, 
                score=0.9, 
                payload={"text": "Vector Result 1", "page": 1}, 
                vector=None
            ),
            models.ScoredPoint(
                id=2, 
                version=1, 
                score=0.8, 
                payload={"text": "Vector Result 2", "page": 2}, 
                vector=None
            )
        ]
        mock_qdrant.search.return_value = mock_vector_result

        # 3. Mock Qdrant Keyword Search (Scroll) Response
        # Qdrant Scroll returns a tuple (points, offset)
        # We simulate that Keyword search found 'Vector Result 2' (id=2) and a new 'Keyword Result 3' (id=3)
        mock_keyword_result = (
            [
                models.Record(
                    id=2, 
                    payload={"text": "Vector Result 2", "page": 2}, 
                    vector=None
                ),
                models.Record(
                    id=3, 
                    payload={"text": "Keyword Result 3", "page": 3}, 
                    vector=None
                )
            ],
            None # next_page_offset
        )
        mock_qdrant.scroll.return_value = mock_keyword_result

        # 4. Perform Request
        response = self.client.post("/search", json={"query": "test query", "top_k": 5})

        # 5. Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # We expect 3 unique results (ID 1, 2, 3)
        self.assertEqual(len(data['results']), 3)
        
        # Verify RRF Logic roughly
        # ID 2 appears in both, so it should likely be near the top.
        # RRF score for ID 2 = 1/(60+2) + 1/(60+1) (Rank 2 in vector, Rank 1 in keyword... wait, 0-indexed?)
        # function implementation: 
        # Vector: ID1 (rank 0), ID2 (rank 1)
        # Keyword: ID2 (rank 0), ID3 (rank 1)
        # ID1 Score: 1/(60+0+1) = 1/61 ≈ 0.01639
        # ID2 Score: 1/(60+1+1) + 1/(60+0+1) = 1/62 + 1/61 ≈ 0.01612 + 0.01639 = 0.0325
        # ID3 Score: 1/(60+1+1) = 1/62 ≈ 0.01612
        # Expected Order: ID2, ID1, ID3 (roughly)
        
        results = data['results']
        self.assertEqual(results[0]['metadata']['page'], 2) # ID2 is top
        self.assertEqual(results[1]['metadata']['page'], 1) # ID1 is second
        self.assertEqual(results[2]['metadata']['page'], 3) # ID3 is third

        # Check content
        self.assertEqual(results[0]['text'], "Vector Result 2")
        self.assertEqual(results[1]['text'], "Vector Result 1")

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch('services.retrieval.main.client')
    @patch('services.retrieval.main.requests.post')
    def test_embedding_failure(self, mock_post, mock_qdrant):
        # Simulate Embedding Service Failure
        mock_post.side_effect = Exception("Connection refused")
        
        response = self.client.post("/search", json={"query": "fail", "top_k": 5})
        
        self.assertEqual(response.status_code, 500)
        self.assertIn("Embedding service failed", response.json()['detail'])

if __name__ == '__main__':
    unittest.main()
