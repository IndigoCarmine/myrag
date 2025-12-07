# Embedding Service Interface

## Overview
The Embedding Service provides a dedicated API for converting text into vector representations. It hosts the embedding model (e.g., `multilingual-e5-large`) in memory to ensure low latency and efficient resource usage.

## Endpoints

### 1. Generate Embeddings
*   **URL**: `/embed`
*   **Method**: `POST`
*   **Description**: Converts input text into vectors.
*   **Request Body**:
    ```json
    {
      "text": ["Hello world", "Another sentence"]
    }
    ```
    *   Note: Accepts a list of strings for batch processing.
*   **Response**:
    ```json
    {
      "vectors": [
        [0.1, 0.2, ...],
        [0.3, 0.4, ...]
      ],
      "dimension": 1024
    }
    ```

### 2. Health Check
*   **URL**: `/health`
*   **Method**: `GET`
*   **Response**: `{"status": "ok", "model": "intfloat/multilingual-e5-large"}`
