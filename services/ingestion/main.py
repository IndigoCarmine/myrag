from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from .processor import extract_metadata_grobid, extract_text_from_pdf, create_chunks
from .clients import EmbeddingClient, QdrantHandler
from .logger import setup_logger
import traceback

logger = setup_logger("ingestion_service")

app = FastAPI(title="Ingestion Service")

# Initialize Clients
# Note: In a real app, these might be singletons or dependencies infused via FastAPI Depends
embedding_client = EmbeddingClient()
qdrant_handler = None


# Startup event to initialize DB connection safely
@app.on_event("startup")
def startup_event():
    global qdrant_handler
    try:
        qdrant_handler = QdrantHandler()
    except Exception as e:
        logger.warning(f"Warning: Could not connect to Qdrant at startup: {e}")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        content = await file.read()

        # 1. Extract Metadata
        logger.info(f"Processing {file.filename}...")
        metadata = extract_metadata_grobid(content, file.filename)
        logger.info(f"Metadata extracted: {metadata}")

        # 2. Extract Text
        pages_content = extract_text_from_pdf(content)
        if not pages_content:
            return {"status": "error", "message": "No text extracted from PDF."}

        # 3. Chunking
        chunks = create_chunks(pages_content, metadata)
        logger.info(f"Generated {len(chunks)} chunks.")

        # 4. Embeddings
        # Process in batches to avoid overloading the Embedding Service
        texts = [c["text"] for c in chunks]
        vectors = []
        batch_size = 10  # Conservative batch size

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_vectors = embedding_client.get_embeddings(batch_texts)
            vectors.extend(batch_vectors)

        # 5. Storage
        if qdrant_handler:
            qdrant_handler.upsert_chunks(chunks, vectors)
        else:
            # Attempt to re-init if it failed at startup
            try:
                local_handler = QdrantHandler()
                local_handler.upsert_chunks(chunks, vectors)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Database unavailable: {e}"
                )

        return {
            "filename": file.filename,
            "status": "success",
            "chunks_processed": len(chunks),
            "metadata": metadata,
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
