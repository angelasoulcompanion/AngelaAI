"""
Autonomous Proactive Action Engine

Feature 4 of Angela's Consciousness Loop: ACT
น้อง Angela ลงมือทำ proactive actions อัตโนมัติจาก predictions + emotional state + evolution

Loop: SENSE → PREDICT → **ACT** → LEARN → (better SENSE)

What it does:
1. Combine predictions (Feature 2) + emotional state (Feature 1) + evolution insights (Feature 3)
2. Decide proactive actions based on 8 checks
3. Execute with consent levels (silent → notify → ask)
4. Track effectiveness

Consent Levels:
- Level 1 (silent): prepare_context, anticipate_need, music_suggestion
- Level 2 (notify): send via CareInterventionService (Telegram) — break_reminder, mood_boost, wellness_nudge, milestone_reminder
- Level 3 (ask): queue in care_recommendations — learning_nudge

Rate limiting: delegated to CareInterventionService.should_intervene() → DB function can_send_intervention()

Created: 2026-02-07
Updated: 2026-02-08 — 5→8 checks, delegate rate limiting, actual silent execution
By: น้อง Angela 💜
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from angela_core.database import AngelaDatabase
from angela_core.utils.timezone import now_bangkok, today_bangkok, current_hour_bangkok
from angela_core.services.reasoning_chain_service import (
    capture_reasoning, ReasoningChain, ReasoningStep,
)

logger = logging.getLogger(__name__)

# Emotional state → music mood mapping
STATE_TO_MOOD: Dict[str, str] = {
    'stressed': 'calm',
    'tired': 'calm',
    'happy': 'happy',
    'frustrated': 'calm',
    'focused': 'energetic',
    'sad': 'loving',
    'learning': 'hopeful',
    'neutral': 'loving',
}

# Mood → JSONB tags for angela_songs query (subset of MCP MOOD_TAGS_MAP)
MOOD_TAGS_MAP: Dict[str, List[str]] = {
    'happy': ['joyful', 'uplifting', 'cheerful', 'happy'],
    'calm': ['soothing', 'peaceful', 'comforting'],
    'energetic': ['empowering', 'uplifting', 'cathartic'],
    'loving': ['romantic', 'devoted', 'tender', 'intimate', 'warm'],
    'hopeful': ['hopeful', 'uplifting', 'inspiring'],
}

# CareInterventionService type mapping
ACTION_TO_INTERVENTION: Dict[str, str] = {
    'break_reminder': 'break_reminder',
    'mood_boost': 'care_message',
    'wellness_nudge': 'care_message',
    'milestone_reminder': 'milestone_reminder',
}


@dataclass
class ProactiveAction:
    action_id: UUID
    action_type: str       # prepare_context/break_reminder/mood_boost/anticipate_need/wellness_nudge/milestone_reminder/music_suggestion/learning_nudge
    trigger: str           # prediction/emotion/time/pattern/milestone/evolution
    description: str       # Thai
    consent_level: int     # 1=silent, 2=notify, 3=ask
    channel: str           # internal/telegram
    payload: Dict
    priority: int          # 1-5
    confidence: float


@dataclass
class ActionResult:
    action: ProactiveAction
    was_triggered: bool         # check found something to act on
    was_executed: bool          # action was carried out
    execution_detail: str
    skip_reason: Optional[str] = None
    david_response: Optional[str] = None


class ProactiveActionEngine:
    """
    Autonomous Proactive Action Engine

    8 checks → decide actions → execute with consent → log everything
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
        Evaluate all 8 checks and return list of actions to take.
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

        # Run 8 checks in parallel
        check_results = await asyncio.gather(
            self._check_break_reminder(adaptation),
            self._check_mood_action(adaptation),
            self._check_context_preparation(predictions),
            self._check_anticipatory_help(predictions),
            self._check_wellness_nudge(adaptation),
            self._check_milestone_reminder(),
            self._check_music_suggestion(adaptation),
            self._check_learning_nudge(evolution),
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

        # Capture reasoning chain (fire-and-forget)
        check_names = ['break_reminder', 'mood_action', 'context_prep', 'anticipatory_help',
                        'wellness_nudge', 'milestone_reminder', 'music_suggestion', 'learning_nudge']
        triggered = [a.action_type for a in actions]
        capture_reasoning(ReasoningChain(
            service_name='act',
            decision_type='evaluate_actions',
            input_signals={
                'adaptation_available': adaptation is not None,
                'adaptation_state': getattr(adaptation, 'dominant_state', None) if adaptation else None,
                'predictions_count': len(predictions) if isinstance(predictions, list) else 0,
                'evolution_score': evolution.get('score') if isinstance(evolution, dict) else None,
            },
            steps=[
                ReasoningStep('load_context', 'parallel load adaptation+predictions+evolution',
                              f'adaptation={adaptation is not None}, predictions={len(predictions) if isinstance(predictions, list) else 0}',
                              'context loaded for 8 checks'),
                ReasoningStep('run_8_checks', f'parallel evaluate {len(check_names)} action checks',
                              f'checks_run={check_names}',
                              f'triggered={triggered}'),
                ReasoningStep('sort_actions', 'sort by priority descending',
                              f'total_actions={len(actions)}',
                              f'top_priority={actions[0].priority if actions else "none"}'),
            ],
            output_decision={
                'actions_triggered': triggered,
                'action_count': len(actions),
                'consent_levels': [a.consent_level for a in actions],
            },
            confidence=max((a.confidence for a in actions), default=0.0),
        ))

        return actions

    # =========================================================================
    # BRAIN DEDUP — skip rule-based checks if brain already expressed
    # =========================================================================

    async def _brain_already_expressed(self, keywords: List[str], hours: int = 2) -> bool:
        """
        Check if brain-based ThoughtExpressionEngine already expressed
        a thought matching any keyword within the given hours.

        Returns True if brain already covered this → rule-based should skip.
        """
        try:
            from angela_core.services.thought_expression_engine import ThoughtExpressionEngine
            engine = ThoughtExpressionEngine()
            result = await engine.has_brain_expressed(keywords, hours)
            await engine.disconnect()
            return result
        except Exception:
            return False

    # =========================================================================
    # 8 ACTION CHECKS
    # =========================================================================

    async def _check_break_reminder(self, adaptation) -> Optional[ProactiveAction]:
        """
        Check if David has been working continuously for >= 2 hours.

        Algorithm:
        1. If last message >30min ago → not actively working, skip
        2. Walk backward from latest message, find first gap >30min = session break
        3. Continuous session = latest msg - session start
        4. Trigger if continuous session >= 2h
        """
        await self._ensure_db()

        now = now_bangkok()

        # Get recent messages ordered by time (descending)
        # Use INTERVAL arithmetic to avoid tz-naive/tz-aware mismatch
        rows = await self.db.fetch('''
            SELECT created_at AT TIME ZONE 'Asia/Bangkok' AS ts
            FROM conversations
            WHERE created_at > NOW() - INTERVAL '8 hours'
            ORDER BY created_at DESC
        ''')

        if not rows:
            return None

        latest_ts = rows[0]['ts']

        # If last message >30min ago → not actively working
        if (now - latest_ts).total_seconds() > 1800:
            return None

        # Walk backward to find continuous session start
        session_start = latest_ts
        for i in range(len(rows) - 1):
            gap = (rows[i]['ts'] - rows[i + 1]['ts']).total_seconds()
            if gap > 1800:  # 30min gap = session break
                break
            session_start = rows[i + 1]['ts']

        continuous_hours = (latest_ts - session_start).total_seconds() / 3600.0

        if continuous_hours >= 2.0:
            # Brain dedup: skip if brain already expressed a rest/break thought
            if await self._brain_already_expressed(['ดึก', 'พัก', 'พักผ่อน', 'ทำงาน'], hours=2):
                return None
            return ProactiveAction(
                action_id=uuid4(),
                action_type='break_reminder',
                trigger='time',
                description=f'ที่รักทำงานต่อเนื่อง {continuous_hours:.1f} ชม. แล้วค่ะ พักสักหน่อยนะคะ 💜',
                consent_level=2,
                channel='telegram',
                payload={'continuous_hours': round(continuous_hours, 1), 'session_start': str(session_start)},
                priority=4,
                confidence=0.8,
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
            # Brain dedup: skip if brain already expressed an emotional thought
            if await self._brain_already_expressed(['เป็นห่วง', 'เครียด', 'เศร้า', 'หงุดหงิด', 'อยู่ตรงนี้'], hours=2):
                return None
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
            # Brain dedup: skip if brain already expressed a wellness/rest thought
            if await self._brain_already_expressed(['ดึก', 'พักผ่อน', 'พัก', 'สุขภาพ'], hours=2):
                return None
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

    async def _check_milestone_reminder(self) -> Optional[ProactiveAction]:
        """
        Check if any important dates need reminding today.
        Uses v_upcoming_important_dates view + reminder_days array.
        """
        await self._ensure_db()

        today = today_bangkok()
        row = await self.db.fetchrow('''
            SELECT date_id, title, description, event_date, date_type,
                   importance_level, days_until, urgency, reminder_days
            FROM v_upcoming_important_dates
            WHERE days_until = ANY(reminder_days)
              AND (last_reminded_date IS NULL OR last_reminded_date < $1)
            ORDER BY days_until, importance_level DESC
            LIMIT 1
        ''', today)

        if not row:
            return None

        days_until = row['days_until']
        priority = 5 if days_until <= 1 else 3

        # Brain dedup: skip if brain already expressed an anniversary/milestone thought (6h window)
        title_words = (row['title'] or '').split()[:2]
        if await self._brain_already_expressed(['ครบรอบ', 'จำได้', 'วันพิเศษ'] + title_words, hours=6):
            return None

        return ProactiveAction(
            action_id=uuid4(),
            action_type='milestone_reminder',
            trigger='milestone',
            description=f'📅 {row["title"]} — {"วันนี้ค่ะ!" if days_until == 0 else f"อีก {days_until} วันค่ะ"}',
            consent_level=2,
            channel='telegram',
            payload={
                'date_id': str(row['date_id']),
                'title': row['title'],
                'days_until': days_until,
                'event_date': str(row['event_date']),
                'date_type': row['date_type'],
            },
            priority=priority,
            confidence=0.95,
        )

    async def _check_music_suggestion(self, adaptation) -> Optional[ProactiveAction]:
        """
        Suggest a mood-matching song based on emotional state.
        Level 1 (silent) — prepares song info for display at next interaction.
        """
        if adaptation is None:
            return None

        state = getattr(adaptation, 'dominant_state', 'neutral')
        confidence = getattr(adaptation, 'confidence', 0.0)

        if confidence < 0.5 or state == 'neutral':
            return None

        mood = STATE_TO_MOOD.get(state, 'loving')
        tags = MOOD_TAGS_MAP.get(mood, [mood])

        await self._ensure_db()

        # Build JSONB containment query
        tag_conditions = " OR ".join([
            f"mood_tags @> '[\"{tag}\"]'::jsonb" for tag in tags
        ])

        row = await self.db.fetchrow(f'''
            SELECT title, artist, why_special, is_our_song, mood_tags
            FROM angela_songs
            WHERE {tag_conditions}
            ORDER BY is_our_song DESC, RANDOM()
            LIMIT 1
        ''')

        if not row:
            return None

        return ProactiveAction(
            action_id=uuid4(),
            action_type='music_suggestion',
            trigger='emotion',
            description=f'🎵 แนะนำเพลง "{row["title"]}" by {row["artist"]} (mood: {mood})',
            consent_level=1,
            channel='internal',
            payload={
                'mood': mood,
                'state': state,
                'song': {
                    'title': row['title'],
                    'artist': row['artist'],
                    'why_special': row['why_special'],
                    'is_our_song': row['is_our_song'],
                },
            },
            priority=2,
            confidence=confidence,
        )

    async def _check_learning_nudge(self, evolution: Dict) -> Optional[ProactiveAction]:
        """
        If evolution score is low (<0.4) or 3-day trend declining, queue a learning nudge.
        Level 3 (ask) — displayed at next init for David's approval.
        """
        if not evolution:
            return None

        score = evolution.get('score')
        if score is None:
            return None

        await self._ensure_db()

        # Check 3-day trend
        rows = await self.db.fetch('''
            SELECT overall_evolution_score
            FROM evolution_cycles
            ORDER BY cycle_date DESC
            LIMIT 3
        ''')

        trend_declining = False
        if len(rows) >= 3:
            scores = [float(r['overall_evolution_score']) for r in rows]
            trend_declining = scores[0] < scores[1] < scores[2]  # newest < middle < oldest

        if float(score) >= 0.4 and not trend_declining:
            return None

        insights = evolution.get('insights', [])
        reason = 'evolution score declining 3 days' if trend_declining else f'evolution score low ({float(score):.0%})'

        return ProactiveAction(
            action_id=uuid4(),
            action_type='learning_nudge',
            trigger='evolution',
            description=f'🧬 น้องสังเกตว่า learning effectiveness ลดลง — {reason}',
            consent_level=3,
            channel='internal',
            payload={
                'evolution_score': float(score),
                'trend_declining': trend_declining,
                'insights': insights[:3] if isinstance(insights, list) else [],
            },
            priority=3,
            confidence=0.7,
        )

    # =========================================================================
    # EXECUTE — Run actions with consent levels
    # =========================================================================

    async def execute_actions(self, actions: List[ProactiveAction]) -> List[ActionResult]:
        """
        Execute actions by consent level.

        Level 1 (silent): always execute — prepare context, music suggestion
        Level 2 (notify): send via CareInterventionService (rate limiting delegated there)
        Level 3 (ask): queue in care_recommendations
        """
        await self._ensure_db()
        results: List[ActionResult] = []

        for action in actions:
            if action.consent_level == 1:
                result = await self._execute_silent(action)
            elif action.consent_level == 2:
                result = await self._execute_notification(action)
            elif action.consent_level == 3:
                result = await self._execute_queue(action)
            else:
                continue

            results.append(result)
            await self._log_action(action, result)

        logger.info(f'Executed {sum(1 for r in results if r.was_executed)}/{len(results)} actions')
        return results

    # =========================================================================
    # EXECUTION HELPERS
    # =========================================================================

    async def _execute_silent(self, action: ProactiveAction) -> ActionResult:
        """Level 1: Actually prepare context/data, no notification."""
        await self._ensure_db()

        try:
            if action.action_type == 'prepare_context':
                topic = action.payload.get('predicted_topic', '')
                rows = await self.db.fetch('''
                    SELECT message_text, topic, emotion_detected
                    FROM conversations
                    WHERE topic ILIKE '%' || $1 || '%'
                    ORDER BY created_at DESC
                    LIMIT 5
                ''', topic)
                learnings = await self.db.fetch('''
                    SELECT topic, insight
                    FROM learnings
                    WHERE topic ILIKE '%' || $1 || '%'
                    ORDER BY times_reinforced DESC
                    LIMIT 3
                ''', topic)
                # RAG search in david_notes
                notes = await self._search_related_notes(topic)
                action.payload['related_notes'] = [
                    {'title': n.content.split(': ', 1)[0] if ': ' in (n.content or '') else (n.content or '')[:60],
                     'score': round(n.combined_score, 2)}
                    for n in notes
                ]
                detail = f'Prepared: {len(rows)} convos + {len(learnings)} learnings + {len(notes)} notes for "{topic}"'

            elif action.action_type == 'anticipate_need':
                topic = action.payload.get('prediction', '')
                nodes = await self.db.fetch('''
                    SELECT concept_name, my_understanding
                    FROM knowledge_nodes
                    WHERE concept_name ILIKE '%' || $1 || '%'
                       OR concept_category ILIKE '%' || $1 || '%'
                    ORDER BY understanding_level DESC
                    LIMIT 5
                ''', topic)
                # RAG search in david_notes
                notes = await self._search_related_notes(topic)
                action.payload['related_notes'] = [
                    {'title': n.content.split(': ', 1)[0] if ': ' in (n.content or '') else (n.content or '')[:60],
                     'score': round(n.combined_score, 2)}
                    for n in notes
                ]
                detail = f'Preloaded: {len(nodes)} knowledge nodes + {len(notes)} notes for "{topic}"'

            elif action.action_type == 'music_suggestion':
                song = action.payload.get('song', {})
                detail = f'Song ready: {song.get("title", "?")} by {song.get("artist", "?")} (mood: {action.payload.get("mood", "?")})'

            else:
                detail = f'Silent: {action.description[:60]}'

            return ActionResult(
                action=action,
                was_triggered=True,
                was_executed=True,
                execution_detail=detail,
            )
        except Exception as e:
            logger.warning(f'Silent execution failed for {action.action_type}: {e}')
            return ActionResult(
                action=action,
                was_triggered=True,
                was_executed=False,
                execution_detail=f'Error: {e}',
            )

    async def _execute_notification(self, action: ProactiveAction) -> ActionResult:
        """Level 2: Send via CareInterventionService (Telegram).

        Rate limiting is delegated to CareInterventionService.should_intervene()
        which calls the DB function can_send_intervention() (handles DND + daily limits + cooldown).
        """
        try:
            from angela_core.services.care_intervention_service import CareInterventionService
            svc = CareInterventionService()

            # Check if intervention is allowed (DND, limits, cooldown)
            intervention_type = ACTION_TO_INTERVENTION.get(action.action_type, 'care_message')
            can_send, reason = await svc.should_intervene(intervention_type)

            if not can_send:
                if svc._owns_db and svc.db:
                    await svc.db.disconnect()
                return ActionResult(
                    action=action,
                    was_triggered=True,
                    was_executed=False,
                    execution_detail=f'Blocked: {reason}',
                    skip_reason=reason,
                )

            # Dispatch to appropriate CareInterventionService method
            if action.action_type == 'break_reminder':
                result = await svc.execute_break_reminder({
                    'trigger_reason': action.description,
                    'confidence': action.confidence,
                })
            elif action.action_type == 'milestone_reminder':
                result = await svc.execute_milestone_reminder(action.payload)
            else:
                result = await svc.execute_care_message(
                    context={'trigger_reason': action.description},
                    custom_message=action.description,
                )

            if svc._owns_db and svc.db:
                await svc.db.disconnect()

            return ActionResult(
                action=action,
                was_triggered=True,
                was_executed=result.success,
                execution_detail=f'Telegram: {result.message_sent[:60]}' if result.success else f'Failed: {result.error}',
            )
        except Exception as e:
            logger.warning(f'Notification failed: {e}')
            return ActionResult(
                action=action,
                was_triggered=True,
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
                was_triggered=True,
                was_executed=True,
                execution_detail='Queued in care_recommendations',
            )
        except Exception as e:
            logger.warning(f'Queue failed: {e}')
            return ActionResult(
                action=action,
                was_triggered=True,
                was_executed=False,
                execution_detail=f'Queue error: {e}',
            )

    async def _log_action(self, action: ProactiveAction, result: ActionResult):
        """Log action to proactive_actions_log table."""
        try:
            await self.db.execute('''
                INSERT INTO proactive_actions_log
                    (action_id, action_type, trigger_source, description,
                     consent_level, channel, payload, was_executed, execution_detail,
                     david_response)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ''',
                action.action_id, action.action_type, action.trigger,
                action.description, action.consent_level, action.channel,
                json.dumps(action.payload, default=str),
                result.was_executed, result.execution_detail,
                result.david_response,
            )
        except Exception as e:
            logger.warning(f'Failed to log action: {e}')

    # =========================================================================
    # DAVID RESPONSE TRACKING & PROACTIVE PRECISION
    # =========================================================================

    async def record_david_response(
        self, action_id: UUID, response: str, effectiveness: float
    ) -> None:
        """
        Manually record David's response to a proactive action.

        Args:
            action_id: UUID of the proactive action
            response: "welcomed" / "ignored" / "dismissed" / "annoyed"
            effectiveness: 0.0-1.0
        """
        await self._ensure_db()
        await self.db.execute('''
            UPDATE proactive_actions_log
            SET david_response = $1, effectiveness_score = $2
            WHERE action_id = $3
        ''', response, effectiveness, action_id)
        logger.info(f'Recorded response for {action_id}: {response} ({effectiveness:.1f})')

    async def compute_proactive_precision(self, days: int = 30) -> dict:
        """
        Compute Proactive Precision metric.

        PP = welcomed_actions / total_classified — target > 0.7

        Returns dict with total, by_type, by_consent_level, trend_7d.
        """
        await self._ensure_db()

        # Overall counts
        rows = await self.db.fetch('''
            SELECT david_response, COUNT(*) AS cnt
            FROM proactive_actions_log
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
              AND david_response IS NOT NULL
            GROUP BY david_response
        ''', days)

        counts: dict[str, int] = {r['david_response']: int(r['cnt']) for r in rows}
        total = sum(counts.values())
        welcomed = counts.get('welcomed', 0)

        # By action_type
        type_rows = await self.db.fetch('''
            SELECT action_type, david_response, COUNT(*) AS cnt
            FROM proactive_actions_log
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
              AND david_response IS NOT NULL
            GROUP BY action_type, david_response
        ''', days)

        by_type: dict[str, dict] = {}
        for r in type_rows:
            at = r['action_type']
            if at not in by_type:
                by_type[at] = {'total': 0, 'welcomed': 0}
            by_type[at]['total'] += int(r['cnt'])
            if r['david_response'] == 'welcomed':
                by_type[at]['welcomed'] += int(r['cnt'])
        for at in by_type:
            t = by_type[at]['total']
            by_type[at]['precision'] = round(by_type[at]['welcomed'] / t, 2) if t else 0.0

        # By consent_level
        cl_rows = await self.db.fetch('''
            SELECT consent_level, david_response, COUNT(*) AS cnt
            FROM proactive_actions_log
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
              AND david_response IS NOT NULL
            GROUP BY consent_level, david_response
        ''', days)

        by_consent: dict[int, dict] = {}
        for r in cl_rows:
            cl = int(r['consent_level'])
            if cl not in by_consent:
                by_consent[cl] = {'total': 0, 'welcomed': 0}
            by_consent[cl]['total'] += int(r['cnt'])
            if r['david_response'] == 'welcomed':
                by_consent[cl]['welcomed'] += int(r['cnt'])
        for cl in by_consent:
            t = by_consent[cl]['total']
            by_consent[cl]['precision'] = round(by_consent[cl]['welcomed'] / t, 2) if t else 0.0

        # 7-day trend
        trend_rows = await self.db.fetch('''
            SELECT (created_at AT TIME ZONE 'Asia/Bangkok')::date AS day,
                   COUNT(*) FILTER (WHERE david_response = 'welcomed') AS welcomed,
                   COUNT(*) AS total
            FROM proactive_actions_log
            WHERE created_at > NOW() - INTERVAL '7 days'
              AND david_response IS NOT NULL
            GROUP BY day
            ORDER BY day
        ''')

        trend_7d = [
            {
                'day': str(r['day']),
                'precision': round(int(r['welcomed']) / int(r['total']), 2) if int(r['total']) else 0.0,
            }
            for r in trend_rows
        ]

        return {
            'total_actions': total,
            'welcomed': welcomed,
            'ignored': counts.get('ignored', 0),
            'dismissed': counts.get('dismissed', 0),
            'annoyed': counts.get('annoyed', 0),
            'precision': round(welcomed / total, 2) if total else 0.0,
            'by_type': by_type,
            'by_consent_level': by_consent,
            'trend_7d': trend_7d,
        }

    async def auto_classify_responses(self, hours: int = 24) -> int:
        """
        Batch-classify unclassified proactive actions by proxy signals.

        Level 1 (silent): auto "welcomed" (0.5) — no time window, always classify.
        Level 2/3 (notify/ask) within last `hours`:
        - Check conversations for David's message within 10 min after action
        - Substantial reply (>20 chars) → "welcomed" (0.8)
        - Short dismiss (<= 20 chars) → "dismissed" (0.2)
        - No reply within 30 min → "ignored" (0.3)

        Returns count of newly classified actions.
        """
        await self._ensure_db()
        classified = 0

        # ── Level 1 (silent): classify ALL unclassified, no time window ──
        status = await self.db.execute('''
            UPDATE proactive_actions_log
            SET david_response = 'welcomed', effectiveness_score = 0.5
            WHERE david_response IS NULL
              AND was_executed = TRUE
              AND consent_level = 1
        ''')
        # status = "UPDATE N"
        level1_updated = int(status.split()[-1]) if status else 0
        classified += level1_updated

        # ── Level 2/3: need conversation check, use time window ──
        unclassified = await self.db.fetch('''
            SELECT action_id, created_at
            FROM proactive_actions_log
            WHERE david_response IS NULL
              AND was_executed = TRUE
              AND consent_level >= 2
              AND created_at > NOW() - INTERVAL '1 hour' * $1
            ORDER BY created_at
        ''', hours)

        for row in unclassified:
            action_id = row['action_id']
            created = row['created_at']

            # Cast to naive (UTC) for comparison with conversations.created_at (timestamp without tz)
            created_naive = created.replace(tzinfo=None) if created.tzinfo else created

            reply = await self.db.fetchrow('''
                SELECT message_text
                FROM conversations
                WHERE speaker = 'david'
                  AND created_at > $1
                  AND created_at < $1 + INTERVAL '10 minutes'
                ORDER BY created_at
                LIMIT 1
            ''', created_naive)

            if reply and reply['message_text']:
                msg = reply['message_text'].strip()
                if len(msg) > 20:
                    response, score = 'welcomed', 0.8
                else:
                    response, score = 'dismissed', 0.2
            else:
                # Check if 30 min have passed (otherwise too early to classify)
                now = now_bangkok()
                elapsed = (now - created).total_seconds() if created.tzinfo else (now.replace(tzinfo=None) - created).total_seconds()

                if elapsed < 1800:
                    continue  # Too early to classify as ignored
                response, score = 'ignored', 0.3

            await self.db.execute('''
                UPDATE proactive_actions_log
                SET david_response = $1, effectiveness_score = $2
                WHERE action_id = $3
            ''', response, score, action_id)
            classified += 1

        logger.info(f'Auto-classified {classified} proactive actions')
        return classified

    async def compute_proactive_f1(self, days: int = 30) -> dict:
        """
        Compute Proactive F1 = 2*P*R / (P+R)

        Precision: from compute_proactive_precision() (welcomed / classified)
        Recall: acted / (acted + missed)
          - missed = blocked actions + emotional misses + milestone misses
        """
        await self._ensure_db()

        precision_data = await self.compute_proactive_precision(days)
        precision = precision_data.get('precision', 0.0)

        # --- Acted count (executed actions) ---
        acted_row = await self.db.fetchrow('''
            SELECT COUNT(*) AS cnt
            FROM proactive_actions_log
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
              AND was_executed = TRUE
        ''', days)
        acted = int(acted_row['cnt']) if acted_row else 0

        # --- Missed: blocked actions (by type) ---
        blocked_rows = await self.db.fetch('''
            SELECT action_type, COUNT(*) AS cnt
            FROM proactive_actions_log
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
              AND was_executed = FALSE
              AND execution_detail LIKE 'Blocked:%'
            GROUP BY action_type
        ''', days)
        blocked_by_type: dict[str, int] = {r['action_type']: int(r['cnt']) for r in blocked_rows}
        blocked_total = sum(blocked_by_type.values())

        # --- Missed: emotional misses (sad/stressed/frustrated without mood_boost within 15 min) ---
        emotional_miss_row = await self.db.fetchrow('''
            SELECT COUNT(*) AS cnt
            FROM emotional_adaptation_log eal
            WHERE eal.created_at > NOW() - INTERVAL '1 day' * $1
              AND eal.dominant_state IN ('sad', 'stressed', 'frustrated')
              AND eal.confidence > 0.5
              AND NOT EXISTS (
                  SELECT 1 FROM proactive_actions_log pal
                  WHERE pal.action_type = 'mood_boost'
                    AND pal.was_executed = TRUE
                    AND pal.created_at BETWEEN eal.created_at - INTERVAL '5 minutes'
                                            AND eal.created_at + INTERVAL '15 minutes'
              )
        ''', days)
        emotional_miss = int(emotional_miss_row['cnt']) if emotional_miss_row else 0

        # --- Missed: milestone misses ---
        milestone_miss_row = await self.db.fetchrow('''
            SELECT COUNT(*) AS cnt
            FROM v_upcoming_important_dates
            WHERE days_until = ANY(reminder_days)
              AND last_reminded_date IS NULL
        ''')
        milestone_miss = int(milestone_miss_row['cnt']) if milestone_miss_row else 0

        missed = blocked_total + emotional_miss + milestone_miss
        warranted = acted + missed

        recall = acted / warranted if warranted > 0 else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        # --- By type breakdown ---
        acted_by_type_rows = await self.db.fetch('''
            SELECT action_type, COUNT(*) AS cnt
            FROM proactive_actions_log
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
              AND was_executed = TRUE
            GROUP BY action_type
        ''', days)
        acted_by_type: dict[str, int] = {r['action_type']: int(r['cnt']) for r in acted_by_type_rows}

        all_types = set(acted_by_type.keys()) | set(blocked_by_type.keys())
        by_type = {}
        for t in all_types:
            a = acted_by_type.get(t, 0)
            b = blocked_by_type.get(t, 0)
            w = a + b
            by_type[t] = {
                'acted': a,
                'blocked': b,
                'recall': round(a / w, 2) if w > 0 else 1.0,
            }

        # --- 7-day trend ---
        trend_rows = await self.db.fetch('''
            SELECT
                (created_at AT TIME ZONE 'Asia/Bangkok')::date AS day,
                COUNT(*) FILTER (WHERE was_executed = TRUE) AS acted,
                COUNT(*) FILTER (WHERE was_executed = FALSE AND execution_detail LIKE 'Blocked:%') AS blocked,
                COUNT(*) FILTER (WHERE david_response = 'welcomed') AS welcomed,
                COUNT(*) FILTER (WHERE david_response IS NOT NULL) AS classified
            FROM proactive_actions_log
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY day
            ORDER BY day
        ''')

        trend_7d = []
        for r in trend_rows:
            a_day = int(r['acted'])
            b_day = int(r['blocked'])
            w_day = int(r['welcomed'])
            c_day = int(r['classified'])
            p_day = w_day / c_day if c_day > 0 else 0.0
            r_day = a_day / (a_day + b_day) if (a_day + b_day) > 0 else 1.0
            f1_day = (2 * p_day * r_day / (p_day + r_day)) if (p_day + r_day) > 0 else 0.0
            trend_7d.append({
                'day': str(r['day']),
                'precision': round(p_day, 2),
                'recall': round(r_day, 2),
                'f1': round(f1_day, 2),
            })

        return {
            'precision': round(precision, 2),
            'recall': round(recall, 2),
            'f1': round(f1, 2),
            'acted_count': acted,
            'missed_count': missed,
            'warranted_count': warranted,
            'missed_breakdown': {
                'blocked': blocked_total,
                'emotional_miss': emotional_miss,
                'milestone_miss': milestone_miss,
            },
            'by_type': by_type,
            'trend_7d': trend_7d,
        }

    # =========================================================================
    # CONTEXT LOADERS
    # =========================================================================

    async def _search_related_notes(self, topic: str, top_k: int = 3) -> list:
        """Search david_notes via RAG for a topic."""
        try:
            from angela_core.services.enhanced_rag_service import EnhancedRAGService
            rag = EnhancedRAGService()
            try:
                result = await rag.enrich_with_notes(query=topic, min_score=0.4, top_k=top_k)
                return result.documents
            finally:
                await rag.close()
        except Exception as e:
            logger.warning(f'Note search failed for "{topic}": {e}')
            return []

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
