import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import fitz  # PyMuPDF

# Import app. Since clients are initialized at module level or startup, we need to patch them.
from services.ingestion.main import app

client = TestClient(app)


@pytest.fixture
def mock_pdf_content():
    # create a minimal valid PDF in memory using fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World! This is a test PDF.")
    return doc.write()


@patch("services.ingestion.main.EmbeddingClient")
@patch("services.ingestion.main.QdrantHandler")
def test_ingest_document_success(MockQdrant, MockEmbedding, mock_pdf_content):
    # Setup Mocks
    mock_embedding_instance = MockEmbedding.return_value
    mock_embedding_instance.get_embeddings.return_value = [
        [0.1, 0.2]
    ] * 10  # return dummy vectors

    mock_qdrant_instance = MockQdrant.return_value

    # We need to patch the global instances in main.py because they might be instantiated already
    # or we need to ensure dependency injection.
    # In main.py:
    # embedding_client = EmbeddingClient()
    # qdrant_handler = None (init on startup)

    with patch(
        "services.ingestion.main.embedding_client", mock_embedding_instance
    ), patch("services.ingestion.main.qdrant_handler", mock_qdrant_instance):

        response = client.post(
            "/ingest", files={"file": ("test.pdf", mock_pdf_content, "application/pdf")}
        )

    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["status"] == "success"
    assert json_resp["filename"] == "test.pdf"
    assert json_resp["chunks_processed"] > 0

    # Verify methods were called
    mock_embedding_instance.get_embeddings.assert_called()
    mock_qdrant_instance.upsert_chunks.assert_called()


def test_ingest_invalid_file_type():
    response = client.post(
        "/ingest", files={"file": ("test.txt", b"plain text", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
