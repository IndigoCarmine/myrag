import os
import structlog
import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict
from sentence_transformers import SentenceTransformer

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

app = FastAPI(title="Embedding Service")

# Configuration
MODEL_NAME: str = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"

model: SentenceTransformer | None = None

try:
    logger.info("loading_model", model=MODEL_NAME, device=DEVICE)
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    model.eval()
    logger.info("model_loaded", status="success")
except Exception as e:
    logger.error("model_load_failed", error=str(e))
    # In a real production scenario, we might want to exit here,
    # but for now we let the app start so health check works (reporting failure)
    pass


class EmbedRequest(BaseModel):
    text: List[str]


class EmbedResponse(BaseModel):
    vectors: List[List[float]]
    dimension: int


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Dict[str, str]: Status information including model loaded state and device.
    """
    status = "ok" if model is not None else "error"
    return {"status": status, "model": MODEL_NAME, "device": DEVICE}


@app.post("/embed", response_model=EmbedResponse)
async def generate_embeddings(request: EmbedRequest) -> EmbedResponse:
    """
    Generates embeddings for a list of texts.

    Args:
        request (EmbedRequest): The request body containing a list of strings.

    Returns:
        EmbedResponse: JSON response containing vectors and their dimension.

    Raises:
        HTTPException: If the model is not loaded or inference fails.
    """
    if model is None:
        logger.error("inference_failed", reason="model_not_loaded")
        raise HTTPException(status_code=503, detail="Embedding model is not loaded.")

    if not request.text:
        # Handle empty list gracefully
        return EmbedResponse(
            vectors=[], dimension=model.get_sentence_embedding_dimension()
        )

    try:
        # Note: SPEC says "Caller handles prefixes", so we pass text raw.
        # batch_size=32 is a reasonable default mentioned in SPEC.
        # Using convert_to_numpy=True to get explicit numpy arrays first
        embeddings = model.encode(request.text, batch_size=32, convert_to_numpy=True)

        # Convert numpy array to list of lists for JSON serialization
        vectors: List[List[float]] = embeddings.tolist()

        logger.info(
            "embeddings_generated",
            count=len(vectors),
            dimension=len(vectors[0]) if vectors else 0,
        )

        return EmbedResponse(
            vectors=vectors, dimension=model.get_sentence_embedding_dimension()
        )
    except Exception as e:
        logger.error("inference_failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Inference processing failed: {str(e)}"
        )


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
