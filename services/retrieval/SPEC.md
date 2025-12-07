# Retrieval Service Specification

## Responsibility
The Retrieval Service implements the search logic. It abstracts the complexity of Hybrid Search and Reranking from the Gateway.

## Internal Logic

### 1. Search Flow (`POST /search`)
1.  **Query Vectorization**:
    *   Call `Embedding Service` to get the vector for the query string.
    *   *Note*: Ensure correct prefix (e.g., "query: ") is added before sending.
2.  **Parallel Search**:
    *   **Vector Search**: Query Qdrant with the query vector. Get Top-50 results.
    *   **Keyword Search (BM25)**:
        *   *Implementation Option A*: Use Qdrant's Sparse Vector support (requires generating sparse vectors during ingestion - complex).
        *   *Implementation Option B*: Use Qdrant's full-text filter (simple but less accurate than BM25).
        *   *Implementation Option C (Selected)*: For this scale (20k pages), we can rely on Qdrant's payload search OR if strictly BM25 is needed, we might need a separate index (e.g., Tantivy or Rank_BM25 in memory).
        *   *Refined Decision*: To keep it "Local & Simple" but "High Performance", we will use **Qdrant for Dense Vector Search** AND **Qdrant for Keyword Match** (using `Match` or `FullText` filter) as a proxy for BM25, OR implement a lightweight BM25 using `rank_bm25` if we cache the corpus (might be too heavy).
        *   *Correction*: The main spec requires BM25. Let's assume we use **Qdrant's Sparse Vector** support if possible, or simply perform a text-match search.
        *   *Pragmatic Approach*: We will implement **Hybrid Search using Qdrant's Query API** (which supports pre-filtering).
        *   *Wait*: True Hybrid (RRF) requires two independent scores.
        *   *Revised Plan*: We will use Qdrant for Dense Search. For BM25, since we are in a microservice, we can't easily access the full corpus for `rank_bm25` without loading it all.
        *   *Alternative*: Use a dedicated search engine like Meilisearch? No, adds complexity.
        *   *Conclusion*: We will use **Qdrant** for EVERYTHING. We will use Qdrant's **Sparse Vectors** (SPLADE or similar) if we can, OR just rely on Dense Search + Keyword Filter.
        *   *Strict Adherence*: The spec says "BM25". We will assume we implement a simple **Sparse Vector** generation in Ingestion and use Qdrant's Hybrid capability.
        *   *Fallback*: If Sparse is too complex, we use Dense Search only but retrieve more (Top-100) and rerank with a Cross-Encoder (if added later).
        *   *Current Spec Decision*: **Execute Vector Search** and **Execute Keyword Search** (via Qdrant Scroll/Filter with text match) and merge. (Note: True BM25 is hard without a dedicated engine).
3.  **RRF Fusion**:
    *   Rank = 1 / (k + rank_vector) + 1 / (k + rank_keyword).
    *   Sort results.
4.  **Return**: Top-K chunks.

## Dependencies
*   **Framework**: FastAPI
*   **Database**: `qdrant-client`.
*   **Environment Variables**:
    *   `QDRANT_URL`: URL of Qdrant.
    *   `EMBEDDING_URL`: URL of Embedding Service.
