import pytest
import respx
from httpx import Response, AsyncClient, ASGITransport
import sys
import os

from services.gateway.main import app, RETRIEVAL_URL, OLLAMA_URL

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
@respx.mock
async def test_chat_success(client):
    # Mock Retrieval Service
    retrieval_route = respx.post(f"{RETRIEVAL_URL}/search").mock(return_value=Response(200, json={
        "results": [
            {
                "text": "This is a context text.",
                "score": 0.9,
                "metadata": {"doi": "10.1234/test"}
            }
        ]
    }))

    # Mock Ollama Service
    ollama_route = respx.post(f"{OLLAMA_URL}/api/generate").mock(return_value=Response(200, json={
        "response": "This is the answer."
    }))

    response = await client.post("/chat", json={"query": "test query"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is the answer."
    assert data["citations"] == ["10.1234/test"]
    
    assert retrieval_route.called
    assert ollama_route.called

@pytest.mark.asyncio
@respx.mock
async def test_chat_retrieval_failure_handling(client):
    # Mock Retrieval Service failure
    respx.post(f"{RETRIEVAL_URL}/search").mock(return_value=Response(500))

    # Mock Ollama Service (should still be called with empty context)
    ollama_route = respx.post(f"{OLLAMA_URL}/api/generate").mock(return_value=Response(200, json={
        "response": "Answer without context."
    }))

    response = await client.post("/chat", json={"query": "test query"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Answer without context."
    # Citations might be empty since retrieval failed
    assert data["citations"] == []
    
    assert ollama_route.called

@pytest.mark.asyncio
@respx.mock
async def test_chat_ollama_failure(client):
    # Mock Retrieval Service success
    respx.post(f"{RETRIEVAL_URL}/search").mock(return_value=Response(200, json={"results": []}))

    # Mock Ollama Service failure
    respx.post(f"{OLLAMA_URL}/api/generate").mock(return_value=Response(503))

    response = await client.post("/chat", json={"query": "test query"})
    
    assert response.status_code == 503
    assert "LLM Service" in response.json()["detail"]

@pytest.mark.asyncio
async def test_chat_validation_error(client):
    response = await client.post("/chat", json={"query": ""}) # Empty query
    assert response.status_code == 400
