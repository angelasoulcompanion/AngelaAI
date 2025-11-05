#!/usr/bin/env python3
"""
RAG Service DTOs (Data Transfer Objects)

Request/Response models for unified RAG service.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class SearchStrategy(str, Enum):
    """RAG search strategies."""
    VECTOR = "vector"           # Pure vector similarity search
    KEYWORD = "keyword"         # Pure keyword/BM25 search
    HYBRID = "hybrid"          # Combined vector + keyword (RRF fusion)


class SimilarityMethod(str, Enum):
    """Vector similarity calculation methods."""
    COSINE = "cosine"          # Cosine similarity (default)
    EUCLIDEAN = "euclidean"    # Euclidean distance
    DOT_PRODUCT = "dot_product"  # Dot product


@dataclass
class RAGRequest:
    """
    Request for RAG query.

    Contains all parameters needed for document search and retrieval.
    """
    # Required
    query: str

    # Search configuration
    search_strategy: SearchStrategy = SearchStrategy.HYBRID
    similarity_method: SimilarityMethod = SimilarityMethod.COSINE
    top_k: int = 5
    similarity_threshold: float = 0.65

    # Filters
    document_id: Optional[UUID] = None
    category: Optional[str] = None

    # Enhancement options
    use_query_expansion: bool = True
    use_reranking: bool = True

    # Response generation (if needed)
    generate_answer: bool = False
    model: Optional[str] = None  # For answer generation


@dataclass
class DocumentChunkResult:
    """
    Single document chunk result from search.

    Represents one retrieved chunk with metadata and scores.
    """
    # Identity
    chunk_id: UUID
    document_id: UUID

    # Content
    chunk_text: str
    chunk_index: int

    # Metadata
    document_title: Optional[str] = None
    document_category: Optional[str] = None
    chunk_metadata: Dict[str, Any] = field(default_factory=dict)

    # Scores
    similarity_score: float = 0.0
    keyword_score: Optional[float] = None
    rerank_score: Optional[float] = None
    final_score: float = 0.0

    # Context
    created_at: Optional[datetime] = None


@dataclass
class RAGResponse:
    """
    Response from RAG query.

    Contains retrieved chunks and optional generated answer.
    """
    # Request info
    query: str
    enhanced_query: Optional[str] = None
    search_strategy: SearchStrategy = SearchStrategy.HYBRID

    # Results
    chunks: List[DocumentChunkResult] = field(default_factory=list)
    total_chunks_found: int = 0

    # Scores
    avg_similarity: float = 0.0
    max_similarity: float = 0.0
    confidence_score: float = 0.0

    # Generated answer (optional)
    answer: Optional[str] = None
    answer_metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance
    search_time_ms: Optional[int] = None
    total_time_ms: Optional[int] = None

    # Status
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class QueryExpansion:
    """
    Query expansion result.

    Contains original query plus expanded terms.
    """
    original_query: str
    enhanced_query: str
    added_terms: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    related_terms: List[str] = field(default_factory=list)


@dataclass
class RerankingResult:
    """
    Result after reranking.

    Contains reranked chunks with boosting details.
    """
    chunks: List[DocumentChunkResult]
    reranking_method: str
    boost_factors: Dict[str, float] = field(default_factory=dict)
    diversity_threshold: float = 0.85
    removed_duplicates: int = 0


@dataclass
class SearchMetrics:
    """
    Metrics for search performance analysis.

    Useful for monitoring and optimization.
    """
    # Query
    query_length: int
    query_terms_count: int

    # Results
    total_results: int
    results_above_threshold: int
    avg_score: float
    max_score: float
    min_score: float

    # Performance
    embedding_time_ms: Optional[int] = None
    search_time_ms: Optional[int] = None
    rerank_time_ms: Optional[int] = None
    total_time_ms: Optional[int] = None

    # Strategy
    search_strategy: SearchStrategy = SearchStrategy.HYBRID
    use_query_expansion: bool = False
    use_reranking: bool = False
