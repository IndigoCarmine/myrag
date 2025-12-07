# Gateway Service Specification

## Responsibility
The Gateway Service is the orchestrator of the RAG pipeline. It exposes the public API to the frontend and coordinates interactions between the Retrieval Service and the LLM (Ollama).

## Internal Logic

### 1. Chat Flow (`POST /chat`)
1.  **Input Validation**: Validate `query` string.
2.  **Context Retrieval**:
    *   Call `Retrieval Service` (`POST /search`) with the user's query.
    *   Receive a list of relevant chunks with metadata (DOI, text).
3.  **Prompt Construction**:
    *   Format the retrieved chunks into a context block.
    *   Construct a system prompt instructing the LLM to answer based *only* on the provided context and to cite DOIs.
    *   Example Prompt Template:
        ```text
        You are an academic assistant. Answer the question using ONLY the following context.
        If the answer is not in the context, say "I don't know".
        Always cite the DOI for every statement.

        Context:
        [1] (DOI: 10.xxx) ...text...
        [2] (DOI: 10.yyy) ...text...

        Question: {query}
        ```
4.  **LLM Inference**:
    *   Call Ollama API (`POST /api/generate` or `/api/chat`).
    *   Stream the response or wait for completion (depending on frontend requirements, currently assume blocking for simplicity).
5.  **Response Formatting**:
    *   Extract the answer text.
    *   Parse/Verify citations (optional, but good for robustness).
    *   Return JSON response.

## Dependencies
*   **Framework**: FastAPI
*   **HTTP Client**: `httpx` (Async)
*   **Environment Variables**:
    *   `RETRIEVAL_URL`: URL of the Retrieval Service.
    *   `OLLAMA_URL`: URL of the Ollama instance.

## Error Handling
*   If Retrieval fails: Return error or try to answer without context (with warning).
*   If Ollama fails: Return "Service unavailable".
