# Local RAG Specification (Markdown)

## Architecture Overview (Microservices)

The system is divided into five independent services communicating via HTTP/REST.

```mermaid
graph TD
    User[User] --> Frontend[Frontend Service]
    Frontend --> Gateway
    Frontend --> Ingestion
    Gateway --> Retrieval
    Gateway --> Ollama[Ollama (LLM)]
    
    subgraph "Services"
        Frontend[Frontend Service]
        Gateway[Gateway Service]
        Ingestion[Ingestion Service]
        Embedding[Embedding Service]
        Retrieval[Retrieval Service]
    end

    subgraph "Infrastructure"
        Grobid[Grobid Server]
        Qdrant[Qdrant Vector DB]
        Ollama
    end

    Ingestion --> Grobid
    Ingestion --> Embedding
    Ingestion --> Qdrant
    
    Retrieval --> Embedding
    Retrieval --> Qdrant
```

## Services

### 1. Frontend Service (`/services/frontend`)
*   **Role**: User Interface.
*   **Responsibility**:
    *   Provide a web interface for users to interact with the system.
    *   Chat interface to communicate with Gateway Service.
    *   Document upload interface to communicate with Ingestion Service.
    *   Visualize citations and source documents.

### 2. Gateway Service (`/services/gateway`)
*   **Role**: API Gateway & Orchestrator.
*   **Responsibility**:
    *   Handle user chat requests.
    *   Call Retrieval Service to get context.
    *   Construct prompt and call Ollama.
    *   Return answer with citations.

### 3. Ingestion Service (`/services/ingestion`)
*   **Role**: Document Processor.
*   **Responsibility**:
    *   Accept PDF uploads.
    *   Parse PDF using Grobid (metadata) and PyMuPDF (text).
    *   Chunk text.
    *   Request vectors from Embedding Service.
    *   Upsert data to Qdrant.

### 4. Embedding Service (`/services/embedding`)
*   **Role**: Vector Provider.
*   **Responsibility**:
    *   Load the embedding model (e.g., `multilingual-e5-large`) into memory.
    *   Provide an API to convert text to vectors.
    *   GPU acceleration if available.

### 5. Retrieval Service (`/services/retrieval`)
*   **Role**: Search Engine.
*   **Responsibility**:
    *   Accept search queries.
    *   Request query vector from Embedding Service.
    *   Execute Hybrid Search (BM25 + Vector) on Qdrant.
    *   Perform RRF fusion.
    *   Return ranked chunks.

## Infrastructure

*   **Qdrant**: Vector Database (Port 6333)
*   **Grobid**: PDF Parsing Server (Port 8070)
*   **Ollama**: LLM Server (Port 11434)

## Requirements

*   **Communication**: HTTP (FastAPI)
*   **Containerization**: Docker & Docker Compose
*   **Environment**: Local execution

## Data Volume Estimate

*   Pages: ~20,000
*   Chunks: ~13,000
*   Embedding storage: ~200–300 MB

## Deliverables

*   `spec.md`: System Architecture
*   `services/*/Interface.md`: API Definitions
*   Implementation of services

