# Gateway Service Interface

## Overview
The Gateway Service acts as the main entry point for the frontend/user. It orchestrates the RAG workflow by coordinating with the Retrieval Service and the LLM (Ollama).

## Endpoints

### 1. Chat
*   **URL**: `/chat`
*   **Method**: `POST`
*   **Description**: Processes a user query and returns a generated answer with citations.
*   **Request Body**:
    ```json
    {
      "query": "What is the performance of the proposed method?",
      "history": [] // Optional: Conversation history
    }
    ```
*   **Response**:
    ```json
    {
      "answer": "The method achieves 95% accuracy...",
      "citations": [
        "doi:10.1234/5678",
        "doi:10.9876/5432"
      ]
    }
    ```

### 2. Health Check
*   **URL**: `/health`
*   **Method**: `GET`
*   **Response**: `{"status": "ok"}`
