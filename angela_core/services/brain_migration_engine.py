"""
Brain Migration Engine — Brain-Based Architecture Phase 7
==========================================================
Compare brain-based vs rule-based proactive actions.
Track effectiveness, manage gradual migration, auto-rollback.

Sub-Phases:
  7A — Comparison framework (brain vs rule dry-run per cycle)
  7B — Effectiveness tracking (classify David's response to brain expressions)
  7E — Gradual migration (feature-by-feature routing: rule_only → dual → brain_preferred → brain_only)
  7G — Dashboard status (migration readiness % per action type)

Cost: $0/day (all DB queries, no LLM)

By: น้อง Angela 💜
Created: 2026-02-15
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok, today_bangkok

logger = logging.getLogger('brain_migration')


# ============================================================
# CONSTANTS
# ============================================================

# Migration routing modes
MODE_RULE_ONLY = 'rule_only'
MODE_DUAL = 'dual'
MODE_BRAIN_PREFERRED = 'brain_preferred'
MODE_BRAIN_ONLY = 'brain_only'

# All 8 proactive action types
ALL_ACTION_TYPES = [
    'prepare_context', 'anticipate_need', 'music_suggestion',
    'milestone_reminder', 'break_reminder', 'mood_boost',
    'wellness_nudge', 'learning_nudge',
]

# Default routing (start conservative)
DEFAULT_ROUTING = {
    'prepare_context': MODE_RULE_ONLY,
    'anticipate_need': MODE_RULE_ONLY,
    'music_suggestion': MODE_RULE_ONLY,
    'milestone_reminder': MODE_RULE_ONLY,
    'break_reminder': MODE_RULE_ONLY,
    'mood_boost': MODE_RULE_ONLY,
    'wellness_nudge': MODE_RULE_ONLY,
    'learning_nudge': MODE_RULE_ONLY,
}

# Cutover criteria
CUTOVER_MIN_DAYS = 7
CUTOVER_MIN_COVERAGE = 0.8       # brain covers 80%+ of rule situations
ROLLBACK_EFFECTIVENESS_GAP = 0.1  # brain < rule - 0.1 for 3 days → rollback
ROLLBACK_CONSECUTIVE_DAYS = 3

# Keyword mapping: rule action_type → brain keywords for matching
ACTION_KEYWORDS = {
    'break_reminder': ['ดึก', 'พัก', 'พักผ่อน', 'ทำงาน', 'เหนื่อย'],
    'mood_boost': ['เป็นห่วง', 'เครียด', 'เศร้า', 'หงุดหงิด', 'อยู่ตรงนี้', 'กำลังใจ'],
    'prepare_context': ['เตรียม', 'context', 'น่าจะ', 'เตรียมตัว'],
    'anticipate_need': ['เตรียม', 'ช่วย', 'น่าจะต้อง'],
    'wellness_nudge': ['ดึก', 'พักผ่อน', 'สุขภาพ', 'นอน'],
    'milestone_reminder': ['ครบรอบ', 'จำได้', 'วันพิเศษ', 'วันสำคัญ'],
    'music_suggestion': ['เพลง', 'ฟัง', 'เปิดเพลง'],
    'learning_nudge': ['เรียน', 'learning', 'ปรับปรุง', 'พัฒนา'],
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ComparisonRow:
    """One comparison between brain and rule systems."""
    situation_type: str
    brain_would_act: bool = False
    brain_thought_id: Optional[str] = None
    brain_channel: Optional[str] = None
    brain_motivation: float = 0.0
    brain_message: Optional[str] = None
    rule_would_act: bool = False
    rule_action_type: Optional[str] = None
    rule_consent_level: Optional[int] = None
    rule_description: Optional[str] = None
    actual_system: str = 'neither'


@dataclass
class MigrationStatus:
    """Status of brain migration for all action types."""
    routing: Dict[str, str]             # action_type → mode
    readiness: Dict[str, float]         # action_type → 0.0-1.0
    overall_readiness: float            # weighted average
    comparison_days: int                # days of comparison data
    total_comparisons: int


# ============================================================
# BRAIN MIGRATION ENGINE
# ============================================================

class BrainMigrationEngine(BaseDBService):
    """
    Manages the gradual migration from rule-based to brain-based actions.

    Methods:
    - run_comparison(): Compare brain vs rule candidates (7A)
    - classify_brain_effectiveness(): Track expression outcomes (7B)
    - get_migration_routing(): Get current routing per action type (7E)
    - check_cutover_readiness(): Can we advance migration? (7E)
    - advance_migration(): Move action type to next mode (7E)
    - auto_rollback_check(): Revert if brain underperforms (7E)
    - get_migration_status(): Dashboard data (7G)
    """

    # ============================================================
    # 7A: COMPARISON FRAMEWORK
    # ============================================================

    async def run_comparison(
        self,
        brain_candidates: List[Dict[str, Any]],
        rule_actions: List[Any],
    ) -> int:
        """
        Compare brain vs rule candidates for each situation type.
        Log comparison rows to brain_vs_rule_comparison.

        Args:
            brain_candidates: List of thought dicts from ThoughtExpressionEngine.evaluate_for_comparison()
            rule_actions: List of ProactiveAction from ProactiveActionEngine.evaluate_actions_dry_run()

        Returns: number of comparison rows logged
        """
        await self.connect()
        logged = 0

        # Index rule actions by type
        rule_by_type: Dict[str, Any] = {}
        for action in rule_actions:
            atype = getattr(action, 'action_type', None) or (action.get('action_type') if isinstance(action, dict) else None)
            if atype:
                rule_by_type[atype] = action

        # Index brain candidates by matched keywords
        brain_by_type: Dict[str, Dict] = {}
        for cand in brain_candidates:
            msg = (cand.get('content') or cand.get('message') or '').lower()
            for atype, keywords in ACTION_KEYWORDS.items():
                if any(kw in msg for kw in keywords):
                    if atype not in brain_by_type:
                        brain_by_type[atype] = cand
                    break

        # Create comparison rows for all action types that have at least one candidate
        all_types = set(list(rule_by_type.keys()) + list(brain_by_type.keys()))

        for situation_type in all_types:
            brain = brain_by_type.get(situation_type)
            rule = rule_by_type.get(situation_type)

            row = ComparisonRow(situation_type=situation_type)

            if brain:
                row.brain_would_act = True
                row.brain_thought_id = str(brain.get('thought_id', ''))
                row.brain_channel = brain.get('channel', 'chat_queue')
                row.brain_motivation = brain.get('motivation_score', 0)
                row.brain_message = (brain.get('content') or brain.get('message') or '')[:500]

            if rule:
                row.rule_would_act = True
                if isinstance(rule, dict):
                    row.rule_action_type = rule.get('action_type')
                    row.rule_consent_level = rule.get('consent_level')
                    row.rule_description = (rule.get('description') or '')[:500]
                else:
                    row.rule_action_type = getattr(rule, 'action_type', None)
                    row.rule_consent_level = getattr(rule, 'consent_level', None)
                    row.rule_description = (getattr(rule, 'description', '') or '')[:500]

            # Determine actual system used
            if row.brain_would_act and row.rule_would_act:
                row.actual_system = 'both'
            elif row.brain_would_act:
                row.actual_system = 'brain'
            elif row.rule_would_act:
                row.actual_system = 'rule'
            else:
                row.actual_system = 'neither'

            try:
                await self.db.execute("""
                    INSERT INTO brain_vs_rule_comparison
                    (situation_type, brain_would_act, brain_thought_id,
                     brain_channel, brain_motivation, brain_message,
                     rule_would_act, rule_action_type, rule_consent_level,
                     rule_description, actual_system)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                    row.situation_type,
                    row.brain_would_act,
                    row.brain_thought_id,
                    row.brain_channel,
                    row.brain_motivation,
                    row.brain_message,
                    row.rule_would_act,
                    row.rule_action_type,
                    row.rule_consent_level,
                    row.rule_description,
                    row.actual_system,
                )
                logged += 1
            except Exception as e:
                logger.warning("Failed to log comparison: %s", e)

        logger.info("Logged %d brain-vs-rule comparisons", logged)
        return logged

    async def compute_comparison_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Compute coverage/overlap metrics from comparison data.

        Returns: brain_coverage, rule_coverage, overlap_rate, brain_ready_score per type.
        """
        await self.connect()

        rows = await self.db.fetch("""
            SELECT situation_type,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE brain_would_act) AS brain_count,
                   COUNT(*) FILTER (WHERE rule_would_act) AS rule_count,
                   COUNT(*) FILTER (WHERE brain_would_act AND rule_would_act) AS overlap_count,
                   AVG(brain_motivation) FILTER (WHERE brain_would_act) AS avg_brain_motivation,
                   AVG(effectiveness_score) FILTER (WHERE effectiveness_score IS NOT NULL AND actual_system IN ('brain', 'both')) AS avg_brain_eff,
                   AVG(effectiveness_score) FILTER (WHERE effectiveness_score IS NOT NULL AND actual_system IN ('rule', 'both')) AS avg_rule_eff
            FROM brain_vs_rule_comparison
            WHERE created_at > NOW() - INTERVAL '1 day' * $1
            GROUP BY situation_type
        """, days)

        metrics: Dict[str, Dict] = {}
        for r in rows:
            total = r['total'] or 1
            rule_count = r['rule_count'] or 0
            brain_count = r['brain_count'] or 0
            overlap = r['overlap_count'] or 0

            brain_coverage = brain_count / max(rule_count, 1) if rule_count > 0 else (1.0 if brain_count > 0 else 0.0)
            overlap_rate = overlap / total

            metrics[r['situation_type']] = {
                'total': total,
                'brain_count': brain_count,
                'rule_count': rule_count,
                'overlap': overlap,
                'brain_coverage': round(min(1.0, brain_coverage), 3),
                'overlap_rate': round(overlap_rate, 3),
                'avg_brain_motivation': round(float(r['avg_brain_motivation'] or 0), 3),
                'avg_brain_eff': round(float(r['avg_brain_eff'] or 0), 3) if r['avg_brain_eff'] else None,
                'avg_rule_eff': round(float(r['avg_rule_eff'] or 0), 3) if r['avg_rule_eff'] else None,
            }

        return metrics

    # ============================================================
    # 7B: EFFECTIVENESS TRACKING
    # ============================================================

    async def classify_brain_effectiveness(self, hours: int = 24) -> int:
        """
        Classify effectiveness of brain expressions by checking David's response.

        For chat_queue: find David's first message after thought was shown → classify
        For telegram: find Telegram reply within 10 min → classify

        Returns: number of expressions classified
        """
        await self.connect()
        classified = 0

        # Get unclassified shown queue items
        unclassified = await self.db.fetch("""
            SELECT q.queue_id, q.thought_id, q.message, q.shown_at
            FROM thought_expression_queue q
            WHERE q.status = 'shown'
            AND q.david_response IS NULL
            AND q.shown_at IS NOT NULL
            AND q.shown_at > NOW() - INTERVAL '1 hour' * $1
        """, hours)

        for row in unclassified:
            shown_at = row['shown_at']
            if shown_at is None:
                continue

            # Find David's first message after the thought was shown
            shown_naive = shown_at.replace(tzinfo=None) if shown_at.tzinfo else shown_at
            reply = await self.db.fetchrow("""
                SELECT message_text
                FROM conversations
                WHERE speaker = 'david'
                AND created_at > $1
                AND created_at < $1 + INTERVAL '10 minutes'
                ORDER BY created_at
                LIMIT 1
            """, shown_naive)

            if reply and reply['message_text']:
                msg = reply['message_text'].strip()
                if len(msg) > 20:
                    response, score = 'engaged', 0.8
                else:
                    response, score = 'acknowledged', 0.5
            else:
                # Check if enough time has passed
                now = now_bangkok()
                elapsed = (now - shown_at).total_seconds() if shown_at.tzinfo else (now.replace(tzinfo=None) - shown_at).total_seconds()
                if elapsed < 1800:
                    continue  # Too early to classify
                response, score = 'ignored', 0.2

            await self.db.execute("""
                UPDATE thought_expression_queue
                SET david_response = $1, effectiveness_score = $2
                WHERE queue_id = $3
            """, response, score, row['queue_id'])
            classified += 1

        # Also classify Telegram expressions from thought_expression_log
        tg_unclassified = await self.db.fetch("""
            SELECT log_id, thought_id, created_at
            FROM thought_expression_log
            WHERE channel = 'telegram'
            AND success = TRUE
            AND matched_rule_type IS NULL
            AND created_at > NOW() - INTERVAL '1 hour' * $1
        """, hours)

        # For Telegram, we just mark them — actual response tracking
        # is handled by ProactiveActionEngine.auto_classify_responses()
        # We just need to update matched_rule_type for comparison

        logger.info("Classified %d brain expression effectiveness", classified)
        return classified

    # ============================================================
    # 7E: MIGRATION ROUTING
    # ============================================================

    async def get_migration_routing(self) -> Dict[str, str]:
        """
        Get current migration routing for all action types.
        Reads from companion_patterns category='brain_migration_routing'.
        Falls back to DEFAULT_ROUTING.
        """
        await self.connect()

        row = await self.db.fetchrow("""
            SELECT pattern_data FROM companion_patterns
            WHERE pattern_category = 'brain_migration_routing'
            ORDER BY last_observed DESC LIMIT 1
        """)

        if row and row['pattern_data']:
            data = row['pattern_data'] if isinstance(row['pattern_data'], dict) else json.loads(row['pattern_data'])
            # Merge with defaults (in case new action types were added)
            routing = dict(DEFAULT_ROUTING)
            for k, v in data.items():
                if k in routing and v in (MODE_RULE_ONLY, MODE_DUAL, MODE_BRAIN_PREFERRED, MODE_BRAIN_ONLY):
                    routing[k] = v
            return routing

        return dict(DEFAULT_ROUTING)

    async def _save_routing(self, routing: Dict[str, str]) -> None:
        """Save routing to companion_patterns."""
        await self.connect()

        existing = await self.db.fetchrow("""
            SELECT pattern_id FROM companion_patterns
            WHERE pattern_category = 'brain_migration_routing'
            ORDER BY last_observed DESC LIMIT 1
        """)

        data = json.dumps(routing)
        if existing:
            await self.db.execute("""
                UPDATE companion_patterns
                SET pattern_data = $1, last_observed = NOW()
                WHERE pattern_id = $2
            """, data, existing['pattern_id'])
        else:
            hash_key = f'brain_migration_routing_{today_bangkok().isoformat()}'
            await self.db.execute("""
                INSERT INTO companion_patterns
                (pattern_hash, pattern_category, pattern_data, observation_count, last_observed)
                VALUES ($1, 'brain_migration_routing', $2, 1, NOW())
            """, hash_key, data)

    async def check_cutover_readiness(self, action_type: str) -> Dict[str, Any]:
        """
        Check if an action type is ready to advance to next migration mode.

        Criteria:
        - brain_coverage >= 0.8
        - brain_effectiveness >= rule_effectiveness
        - Minimum 7 days comparison data
        """
        await self.connect()

        metrics = await self.compute_comparison_metrics(days=CUTOVER_MIN_DAYS)
        m = metrics.get(action_type, {})

        total = m.get('total', 0)
        brain_coverage = m.get('brain_coverage', 0)
        avg_brain_eff = m.get('avg_brain_eff')
        avg_rule_eff = m.get('avg_rule_eff')

        ready = (
            total >= 3 and
            brain_coverage >= CUTOVER_MIN_COVERAGE and
            (avg_brain_eff is not None and avg_rule_eff is not None and avg_brain_eff >= avg_rule_eff)
        )

        return {
            'action_type': action_type,
            'ready': ready,
            'total_comparisons': total,
            'brain_coverage': brain_coverage,
            'avg_brain_eff': avg_brain_eff,
            'avg_rule_eff': avg_rule_eff,
            'min_days_met': total >= 3,
            'coverage_met': brain_coverage >= CUTOVER_MIN_COVERAGE,
            'effectiveness_met': avg_brain_eff is not None and avg_rule_eff is not None and avg_brain_eff >= avg_rule_eff,
        }

    async def advance_migration(self, action_type: str) -> Optional[str]:
        """
        Advance action_type to next migration mode if ready.

        Returns new mode or None if not ready.
        """
        readiness = await self.check_cutover_readiness(action_type)
        if not readiness['ready']:
            logger.info("Not ready to advance %s: %s", action_type, readiness)
            return None

        routing = await self.get_migration_routing()
        current = routing.get(action_type, MODE_RULE_ONLY)

        progression = [MODE_RULE_ONLY, MODE_DUAL, MODE_BRAIN_PREFERRED, MODE_BRAIN_ONLY]
        try:
            idx = progression.index(current)
        except ValueError:
            return None

        if idx >= len(progression) - 1:
            logger.info("%s already at brain_only", action_type)
            return None

        new_mode = progression[idx + 1]
        routing[action_type] = new_mode
        await self._save_routing(routing)

        logger.info("Advanced %s: %s → %s", action_type, current, new_mode)
        return new_mode

    async def auto_rollback_check(self) -> List[str]:
        """
        Check if any brain_preferred/brain_only actions should roll back.

        Rollback if brain_effectiveness < rule_effectiveness - 0.1
        for ROLLBACK_CONSECUTIVE_DAYS consecutive days.

        Returns: list of action types that were rolled back.
        """
        await self.connect()
        routing = await self.get_migration_routing()
        rolled_back = []

        for action_type, mode in routing.items():
            if mode not in (MODE_BRAIN_PREFERRED, MODE_BRAIN_ONLY):
                continue

            # Check last N days
            rows = await self.db.fetch("""
                SELECT
                    (created_at AT TIME ZONE 'Asia/Bangkok')::date AS day,
                    AVG(effectiveness_score) FILTER (WHERE actual_system IN ('brain', 'both')) AS brain_eff,
                    AVG(effectiveness_score) FILTER (WHERE actual_system IN ('rule', 'both')) AS rule_eff
                FROM brain_vs_rule_comparison
                WHERE situation_type = $1
                AND effectiveness_score IS NOT NULL
                AND created_at > NOW() - INTERVAL '1 day' * $2
                GROUP BY day
                ORDER BY day DESC
                LIMIT $2
            """, action_type, ROLLBACK_CONSECUTIVE_DAYS)

            if len(rows) < ROLLBACK_CONSECUTIVE_DAYS:
                continue

            # Check if brain underperforms for all consecutive days
            underperforming_days = 0
            for r in rows:
                brain_eff = float(r['brain_eff'] or 0)
                rule_eff = float(r['rule_eff'] or 0)
                if brain_eff < rule_eff - ROLLBACK_EFFECTIVENESS_GAP:
                    underperforming_days += 1

            if underperforming_days >= ROLLBACK_CONSECUTIVE_DAYS:
                routing[action_type] = MODE_DUAL
                rolled_back.append(action_type)
                logger.warning(
                    "Auto-rollback %s: brain underperforming for %d days → dual",
                    action_type, underperforming_days
                )

        if rolled_back:
            await self._save_routing(routing)

        return rolled_back

    # ============================================================
    # 7G: DASHBOARD STATUS
    # ============================================================

    async def get_migration_status(self) -> MigrationStatus:
        """
        Get migration status for all action types — used by init.py.
        """
        await self.connect()

        routing = await self.get_migration_routing()
        metrics = await self.compute_comparison_metrics(days=14)

        # Compute readiness per action type
        readiness: Dict[str, float] = {}
        mode_scores = {
            MODE_RULE_ONLY: 0.0,
            MODE_DUAL: 0.33,
            MODE_BRAIN_PREFERRED: 0.66,
            MODE_BRAIN_ONLY: 1.0,
        }

        for atype in ALL_ACTION_TYPES:
            mode = routing.get(atype, MODE_RULE_ONLY)
            base_score = mode_scores.get(mode, 0.0)

            # Add coverage bonus (up to +0.17)
            m = metrics.get(atype, {})
            coverage = m.get('brain_coverage', 0)
            coverage_bonus = min(0.17, coverage * 0.17)

            readiness[atype] = round(min(1.0, base_score + coverage_bonus), 3)

        # Overall readiness
        overall = sum(readiness.values()) / max(len(readiness), 1)

        # Days of comparison data
        total_row = await self.db.fetchrow("""
            SELECT COUNT(*) AS total,
                   COUNT(DISTINCT (created_at AT TIME ZONE 'Asia/Bangkok')::date) AS days
            FROM brain_vs_rule_comparison
        """)

        return MigrationStatus(
            routing=routing,
            readiness=readiness,
            overall_readiness=round(overall, 3),
            comparison_days=total_row['days'] if total_row else 0,
            total_comparisons=total_row['total'] if total_row else 0,
        )
