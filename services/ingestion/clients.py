import os
import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models
from .logger import setup_logger

logger = setup_logger("ingestion_clients")

# Configuration
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://localhost:8003")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "papers"


class EmbeddingClient:
    def __init__(self, base_url: str = EMBEDDING_URL):
        self.base_url = base_url

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        try:
            response = requests.post(f"{self.base_url}/embed", json={"text": texts})
            response.raise_for_status()
            return response.json()["vectors"]
        except Exception as e:
            logger.error(f"Error fetching embeddings: {e}")
            raise


class QdrantHandler:
    def __init__(self, url: str = QDRANT_URL):
        self.client = QdrantClient(url=url)
        self.collection_name = COLLECTION_NAME
        self._ensure_collection()

    def _ensure_collection(self):
        # Check if collection exists, if not create it
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            # We don't know the dimension yet strictly speaking,
            # but usually e5-large is 1024.
            # Ideally we check embedding service or assume 1024.
            # I will assume 1024 as per the Embedding Service Interface example.
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1024, distance=models.Distance.COSINE
                ),
            )

    def upsert_chunks(self, chunks: list, vectors: list[list[float]]):
        points = []
        for chunk, vector in zip(chunks, vectors):
            points.append(
                models.PointStruct(
                    id=chunk["id"],
                    vector=vector,
                    payload={"text": chunk["text"], **chunk["metadata"]},
                )
            )

        # Batch upsert
        self.client.upsert(collection_name=self.collection_name, points=points)
