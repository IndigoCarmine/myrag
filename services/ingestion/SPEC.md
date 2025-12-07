# Ingestion Service Specification

## Responsibility
The Ingestion Service is responsible for converting raw PDF files into searchable vectors. It handles parsing, text extraction, chunking, embedding generation, and database upsert.

## Internal Logic

### 1. Ingestion Flow (`POST /ingest`)
1.  **File Reception**: Receive PDF file via `multipart/form-data`.
2.  **Metadata Extraction (Grobid)**:
    *   Send PDF to Grobid (`POST /api/processHeaderDocument`).
    *   Extract `Title`, `Authors`, `DOI`, `Date`.
    *   *Fallback*: If Grobid fails or returns low confidence, try to extract basic metadata from PDF properties or filename.
3.  **Text Extraction (PyMuPDF)**:
    *   Iterate through pages.
    *   Extract text blocks.
    *   Keep track of page numbers.
4.  **Chunking**:
    *   **Strategy**: Recursive Character or Token-based chunking.
    *   **Size**: 1000 tokens.
    *   **Overlap**: 200 tokens.
    *   **Metadata Attachment**: Attach DOI, Title, Page Number to each chunk.
5.  **Vectorization**:
    *   Send batch of chunk texts to `Embedding Service` (`POST /embed`).
    *   Receive vectors.
6.  **Storage (Qdrant)**:
    *   Upsert points into Qdrant collection.
    *   Payload: `{ "text": "...", "doi": "...", "page": 1, "title": "..." }`.
    *   Vector: The received embedding.
    *   ID: UUID generated from text hash to avoid duplicates.

## Dependencies
*   **Framework**: FastAPI
*   **PDF Tools**: `PyMuPDF` (fitz)
*   **Grobid Client**: `grobid-client-python` or direct HTTP requests.
*   **Qdrant Client**: `qdrant-client`.
*   **Environment Variables**:
    *   `GROBID_URL`: URL of Grobid server.
    *   `EMBEDDING_URL`: URL of Embedding Service.
    *   `QDRANT_URL`: URL of Qdrant.
