"""
Pythia — Embedding Service (Ollama nomic-embed-text)
Free local embeddings for RAG vector search.
"""
from typing import Optional

import httpx

from config import PythiaConfig


class EmbeddingService:
    """Generate vector embeddings via Ollama."""

    async def embed(self, text: str) -> Optional[list[float]]:
        """Embed a single text. Returns None on failure."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{PythiaConfig.OLLAMA_URL}/api/embed",
                    json={
                        "model": PythiaConfig.EMBEDDING_MODEL,
                        "input": text,
                    },
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
                embeddings = data.get("embeddings", [])
                if embeddings and len(embeddings) > 0:
                    return embeddings[0]
                return None
        except Exception:
            return None

    async def embed_batch(self, texts: list[str]) -> list[Optional[list[float]]]:
        """Embed multiple texts. Returns list of embeddings (None for failures)."""
        results: list[Optional[list[float]]] = []
        for text in texts:
            emb = await self.embed(text)
            results.append(emb)
        return results

    async def get_dimension(self) -> int:
        """Probe embedding dimension by embedding a test string."""
        emb = await self.embed("test")
        return len(emb) if emb else 0


# Singleton
embedding_service = EmbeddingService()
