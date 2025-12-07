# Frontend Service Interface

## Overview
The Frontend Service is a Single Page Application (SPA) that serves as the visual interface for the RAG system. It is accessible via a web browser by the end-user.

## Access Points

### 1. Web Application
*   **URL**: `/`
*   **Method**: `GET` (Browser Navigation)
*   **Description**: Loads the main user interface. The UI includes:
    *   **Chat Tab**: Interface for interacting with the RAG chatbot (communicates with Gateway Service).
    *   **Manage Documents Tab**: Interface for uploading PDF documents (communicates with Ingestion Service).
*   **Response**: HTML/JS Application Bundle.

## Network Configuration
*   **Port**: 5173 (Development) / 80 (Production build served via Nginx/Docker)
*   **Protocol**: HTTP/HTTPS
