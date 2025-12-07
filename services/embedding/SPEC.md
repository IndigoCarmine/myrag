# Embedding Service Specification

## Responsibility
The Embedding Service is a specialized worker that hosts the transformer model. Its sole purpose is to compute embeddings for text. It isolates the heavy ML dependencies (PyTorch/Transformers) from the rest of the system.

## Internal Logic

### 1. Initialization
*   Load the specified model (e.g., `intfloat/multilingual-e5-large`) using `sentence-transformers`.
*   Move model to GPU if available (`cuda`), otherwise CPU.
*   *Optimization*: Enable `torch.compile` or quantization if supported and beneficial.

### 2. Embedding Flow (`POST /embed`)
1.  **Input**: List of strings `["text1", "text2", ...]`.
2.  **Preprocessing**: Add model-specific prefixes if required (e.g., E5 requires "query: " or "passage: " prefixes).
    *   *Policy*: The caller should probably handle prefixes, OR this service exposes specific endpoints like `/embed/query` and `/embed/document`.
    *   *Decision*: For simplicity, assume raw text input, but document in API that caller handles prefixes if needed, OR auto-detect. Let's stick to **Caller handles prefixes** for maximum flexibility.
3.  **Inference**:
    *   Run `model.encode(texts, batch_size=32, convert_to_numpy=True)`.
4.  **Output**: Return list of float arrays.

## Dependencies
*   **Framework**: FastAPI
*   **ML Library**: `sentence-transformers`, `torch`.
*   **Hardware**: NVIDIA GPU (Optional but recommended).

## Performance Goals
*   Keep model in memory (warm).
*   Handle batch requests efficiently.
