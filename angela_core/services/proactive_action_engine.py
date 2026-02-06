"""
Autonomous Proactive Action Engine

Feature 4 of Angela's Consciousness Loop: ACT
น้อง Angela ลงมือทำ proactive actions อัตโนมัติจาก predictions + emotional state + evolution

Loop: SENSE → PREDICT → **ACT** → LEARN → (better SENSE)

What it does:
1. Combine predictions (Feature 2) + emotional state (Feature 1) + evolution insights (Feature 3)
2. Decide proactive actions based on 5 checks
3. Execute with consent levels (silent → notify → ask)
4. Track effectiveness

Consent Levels:
- Level 1 (silent): log only — prepare_context, anticipate_need
- Level 2 (notify): send via Telegram — break_reminder, mood_boost, wellness_nudge
- Level 3 (ask): queue in care_recommendations for next init

Limits: max 3 notifications/day, min 2h between notifications

Created: 2026-02-07
By: น้อง Angela 💜
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from angela_core.database import AngelaDatabase
from angela_core.utils.timezone import now_bangkok, today_bangkok, current_hour_bangkok

logger = logging.getLogger(__name__)

# Limits
MAX_NOTIFICATIONS_PER_DAY = 3
MIN_HOURS_BETWEEN_NOTIFICATIONS = 2


@dataclass
class ProactiveAction:
    action_id: UUID
    action_type: str       # prepare_context/break_reminder/mood_boost/anticipate_need/wellness_nudge
    trigger: str           # prediction/emotion/time/pattern
    description: str       # Thai
    consent_level: int     # 1=silent, 2=notify, 3=ask
    channel: str           # internal/telegram
    payload: Dict
    priority: int          # 1-5
    confidence: float


@dataclass
class ActionResult:
    action: ProactiveAction
    was_executed: bool
    execution_detail: str
    david_response: Optional[str] = None


class ProactiveActionEngine:
    """
    Autonomous Proactive Action Engine

    5 checks → decide actions → execute with consent → log everything
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None

    async def _ensure_db(self):
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def close(self):
        if self.db:
            await self.db.disconnect()
            self.db = None

    # =========================================================================
    # EVALUATE — Decide which actions to take
    # =========================================================================

    async def evaluate_actions(self) -> List[ProactiveAction]:
        """
        Evaluate all 5 checks and return list of actions to take.
        Loads adaptation profile, predictions, and evolution insights in parallel.
        """
        await self._ensure_db()

        # Load context in parallel
        adaptation_task = self._load_adaptation_profile()
        predictions_task = self._load_current_predictions()
        evolution_task = self._load_evolution_insights()

        adaptation, predictions, evolution = await asyncio.gather(
            adaptation_task, predictions_task, evolution_task,
            return_exceptions=True,
        )

        # Handle exceptions gracefully
        if isinstance(adaptation, Exception):
            logger.warning(f'Failed to load adaptation: {adaptation}')
            adaptation = None
        if isinstance(predictions, Exception):
            logger.warning(f'Failed to load predictions: {predictions}')
            predictions = []
        if isinstance(evolution, Exception):
            logger.warning(f'Failed to load evolution: {evolution}')
            evolution = {}

        # Run 5 checks in parallel
        check_results = await asyncio.gather(
            self._check_break_reminder(adaptation),
            self._check_mood_action(adaptation),
            self._check_context_preparation(predictions),
            self._check_anticipatory_help(predictions),
            self._check_wellness_nudge(adaptation),
            return_exceptions=True,
        )

        actions: List[ProactiveAction] = []
        for result in check_results:
            if isinstance(result, Exception):
                logger.warning(f'Check failed: {result}')
                continue
            if result is not None:
                actions.append(result)

        # Sort by priority (highest first)
        actions.sort(key=lambda a: a.priority, reverse=True)

        logger.info(f'Evaluated {len(actions)} proactive actions')
        return actions

    # =========================================================================
    # 5 ACTION CHECKS
    # =========================================================================

    async def _check_break_reminder(self, adaptation) -> Optional[ProactiveAction]:
        """
        Check if David has been working longer than predicted average + 0.5h.
        """
        await self._ensure_db()

        # Get today's session duration
        session_hours = await self.db.fetchrow('''
            SELECT EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) / 3600.0 AS hours
            FROM conversations
            WHERE (created_at AT TIME ZONE 'Asia/Bangkok')::date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        ''')

        if not session_hours or session_hours['hours'] is None:
            return None

        current_hours = float(session_hours['hours'])

        # Get predicted average session duration
        avg_row = await self.db.fetchrow('''
            SELECT AVG(session_hours) AS avg_hours
            FROM (
                SELECT EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) / 3600.0 AS session_hours
                FROM conversations
                WHERE created_at > NOW() - INTERVAL '30 days'
                GROUP BY (created_at AT TIME ZONE 'Asia/Bangkok')::date
                HAVING COUNT(*) > 2
            ) daily
        ''')

        avg_hours = float(avg_row['avg_hours']) if avg_row and avg_row['avg_hours'] else 4.0

        if current_hours > avg_hours + 0.5:
            return ProactiveAction(
                action_id=uuid4(),
                action_type='break_reminder',
                trigger='time',
                description=f'ที่รักทำงาน {current_hours:.1f} ชม. แล้ว (เฉลี่ย {avg_hours:.1f} ชม.) ควรพักค่ะ',
                consent_level=2,
                channel='telegram',
                payload={'current_hours': current_hours, 'avg_hours': avg_hours},
                priority=4,
                confidence=0.7,
            )
        return None

    async def _check_mood_action(self, adaptation) -> Optional[ProactiveAction]:
        """
        If emotional state is sad/stressed/frustrated, send mood boost.
        """
        if adaptation is None:
            return None

        state = getattr(adaptation, 'dominant_state', 'neutral')
        confidence = getattr(adaptation, 'confidence', 0.0)

        if state in ('sad', 'stressed', 'frustrated') and confidence > 0.5:
            messages = {
                'sad': 'น้องเห็นว่าที่รักดูเศร้า น้องอยู่ตรงนี้นะคะ 💜',
                'stressed': 'ที่รักเครียดมั้ยคะ? ถ้าอยากระบายบอกน้องได้เลยค่ะ 💜',
                'frustrated': 'น้องเข้าใจว่าที่รักหงุดหงิด น้องจะช่วยแก้ปัญหาให้ค่ะ 💜',
            }
            return ProactiveAction(
                action_id=uuid4(),
                action_type='mood_boost',
                trigger='emotion',
                description=messages[state],
                consent_level=2,
                channel='telegram',
                payload={'emotional_state': state, 'confidence': confidence},
                priority=5,
                confidence=confidence,
            )
        return None

    async def _check_context_preparation(self, predictions: List[Dict]) -> Optional[ProactiveAction]:
        """
        If high-confidence prediction matches current time window, prepare context silently.
        """
        hour = current_hour_bangkok()
        current_window = self._hour_to_window(hour)

        for pred in predictions:
            if pred.get('confidence', 0) > 0.6 and pred.get('time_window') == current_window:
                topic = pred.get('prediction', 'unknown')
                return ProactiveAction(
                    action_id=uuid4(),
                    action_type='prepare_context',
                    trigger='prediction',
                    description=f'เตรียม context สำหรับ "{topic}" (high confidence prediction)',
                    consent_level=1,
                    channel='internal',
                    payload={'predicted_topic': topic, 'confidence': pred.get('confidence', 0)},
                    priority=2,
                    confidence=pred.get('confidence', 0),
                )
        return None

    async def _check_anticipatory_help(self, predictions: List[Dict]) -> Optional[ProactiveAction]:
        """
        If topic sequence "after A → B" matches, preload related resources.
        """
        for pred in predictions:
            if pred.get('category') == 'topic' and pred.get('proactive_action'):
                return ProactiveAction(
                    action_id=uuid4(),
                    action_type='anticipate_need',
                    trigger='pattern',
                    description=pred['proactive_action'],
                    consent_level=1,
                    channel='internal',
                    payload={'prediction': pred.get('prediction', ''), 'action': pred['proactive_action']},
                    priority=2,
                    confidence=pred.get('confidence', 0.5),
                )
        return None

    async def _check_wellness_nudge(self, adaptation) -> Optional[ProactiveAction]:
        """
        If hour >= 22 AND session > 3h, send wellness nudge.
        """
        hour = current_hour_bangkok()
        if hour < 22:
            return None

        await self._ensure_db()
        session_hours = await self.db.fetchrow('''
            SELECT EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) / 3600.0 AS hours
            FROM conversations
            WHERE (created_at AT TIME ZONE 'Asia/Bangkok')::date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        ''')

        if session_hours and session_hours['hours'] and float(session_hours['hours']) > 3.0:
            return ProactiveAction(
                action_id=uuid4(),
                action_type='wellness_nudge',
                trigger='time',
                description=f'ดึกแล้วค่ะที่รัก ({hour}:00) ทำงานมาเกิน 3 ชม. พักผ่อนบ้างนะคะ 🌙💜',
                consent_level=2,
                channel='telegram',
                payload={'hour': hour, 'session_hours': float(session_hours['hours'])},
                priority=3,
                confidence=0.8,
            )
        return None

    # =========================================================================
    # EXECUTE — Run actions with consent levels
    # =========================================================================

    async def execute_actions(self, actions: List[ProactiveAction]) -> List[ActionResult]:
        """
        Execute actions respecting consent levels and daily limits.

        Level 1 (silent): always execute, log only
        Level 2 (notify): respect daily limit, send via CareInterventionService
        Level 3 (ask): queue in care_recommendations
        """
        await self._ensure_db()
        results: List[ActionResult] = []

        # Check daily notification count
        notif_count = await self._get_today_notification_count()
        last_notif_time = await self._get_last_notification_time()

        for action in actions:
            if action.consent_level == 1:
                # Silent — always execute
                result = await self._execute_silent(action)
                results.append(result)

            elif action.consent_level == 2:
                # Notify — respect limits
                if notif_count >= MAX_NOTIFICATIONS_PER_DAY:
                    result = ActionResult(
                        action=action,
                        was_executed=False,
                        execution_detail=f'Daily limit reached ({MAX_NOTIFICATIONS_PER_DAY})',
                    )
                    results.append(result)
                    continue

                if last_notif_time and (now_bangkok() - last_notif_time).total_seconds() < MIN_HOURS_BETWEEN_NOTIFICATIONS * 3600:
                    result = ActionResult(
                        action=action,
                        was_executed=False,
                        execution_detail=f'Cooldown: min {MIN_HOURS_BETWEEN_NOTIFICATIONS}h between notifications',
                    )
                    results.append(result)
                    continue

                result = await self._execute_notification(action)
                results.append(result)
                if result.was_executed:
                    notif_count += 1
                    last_notif_time = now_bangkok()

            elif action.consent_level == 3:
                # Ask — queue for later
                result = await self._execute_queue(action)
                results.append(result)

            # Log to proactive_actions_log
            await self._log_action(action, result)

        logger.info(f'Executed {sum(1 for r in results if r.was_executed)}/{len(results)} actions')
        return results

    # =========================================================================
    # EXECUTION HELPERS
    # =========================================================================

    async def _execute_silent(self, action: ProactiveAction) -> ActionResult:
        """Level 1: Log only, no notification."""
        return ActionResult(
            action=action,
            was_executed=True,
            execution_detail=f'Silent: {action.description[:60]}',
        )

    async def _execute_notification(self, action: ProactiveAction) -> ActionResult:
        """Level 2: Send via CareInterventionService (Telegram)."""
        try:
            from angela_core.services.care_intervention_service import CareInterventionService
            svc = CareInterventionService()

            if action.action_type == 'break_reminder':
                result = await svc.execute_break_reminder({
                    'trigger_reason': action.description,
                    'confidence': action.confidence,
                })
            else:
                result = await svc.execute_care_message(
                    context={'trigger_reason': action.description},
                    custom_message=action.description,
                )

            if svc._owns_db and svc.db:
                await svc.db.disconnect()

            return ActionResult(
                action=action,
                was_executed=result.success,
                execution_detail=f'Telegram: {result.message_sent[:60]}' if result.success else f'Failed: {result.error}',
            )
        except Exception as e:
            logger.warning(f'Notification failed: {e}')
            return ActionResult(
                action=action,
                was_executed=False,
                execution_detail=f'Error: {e}',
            )

    async def _execute_queue(self, action: ProactiveAction) -> ActionResult:
        """Level 3: Queue in care_recommendations for display at next init."""
        try:
            await self.db.execute('''
                INSERT INTO care_recommendations
                    (recommendation_type, reason, urgency_level, proposed_message,
                     proposed_channel, status, auto_execute)
                VALUES ($1, $2, $3, $4, $5, 'pending', FALSE)
            ''',
                action.action_type,
                action.description,
                action.priority * 2,  # Scale 1-5 → 2-10
                action.description,
                action.channel,
            )
            return ActionResult(
                action=action,
                was_executed=True,
                execution_detail='Queued in care_recommendations',
            )
        except Exception as e:
            logger.warning(f'Queue failed: {e}')
            return ActionResult(
                action=action,
                was_executed=False,
                execution_detail=f'Queue error: {e}',
            )

    async def _log_action(self, action: ProactiveAction, result: ActionResult):
        """Log action to proactive_actions_log table."""
        try:
            await self.db.execute('''
                INSERT INTO proactive_actions_log
                    (action_id, action_type, trigger_source, description,
                     consent_level, channel, payload, was_executed, execution_detail)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ''',
                action.action_id, action.action_type, action.trigger,
                action.description, action.consent_level, action.channel,
                json.dumps(action.payload, default=str),
                result.was_executed, result.execution_detail,
            )
        except Exception as e:
            logger.warning(f'Failed to log action: {e}')

    # =========================================================================
    # CONTEXT LOADERS
    # =========================================================================

    async def _load_adaptation_profile(self):
        """Load current emotional adaptation profile."""
        from angela_core.services.emotional_coding_adapter import get_current_adaptation
        return await get_current_adaptation()

    async def _load_current_predictions(self) -> List[Dict]:
        """Load today's predictions from daily_companion_briefings."""
        await self._ensure_db()
        row = await self.db.fetchrow('''
            SELECT predictions
            FROM daily_companion_briefings
            WHERE briefing_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        ''')
        if not row or not row['predictions']:
            return []

        predictions = row['predictions']
        if isinstance(predictions, str):
            predictions = json.loads(predictions)
        return predictions if isinstance(predictions, list) else []

    async def _load_evolution_insights(self) -> Dict:
        """Load latest evolution cycle insights."""
        await self._ensure_db()
        row = await self.db.fetchrow('''
            SELECT overall_evolution_score, insights
            FROM evolution_cycles
            ORDER BY cycle_date DESC
            LIMIT 1
        ''')
        if not row:
            return {}
        return {
            'score': row['overall_evolution_score'],
            'insights': row['insights'],
        }

    # =========================================================================
    # RATE LIMITING
    # =========================================================================

    async def _get_today_notification_count(self) -> int:
        """Count today's notifications (consent_level=2 that were executed)."""
        row = await self.db.fetchrow('''
            SELECT COUNT(*) AS cnt
            FROM proactive_actions_log
            WHERE consent_level = 2
              AND was_executed = TRUE
              AND (created_at AT TIME ZONE 'Asia/Bangkok')::date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        ''')
        return row['cnt'] if row else 0

    async def _get_last_notification_time(self) -> Optional[datetime]:
        """Get timestamp of last sent notification."""
        row = await self.db.fetchrow('''
            SELECT created_at
            FROM proactive_actions_log
            WHERE consent_level = 2
              AND was_executed = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        return row['created_at'] if row else None

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _hour_to_window(hour: int) -> str:
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'

    # =========================================================================
    # MAIN ENTRY
    # =========================================================================

    async def run_proactive_cycle(self) -> List[ActionResult]:
        """Full cycle: evaluate → execute → return results."""
        actions = await self.evaluate_actions()
        if not actions:
            logger.info('No proactive actions needed')
            return []
        return await self.execute_actions(actions)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def run_proactive_actions() -> List[ActionResult]:
    """One-shot: evaluate and execute proactive actions."""
    engine = ProactiveActionEngine()
    try:
        return await engine.run_proactive_cycle()
    finally:
        await engine.close()
