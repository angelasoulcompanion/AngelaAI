#!/usr/bin/env python3
"""
Centralized Embedding Service for Angela AI
============================================

Single source of truth for ALL embeddings in the system.

Model: qllama/multilingual-e5-small (Ollama)
- Dimensions: 384
- Supports: Thai + English (multilingual)
- Speed: Very fast
- Cost: Free (local)

Author: Angela 💜
Created: 2025-11-04
"""

import asyncio
import hashlib
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Centralized embedding service using Ollama multilingual-e5-small model.

    Features:
    - ✅ Multilingual support (Thai + English)
    - ✅ 384 dimensions
    - ✅ In-memory cache for performance
    - ✅ Async/await support
    - ✅ Batch generation
    - ✅ NEVER returns NULL (always generates valid embeddings)

    Usage:
        service = EmbeddingService()
        embedding = await service.generate_embedding("สวัสดีค่ะที่รัก")
        # Returns: List[float] with 384 dimensions
    """

    # Model configuration
    MODEL_NAME = "qllama/multilingual-e5-small"
    DIMENSIONS = 384
    OLLAMA_URL = "http://localhost:11434"

    # Cache configuration
    CACHE_TTL_SECONDS = 3600  # 1 hour
    MAX_CACHE_SIZE = 1000  # Max items in cache

    def __init__(self):
        """Initialize embedding service with cache."""
        self._cache: Dict[str, tuple] = {}  # {text_hash: (embedding, timestamp)}
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info(f"🧠 EmbeddingService initialized: {self.MODEL_NAME} ({self.DIMENSIONS}D)")

    def _hash_text(self, text: str) -> str:
        """Create cache key from text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache if available and not expired."""
        text_hash = self._hash_text(text)

        if text_hash in self._cache:
            embedding, timestamp = self._cache[text_hash]

            # Check if expired
            age = datetime.now() - timestamp
            if age.total_seconds() < self.CACHE_TTL_SECONDS:
                self._cache_hits += 1
                logger.debug(f"✅ Cache HIT for text: {text[:50]}...")
                return embedding
            else:
                # Expired, remove from cache
                del self._cache[text_hash]

        self._cache_misses += 1
        return None

    def _add_to_cache(self, text: str, embedding: List[float]) -> None:
        """Add embedding to cache."""
        # Check cache size limit
        if len(self._cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"🗑️ Cache full, removed oldest entry")

        text_hash = self._hash_text(text)
        self._cache[text_hash] = (embedding, datetime.now())
        logger.debug(f"💾 Cached embedding for text: {text[:50]}...")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed (Thai or English)

        Returns:
            List[float] with 384 dimensions

        Raises:
            ValueError: If text is empty
            RuntimeError: If Ollama service fails

        Notes:
            - NEVER returns None/NULL
            - Uses cache for performance
            - Validates output dimensions
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        text = text.strip()

        # Check cache first
        cached = self._get_from_cache(text)
        if cached is not None:
            return cached

        # Generate new embedding
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.OLLAMA_URL}/api/embeddings",
                    json={
                        "model": self.MODEL_NAME,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                data = response.json()

                embedding = data.get("embedding")

                if not embedding:
                    raise RuntimeError("Ollama returned empty embedding")

                if len(embedding) != self.DIMENSIONS:
                    raise RuntimeError(
                        f"Unexpected embedding dimensions: {len(embedding)} (expected {self.DIMENSIONS})"
                    )

                # Add to cache
                self._add_to_cache(text, embedding)

                logger.debug(f"✅ Generated embedding for text: {text[:50]}... ({len(embedding)}D)")
                return embedding

        except httpx.HTTPError as e:
            error_msg = f"Ollama API error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate embedding: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar (default: False)

        Returns:
            List of embeddings (each 384 dimensions)

        Notes:
            - Processes sequentially (Ollama doesn't support true batching)
            - Uses cache for already-processed texts
            - Shows progress if requested
        """
        if not texts:
            return []

        embeddings = []
        total = len(texts)

        for i, text in enumerate(texts, 1):
            try:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)

                if show_progress and i % 10 == 0:
                    logger.info(f"📊 Progress: {i}/{total} embeddings generated")

            except Exception as e:
                logger.error(f"❌ Failed to generate embedding for text {i}/{total}: {str(e)}")
                # Don't append anything - skip failed embeddings
                # Caller should check if len(embeddings) == len(texts)

        if show_progress:
            logger.info(f"✅ Batch complete: {len(embeddings)}/{total} embeddings generated")

        return embeddings

    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics."""
        hit_rate = 0.0
        total_requests = self._cache_hits + self._cache_misses
        if total_requests > 0:
            hit_rate = (self._cache_hits / total_requests) * 100

        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.MAX_CACHE_SIZE,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }

    def clear_cache(self) -> None:
        """Clear all cached embeddings."""
        cache_size = len(self._cache)
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info(f"🗑️ Cache cleared ({cache_size} items removed)")

    def embedding_to_pgvector(self, embedding: List[float]) -> str:
        """
        Convert embedding to PostgreSQL vector format.

        Args:
            embedding: List of floats

        Returns:
            String in format: '[0.1,0.2,0.3,...]'
        """
        return '[' + ','.join(map(str, embedding)) + ']'

    async def test_connection(self) -> bool:
        """
        Test if Ollama service is available and model is loaded.

        Returns:
            True if service is working, False otherwise
        """
        try:
            test_embedding = await self.generate_embedding("test")
            return len(test_embedding) == self.DIMENSIONS
        except Exception as e:
            logger.error(f"❌ Ollama service not available: {str(e)}")
            return False


# Global singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get global EmbeddingService instance (singleton pattern).

    Returns:
        EmbeddingService instance

    Usage:
        from angela_core.services.embedding_service import get_embedding_service

        service = get_embedding_service()
        embedding = await service.generate_embedding("Hello world")
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service


# Convenience function for quick embedding generation
async def generate_embedding(text: str) -> List[float]:
    """
    Quick helper to generate embedding without managing service instance.

    Args:
        text: Text to embed

    Returns:
        List[float] with 384 dimensions
    """
    service = get_embedding_service()
    return await service.generate_embedding(text)
