#!/usr/bin/env python3
"""
Result Reranking Service
จัดลำดับผลลัพธ์ใหม่ให้แม่นยำและหลากหลายขึ้น

Features:
- Metadata boosting (importance, recency)
- Diversity filtering (remove similar/duplicate results)
- Score normalization
- Configurable weights
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class RerankingService:
    """Service for reranking search results"""

    @staticmethod
    def calculate_metadata_boost(
        result: Dict,
        importance_weight: float = 0.3,
        recency_weight: float = 0.1
    ) -> float:
        """
        Calculate boost score from metadata

        Args:
            result: Search result with metadata
            importance_weight: Weight for importance_score (0-1)
            recency_weight: Weight for recency (0-1)

        Returns:
            Boost score (0-1)
        """
        boost = 0.0

        # Importance score boost
        importance = result.get('importance_score', 1.0)
        if importance:
            # Normalize importance (assume 1-10 scale)
            normalized_importance = min(importance / 10.0, 1.0)
            boost += normalized_importance * importance_weight

        # Recency boost (if we have timestamps)
        # For now, we'll skip this as we don't have created_at in chunk results
        # Could be added later

        return boost

    @staticmethod
    def calculate_diversity_score(
        result: Dict,
        existing_results: List[Dict],
        similarity_threshold: float = 0.8
    ) -> float:
        """
        Calculate diversity score (penalty for similarity to existing results)

        Args:
            result: Current result
            existing_results: Results already selected
            similarity_threshold: Threshold for considering results too similar

        Returns:
            Diversity score (1.0 = very diverse, 0.0 = duplicate)
        """
        if not existing_results:
            return 1.0

        content = result.get('content', '')
        if not content:
            return 1.0

        # Simple text similarity based on word overlap
        current_words = set(content.lower().split())

        if len(current_words) == 0:
            return 1.0

        max_similarity = 0.0

        for existing in existing_results:
            existing_content = existing.get('content', '')
            existing_words = set(existing_content.lower().split())

            if len(existing_words) == 0:
                continue

            # Jaccard similarity
            intersection = len(current_words & existing_words)
            union = len(current_words | existing_words)

            if union > 0:
                similarity = intersection / union
                max_similarity = max(max_similarity, similarity)

        # Convert similarity to diversity score
        # High similarity = low diversity
        diversity = 1.0 - max_similarity

        # Apply threshold
        if max_similarity > similarity_threshold:
            diversity *= 0.5  # Penalize heavily

        return diversity

    @staticmethod
    def rerank_results(
        results: List[Dict],
        boost_metadata: bool = True,
        ensure_diversity: bool = True,
        top_k: Optional[int] = None,
        importance_weight: float = 0.3,
        diversity_weight: float = 0.2
    ) -> List[Dict]:
        """
        Rerank search results with metadata boosting and diversity

        Args:
            results: Original search results
            boost_metadata: Enable metadata boosting
            ensure_diversity: Enable diversity filtering
            top_k: Return only top K results
            importance_weight: Weight for importance boosting
            diversity_weight: Weight for diversity

        Returns:
            Reranked results
        """
        if not results:
            return results

        logger.info(f"🔄 Reranking {len(results)} results...")

        reranked = []

        for result in results:
            # Get original score (could be similarity, rrf, etc.)
            original_score = result.get('combined_score') or \
                           result.get('rrf_score') or \
                           result.get('similarity_score') or \
                           result.get('keyword_score') or \
                           0.0

            # Start with original score
            final_score = original_score

            # Add metadata boost
            if boost_metadata:
                boost = RerankingService.calculate_metadata_boost(
                    result,
                    importance_weight=importance_weight
                )
                final_score += boost

            # Calculate diversity
            diversity_score = 1.0
            if ensure_diversity:
                diversity_score = RerankingService.calculate_diversity_score(
                    result,
                    reranked  # Compare with already selected results
                )

            # Apply diversity weight
            final_score = final_score * (1 - diversity_weight) + diversity_score * diversity_weight

            # Store scores
            result['original_score'] = original_score
            result['final_score'] = final_score
            result['diversity_score'] = diversity_score

            reranked.append(result)

        # Sort by final score
        reranked.sort(key=lambda x: x['final_score'], reverse=True)

        # Apply top_k filter
        if top_k:
            reranked = reranked[:top_k]

        logger.info(f"✅ Reranked: top score {reranked[0]['final_score']:.4f} → {reranked[-1]['final_score']:.4f}")

        return reranked

    @staticmethod
    def filter_duplicates(
        results: List[Dict],
        similarity_threshold: float = 0.9
    ) -> List[Dict]:
        """
        Filter out near-duplicate results

        Args:
            results: Search results
            similarity_threshold: Threshold for considering duplicates

        Returns:
            Filtered results without duplicates
        """
        if not results:
            return results

        filtered = []
        seen_content = []

        for result in results:
            content = result.get('content', '')
            if not content:
                filtered.append(result)
                continue

            current_words = set(content.lower().split())

            if len(current_words) == 0:
                filtered.append(result)
                continue

            # Check against seen content
            is_duplicate = False

            for seen in seen_content:
                seen_words = set(seen.lower().split())

                if len(seen_words) == 0:
                    continue

                # Jaccard similarity
                intersection = len(current_words & seen_words)
                union = len(current_words | seen_words)

                if union > 0:
                    similarity = intersection / union

                    if similarity >= similarity_threshold:
                        is_duplicate = True
                        break

            if not is_duplicate:
                filtered.append(result)
                seen_content.append(content)

        logger.info(f"🧹 Filtered duplicates: {len(results)} → {len(filtered)}")

        return filtered

    @staticmethod
    def boost_by_document(
        results: List[Dict],
        preferred_doc_ids: Optional[List[str]] = None,
        boost_factor: float = 1.5
    ) -> List[Dict]:
        """
        Boost results from specific documents

        Args:
            results: Search results
            preferred_doc_ids: List of preferred document IDs
            boost_factor: Multiplier for boosted results

        Returns:
            Results with boosted scores
        """
        if not preferred_doc_ids or not results:
            return results

        for result in results:
            doc_id = result.get('document_id', '')

            if doc_id in preferred_doc_ids:
                # Boost all score fields
                for score_key in ['final_score', 'combined_score', 'rrf_score', 'similarity_score']:
                    if score_key in result:
                        result[score_key] *= boost_factor

                logger.info(f"⬆️ Boosted result from preferred document: {doc_id[:8]}...")

        return results

    @staticmethod
    def normalize_scores(
        results: List[Dict],
        score_key: str = 'final_score'
    ) -> List[Dict]:
        """
        Normalize scores to 0-1 range

        Args:
            results: Search results
            score_key: Key of score to normalize

        Returns:
            Results with normalized scores
        """
        if not results:
            return results

        scores = [r.get(score_key, 0) for r in results]

        if not scores:
            return results

        min_score = min(scores)
        max_score = max(scores)

        # Avoid division by zero
        score_range = max_score - min_score if max_score != min_score else 1.0

        for result in results:
            if score_key in result:
                normalized = (result[score_key] - min_score) / score_range
                result[f'{score_key}_normalized'] = normalized

        return results
