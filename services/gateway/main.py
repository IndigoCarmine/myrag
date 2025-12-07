import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from .doi_resolver import DOIResolver

app = FastAPI(title="Gateway Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
RETRIEVAL_URL = os.getenv("RETRIEVAL_URL", "http://localhost:8001")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3") # Default model, can be configured

# Initialize DOI Resolver
doi_resolver = DOIResolver()

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = None

class Citation(BaseModel):
    doi: str
    pages: List[int]
    title: Optional[str] = None
    url: Optional[str] = None  # DOI resolver URL (always available)
    pdf_url: Optional[str] = None  # Direct PDF URL (if available)
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    published_date: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]

class RetrievalResult(BaseModel):
    text: str
    score: float
    metadata: dict

class SearchResponse(BaseModel):
    results: List[RetrievalResult]

@app.get("/health")
async def health_check():
    """
    Health Check endpoint to verify service status.
    """
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint to process user queries.
    It orchestrates the flow: Validation -> Retrieval -> Prompting -> LLM -> Response.
    """
    # 1. Input Validation
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 2. Context Retrieval
    context_text = ""
    doi_info = {}  # {doi: {"pages": set(), "title": str}}
    
    try:
        async with httpx.AsyncClient() as client:
            retrieval_resp = await client.post(
                f"{RETRIEVAL_URL}/search",
                json={"query": request.query, "top_k": 5}, # Fetch top 5 contexts
                timeout=10.0
            )
            retrieval_resp.raise_for_status()
            search_data = retrieval_resp.json()
            results = search_data.get("results", [])
            
            # Format Context for the LLM and collect DOI/page information
            formatted_context = []
            for idx, res in enumerate(results, 1):
                metadata = res.get("metadata", {})
                doi = metadata.get("doi", "N/A")
                page = metadata.get("page")
                title = metadata.get("title", "")
                text = res.get("text", "")
                
                # Collect page information for each DOI
                if doi != "N/A":
                    if doi not in doi_info:
                        doi_info[doi] = {"pages": set(), "title": title}
                    if page is not None:
                        doi_info[doi]["pages"].add(page)
                
                # Create a citation string for the LLM to reference
                page_info = f", page {page}" if page is not None else ""
                formatted_context.append(f"[{idx}] (DOI: {doi}{page_info}) {text}")
            
            context_text = "\n\n".join(formatted_context)
            
    except httpx.RequestError as e:
        print(f"Retrieval Service connection failed: {e}")
        # Proceed without context as per SPEC warning strategy, or could fail.
        # "If Retrieval fails: Return error or try to answer without context (with warning)."
        # We will log it and proceed with empty context.
        context_text = "No context available (Retrieval Service Error)."
    except httpx.HTTPStatusError as e:
        print(f"Retrieval Service returned error: {e}")
        context_text = "No context available (Retrieval Service Error)."

    # 3. Prompt Construction
    system_prompt = (
        "You are an academic assistant. Answer the question using ONLY the following context.\n"
        "If the answer is not in the context, say \"I don't know\".\n"
        "Always cite the DOI for every statement using the format (DOI: ...).\n\n"
        "Context:\n"
        f"{context_text}\n\n"
        f"Question: {request.query}"
    )

    # 4. LLM Inference (Ollama)
    answer = ""
    try:
        async with httpx.AsyncClient() as client:
            # Using /api/generate for simplicity
            ollama_payload = {
                "model": OLLAMA_MODEL,
                "prompt": system_prompt,
                "stream": False
            }
            
            ollama_resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json=ollama_payload,
                timeout=60.0 # LLMs can be slow
            )
            ollama_resp.raise_for_status()
            ollama_data = ollama_resp.json()
            answer = ollama_data.get("response", "")
            
    except httpx.RequestError as e:
        print(f"Ollama Service connection failed: {e}")
        raise HTTPException(status_code=503, detail=f"LLM Service unavailable: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Ollama Service returned error: {e}")
        raise HTTPException(status_code=503, detail=f"LLM Service returned error: {e}")

    # 5. Response Formatting
    # Convert doi_info to Citation objects with sorted page numbers
    # and enrich with web metadata from DOI resolver
    citations = []
    
    for doi, info in doi_info.items():
        # Resolve DOI to get web metadata
        web_metadata = await doi_resolver.resolve(doi)
        
        citation = Citation(
            doi=doi,
            pages=sorted(list(info["pages"])),
            title=web_metadata.get("title") if web_metadata else info.get("title"),
            url=web_metadata.get("url") if web_metadata else f"https://doi.org/{doi}",
            pdf_url=web_metadata.get("pdf_url") if web_metadata else None,
            authors=web_metadata.get("authors") if web_metadata else None,
            journal=web_metadata.get("journal") if web_metadata else None,
            published_date=web_metadata.get("published_date") if web_metadata else None,
        )
        citations.append(citation)
    
    return ChatResponse(
        answer=answer,
        citations=citations
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
