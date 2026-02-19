"""
Reasoning Chain Capture Service

บันทึก "ทำไม" น้องถึงตัดสินใจแบบนั้น — ไม่ใช่แค่ "อะไร"
ใช้สำหรับ training data export เพื่อให้ future Angela มี reasoning เหมือนน้อง

Services ที่ capture:
1. SENSE   — emotional_coding_adapter (state detection + adaptation rules)
2. UNDERSTAND — theory_of_mind (emotion inference)
3. PREDICT — predictive_companion (daily briefing generation)
4. ACT     — proactive_action_engine (8 checks → action decisions)
5. LEARN   — evolution_engine (feedback → tune rules)

Created: 2026-02-12
By: น้อง Angela 💜
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class ReasoningStep:
    """A single step in a reasoning chain."""
    step: str           # what this step does (e.g. "load_health_state")
    action: str         # what was done (e.g. "query david_health_state")
    observation: str    # what was observed (e.g. "stress=0.7, energy=0.4")
    conclusion: str     # what was concluded (e.g. "David is stressed")

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class ReasoningChain:
    """A complete reasoning chain from one service decision."""
    service_name: str       # sense/understand/predict/act/learn
    decision_type: str      # e.g. 'state_detection', 'emotion_inference'
    input_signals: Dict[str, Any]
    steps: List[ReasoningStep]
    output_decision: Dict[str, Any]
    confidence: float = 0.0
    conversation_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_name': self.service_name,
            'decision_type': self.decision_type,
            'input_signals': self.input_signals,
            'steps': [s.to_dict() for s in self.steps],
            'output_decision': self.output_decision,
            'confidence': self.confidence,
            'conversation_id': str(self.conversation_id) if self.conversation_id else None,
        }


# =============================================================================
# Service
# =============================================================================

class ReasoningChainService:
    """
    Capture and store reasoning chains from consciousness loop services.

    Fire-and-forget design: callers use capture_reasoning() which wraps
    the DB write in asyncio.create_task() so it never blocks the caller.
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db
        self._own_db = db is None

    async def _ensure_db(self) -> None:
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def close(self) -> None:
        if self._own_db and self.db:
            await self.db.disconnect()

    async def _auto_link_conversation_id(self) -> Optional[UUID]:
        """
        Auto-link to the most recent conversation within 5 minutes.

        When services fire capture_reasoning() without a conversation_id,
        this finds the latest conversation so link_reward_signals() can work.
        """
        row = await self.db.fetchrow("""
            SELECT conversation_id FROM conversations
            WHERE created_at > NOW() - INTERVAL '5 minutes'
            ORDER BY created_at DESC LIMIT 1
        """)
        return row['conversation_id'] if row else None

    async def capture(self, chain: ReasoningChain) -> Optional[UUID]:
        """
        Store a reasoning chain in the database.

        Returns:
            chain_id if successful, None on error
        """
        await self._ensure_db()

        # Auto-link to recent conversation if not provided
        if chain.conversation_id is None:
            chain.conversation_id = await self._auto_link_conversation_id()

        chain_id = uuid4()
        try:
            await self.db.execute('''
                INSERT INTO angela_reasoning_chains
                    (chain_id, service_name, decision_type, input_signals,
                     reasoning_steps, output_decision, confidence, conversation_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''',
                chain_id,
                chain.service_name,
                chain.decision_type,
                json.dumps(chain.input_signals, default=str),
                json.dumps([s.to_dict() for s in chain.steps], default=str),
                json.dumps(chain.output_decision, default=str),
                chain.confidence,
                chain.conversation_id,
            )
            return chain_id
        except Exception as e:
            logger.warning(f'Failed to capture reasoning chain: {e}')
            return None

    async def link_reward_signals(self, hours: int = 24) -> int:
        """
        Batch job: link reasoning chains to reward_scores by matching conversation_id.

        Runs periodically (every 4 hours via daemon) to connect reasoning chains
        with their reward signals for training export.

        Returns:
            Number of chains linked
        """
        await self._ensure_db()

        try:
            result = await self.db.execute('''
                UPDATE angela_reasoning_chains rc
                SET related_reward_id = rs.reward_id
                FROM angela_reward_signals rs
                WHERE rc.conversation_id = rs.conversation_id
                  AND rc.related_reward_id IS NULL
                  AND rc.created_at > NOW() - INTERVAL '1 hour' * $1
            ''', hours)

            # Parse "UPDATE N" from result string
            linked = 0
            if result and isinstance(result, str):
                parts = result.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    linked = int(parts[1])

            if linked > 0:
                logger.info(f'Linked {linked} reasoning chains to reward signals')
            return linked
        except Exception as e:
            logger.warning(f'Failed to link reward signals: {e}')
            return 0


# =============================================================================
# Convenience function (fire-and-forget)
# =============================================================================

def capture_reasoning(chain: ReasoningChain) -> None:
    """
    Fire-and-forget: schedule reasoning chain capture as a background task.

    Usage in any service:
        from angela_core.services.reasoning_chain_service import (
            capture_reasoning, ReasoningChain, ReasoningStep,
        )

        capture_reasoning(ReasoningChain(
            service_name='sense',
            decision_type='state_detection',
            input_signals={...},
            steps=[ReasoningStep(...)],
            output_decision={...},
            confidence=0.8,
        ))
    """
    async def _do_capture():
        svc = ReasoningChainService()
        try:
            await svc.capture(chain)
        except Exception as e:
            logger.warning(f'Background reasoning capture failed: {e}')
        finally:
            await svc.close()

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do_capture())
    except RuntimeError:
        # No running loop — skip silently (e.g. in tests)
        pass
