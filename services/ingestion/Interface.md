# Ingestion Service Interface

## Overview
The Ingestion Service handles the processing of PDF documents. It parses metadata (Grobid), extracts text (PyMuPDF), chunks the content, generates embeddings (via Embedding Service), and stores them in the Vector DB (Qdrant).

## Endpoints

### 1. Ingest Document
*   **URL**: `/ingest`
*   **Method**: `POST`
*   **Description**: Uploads and processes a PDF file.
*   **Request**: `multipart/form-data`
    *   `file`: The PDF file object.
*   **Response**:
    ```json
    {
      "filename": "paper.pdf",
      "status": "success",
      "chunks_processed": 15,
      "metadata": {
        "title": "A New Method for...",
        "doi": "10.1234/5678"
      }
    }
    ```

### 2. Health Check
*   **URL**: `/health`
*   **Method**: `GET`
*   **Response**: `{"status": "ok"}`
