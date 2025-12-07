
import os
import structlog
import requests
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configure Structured Logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

app = FastAPI(title="Retrieval Service")

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://localhost:8003")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "papers")

# Initialize Qdrant Client
try:
    client = QdrantClient(url=QDRANT_URL)
    logger.info("initialized_qdrant_client", url=QDRANT_URL)
except Exception as e:
    logger.error("failed_init_qdrant", error=str(e))
    # We allow startup even if DB is down, but health check will fail?
    # Or should we crash? The instructions say "All exceptions must be caught... or escalated".
    # For a service, maybe just logging is fine initially, but subsequent calls will fail.
    client = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10

class SearchResult(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchResult]

def get_embedding(text: str) -> List[float]:
    """
    Calls the Embedding Service to get the vector for the query.
    
    Args:
        text: The input query string.
        
    Returns:
        List[float]: The vector representation of the query.
        
    Raises:
        HTTPException: If the embedding service returns a non-200 status or connection fails.
    """
    query_text = f"query: {text}"
    logger.info("calling_embedding_service", text_length=len(text))
    
    try:
        response = requests.post(
            f"{EMBEDDING_URL}/embed", 
            json={"text": [query_text]},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data["vectors"][0]
    except Exception as e:
        logger.error("embedding_service_failure", error=str(e))
        raise HTTPException(status_code=500, detail=f"Embedding service failed: {str(e)}")

def perform_vector_search(vector: List[float], k: int) -> List[models.ScoredPoint]:
    """
    Performs dense vector search on Qdrant.
    
    Args:
        vector: The query vector.
        k: Number of results to retrieve.
        
    Returns:
        List[models.ScoredPoint]: List of scored points from Qdrant.
    """
    if not client:
        logger.error("qdrant_client_not_initialized")
        return []

    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=k,
            with_payload=True
        )
        logger.info("vector_search_complete", num_results=len(results))
        return results
    except Exception as e:
        logger.error("vector_search_error", error=str(e))
        return []

def perform_keyword_search(query: str, k: int) -> List[models.Record]:
    """
    Performs keyword search using Qdrant Scroll with a text match filter.
    
    Args:
        query: The raw query text.
        k: Limit for the search results.
        
    Returns:
        List[models.Record]: List of records matching the keywords.
    """
    if not client:
        return []

    try:
        words = query.split()
        should_clauses = [
            models.FieldCondition(
                key="text",
                match=models.MatchText(text=word)
            ) for word in words if len(word) > 2 
        ]
        
        if not should_clauses:
            return []

        scroll_filter = models.Filter(should=should_clauses)

        results, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=scroll_filter,
            limit=k,
            with_payload=True
        )
        logger.info("keyword_search_complete", num_results=len(results))
        return results
    except Exception as e:
        logger.error("keyword_search_error", error=str(e))
        return []

def rrf_fusion(
    vector_results: List[models.ScoredPoint], 
    keyword_results: List[models.Record], 
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combines results using Reciprocal Rank Fusion.
    
    Args:
        vector_results: Results from vector search.
        keyword_results: Results from keyword search.
        k: Constant for RRF smoothing (default 60).
        
    Returns:
        List[Dict[str, Any]]: Merged list of items with new scores.
    """
    scores: Dict[Any, float] = {}
    id_to_item: Dict[Any, Any] = {}

    for rank, item in enumerate(vector_results):
        doc_id = item.id
        id_to_item[doc_id] = item
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1.0))

    for rank, item in enumerate(keyword_results):
        doc_id = item.id
        if doc_id not in id_to_item:
            id_to_item[doc_id] = item
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1.0))

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    
    final_results = []
    for doc_id in sorted_ids:
        final_results.append({
            "item": id_to_item[doc_id],
            "score": scores[doc_id]
        })
    
    return final_results

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Search endpoint executing hybrid search.
    """
    logger.info("search_request_received", query=request.query, top_k=request.top_k)
    
    # 1. Vectorization
    query_vector = get_embedding(request.query)
    
    # 2. Parallel Search
    search_limit = max(50, request.top_k * 2)
    
    vector_results = perform_vector_search(query_vector, search_limit)
    keyword_results = perform_keyword_search(request.query, search_limit)
    
    # 3. RRF Fusion
    fused_results = rrf_fusion(vector_results, keyword_results)
    
    # 4. Format Output
    response_items = []
    for res in fused_results[:request.top_k]:
        item = res["item"]
        payload = item.payload or {}
        
        metadata = payload.copy()
        text_content = metadata.pop("text", "")
        
        response_items.append(SearchResult(
            text=str(text_content),
            score=float(res["score"]),
            metadata=metadata
        ))
        
    logger.info("search_completed", results_returned=len(response_items))
    return SearchResponse(results=response_items)

@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
