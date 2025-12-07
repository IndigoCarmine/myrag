# CLI Tester Service

## Overview

The CLI Tester Service is an interactive command-line tool that simulates the same interactions as the Frontend application. It allows you to test the RAG system's functionality directly from the terminal without needing to use the web interface.

## Features

- **Chat Testing**: Send queries to the Gateway Service and view formatted responses with citations
- **Document Upload**: Upload PDF documents to the Ingestion Service
- **Service Health Check**: Verify that all required services are running
- **Conversation History**: View past queries and responses
- **Color-coded Output**: Easy-to-read terminal output with ANSI colors

## Prerequisites

Make sure the following services are running:
- Gateway Service (Port 8000)
- Ingestion Service (Port 8002)
- Retrieval Service (Port 8001)
- Embedding Service (Port 8003)
- Qdrant (Port 6333)
- Ollama (Port 11434)

You can start all services with:
```bash
uv run poe dev
```

## Usage

### Starting the CLI Tester

```bash
uv run poe test-cli
```

Or directly:
```bash
uv run python -m services.cli_tester.main
```

### Available Commands

Once the CLI tester is running, you can use the following commands:

#### `chat`
Send a chat message to the Gateway Service.

Example:
```
> chat
Enter your question: What is the performance of the proposed method?
```

The response will include:
- The generated answer from the LLM
- Citations with full metadata (title, authors, journal, DOI, pages, PDF URL)

#### `upload`
Upload a PDF document to the Ingestion Service.

Example:
```
> upload
Enter PDF file path: /path/to/document.pdf
```

The tool will:
- Validate the file exists and is a PDF
- Upload it to the Ingestion Service
- Display processing status and metadata

#### `health`
Check the health status of all required services.

Example:
```
> health
```

#### `history`
View your conversation history.

Example:
```
> history
```

#### `help`
Display the list of available commands.

Example:
```
> help
```

#### `quit` or `exit`
Exit the CLI tester.

Example:
```
> quit
```

## Example Session

```
============================================================
              RAG System CLI Tester
============================================================

Welcome to the RAG System CLI Tester!
This tool simulates the same interactions as the Frontend.

============================================================
                Service Health Check
============================================================

✓ Gateway Service (Port 8000): OK
✓ Ingestion Service (Port 8002): OK

Available Commands:
  chat     - Send a chat message
  upload   - Upload a PDF document
  history  - View conversation history
  health   - Check service health
  help     - Show this menu
  quit     - Exit the tester

> chat
Enter your question: What are the main findings?

============================================================
                    Chat Request
============================================================

ℹ Query: What are the main findings?

Answer:
Based on the provided context, the main findings are...

📚 Sources (2):

[1] A Novel Approach to Machine Learning
    Authors: John Doe, Jane Smith
    Journal: Journal of Machine Learning Research
    Published: 2023-05-15
    DOI: 10.1234/5678
    URL: https://doi.org/10.1234/5678
    Pages: 3, 5, 7
    PDF: https://example.com/paper.pdf

[2] Deep Learning Fundamentals
    Authors: Alice Johnson
    Journal: Neural Networks
    Published: 2022-11-20
    DOI: 10.9876/5432
    URL: https://doi.org/10.9876/5432
    Pages: 12

✓ Chat request completed successfully

> quit
ℹ Goodbye!
```

## Environment Variables

You can customize the service URLs using environment variables:

- `GATEWAY_URL`: Gateway Service URL (default: `http://localhost:8000`)
- `INGESTION_URL`: Ingestion Service URL (default: `http://localhost:8002`)

Example:
```bash
GATEWAY_URL=http://localhost:9000 uv run poe test-cli
```

## Comparison with Frontend

The CLI Tester performs the exact same API calls as the Frontend:

| Feature | Frontend | CLI Tester |
|---------|----------|------------|
| Chat | POST to `/chat` | POST to `/chat` |
| Upload | POST to `/ingest` | POST to `/ingest` |
| Health Check | GET `/health` | GET `/health` |
| Response Format | JSON | Formatted terminal output |
| Citations | Displayed in UI | Displayed in terminal |

## Troubleshooting

### Services Not Reachable

If you see errors like "Gateway Service (Port 8000): Not reachable", make sure:
1. All services are running (`uv run poe dev`)
2. The ports are not blocked by firewall
3. No other applications are using the same ports

### Upload Fails

If document upload fails:
1. Check that the file path is correct
2. Ensure the file is a valid PDF
3. Verify the Ingestion Service is running
4. Check that Grobid and Qdrant are accessible

### Chat Returns Empty Response

If chat returns empty or error responses:
1. Verify Ollama is running and has the required model
2. Check that documents have been uploaded and indexed
3. Ensure the Retrieval Service can connect to Qdrant
4. Verify the Embedding Service is running

## Development

The CLI Tester is located in `services/cli_tester/` and consists of:

- `main.py`: Main CLI application with interactive commands
- `__init__.py`: Package initialization

To modify the CLI Tester, edit these files and restart the application.
