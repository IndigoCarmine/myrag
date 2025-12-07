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
        {
          "doi": "10.1234/5678",
          "pages": [3, 5, 7],
          "title": "A Novel Approach to Machine Learning",
          "url": "https://doi.org/10.1234/5678",
          "pdf_url": "https://example.com/paper.pdf",
          "authors": ["John Doe", "Jane Smith"],
          "journal": "Journal of Machine Learning Research",
          "published_date": "2023-05-15"
        },
        {
          "doi": "10.9876/5432",
          "pages": [12],
          "title": "Deep Learning Fundamentals",
          "url": "https://doi.org/10.9876/5432",
          "pdf_url": null,
          "authors": ["Alice Johnson"],
          "journal": "Neural Networks",
          "published_date": "2022-11-20"
        }
      ]
    }
    ```
    
    **Note**: The `url` field always contains the DOI resolver URL, which redirects to the publisher's page. The `pdf_url` may be `null` if not available from the publisher.

### 2. Health Check
*   **URL**: `/health`
*   **Method**: `GET`
*   **Response**: `{"status": "ok"}`
