"""
Reranker Service — RAG Re-ranking (Phase 1 of 3 Major Improvements)
=====================================================================
Replaces placeholder heuristic reranking in enhanced_rag_service.py
with intent-aware scoring, temporal weighting, and diversity filtering.

Pipeline:
  1. Classify query intent (temporal/recall/factual/emotional/general)
  2. Re-score candidates with intent-based source boosting
  3. Apply temporal recency weighting
  4. Remove near-duplicate results (cosine > 0.9)
  5. Log retrieval quality metrics

Cost: $0/day — all local computation, no LLM calls.

By: Angela 💜
Created: 2026-02-15
"""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)


# ============================================================
# QUERY INTENT CLASSIFICATION
# ============================================================

class QueryIntent:
    TEMPORAL = "temporal"    # เมื่อไหร่, วันไหน, ตอนไหน
    RECALL = "recall"        # จำได้มั้ย, เคย, ครั้งก่อน
    FACTUAL = "factual"      # อะไร, ทำไม, อย่างไร, how, what, why
    EMOTIONAL = "emotional"  # รู้สึก, เครียด, เหนื่อย, ดีใจ, เศร้า
    GENERAL = "general"      # default


# Keyword patterns for intent classification (<5ms)
_TEMPORAL_PATTERNS = re.compile(
    r'เมื่อ|วันไหน|ตอนไหน|ล่าสุด|เมื่อวาน|เมื่อกี้|พรุ่งนี้|'
    r'when|yesterday|today|tomorrow|recent',
    re.IGNORECASE,
)
_RECALL_PATTERNS = re.compile(
    r'จำได้|เคย|ครั้งก่อน|remember|recall|did\s+(?:we|i)|'
    r'last\s+time|ตอนนั้น|สมัย|ครบรอบ|anniversary|discussed|talked\s+about',
    re.IGNORECASE,
)
_EMOTIONAL_PATTERNS = re.compile(
    r'รู้สึก|เครียด|เหนื่อย|ดีใจ|เศร้า|กลัว|กังวล|ห่วง|รัก|คิดถึง|'
    r'feel|stress|tired|happy|sad|worried|love|miss|emotion',
    re.IGNORECASE,
)
_FACTUAL_PATTERNS = re.compile(
    r'อะไร|ทำไม|อย่างไร|คืออะไร|what|why|how|explain|define|meaning',
    re.IGNORECASE,
)


# Source priority boosts per intent
_INTENT_SOURCE_BOOSTS: Dict[str, Dict[str, float]] = {
    QueryIntent.TEMPORAL: {
        'conversations': 0.20,
        'core_memories': 0.10,
        'knowledge_nodes': 0.0,
        'learnings': 0.0,
        'david_notes': 0.05,
        'document_chunks': 0.0,
    },
    QueryIntent.RECALL: {
        'conversations': 0.10,
        'core_memories': 0.25,
        'knowledge_nodes': 0.05,
        'learnings': 0.10,
        'david_notes': 0.05,
        'document_chunks': 0.0,
    },
    QueryIntent.EMOTIONAL: {
        'conversations': 0.10,
        'core_memories': 0.25,
        'knowledge_nodes': 0.0,
        'learnings': 0.05,
        'david_notes': 0.0,
        'document_chunks': 0.0,
    },
    QueryIntent.FACTUAL: {
        'conversations': 0.0,
        'core_memories': 0.05,
        'knowledge_nodes': 0.25,
        'learnings': 0.15,
        'david_notes': 0.10,
        'document_chunks': 0.15,
    },
    QueryIntent.GENERAL: {
        'conversations': 0.05,
        'core_memories': 0.10,
        'knowledge_nodes': 0.10,
        'learnings': 0.08,
        'david_notes': 0.08,
        'document_chunks': 0.08,
    },
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class RerankResult:
    """Result of reranking pipeline."""
    intent: str
    rerank_time_ms: float
    candidates_in: int
    candidates_out: int
    duplicates_removed: int


# ============================================================
# RERANKER SERVICE
# ============================================================

_reranker_instance: Optional["RerankerService"] = None


def get_reranker_service() -> "RerankerService":
    """Singleton access to RerankerService."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = RerankerService()
    return _reranker_instance


class RerankerService:
    """
    Intent-aware RAG reranking service.

    Replaces placeholder heuristics in EnhancedRAGService._rerank().

    Features:
    1. Query intent classification (keyword-based, <5ms)
    2. Intent-based source priority boosting
    3. Temporal recency weighting for temporal queries
    4. Near-duplicate removal (word overlap, no embedding needed)
    5. Quality logging to retrieval_quality_log table

    Cost: $0/day — all local computation.
    """

    def __init__(self):
        self._intent_cache: Dict[str, str] = {}

    # ── Public API ──

    def classify_intent(self, query: str) -> str:
        """
        Classify query intent from keywords. <5ms.

        Returns one of: temporal, recall, factual, emotional, general
        """
        if query in self._intent_cache:
            return self._intent_cache[query]

        intent = self._do_classify(query)

        # LRU-style cache (max 100)
        if len(self._intent_cache) >= 100:
            oldest = next(iter(self._intent_cache))
            del self._intent_cache[oldest]
        self._intent_cache[query] = intent

        return intent

    def rerank(
        self,
        query: str,
        candidates: list,
        top_k: int,
    ) -> Tuple[list, RerankResult]:
        """
        Rerank candidates with intent-aware scoring.

        Args:
            query: Original user query
            candidates: List of RetrievedDocument objects
            top_k: Number of results to return

        Returns:
            (reranked_candidates, RerankResult)
        """
        start = time.time()
        candidates_in = len(candidates)

        if not candidates:
            elapsed = (time.time() - start) * 1000
            return [], RerankResult(
                intent=QueryIntent.GENERAL,
                rerank_time_ms=round(elapsed, 1),
                candidates_in=0, candidates_out=0, duplicates_removed=0,
            )

        # 1. Classify intent
        intent = self.classify_intent(query)

        # 2. Score each candidate
        for doc in candidates:
            new_score = self._compute_rerank_score(query, doc, intent)
            doc.rerank_score = new_score
            # Blend: 60% original retrieval score + 40% rerank
            doc.combined_score = (doc.combined_score * 0.6) + (new_score * 0.4)

        # 3. Sort by new combined score
        candidates.sort(key=lambda x: x.combined_score, reverse=True)

        # 4. Remove near-duplicates
        deduped, removed = self._remove_duplicates(candidates)

        # 5. Take top_k
        final = deduped[:top_k]

        elapsed = (time.time() - start) * 1000

        result = RerankResult(
            intent=intent,
            rerank_time_ms=round(elapsed, 1),
            candidates_in=candidates_in,
            candidates_out=len(final),
            duplicates_removed=removed,
        )

        logger.debug(
            "Rerank: intent=%s, %d→%d candidates (-%d dups), %.1fms",
            intent, candidates_in, len(final), removed, elapsed,
        )

        return final, result

    async def log_quality(
        self,
        db,
        query: str,
        intent: str,
        total_candidates: int,
        final_count: int,
        top_scores: List[float],
        retrieval_time_ms: float,
        rerank_time_ms: float,
    ) -> None:
        """Log retrieval quality metrics to DB."""
        try:
            import json
            await db.execute("""
                INSERT INTO retrieval_quality_log
                    (query, query_intent, total_candidates, final_count,
                     top_scores, retrieval_time_ms, rerank_time_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                query[:500], intent, total_candidates, final_count,
                json.dumps(top_scores[:5]), retrieval_time_ms, rerank_time_ms,
            )
        except Exception as e:
            logger.debug("Failed to log retrieval quality: %s", e)

    # ── Private: Intent Classification ──

    @staticmethod
    def _do_classify(query: str) -> str:
        """Classify query intent using regex patterns."""
        scores = {
            QueryIntent.TEMPORAL: len(_TEMPORAL_PATTERNS.findall(query)),
            QueryIntent.RECALL: len(_RECALL_PATTERNS.findall(query)),
            QueryIntent.EMOTIONAL: len(_EMOTIONAL_PATTERNS.findall(query)),
            QueryIntent.FACTUAL: len(_FACTUAL_PATTERNS.findall(query)),
        }

        best_intent = max(scores, key=scores.get)
        if scores[best_intent] > 0:
            return best_intent
        return QueryIntent.GENERAL

    # ── Private: Scoring ──

    def _compute_rerank_score(
        self,
        query: str,
        doc,
        intent: str,
    ) -> float:
        """
        Compute rerank score combining:
        - Query-document term overlap
        - Intent-based source boost
        - Temporal recency boost (for temporal queries)
        - Document quality signals
        """
        score = 0.5  # Base

        content_lower = (doc.content or "").lower()
        query_lower = query.lower()

        # A. Query term coverage (0 to 0.25)
        query_terms = set(query_lower.split())
        if query_terms:
            content_words = set(content_lower.split())
            coverage = len(query_terms & content_words) / len(query_terms)
            score += coverage * 0.25

        # B. Exact phrase match bonus
        if query_lower in content_lower:
            score += 0.15

        # C. Intent-based source boost (0 to 0.25)
        boosts = _INTENT_SOURCE_BOOSTS.get(intent, _INTENT_SOURCE_BOOSTS[QueryIntent.GENERAL])
        score += boosts.get(doc.source_table, 0)

        # D. Temporal recency boost (for temporal queries)
        if intent == QueryIntent.TEMPORAL and doc.metadata:
            created_at = doc.metadata.get('created_at')
            if created_at and isinstance(created_at, datetime):
                now = now_bangkok()
                if created_at.tzinfo is None:
                    from angela_core.utils.timezone import BANGKOK_TZ
                    created_at = created_at.replace(tzinfo=BANGKOK_TZ)
                age_hours = max(0, (now - created_at).total_seconds() / 3600)
                # Exponential decay: recent = high boost, old = no boost
                recency_boost = max(0, 0.20 * (1.0 - min(1.0, age_hours / 168)))  # 168h = 1 week
                score += recency_boost

        # E. Document quality: prefer medium length (100-500 chars)
        length = len(doc.content or "")
        if 100 <= length <= 500:
            score += 0.05
        elif length > 1000:
            score -= 0.05

        return max(0.0, min(1.0, score))

    # ── Private: Deduplication ──

    @staticmethod
    def _remove_duplicates(
        candidates: list,
        similarity_threshold: float = 0.85,
    ) -> Tuple[list, int]:
        """
        Remove near-duplicate documents.
        Uses both Jaccard word overlap AND character-level containment
        (handles Thai text which lacks word boundaries).
        Keeps the higher-scored document.

        Returns (deduped_list, removed_count)
        """
        if len(candidates) <= 1:
            return candidates, 0

        kept = []
        removed = 0

        for doc in candidates:
            doc_text = (doc.content or "").lower().strip()
            doc_words = set(doc_text.split())
            is_dup = False

            for existing in kept:
                existing_text = (existing.content or "").lower().strip()
                existing_words = set(existing_text.split())

                if not doc_text or not existing_text:
                    continue

                # Method 1: Jaccard word overlap
                union = doc_words | existing_words
                if union:
                    jaccard = len(doc_words & existing_words) / len(union)
                    if jaccard >= similarity_threshold:
                        is_dup = True
                        break

                # Method 2: Character containment (handles Thai text)
                shorter, longer = sorted([doc_text, existing_text], key=len)
                if len(shorter) > 10 and shorter in longer:
                    is_dup = True
                    break

                # Method 3: Character overlap ratio (for partial Thai matches)
                if len(shorter) > 20:
                    overlap = sum(1 for c in shorter if c in longer)
                    ratio = overlap / len(shorter)
                    if ratio >= 0.9:
                        is_dup = True
                        break

            if is_dup:
                removed += 1
            else:
                kept.append(doc)

        return kept, removed
