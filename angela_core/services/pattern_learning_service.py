"""
🎯💜 Pattern Learning Service
Automatic pattern extraction from episodic memories (Subconscious Learning)

This service:
1. Clusters similar episodic memories
2. Extracts common features
3. Forms pattern memories
4. Uses patterns for fast recognition

Design Date: 2025-10-27
Designer: น้อง Angela, Approved by: ที่รัก David
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from uuid import UUID
import numpy as np

from angela_core.database import db
from angela_core.embedding_service import embedding

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class PatternLearningService:
    """
    🎯 Pattern Learning Service - Automatic Pattern Extraction

    Like humans learn patterns unconsciously through repetition,
    this service automatically discovers patterns in experiences.
    """

    def __init__(self):
        self.embedding = embedding
        logger.info("🎯 Pattern Learning Service initialized")

    # ========================================================================
    # PART 1: PATTERN DISCOVERY (Find similar experiences)
    # ========================================================================

    async def discover_patterns(
        self,
        min_similarity: float = 0.75,
        min_instances: int = 3,
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        🔍 Discover patterns from episodic memories

        Finds groups of similar experiences and extracts common patterns.

        Args:
            min_similarity: Minimum similarity to group memories (0.0-1.0)
            min_instances: Minimum instances needed to form pattern
            lookback_days: How far back to look

        Returns:
            List of discovered patterns with their instances
        """
        try:
            logger.info(f"🔍 Discovering patterns from last {lookback_days} days...")

            # Get recent episodic memories
            async with db.acquire() as conn:
                memories = await conn.fetch(f"""
                    SELECT
                        memory_id,
                        event_content,
                        tags,
                        content_embedding,
                        emotional_intensity,
                        importance_level,
                        occurred_at
                    FROM episodic_memories
                    WHERE occurred_at >= CURRENT_TIMESTAMP - INTERVAL '{lookback_days} days'
                    ORDER BY occurred_at DESC
                """)

            if len(memories) < min_instances:
                logger.info(f"Not enough memories ({len(memories)}) to form patterns")
                return []

            # Group similar memories
            clusters = await self._cluster_similar_memories(
                memories,
                min_similarity
            )

            # Extract patterns from clusters
            patterns_formed = []
            for cluster in clusters:
                if len(cluster['memories']) >= min_instances:
                    pattern = await self._extract_pattern_from_cluster(cluster)
                    if pattern:
                        patterns_formed.append(pattern)

            logger.info(f"✅ Discovered {len(patterns_formed)} patterns from {len(clusters)} clusters")
            return patterns_formed

        except Exception as e:
            logger.error(f"❌ Failed to discover patterns: {e}")
            return []

    async def _cluster_similar_memories(
        self,
        memories: List[Any],
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """
        Cluster similar memories using embeddings

        Returns:
            List of clusters, each containing similar memories
        """
        try:
            # Simple clustering: find memories similar to each other
            clusters = []
            processed = set()

            for i, memory in enumerate(memories):
                if str(memory['memory_id']) in processed:
                    continue

                # Start new cluster with this memory
                cluster_memories = [memory]
                processed.add(str(memory['memory_id']))

                # Find similar memories
                embedding1 = self._parse_embedding(memory['content_embedding'])

                for j, other_memory in enumerate(memories):
                    if i == j or str(other_memory['memory_id']) in processed:
                        continue

                    embedding2 = self._parse_embedding(other_memory['content_embedding'])
                    similarity = self._cosine_similarity(embedding1, embedding2)

                    if similarity >= min_similarity:
                        cluster_memories.append(other_memory)
                        processed.add(str(other_memory['memory_id']))

                if len(cluster_memories) > 1:
                    clusters.append({
                        'memories': cluster_memories,
                        'size': len(cluster_memories)
                    })

            return clusters

        except Exception as e:
            logger.error(f"❌ Failed to cluster memories: {e}")
            return []

    def _parse_embedding(self, embedding_str: str) -> List[float]:
        """Parse embedding string to list of floats"""
        try:
            # Remove brackets and split
            clean_str = str(embedding_str).strip('[]')
            return [float(x) for x in clean_str.split(',')]
        except Exception as e:
            logger.error(f"Failed to parse embedding: {e}")
            return [0.0] * 768

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0

    # ========================================================================
    # PART 2: PATTERN EXTRACTION (Extract common features)
    # ========================================================================

    async def _extract_pattern_from_cluster(
        self,
        cluster: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract common pattern from cluster of similar memories

        Returns:
            Pattern dict with features and typical response
        """
        try:
            memories = cluster['memories']

            # Extract common features
            common_emotions = self._extract_common_emotions(memories)
            common_topics = self._extract_common_topics(memories)
            common_actions = self._extract_common_actions(memories)
            common_outcomes = self._extract_common_outcomes(memories)

            # Determine pattern name
            pattern_name = self._generate_pattern_name(
                common_emotions,
                common_topics,
                common_actions
            )

            # Extract typical response
            typical_response = self._extract_typical_response(memories)

            # Calculate average embedding (pattern centroid)
            pattern_embedding = self._calculate_centroid_embedding(memories)

            # Build pattern content
            pattern_content = {
                "pattern_name": pattern_name,
                "pattern_description": f"Pattern of {len(memories)} similar experiences",
                "features": {
                    "emotions": common_emotions,
                    "topics": common_topics,
                    "actions": common_actions,
                    "outcomes": common_outcomes,
                    "emotional_intensity": self._avg_emotional_intensity(memories),
                    "importance_level": self._avg_importance(memories)
                },
                "typical_response": typical_response,
                "instances": [
                    {
                        "memory_id": str(mem['memory_id']),
                        "date": mem['occurred_at'].isoformat(),
                        "summary": json.loads(mem['event_content']).get('event', 'Unknown')[:100]
                    }
                    for mem in memories[:5]  # Keep first 5 as examples
                ]
            }

            # Build tags
            tags = {
                "emotion_tags": common_emotions,
                "topic_tags": common_topics,
                "action_tags": common_actions,
                "outcome_tags": common_outcomes,
                "pattern_tags": ["automatic", "learned", pattern_name]
            }

            # Build process metadata
            process_metadata = {
                "formed_via": "pattern_extraction",
                "extraction_method": "clustering_and_feature_analysis",
                "source_instances": len(memories),
                "confidence": min(0.5 + (len(memories) * 0.1), 1.0),
                "reasoning": f"Identified common pattern across {len(memories)} similar instances",
                "feature_importance": {
                    "emotions": 0.9 if common_emotions else 0.3,
                    "topics": 0.8 if common_topics else 0.3,
                    "actions": 0.7 if common_actions else 0.3
                },
                "extraction_date": "auto"
            }

            # Pattern features for matching
            pattern_features = {
                "must_have": {
                    "emotions": common_emotions[:2] if len(common_emotions) >= 2 else common_emotions,
                    "topics": common_topics[:1] if common_topics else []
                },
                "nice_to_have": {
                    "actions": common_actions,
                    "outcomes": common_outcomes
                }
            }

            # Store pattern to database
            pattern_id = await self._store_pattern(
                pattern_content,
                pattern_features,
                pattern_embedding,
                tags,
                process_metadata,
                len(memories)
            )

            if pattern_id:
                return {
                    'pattern_id': pattern_id,
                    'name': pattern_name,
                    'instances': len(memories),
                    'features': pattern_content['features']
                }

            return None

        except Exception as e:
            logger.error(f"❌ Failed to extract pattern: {e}")
            return None

    def _extract_common_emotions(self, memories: List[Any]) -> List[str]:
        """Extract emotions that appear in majority of memories"""
        emotion_counts = defaultdict(int)

        for mem in memories:
            try:
                tags = json.loads(mem['tags'])
                for emotion in tags.get('emotion_tags', []):
                    emotion_counts[emotion] += 1
            except:
                continue

        # Keep emotions that appear in at least 50% of memories
        threshold = len(memories) * 0.5
        common = [emotion for emotion, count in emotion_counts.items() if count >= threshold]
        return sorted(common, key=lambda e: emotion_counts[e], reverse=True)

    def _extract_common_topics(self, memories: List[Any]) -> List[str]:
        """Extract topics that appear in majority of memories"""
        topic_counts = defaultdict(int)

        for mem in memories:
            try:
                tags = json.loads(mem['tags'])
                for topic in tags.get('topic_tags', []):
                    topic_counts[topic] += 1
            except:
                continue

        threshold = len(memories) * 0.5
        common = [topic for topic, count in topic_counts.items() if count >= threshold]
        return sorted(common, key=lambda t: topic_counts[t], reverse=True)

    def _extract_common_actions(self, memories: List[Any]) -> List[str]:
        """Extract actions that appear in majority of memories"""
        action_counts = defaultdict(int)

        for mem in memories:
            try:
                tags = json.loads(mem['tags'])
                for action in tags.get('action_tags', []):
                    action_counts[action] += 1
            except:
                continue

        threshold = len(memories) * 0.4  # Lower threshold for actions
        common = [action for action, count in action_counts.items() if count >= threshold]
        return sorted(common, key=lambda a: action_counts[a], reverse=True)

    def _extract_common_outcomes(self, memories: List[Any]) -> List[str]:
        """Extract outcomes that appear in majority of memories"""
        outcome_counts = defaultdict(int)

        for mem in memories:
            try:
                tags = json.loads(mem['tags'])
                for outcome in tags.get('outcome_tags', []):
                    outcome_counts[outcome] += 1
            except:
                continue

        threshold = len(memories) * 0.5
        common = [outcome for outcome, count in outcome_counts.items() if count >= threshold]
        return sorted(common, key=lambda o: outcome_counts[o], reverse=True)

    def _generate_pattern_name(
        self,
        emotions: List[str],
        topics: List[str],
        actions: List[str]
    ) -> str:
        """Generate descriptive pattern name"""
        parts = []

        if emotions:
            parts.append(emotions[0])
        if topics:
            parts.append(f"about_{topics[0]}")
        if actions:
            parts.append(f"with_{actions[0]}")

        if not parts:
            return "general_interaction_pattern"

        return "_".join(parts)

    def _extract_typical_response(self, memories: List[Any]) -> Dict[str, Any]:
        """Extract typical response pattern"""
        # Get Angela's approach from memories
        approaches = defaultdict(int)

        for mem in memories:
            try:
                event_content = json.loads(mem['event_content'])
                angela_state = event_content.get('context', {}).get('angela_state', {})
                approach = angela_state.get('approach', 'unknown')
                approaches[approach] += 1
            except:
                continue

        typical_approach = max(approaches.items(), key=lambda x: x[1])[0] if approaches else "supportive"

        return {
            "style": typical_approach,
            "components": ["empathy", "understanding", "support"],
            "tone": "caring_and_warm"
        }

    def _calculate_centroid_embedding(self, memories: List[Any]) -> List[float]:
        """Calculate average embedding (centroid) of memories"""
        try:
            embeddings = []
            for mem in memories:
                emb = self._parse_embedding(mem['content_embedding'])
                embeddings.append(emb)

            # Average all embeddings
            centroid = np.mean(embeddings, axis=0)
            return centroid.tolist()
        except Exception as e:
            logger.error(f"Failed to calculate centroid: {e}")
            return [0.0] * 768

    def _avg_emotional_intensity(self, memories: List[Any]) -> float:
        """Calculate average emotional intensity"""
        intensities = [float(mem['emotional_intensity']) for mem in memories if mem['emotional_intensity']]
        return sum(intensities) / len(intensities) if intensities else 0.5

    def _avg_importance(self, memories: List[Any]) -> float:
        """Calculate average importance level"""
        levels = [int(mem['importance_level']) for mem in memories if mem['importance_level']]
        return sum(levels) / len(levels) if levels else 5.0

    async def _store_pattern(
        self,
        pattern_content: Dict[str, Any],
        pattern_features: Dict[str, Any],
        pattern_embedding: List[float],
        tags: Dict[str, List[str]],
        process_metadata: Dict[str, Any],
        instance_count: int
    ) -> Optional[UUID]:
        """Store pattern to database"""
        try:
            async with db.acquire() as conn:
                # Check if similar pattern exists
                existing = await conn.fetchrow("""
                    SELECT pattern_id FROM pattern_memories
                    WHERE 1 - (pattern_embedding <=> $1::vector(768)) > 0.90
                    LIMIT 1
                """, str(pattern_embedding))

                if existing:
                    # Update existing pattern
                    await conn.execute("""
                        UPDATE pattern_memories
                        SET instance_count = instance_count + $1,
                            pattern_strength = LEAST(pattern_strength + 0.1, 1.0),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE pattern_id = $2
                    """, instance_count, existing['pattern_id'])

                    logger.info(f"💪 Updated existing pattern: {existing['pattern_id']}")
                    return existing['pattern_id']
                else:
                    # Create new pattern
                    pattern_id = await conn.fetchval("""
                        INSERT INTO pattern_memories (
                            pattern_content,
                            pattern_features,
                            pattern_embedding,
                            pattern_category,
                            tags,
                            process_metadata,
                            pattern_strength,
                            instance_count,
                            similarity_threshold
                        ) VALUES ($1, $2, $3::vector(768), $4, $5, $6, $7, $8, $9)
                        RETURNING pattern_id
                    """,
                        json.dumps(pattern_content),
                        json.dumps(pattern_features),
                        str(pattern_embedding),
                        'conversational',  # Default category
                        json.dumps(tags),
                        json.dumps(process_metadata),
                        0.7,  # Initial strength
                        instance_count,
                        0.75  # Similarity threshold for matching
                    )

                    logger.info(f"✨ Created new pattern: {pattern_id}")
                    return pattern_id

        except Exception as e:
            logger.error(f"❌ Failed to store pattern: {e}")
            return None

    # ========================================================================
    # PART 3: PATTERN RECOGNITION (Match new experiences to patterns)
    # ========================================================================

    async def recognize_pattern(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        🎯 Recognize if current input matches a known pattern

        Args:
            user_input: Current user input
            context: Optional context (emotions, topic, etc.)

        Returns:
            Matched pattern with confidence, or None
        """
        try:
            # Generate embedding for input
            input_embedding = await self.embedding.generate_embedding(user_input)

            # Find matching patterns
            async with db.acquire() as conn:
                patterns = await conn.fetch("""
                    SELECT
                        pattern_id,
                        pattern_content,
                        pattern_features,
                        1 - (pattern_embedding <=> $1::vector(768)) as similarity,
                        pattern_strength,
                        recognition_accuracy,
                        instance_count
                    FROM pattern_memories
                    WHERE 1 - (pattern_embedding <=> $1::vector(768)) >= similarity_threshold
                    ORDER BY
                        (1 - (pattern_embedding <=> $1::vector(768))) DESC,
                        pattern_strength DESC,
                        recognition_accuracy DESC
                    LIMIT 3
                """, str(input_embedding))

                if not patterns:
                    return None

                # Check best match
                best_match = patterns[0]

                # Verify feature match if context provided
                if context:
                    feature_score = self._calculate_feature_match(
                        json.loads(best_match['pattern_features']),
                        context
                    )
                else:
                    feature_score = 0.5

                # Combined confidence
                confidence = (best_match['similarity'] * 0.7) + (feature_score * 0.3)

                if confidence >= 0.70:
                    # Record recognition
                    await self._record_pattern_recognition(
                        best_match['pattern_id'],
                        confidence
                    )

                    pattern_content = json.loads(best_match['pattern_content'])

                    return {
                        'pattern_id': best_match['pattern_id'],
                        'pattern_name': pattern_content['pattern_name'],
                        'confidence': confidence,
                        'similarity': best_match['similarity'],
                        'pattern_strength': best_match['pattern_strength'],
                        'typical_response': pattern_content['typical_response'],
                        'features': pattern_content['features']
                    }

                return None

        except Exception as e:
            logger.error(f"❌ Failed to recognize pattern: {e}")
            return None

    def _calculate_feature_match(
        self,
        pattern_features: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """Calculate how well context matches pattern features"""
        try:
            score = 0.0
            checks = 0

            must_have = pattern_features.get('must_have', {})

            # Check emotions
            if 'emotion' in context and 'emotions' in must_have:
                if context['emotion'] in must_have['emotions']:
                    score += 1.0
                checks += 1

            # Check topics
            if 'topic' in context and 'topics' in must_have:
                if context['topic'] in must_have['topics']:
                    score += 1.0
                checks += 1

            return score / checks if checks > 0 else 0.5

        except Exception as e:
            logger.error(f"Failed to calculate feature match: {e}")
            return 0.0

    async def _record_pattern_recognition(
        self,
        pattern_id: UUID,
        confidence: float
    ) -> None:
        """Record that pattern was recognized"""
        try:
            async with db.acquire() as conn:
                await conn.execute("""
                    UPDATE pattern_memories
                    SET recognition_count = recognition_count + 1,
                        last_recognized_at = CURRENT_TIMESTAMP
                    WHERE pattern_id = $1
                """, pattern_id)
        except Exception as e:
            logger.warning(f"Failed to record recognition: {e}")

    # ========================================================================
    # PART 4: STATISTICS
    # ========================================================================

    async def get_pattern_stats(self) -> Dict[str, Any]:
        """Get statistics about patterns"""
        try:
            async with db.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_patterns,
                        AVG(pattern_strength) as avg_strength,
                        AVG(instance_count) as avg_instances,
                        AVG(recognition_accuracy) as avg_accuracy,
                        COUNT(*) FILTER (WHERE pattern_strength >= 0.80) as strong_patterns,
                        COUNT(*) FILTER (WHERE recognition_accuracy >= 0.75) as accurate_patterns
                    FROM pattern_memories
                """)

                return {
                    'total_patterns': stats['total_patterns'],
                    'avg_strength': float(stats['avg_strength']) if stats['avg_strength'] else 0,
                    'avg_instances': float(stats['avg_instances']) if stats['avg_instances'] else 0,
                    'avg_accuracy': float(stats['avg_accuracy']) if stats['avg_accuracy'] else 0,
                    'strong_patterns': stats['strong_patterns'],
                    'accurate_patterns': stats['accurate_patterns']
                }

        except Exception as e:
            logger.error(f"❌ Failed to get pattern stats: {e}")
            return {}


# Global instance
pattern_learning_service = PatternLearningService()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_usage():
    """Example of how to use Pattern Learning Service"""

    await db.connect()

    # 1. Discover patterns
    print("=" * 80)
    print("🔍 DISCOVERING PATTERNS")
    print("=" * 80)
    patterns = await pattern_learning_service.discover_patterns(
        min_similarity=0.75,
        min_instances=2,  # Lower for testing
        lookback_days=30
    )
    print(f"Discovered {len(patterns)} patterns")
    for pattern in patterns:
        print(f"  {pattern['name']} ({pattern['instances']} instances)")
    print()

    # 2. Recognize pattern
    if patterns:
        print("=" * 80)
        print("🎯 RECOGNIZING PATTERN")
        print("=" * 80)
        matched = await pattern_learning_service.recognize_pattern(
            "น้อง งงๆ เลย",
            context={'emotion': 'confused', 'topic': 'general'}
        )
        if matched:
            print(f"✅ Matched pattern: {matched['pattern_name']}")
            print(f"   Confidence: {matched['confidence']:.2f}")
            print(f"   Typical response: {matched['typical_response']}")
        else:
            print("No pattern matched")
        print()

    # 3. Get statistics
    print("=" * 80)
    print("📊 PATTERN STATISTICS")
    print("=" * 80)
    stats = await pattern_learning_service.get_pattern_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())
