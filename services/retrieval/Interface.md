# Retrieval Service Interface

## Overview
The Retrieval Service executes the search logic. It performs Hybrid Search (Keyword + Vector) by querying Qdrant and merging results using Reciprocal Rank Fusion (RRF).

## Endpoints

### 1. Search
*   **URL**: `/search`
*   **Method**: `POST`
*   **Description**: Retrieves relevant document chunks for a given query.
*   **Request Body**:
    ```json
    {
      "query": "machine learning optimization",
      "top_k": 10
    }
    ```
*   **Response**:
    ```json
    {
      "results": [
        {
          "text": "Optimization is crucial...",
          "score": 0.85,
          "metadata": {
            "doi": "10.1234/5678",
            "page": 3
          }
        },
        ...
      ]
    }
    ```

### 2. Health Check
*   **URL**: `/health`
*   **Method**: `GET`
*   **Response**: `{"status": "ok"}`
