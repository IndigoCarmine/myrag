# MyRAG System

A local RAG (Retrieval-Augmented Generation) system built with microservices architecture.

## Architecture

The system consists of the following services:

- **Gateway Service** (Port 8000): Main entry point for chat functionality
- **Retrieval Service** (Port 8001): Handles search and retrieval logic
- **Ingestion Service** (Port 8002): Processes and indexes PDF documents
- **Embedding Service** (Port 8003): Converts text to vector embeddings
- **Frontend Service** (Port 5173): Web-based user interface
- **CLI Tester Service**: Command-line interface for testing

### Supporting Infrastructure

- **Qdrant** (Port 6333): Vector database
- **Ollama** (Port 11434): LLM inference
- **Grobid** (Port 8070): PDF metadata extraction

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- uv (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd myrag
```

2. Install Python dependencies:
```bash
uv sync
```

3. Install Frontend dependencies:
```bash
cd services/frontend
npm install
cd ../..
```

4. Start infrastructure services:
```bash
uv run poe start-infra
```

### Running the System

Start all services:
```bash
uv run poe dev
```

This will start:
- Gateway Service on http://localhost:8000
- Retrieval Service on http://localhost:8001
- Ingestion Service on http://localhost:8002
- Embedding Service on http://localhost:8003
- Frontend on http://localhost:5173

### Using the Frontend

1. Open http://localhost:5173 in your browser
2. Go to "Manage Documents" tab to upload PDF files
3. Go to "Chat" tab to ask questions about your documents

### Using the CLI Tester

The CLI Tester provides a command-line interface to test the system without using the web frontend.

Start the CLI Tester:
```bash
uv run poe test-cli
```

Available commands:
- `chat` - Send a chat message to the Gateway Service
- `upload` - Upload a PDF document to the Ingestion Service
- `health` - Check service health status
- `history` - View conversation history
- `help` - Show available commands
- `quit` - Exit the tester

Example session:
```
> health
✓ Gateway Service (Port 8000): OK
✓ Ingestion Service (Port 8002): OK

> chat
Enter your question: What is machine learning?

Answer:
Machine learning is a subset of artificial intelligence...

📚 Sources (2):
[1] Introduction to Machine Learning
    Authors: John Doe, Jane Smith
    DOI: 10.1234/5678
    ...

> quit
ℹ Goodbye!
```

**Quick Demo:**

Run an automated demo to see the CLI Tester in action:
```bash
uv run poe demo-cli
```

This will automatically:
- Check service health
- Send test queries
- Display conversation history
- Show summary statistics

For more details, see [CLI Tester README](services/cli_tester/README.md).

## Service Details

### Gateway Service

Orchestrates the RAG workflow by coordinating with the Retrieval Service and LLM.

**Endpoints:**
- `POST /chat` - Process user queries and return answers with citations
- `GET /health` - Health check

### Retrieval Service

Handles search logic with hybrid search (vector + keyword) and reranking.

**Endpoints:**
- `POST /search` - Search for relevant document chunks
- `GET /health` - Health check

### Ingestion Service

Processes PDF documents, extracts metadata, chunks content, and stores in vector database.

**Endpoints:**
- `POST /ingest` - Upload and process PDF documents
- `GET /health` - Health check

### Embedding Service

Converts text to vector embeddings using sentence-transformers.

**Endpoints:**
- `POST /embed` - Generate embeddings for text
- `GET /health` - Health check

## Development

### Project Structure

```
myrag/
├── services/
│   ├── gateway/          # Gateway Service
│   ├── retrieval/        # Retrieval Service
│   ├── ingestion/        # Ingestion Service
│   ├── embedding/        # Embedding Service
│   ├── frontend/         # Frontend Service (React)
│   └── cli_tester/       # CLI Tester Service
├── test/                 # Test files
├── pyproject.toml        # Python project configuration
├── docker-compose.yml    # Infrastructure services
└── spec.md              # System specification
```

### Running Individual Services

```bash
# Gateway Service
uv run poe start-gateway

# Retrieval Service
uv run poe start-retrieval

# Ingestion Service
uv run poe start-ingestion

# Embedding Service
uv run poe start-embedding

# Frontend
uv run poe start-frontend

# CLI Tester
uv run poe test-cli
```

### Running Tests

```bash
uv run pytest
```

## Configuration

Environment variables can be used to configure service URLs:

- `GATEWAY_URL` - Gateway Service URL (default: http://localhost:8000)
- `RETRIEVAL_URL` - Retrieval Service URL (default: http://localhost:8001)
- `INGESTION_URL` - Ingestion Service URL (default: http://localhost:8002)
- `EMBEDDING_URL` - Embedding Service URL (default: http://localhost:8003)
- `QDRANT_URL` - Qdrant URL (default: http://localhost:6333)
- `OLLAMA_URL` - Ollama URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Ollama model name (default: llama3)
- `GROBID_URL` - Grobid URL (default: http://localhost:8070)

## Troubleshooting

### Services Not Starting

1. Check that all required ports are available
2. Ensure Docker is running for infrastructure services
3. Verify Python and Node.js versions

### Chat Returns Empty Responses

1. Make sure documents have been uploaded and indexed
2. Verify Ollama is running with the correct model
3. Check that all services are healthy using the CLI Tester's `health` command

### Document Upload Fails

1. Ensure the file is a valid PDF
2. Check that Grobid is running
3. Verify Qdrant is accessible

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
