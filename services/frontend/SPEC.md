# Frontend Service Specification

## Responsibility
The Frontend Service provides the graphical user interface for the RAG system. It allows users to chat with the system (via Gateway) and upload documents (via Ingestion).

## Features

### 1. Chat Interface
*   **Endpoint**: Connects to `Gateway Service` at `POST /chat`.
*   **Features**:
    *   Markdown rendering of bot responses.
    *   Display of citations/sources.
    *   Chat history preservation (session-based).
    *   Loading states and error handling.

### 2. Document Management
*   **Endpoint**: Connects to `Ingestion Service` at `POST /ingest`.
*   **Features**:
    *   Drag-and-drop file upload.
    *   Progress tracking.
    *   Status reporting (Success/Failure).

## Tech Stack
*   **Framework**: React (Vite)
*   **Styling**: Vanilla CSS (Glassmorphism design system)
*   **State Management**: React Hooks (`useState`)

## Configuration
*   **Gateway URL**: Defaults to `http://localhost:8000`
*   **Ingestion URL**: Defaults to `http://localhost:8001`
*   *Note*: Ensure CORS is enabled on backend services to allow requests from the frontend (port 5173 by default).
