from fastapi.testclient import TestClient
import sys
import os

from services.embedding.main import app

client = TestClient(app)

def test_health_check():
    """Verify that the health check endpoint returns 200 and correct status."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ok"
    assert "model" in json_data

def test_generate_embeddings():
    """Verify that the embed endpoint returns vectors of correct dimension."""
    test_texts = ["Hello world", "This is a test"]
    response = client.post("/embed", json={"text": test_texts})
    
    assert response.status_code == 200
    json_data = response.json()
    
    assert "vectors" in json_data
    assert "dimension" in json_data
    
    # Check dimensions
    vectors = json_data["vectors"]
    assert len(vectors) == 2
    # Check vector dimension (e5-large is 1024)
    assert len(vectors[0]) == 1024
    assert json_data["dimension"] == 1024
