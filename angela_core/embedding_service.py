#!/usr/bin/env python3
"""
Angela Core Embedding Service
ใช้ Ollama nomic-embed-text (768 dimensions)
Simple, lightweight embedding service สำหรับ Angela
"""

import httpx
import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)


class AngelaEmbeddingService:
    """Simple embedding service for Angela using Ollama"""

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        dimensions: int = 768
    ):
        self.ollama_base_url = ollama_base_url
        self.model = model
        self.dimensions = dimensions
        logger.info(f"🧠 Initialized Angela Embedding Service: {model} ({dimensions}d)")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using Ollama

        Args:
            text: Text to embed

        Returns:
            List[float]: Embedding vector
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                embedding = data["embedding"]

                # Validate dimensions
                if len(embedding) != self.dimensions:
                    logger.warning(
                        f"⚠️ Embedding dimensions mismatch: "
                        f"expected {self.dimensions}, got {len(embedding)}"
                    )

                return embedding

        except httpx.HTTPError as e:
            logger.error(f"❌ Ollama HTTP error: {str(e)}")
            raise Exception(f"Ollama HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {str(e)}")
            raise Exception(f"Embedding generation failed: {str(e)}")

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_delay: float = 0.15
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed
            batch_delay: Delay between requests (seconds)

        Returns:
            List[List[float]]: List of embedding vectors
        """
        embeddings = []
        total = len(texts)

        logger.info(f"🔄 Generating {total} embeddings...")

        async with httpx.AsyncClient(timeout=120.0) as client:
            for i, text in enumerate(texts):
                try:
                    # Clean text
                    cleaned_text = text.strip()
                    if not cleaned_text:
                        # Use zero vector for empty text
                        logger.warning(f"⚠️ Empty text at index {i}, using zero vector")
                        embeddings.append([0.0] * self.dimensions)
                        continue

                    # Generate embedding
                    response = await client.post(
                        f"{self.ollama_base_url}/api/embeddings",
                        json={
                            "model": self.model,
                            "prompt": cleaned_text[:8000]  # Truncate if too long
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    embeddings.append(data["embedding"])

                    # Progress indicator
                    if (i + 1) % 10 == 0 or (i + 1) == total:
                        logger.info(f"  ✓ Generated {i + 1}/{total} embeddings")

                    # Delay to avoid overwhelming Ollama
                    if i < total - 1:
                        await asyncio.sleep(batch_delay)

                except Exception as e:
                    logger.error(f"❌ Failed at index {i}: {str(e)}")
                    # Use zero vector for failed embedding
                    embeddings.append([0.0] * self.dimensions)

        logger.info(f"✅ Batch embedding complete: {len(embeddings)}/{total} successful")
        return embeddings


# Global instance
embedding = AngelaEmbeddingService(
    ollama_base_url="http://localhost:11434",
    model="nomic-embed-text",
    dimensions=768
)


# Backward compatibility function for older code
async def generate_embedding(text: str) -> List[float]:
    """
    Backward compatibility function
    Calls the global embedding instance's generate_embedding method
    """
    return await embedding.generate_embedding(text)
