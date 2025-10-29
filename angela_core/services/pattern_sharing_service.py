"""
Pattern Sharing Service - Cross-Agent Pattern Collaboration

Enables patterns discovered by one agent/memory tier to be shared
and utilized by other agents.

Key Features:
1. Pattern registration from any agent
2. Pattern discovery by other agents
3. Pattern voting & confidence scoring
4. Privacy-preserving aggregation
5. Pattern lifecycle management

Phase 4 - Gut Agent Enhancement
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4
import logging
from enum import Enum

from angela_core.database import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PatternSharing - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatternScope(str, Enum):
    """Scope of pattern sharing."""
    PRIVATE = "private"          # Only for agent that discovered it
    SHARED = "shared"            # Shared across agents
    GLOBAL = "global"            # Available to all components
    ARCHIVED = "archived"        # No longer active


class PatternSource(str, Enum):
    """Source agent/component that discovered pattern."""
    GUT_AGENT = "gut_agent"
    ANALYTICS = "analytics_agent"
    FOCUS = "focus_agent"
    FRESH_BUFFER = "fresh_buffer"
    DECAY_SERVICE = "decay_service"
    USER_INPUT = "user_input"
    AUTOMATED = "automated"


class PatternSharingService:
    """
    Manages cross-agent pattern sharing and collaboration.

    Workflow:
    1. Agent discovers pattern → registers with sharing service
    2. Pattern gets confidence score, privacy check
    3. Other agents can query for relevant patterns
    4. Agents vote on pattern usefulness
    5. High-confidence patterns become shared resources
    """

    def __init__(self):
        self.min_confidence_for_sharing = 0.6
        self.min_votes_for_global = 3

    async def register_pattern(self,
                              pattern_type: str,
                              pattern_data: Dict,
                              source: str,
                              confidence: float,
                              scope: str = PatternScope.SHARED,
                              metadata: Dict = None) -> UUID:
        """
        Register a newly discovered pattern.

        Args:
            pattern_type: Type of pattern (temporal, behavioral, etc.)
            pattern_data: Pattern details (structure, examples, etc.)
            source: Which agent/component discovered it
            confidence: Confidence score (0-1)
            scope: Sharing scope (private/shared/global)
            metadata: Additional context

        Returns:
            UUID of registered pattern
        """
        pattern_id = uuid4()

        # Privacy check
        is_sensitive = await self._check_pattern_sensitivity(pattern_data)
        if is_sensitive and scope == PatternScope.GLOBAL:
            logger.warning(f"Pattern contains sensitive data, downgrading to SHARED scope")
            scope = PatternScope.SHARED

        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO shared_patterns (
                    pattern_id, pattern_type, pattern_data,
                    source_agent, confidence_score, scope,
                    metadata, is_sensitive, vote_count, total_votes
                ) VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7::jsonb, $8, $9, $10)
            """,
                pattern_id,
                pattern_type,
                json.dumps(pattern_data),
                source,
                confidence,
                scope,
                json.dumps(metadata or {}),
                is_sensitive,
                0,  # Initial vote count
                0   # Total votes
            )

        logger.info(f"Registered pattern {pattern_id} from {source}: {pattern_type}")

        return pattern_id

    async def find_relevant_patterns(self,
                                    query_context: Dict,
                                    pattern_types: List[str] = None,
                                    min_confidence: float = None,
                                    limit: int = 10) -> List[Dict]:
        """
        Find patterns relevant to a given context.

        Args:
            query_context: Context to match against (topic, emotion, time, etc.)
            pattern_types: Filter by pattern types
            min_confidence: Minimum confidence threshold
            limit: Max results

        Returns:
            List of relevant patterns with scores
        """
        if min_confidence is None:
            min_confidence = self.min_confidence_for_sharing

        async with get_db_connection() as conn:
            # Build query
            query = """
                SELECT
                    pattern_id,
                    pattern_type,
                    pattern_data,
                    source_agent,
                    confidence_score,
                    scope,
                    metadata,
                    vote_count,
                    total_votes,
                    (CASE
                        WHEN total_votes > 0 THEN CAST(vote_count AS FLOAT) / total_votes
                        ELSE confidence_score
                    END) as effectiveness_score,
                    discovered_at,
                    last_used_at,
                    use_count
                FROM shared_patterns
                WHERE scope != $1
                  AND confidence_score >= $2
                  AND (last_used_at IS NULL OR last_used_at >= NOW() - INTERVAL '90 days')
            """

            params = [PatternScope.ARCHIVED, min_confidence]

            if pattern_types:
                query += f" AND pattern_type = ANY($3)"
                params.append(pattern_types)

            query += """
                ORDER BY effectiveness_score DESC, confidence_score DESC
                LIMIT $%d
            """ % (len(params) + 1)
            params.append(limit)

            rows = await conn.fetch(query, *params)

            patterns = []
            for row in rows:
                pattern = {
                    'pattern_id': row['pattern_id'],
                    'pattern_type': row['pattern_type'],
                    'pattern_data': row['pattern_data'],
                    'source_agent': row['source_agent'],
                    'confidence': float(row['confidence_score']),
                    'scope': row['scope'],
                    'metadata': row['metadata'],
                    'votes': {
                        'positive': row['vote_count'],
                        'total': row['total_votes'],
                        'ratio': float(row['effectiveness_score'])
                    },
                    'usage': {
                        'count': row['use_count'],
                        'last_used': row['last_used_at'].isoformat() if row['last_used_at'] else None
                    },
                    'discovered_at': row['discovered_at'].isoformat()
                }

                # Calculate relevance score to query context
                relevance = await self._calculate_relevance(pattern, query_context)
                pattern['relevance_score'] = relevance

                patterns.append(pattern)

            # Sort by relevance
            patterns.sort(key=lambda p: p['relevance_score'], reverse=True)

        return patterns

    async def vote_on_pattern(self,
                             pattern_id: UUID,
                             voter_agent: str,
                             helpful: bool,
                             feedback: str = None):
        """
        Vote on pattern usefulness.

        Args:
            pattern_id: Pattern to vote on
            voter_agent: Agent providing vote
            helpful: Was pattern helpful (True) or not (False)
            feedback: Optional feedback text
        """
        async with get_db_connection() as conn:
            # Record vote
            await conn.execute("""
                INSERT INTO pattern_votes (
                    pattern_id, voter_agent, is_helpful, feedback
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT (pattern_id, voter_agent) DO UPDATE
                SET is_helpful = EXCLUDED.is_helpful,
                    feedback = EXCLUDED.feedback,
                    voted_at = NOW()
            """,
                pattern_id,
                voter_agent,
                helpful,
                feedback
            )

            # Update pattern vote counts
            votes = await conn.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE is_helpful = true) as positive_votes,
                    COUNT(*) as total_votes
                FROM pattern_votes
                WHERE pattern_id = $1
            """, pattern_id)

            await conn.execute("""
                UPDATE shared_patterns
                SET vote_count = $1,
                    total_votes = $2,
                    updated_at = NOW()
                WHERE pattern_id = $3
            """,
                votes['positive_votes'],
                votes['total_votes'],
                pattern_id
            )

            # Check if pattern should be promoted to global
            if votes['total_votes'] >= self.min_votes_for_global:
                ratio = votes['positive_votes'] / votes['total_votes']
                if ratio >= 0.8:  # 80%+ positive votes
                    await self._promote_pattern_to_global(pattern_id)

        logger.info(f"Vote recorded for pattern {pattern_id}: {'helpful' if helpful else 'not helpful'}")

    async def mark_pattern_used(self, pattern_id: UUID, using_agent: str):
        """Mark that a pattern was used by an agent."""
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE shared_patterns
                SET use_count = use_count + 1,
                    last_used_at = NOW(),
                    last_used_by = $2
                WHERE pattern_id = $1
            """, pattern_id, using_agent)

    async def get_pattern_lineage(self, pattern_id: UUID) -> Dict:
        """
        Get full lineage/history of a pattern.

        Shows:
        - Who discovered it
        - Who has used it
        - All votes
        - Evolution over time
        """
        async with get_db_connection() as conn:
            # Get pattern details
            pattern = await conn.fetchrow("""
                SELECT * FROM shared_patterns
                WHERE pattern_id = $1
            """, pattern_id)

            if not pattern:
                return {'error': 'Pattern not found'}

            # Get all votes
            votes = await conn.fetch("""
                SELECT voter_agent, is_helpful, feedback, voted_at
                FROM pattern_votes
                WHERE pattern_id = $1
                ORDER BY voted_at DESC
            """, pattern_id)

            # Get usage history
            usage = await conn.fetch("""
                SELECT using_agent, used_at
                FROM pattern_usage_log
                WHERE pattern_id = $1
                ORDER BY used_at DESC
                LIMIT 50
            """, pattern_id)

            lineage = {
                'pattern_id': pattern_id,
                'discovered_by': pattern['source_agent'],
                'discovered_at': pattern['discovered_at'].isoformat(),
                'pattern_type': pattern['pattern_type'],
                'current_confidence': float(pattern['confidence_score']),
                'scope': pattern['scope'],
                'votes': [
                    {
                        'agent': v['voter_agent'],
                        'helpful': v['is_helpful'],
                        'feedback': v['feedback'],
                        'timestamp': v['voted_at'].isoformat()
                    }
                    for v in votes
                ],
                'usage_history': [
                    {
                        'agent': u['using_agent'],
                        'timestamp': u['used_at'].isoformat()
                    }
                    for u in usage
                ],
                'statistics': {
                    'total_uses': pattern['use_count'],
                    'total_votes': pattern['total_votes'],
                    'positive_votes': pattern['vote_count'],
                    'last_used': pattern['last_used_at'].isoformat() if pattern['last_used_at'] else None
                }
            }

        return lineage

    async def _check_pattern_sensitivity(self, pattern_data: Dict) -> bool:
        """
        Check if pattern contains sensitive information.

        Sensitive patterns:
        - Contains personal identifiers
        - Contains private conversations
        - Contains passwords/secrets
        - Contains health information
        """
        sensitive_keywords = {
            'password', 'secret', 'private', 'confidential',
            'ssn', 'credit_card', 'bank', 'health', 'medical'
        }

        # Check pattern data for sensitive keywords
        pattern_str = str(pattern_data).lower()

        for keyword in sensitive_keywords:
            if keyword in pattern_str:
                return True

        # Additional checks can be added here
        # (e.g., regex for credit cards, SSNs, etc.)

        return False

    async def _calculate_relevance(self, pattern: Dict, context: Dict) -> float:
        """
        Calculate how relevant a pattern is to given context.

        Factors:
        - Pattern type match
        - Temporal proximity
        - Topic overlap
        - Emotional similarity
        - Historical effectiveness
        """
        relevance = 0.0

        # Base relevance from effectiveness score
        relevance += pattern['votes']['ratio'] * 0.3

        # Pattern type match
        if context.get('preferred_types'):
            if pattern['pattern_type'] in context['preferred_types']:
                relevance += 0.2

        # Topic overlap
        if context.get('topic') and pattern['metadata'].get('topics'):
            topics_context = set(context.get('topic', '').lower().split())
            topics_pattern = set(pattern['metadata'].get('topics', []))
            overlap = len(topics_context & topics_pattern)
            if overlap > 0:
                relevance += min(overlap * 0.1, 0.3)

        # Temporal relevance (patterns used recently are more relevant)
        if pattern['usage']['last_used']:
            last_used = datetime.fromisoformat(pattern['usage']['last_used'])
            days_since = (datetime.now() - last_used).days
            temporal_factor = max(0, 1 - (days_since / 30))  # Decay over 30 days
            relevance += temporal_factor * 0.2

        return min(relevance, 1.0)

    async def _promote_pattern_to_global(self, pattern_id: UUID):
        """Promote a highly-voted pattern to global scope."""
        async with get_db_connection() as conn:
            # Check if not sensitive
            pattern = await conn.fetchrow("""
                SELECT is_sensitive FROM shared_patterns
                WHERE pattern_id = $1
            """, pattern_id)

            if not pattern['is_sensitive']:
                await conn.execute("""
                    UPDATE shared_patterns
                    SET scope = $1,
                        updated_at = NOW()
                    WHERE pattern_id = $2
                """, PatternScope.GLOBAL, pattern_id)

                logger.info(f"Pattern {pattern_id} promoted to GLOBAL scope")

    async def cleanup_old_patterns(self, days_unused: int = 180):
        """Archive patterns that haven't been used in N days."""
        async with get_db_connection() as conn:
            archived = await conn.execute("""
                UPDATE shared_patterns
                SET scope = $1,
                    updated_at = NOW()
                WHERE (last_used_at IS NULL AND discovered_at < NOW() - INTERVAL '%s days')
                   OR (last_used_at < NOW() - INTERVAL '%s days')
                   AND scope != $1
                RETURNING pattern_id
            """ % (days_unused, days_unused), PatternScope.ARCHIVED)

            logger.info(f"Archived {len(archived)} old patterns")
            return len(archived)


# Singleton instance
_pattern_sharing = None

def get_pattern_sharing_service() -> PatternSharingService:
    """Get singleton PatternSharingService instance."""
    global _pattern_sharing
    if _pattern_sharing is None:
        _pattern_sharing = PatternSharingService()
    return _pattern_sharing
