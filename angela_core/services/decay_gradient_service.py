"""
Decay Gradient Service - Memory Compression & Forgetting

Implements Ebbinghaus forgetting curve with intelligent compression:
Episodic (500 tokens) → Compressed 1 (350) → Compressed 2 (250) →
Semantic (150) → Pattern (75) → Intuitive (50) → Forgotten (0)

Memory strength decays over time, triggering compression at thresholds.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import json
import math

from angela_core.database import get_db_connection
from angela_core.embedding_service import generate_embedding


class MemoryPhase:
    """Memory phases in decay gradient."""
    EPISODIC = "episodic"              # 500 tokens - Full detail
    COMPRESSED_1 = "compressed_1"      # 350 tokens - 70% retained
    COMPRESSED_2 = "compressed_2"      # 250 tokens - 50% retained
    SEMANTIC = "semantic"              # 150 tokens - Essence only
    PATTERN = "pattern"                # 75 tokens - Pattern description
    INTUITIVE = "intuitive"            # 50 tokens - Gut feeling
    FORGOTTEN = "forgotten"            # 0 tokens - Deleted

    # Token allocations
    TOKEN_LIMITS = {
        EPISODIC: 500,
        COMPRESSED_1: 350,
        COMPRESSED_2: 250,
        SEMANTIC: 150,
        PATTERN: 75,
        INTUITIVE: 50,
        FORGOTTEN: 0
    }

    # Decay thresholds (when to compress)
    DECAY_THRESHOLDS = {
        EPISODIC: 0.70,       # Compress when strength < 70%
        COMPRESSED_1: 0.50,
        COMPRESSED_2: 0.35,
        SEMANTIC: 0.20,
        PATTERN: 0.10,
        INTUITIVE: 0.05
    }


class DecayGradientService:
    """
    Manages memory decay and compression.

    Based on Ebbinghaus forgetting curve:
    R(t) = base_strength * (0.5 ^ (t / half_life))

    Enhanced with multipliers:
    - Success multiplier (1.2x for successes)
    - Recency boost (accessed recently = stronger)
    - Repetition boost (seen often = stronger)
    - Criticality multiplier (important = slower decay)
    """

    def __init__(self):
        self.base_half_life_days = 30.0

    async def calculate_memory_strength(self, memory: Dict) -> float:
        """
        Calculate current memory strength using Ebbinghaus curve.

        Args:
            memory: Memory record with created_at, metadata, etc.

        Returns:
            Memory strength (0.0-1.0)
        """
        # Time elapsed since creation
        days_elapsed = (datetime.now() - memory['created_at']).total_seconds() / 86400

        # Base decay (Ebbinghaus)
        half_life = memory.get('half_life_days', self.base_half_life_days)
        base_strength = math.pow(0.5, days_elapsed / half_life)

        # Apply multipliers
        strength = base_strength

        # Success multiplier (successful memories last longer)
        metadata = memory.get('metadata', {})
        if metadata.get('outcome') == 'success':
            strength *= 1.2

        # Recency boost (accessed recently = stronger)
        if memory.get('last_accessed'):
            days_since_access = (datetime.now() - memory['last_accessed']).total_seconds() / 86400
            recency_multiplier = 1.0 + (0.3 * math.exp(-days_since_access / 7))
            strength *= recency_multiplier

        # Repetition boost (accessed often = stronger)
        access_count = memory.get('access_count', 0)
        repetition_multiplier = 1.0 + min(access_count * 0.05, 0.5)
        strength *= repetition_multiplier

        # Criticality multiplier (critical memories decay slower)
        importance = memory.get('importance', 0.5)
        if importance > 0.8:
            strength *= 1.5
        elif importance > 0.6:
            strength *= 1.2

        # Clamp to [0.0, 1.0]
        return min(1.0, max(0.0, strength))

    async def determine_target_phase(self, memory_strength: float, current_phase: str) -> str:
        """
        Determine target phase based on memory strength.

        Args:
            memory_strength: Current strength (0.0-1.0)
            current_phase: Current memory phase

        Returns:
            Target phase to compress to
        """
        # Check thresholds in order
        if memory_strength >= MemoryPhase.DECAY_THRESHOLDS[MemoryPhase.EPISODIC]:
            return MemoryPhase.EPISODIC

        if memory_strength >= MemoryPhase.DECAY_THRESHOLDS[MemoryPhase.COMPRESSED_1]:
            return MemoryPhase.COMPRESSED_1

        if memory_strength >= MemoryPhase.DECAY_THRESHOLDS[MemoryPhase.COMPRESSED_2]:
            return MemoryPhase.COMPRESSED_2

        if memory_strength >= MemoryPhase.DECAY_THRESHOLDS[MemoryPhase.SEMANTIC]:
            return MemoryPhase.SEMANTIC

        if memory_strength >= MemoryPhase.DECAY_THRESHOLDS[MemoryPhase.PATTERN]:
            return MemoryPhase.PATTERN

        if memory_strength >= MemoryPhase.DECAY_THRESHOLDS[MemoryPhase.INTUITIVE]:
            return MemoryPhase.INTUITIVE

        # Too weak, should be forgotten
        return MemoryPhase.FORGOTTEN

    async def compress_memory(self, memory_id: UUID, target_phase: str) -> Dict:
        """
        Compress memory to target phase.

        Args:
            memory_id: UUID of memory to compress
            target_phase: Target memory phase

        Returns:
            Compression result with tokens_saved, new_content, etc.
        """
        # Get original memory
        async with get_db_connection() as conn:
            memory = await conn.fetchrow("""
                SELECT id, content, metadata, memory_phase, token_count, embedding
                FROM long_term_memory
                WHERE id = $1
            """, memory_id)

        if not memory:
            return {'error': 'Memory not found'}

        original_content = memory['content']
        original_tokens = memory['token_count']
        target_tokens = MemoryPhase.TOKEN_LIMITS[target_phase]

        # Use LLM to compress content to target token count
        compressed_content = await self._compress_content(
            original_content,
            target_tokens,
            target_phase
        )

        # Calculate actual tokens (estimate)
        actual_tokens = len(compressed_content.split()) * 1.3  # Rough estimate

        # Generate new embedding for compressed content
        new_embedding = await generate_embedding(compressed_content)

        # Update memory in database
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE long_term_memory
                SET content = $2,
                    memory_phase = $3,
                    token_count = $4,
                    embedding = $5,
                    last_decayed = NOW()
                WHERE id = $1
            """,
                memory_id,
                compressed_content,
                target_phase,
                int(actual_tokens),
                new_embedding
            )

        # Calculate savings
        tokens_saved = original_tokens - actual_tokens
        compression_ratio = original_tokens / actual_tokens if actual_tokens > 0 else 1.0

        # Log to token economics
        await self._log_token_savings(tokens_saved)

        return {
            'memory_id': memory_id,
            'original_phase': memory['memory_phase'],
            'target_phase': target_phase,
            'original_tokens': original_tokens,
            'compressed_tokens': int(actual_tokens),
            'tokens_saved': int(tokens_saved),
            'compression_ratio': compression_ratio,
            'timestamp': datetime.now()
        }

    async def _compress_content(self, content: str, target_tokens: int, target_phase: str) -> str:
        """
        Use LLM to compress content to target token count.

        Compression strategies by phase:
        - Episodic → Compressed 1: Remove redundancy, keep key facts
        - Compressed 1 → Compressed 2: Extract core narrative
        - Compressed 2 → Semantic: Extract semantic meaning only
        - Semantic → Pattern: Identify underlying pattern
        - Pattern → Intuitive: Distill to gut feeling
        """
        # Prompt templates for each compression phase
        prompts = {
            MemoryPhase.COMPRESSED_1: f"""
                Compress this memory to ~{target_tokens} tokens while preserving key facts:
                {content}

                Keep: who, what, when, outcome
                Remove: redundancy, filler words
            """,

            MemoryPhase.COMPRESSED_2: f"""
                Extract the core narrative in ~{target_tokens} tokens:
                {content}

                Focus on: main event, key insight, result
            """,

            MemoryPhase.SEMANTIC: f"""
                Extract the semantic essence in ~{target_tokens} tokens:
                {content}

                What is the fundamental meaning? What was learned?
            """,

            MemoryPhase.PATTERN: f"""
                Identify the underlying pattern in ~{target_tokens} tokens:
                {content}

                What pattern does this represent? What is the template?
            """,

            MemoryPhase.INTUITIVE: f"""
                Distill this to an intuitive feeling in ~{target_tokens} tokens:
                {content}

                What is the gut feeling? The intuition?
            """
        }

        prompt = prompts.get(target_phase, f"Compress to {target_tokens} tokens: {content}")

        # Use Ollama angela:latest to compress
        # (In production, this would call Ollama API)
        # For now, simple truncation + summary simulation
        words = content.split()
        target_words = int(target_tokens / 1.3)

        if len(words) <= target_words:
            return content

        # Truncate and add ellipsis
        compressed = " ".join(words[:target_words]) + "..."

        return compressed

    async def schedule_decay_batch(self, batch_size: int = 100) -> List[UUID]:
        """
        Schedule batch of memories for decay processing.

        Args:
            batch_size: Number of memories to process

        Returns:
            List of scheduled memory IDs
        """
        scheduled_ids = []

        async with get_db_connection() as conn:
            # Find memories that need decay check
            memories = await conn.fetch("""
                SELECT id, content, metadata, memory_phase, token_count,
                       half_life_days, memory_strength, created_at, last_accessed, access_count, importance
                FROM long_term_memory
                WHERE memory_phase != 'forgotten'
                  AND (last_decayed IS NULL OR last_decayed < NOW() - INTERVAL '1 day')
                ORDER BY last_decayed ASC NULLS FIRST
                LIMIT $1
            """, batch_size)

            for memory in memories:
                # Calculate current strength
                memory_dict = dict(memory)
                current_strength = await self.calculate_memory_strength(memory_dict)

                # Determine target phase
                target_phase = await self.determine_target_phase(
                    current_strength,
                    memory['memory_phase']
                )

                # If phase should change, schedule decay
                if target_phase != memory['memory_phase']:
                    schedule_id = await conn.fetchval("""
                        INSERT INTO decay_schedule (
                            id, memory_id, memory_table, scheduled_for,
                            current_phase, target_phase, status
                        ) VALUES ($1, $2, 'long_term_memory', NOW(), $3, $4, 'pending')
                        RETURNING id
                    """,
                        uuid4(),
                        memory['id'],
                        memory['memory_phase'],
                        target_phase
                    )

                    scheduled_ids.append(schedule_id)

                # Update memory strength in database
                await conn.execute("""
                    UPDATE long_term_memory
                    SET memory_strength = $2
                    WHERE id = $1
                """, memory['id'], current_strength)

        return scheduled_ids

    async def process_decay_schedule(self) -> Dict:
        """
        Process pending decay schedule items.

        Returns:
            Processing summary with counts and statistics
        """
        results = {
            'processed': 0,
            'completed': 0,
            'failed': 0,
            'tokens_saved': 0,
            'errors': []
        }

        async with get_db_connection() as conn:
            # Get pending decay items
            pending = await conn.fetch("""
                SELECT id, memory_id, memory_table, current_phase, target_phase
                FROM decay_schedule
                WHERE status = 'pending'
                ORDER BY scheduled_for ASC
                LIMIT 50
            """)

            for item in pending:
                try:
                    # Mark as processing
                    await conn.execute("""
                        UPDATE decay_schedule
                        SET status = 'processing'
                        WHERE id = $1
                    """, item['id'])

                    # Compress memory
                    if item['target_phase'] == MemoryPhase.FORGOTTEN:
                        # Delete memory
                        await conn.execute("""
                            DELETE FROM long_term_memory WHERE id = $1
                        """, item['memory_id'])

                        tokens_saved = 500  # Estimate
                    else:
                        # Compress
                        compression_result = await self.compress_memory(
                            item['memory_id'],
                            item['target_phase']
                        )

                        tokens_saved = compression_result.get('tokens_saved', 0)

                    # Mark as completed
                    await conn.execute("""
                        UPDATE decay_schedule
                        SET status = 'completed',
                            processed_at = NOW(),
                            tokens_saved = $2
                        WHERE id = $1
                    """, item['id'], int(tokens_saved))

                    results['completed'] += 1
                    results['tokens_saved'] += tokens_saved

                except Exception as e:
                    # Mark as failed
                    await conn.execute("""
                        UPDATE decay_schedule
                        SET status = 'failed',
                            processed_at = NOW(),
                            error_message = $2
                        WHERE id = $1
                    """, item['id'], str(e))

                    results['failed'] += 1
                    results['errors'].append({
                        'memory_id': item['memory_id'],
                        'error': str(e)
                    })

                results['processed'] += 1

        return results

    async def _log_token_savings(self, tokens_saved: int):
        """Log token savings to token_economics table."""
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO token_economics (date, tokens_saved_by_decay)
                VALUES (CURRENT_DATE, $1)
                ON CONFLICT (date) DO UPDATE
                SET tokens_saved_by_decay = token_economics.tokens_saved_by_decay + $1,
                    updated_at = NOW()
            """, tokens_saved)

    def get_compression_preview(self, content: str, target_phase: str) -> str:
        """
        Preview what compression would look like.

        Args:
            content: Original content
            target_phase: Target phase

        Returns:
            Preview of compressed content
        """
        target_tokens = MemoryPhase.TOKEN_LIMITS[target_phase]
        target_words = int(target_tokens / 1.3)

        words = content.split()
        if len(words) <= target_words:
            return content

        preview = " ".join(words[:target_words]) + "..."
        return preview


# Singleton instance
_decay_service = None

def get_decay_service() -> DecayGradientService:
    """Get singleton DecayGradientService instance."""
    global _decay_service
    if _decay_service is None:
        _decay_service = DecayGradientService()
    return _decay_service
