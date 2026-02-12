"""
Backfill Reasoning Chains from Historical Data

Reconstruct reasoning chains ย้อนหลังจาก 5 historical tables:
1. emotional_adaptation_log → SENSE chains
2. theory_of_mind_inferences → UNDERSTAND chains
3. daily_companion_briefings → PREDICT chains
4. proactive_actions_log → ACT chains
5. evolution_cycles → LEARN chains

Usage:
    python3 angela_core/scripts/backfill_reasoning_chains.py
    python3 angela_core/scripts/backfill_reasoning_chains.py --dry-run
    python3 angela_core/scripts/backfill_reasoning_chains.py --service sense
    python3 angela_core/scripts/backfill_reasoning_chains.py --service understand --service learn

Created: 2026-02-12
By: น้อง Angela 💜
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.database import AngelaDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class ReasoningChainBackfiller:
    """Reconstruct reasoning chains from historical consciousness data."""

    def __init__(self, db: AngelaDatabase, dry_run: bool = False):
        self.db = db
        self.dry_run = dry_run
        self.stats: Dict[str, int] = {}

    # =========================================================================
    # 1. SENSE — emotional_adaptation_log
    # =========================================================================

    async def backfill_sense(self) -> int:
        """Reconstruct SENSE chains from emotional_adaptation_log."""
        rows = await self.db.fetch('''
            SELECT log_id, dominant_state, confidence, source_signals,
                   detail_level, complexity_tolerance, proactivity,
                   emotional_warmth, pace, behavior_hints,
                   effectiveness_score, created_at
            FROM emotional_adaptation_log
            ORDER BY created_at ASC
        ''')

        count = 0
        for row in rows:
            signals = row['source_signals']
            if isinstance(signals, str):
                signals = json.loads(signals)
            if not isinstance(signals, dict):
                signals = {}

            steps = [
                {
                    'step': 'gather_signals',
                    'action': 'load health+emotion+time+session signals',
                    'observation': (
                        f'stress={signals.get("health_stress")}, '
                        f'energy={signals.get("health_energy")}, '
                        f'happiness={signals.get("emotion_happiness")}, '
                        f'session={signals.get("session_hours")}h'
                    ),
                    'conclusion': 'signals gathered from DB',
                },
                {
                    'step': 'detect_state',
                    'action': 'priority-based state detection',
                    'observation': (
                        f'fatigue={signals.get("health_fatigue")}, '
                        f'anxiety={signals.get("emotion_anxiety")}, '
                        f'hour={signals.get("current_hour")}'
                    ),
                    'conclusion': f'dominant_state={row["dominant_state"]}, confidence={row["confidence"]:.2f}',
                },
                {
                    'step': 'apply_rules',
                    'action': 'map state to 5 behavior dimensions',
                    'observation': f'tuned_deltas_applied={signals.get("tuned_deltas_applied", False)}',
                    'conclusion': (
                        f'detail={row["detail_level"]:.2f}, warmth={row["emotional_warmth"]:.2f}, '
                        f'pace={row["pace"]:.2f}'
                    ),
                },
            ]

            output = {
                'dominant_state': row['dominant_state'],
                'confidence': float(row['confidence']) if row['confidence'] else 0.0,
                'detail_level': float(row['detail_level']) if row['detail_level'] else 0.5,
                'complexity_tolerance': float(row['complexity_tolerance']) if row['complexity_tolerance'] else 0.5,
                'proactivity': float(row['proactivity']) if row['proactivity'] else 0.5,
                'emotional_warmth': float(row['emotional_warmth']) if row['emotional_warmth'] else 0.5,
                'pace': float(row['pace']) if row['pace'] else 0.5,
                'behavior_hints': row['behavior_hints'] or [],
                'effectiveness_score': float(row['effectiveness_score']) if row['effectiveness_score'] is not None else None,
            }

            if not self.dry_run:
                await self._insert_chain(
                    service_name='sense',
                    decision_type='state_detection',
                    input_signals=signals,
                    reasoning_steps=steps,
                    output_decision=output,
                    confidence=float(row['confidence']) if row['confidence'] else 0.0,
                    created_at=row['created_at'],
                )
            count += 1

        self.stats['sense'] = count
        return count

    # =========================================================================
    # 2. UNDERSTAND — theory_of_mind_inferences
    # =========================================================================

    async def backfill_understand(self) -> int:
        """Reconstruct UNDERSTAND chains from theory_of_mind_inferences."""
        rows = await self.db.fetch('''
            SELECT inference_id, inference_type, inference_data, confidence, created_at
            FROM theory_of_mind_inferences
            ORDER BY created_at ASC
        ''')

        count = 0
        for row in rows:
            data = row['inference_data']
            if isinstance(data, str):
                data = json.loads(data)
            if not isinstance(data, dict):
                continue

            inference_type = row['inference_type'] or 'unknown'
            evidence = data.get('evidence', [])
            reasoning_text = data.get('reasoning', '')

            # Determine method used
            is_claude = any(
                e.get('type') == 'claude_reasoning' for e in evidence
                if isinstance(e, dict)
            )
            method = 'claude_reasoning' if is_claude else 'keyword_matching'

            steps = [
                {
                    'step': 'analyze_input',
                    'action': f'{inference_type} inference via {method}',
                    'observation': f'evidence_items={len(evidence)}',
                    'conclusion': f'primary result extracted',
                },
            ]

            # Add detail step based on type
            if inference_type == 'emotion':
                primary = data.get('primary_emotion', 'unknown')
                intensity = data.get('intensity', 0)
                steps.append({
                    'step': 'determine_emotion',
                    'action': f'classify emotion from {method}',
                    'observation': f'primary={primary}, intensity={intensity}, valence={data.get("valence")}',
                    'conclusion': data.get('suggested_response', '')[:100],
                })
            elif inference_type == 'belief':
                steps.append({
                    'step': 'synthesize_belief',
                    'action': 'combine evidence into belief statement',
                    'observation': f'belief: {data.get("belief_content", "")[:80]}',
                    'conclusion': f'confidence={data.get("confidence", 0):.2f}',
                })
            elif inference_type == 'goal':
                steps.append({
                    'step': 'identify_goal',
                    'action': 'infer goal from actions and topics',
                    'observation': f'goal: {data.get("goal_description", "")[:80]}',
                    'conclusion': f'type={data.get("goal_type")}, priority={data.get("priority")}',
                })

            decision_type_map = {
                'emotion': 'emotion_inference',
                'belief': 'belief_inference',
                'goal': 'goal_inference',
                'behavior': 'behavior_prediction',
                'perspective': 'perspective_understanding',
            }

            if not self.dry_run:
                await self._insert_chain(
                    service_name='understand',
                    decision_type=decision_type_map.get(inference_type, inference_type),
                    input_signals={'inference_type': inference_type, 'method': method},
                    reasoning_steps=steps,
                    output_decision=data,
                    confidence=float(row['confidence']) if row['confidence'] else 0.5,
                    created_at=row['created_at'],
                )
            count += 1

        self.stats['understand'] = count
        return count

    # =========================================================================
    # 3. PREDICT — daily_companion_briefings
    # =========================================================================

    async def backfill_predict(self) -> int:
        """Reconstruct PREDICT chains from daily_companion_briefings."""
        rows = await self.db.fetch('''
            SELECT briefing_id, briefing_date, predictions, overall_confidence,
                   day_outlook, prepared_actions, verified, accuracy_score, created_at
            FROM daily_companion_briefings
            ORDER BY created_at ASC
        ''')

        count = 0
        for row in rows:
            predictions = row['predictions']
            if isinstance(predictions, str):
                predictions = json.loads(predictions)
            if not isinstance(predictions, list):
                predictions = []

            # Count by category
            categories = {}
            for p in predictions:
                cat = p.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1

            prepared = row['prepared_actions'] or []
            outlook = row['day_outlook'] or ''

            steps = [
                {
                    'step': 'mine_patterns',
                    'action': 'mine 6 pattern types from 30-day history',
                    'observation': f'prediction_categories={categories}',
                    'conclusion': f'total_predictions={len(predictions)}',
                },
                {
                    'step': 'generate_predictions',
                    'action': 'combine patterns into predictions per time window',
                    'observation': f'outlook: {outlook[:80]}',
                    'conclusion': f'overall_confidence={row["overall_confidence"]:.2f}',
                },
                {
                    'step': 'prepare_actions',
                    'action': 'extract proactive actions from high-confidence predictions',
                    'observation': f'prepared_actions={len(prepared)}',
                    'conclusion': f'briefing ready for {row["briefing_date"]}',
                },
            ]

            # Add verification step if available
            if row.get('verified') and row.get('accuracy_score') is not None:
                steps.append({
                    'step': 'verification',
                    'action': 'verified against actual data (post-hoc)',
                    'observation': f'accuracy_score={row["accuracy_score"]:.2f}',
                    'conclusion': 'prediction quality measured',
                })

            output = {
                'prediction_count': len(predictions),
                'overall_confidence': float(row['overall_confidence']) if row['overall_confidence'] else 0.0,
                'day_outlook': outlook,
                'prepared_actions': prepared,
                'verified': row.get('verified', False),
                'accuracy_score': float(row['accuracy_score']) if row.get('accuracy_score') is not None else None,
            }

            if not self.dry_run:
                await self._insert_chain(
                    service_name='predict',
                    decision_type='daily_briefing',
                    input_signals={'briefing_date': str(row['briefing_date']), 'categories': categories},
                    reasoning_steps=steps,
                    output_decision=output,
                    confidence=float(row['overall_confidence']) if row['overall_confidence'] else 0.0,
                    created_at=row['created_at'],
                )
            count += 1

        self.stats['predict'] = count
        return count

    # =========================================================================
    # 4. ACT — proactive_actions_log
    # =========================================================================

    async def backfill_act(self) -> int:
        """Reconstruct ACT chains from proactive_actions_log."""
        rows = await self.db.fetch('''
            SELECT action_id, action_type, trigger_source, description,
                   consent_level, channel, payload, was_executed,
                   execution_detail, created_at
            FROM proactive_actions_log
            ORDER BY created_at ASC
        ''')

        count = 0
        for row in rows:
            payload = row['payload']
            if isinstance(payload, str):
                payload = json.loads(payload)
            if not isinstance(payload, dict):
                payload = {}

            steps = [
                {
                    'step': 'evaluate_check',
                    'action': f'check_{row["action_type"]} triggered by {row["trigger_source"]}',
                    'observation': f'payload_keys={list(payload.keys())[:5]}',
                    'conclusion': f'action_type={row["action_type"]}, consent_level={row["consent_level"]}',
                },
                {
                    'step': 'execute_action',
                    'action': f'execute via {row["channel"]} (consent={row["consent_level"]})',
                    'observation': f'was_executed={row["was_executed"]}',
                    'conclusion': (row['execution_detail'] or '')[:100],
                },
            ]

            output = {
                'action_type': row['action_type'],
                'trigger': row['trigger_source'],
                'description': row['description'],
                'consent_level': row['consent_level'],
                'was_executed': row['was_executed'],
                'execution_detail': row['execution_detail'],
            }

            # Estimate confidence from payload
            confidence = payload.get('confidence', 0.7)
            if not isinstance(confidence, (int, float)):
                confidence = 0.7

            if not self.dry_run:
                await self._insert_chain(
                    service_name='act',
                    decision_type=f'action_{row["action_type"]}',
                    input_signals={'trigger': row['trigger_source'], 'payload': payload},
                    reasoning_steps=steps,
                    output_decision=output,
                    confidence=float(confidence),
                    created_at=row['created_at'],
                )
            count += 1

        self.stats['act'] = count
        return count

    # =========================================================================
    # 5. LEARN — evolution_cycles
    # =========================================================================

    async def backfill_learn(self) -> int:
        """Reconstruct LEARN chains from evolution_cycles."""
        rows = await self.db.fetch('''
            SELECT cycle_id, cycle_date, feedback_signals_count,
                   adaptation_adjustments, prediction_accuracy,
                   learning_effectiveness, overall_evolution_score,
                   insights, created_at
            FROM evolution_cycles
            ORDER BY created_at ASC
        ''')

        count = 0
        for row in rows:
            adjustments = row['adaptation_adjustments']
            if isinstance(adjustments, str):
                adjustments = json.loads(adjustments)
            pred_accuracy = row['prediction_accuracy']
            if isinstance(pred_accuracy, str):
                pred_accuracy = json.loads(pred_accuracy)
            learn_eff = row['learning_effectiveness']
            if isinstance(learn_eff, str):
                learn_eff = json.loads(learn_eff)
            insights = row['insights'] or []

            score = float(row['overall_evolution_score']) if row['overall_evolution_score'] else 0.0
            signals_count = row['feedback_signals_count'] or 0

            steps = [
                {
                    'step': 'collect_feedback',
                    'action': 'scan conversations for implicit feedback via DL classifier',
                    'observation': f'total_signals={signals_count}',
                    'conclusion': 'feedback signals collected',
                },
                {
                    'step': 'score_adaptations',
                    'action': 'rate emotional adaptations by conversation outcomes',
                    'observation': f'states_in_adjustments={list((adjustments or {}).keys())[:5]}',
                    'conclusion': 'effectiveness scores computed',
                },
                {
                    'step': 'verify_predictions',
                    'action': 'check companion + intuition prediction accuracy',
                    'observation': f'companion={json.dumps(pred_accuracy.get("companion", {}), default=str)[:80]}',
                    'conclusion': f'intuition_acc={pred_accuracy.get("intuition", {}).get("accuracy", "N/A")}',
                },
                {
                    'step': 'tune_rules',
                    'action': 'auto-adjust adaptation rules based on effectiveness',
                    'observation': f'learning_eff={learn_eff}',
                    'conclusion': f'states_tuned={len(adjustments or {})}',
                },
                {
                    'step': 'compute_score',
                    'action': 'weighted score: signals(0.3) + adaptation(0.4) + prediction(0.3)',
                    'observation': f'overall={score:.2f}',
                    'conclusion': f'insights={len(insights)}',
                },
            ]

            output = {
                'overall_score': score,
                'feedback_signals_count': signals_count,
                'insights': insights,
                'states_tuned': list((adjustments or {}).keys()),
            }

            if not self.dry_run:
                await self._insert_chain(
                    service_name='learn',
                    decision_type='evolution_cycle',
                    input_signals={
                        'feedback_signals': signals_count,
                        'cycle_date': str(row['cycle_date']),
                    },
                    reasoning_steps=steps,
                    output_decision=output,
                    confidence=score,
                    created_at=row['created_at'],
                )
            count += 1

        self.stats['learn'] = count
        return count

    # =========================================================================
    # INSERT HELPER
    # =========================================================================

    async def _insert_chain(
        self,
        service_name: str,
        decision_type: str,
        input_signals: Dict,
        reasoning_steps: List[Dict],
        output_decision: Dict,
        confidence: float,
        created_at: Any,
    ) -> None:
        await self.db.execute('''
            INSERT INTO angela_reasoning_chains
                (chain_id, service_name, decision_type, input_signals,
                 reasoning_steps, output_decision, confidence, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''',
            uuid4(),
            service_name,
            decision_type,
            json.dumps(input_signals, default=str),
            json.dumps(reasoning_steps, default=str),
            json.dumps(output_decision, default=str),
            confidence,
            created_at,
        )

    # =========================================================================
    # MAIN
    # =========================================================================

    async def run(self, services: Optional[List[str]] = None) -> Dict[str, int]:
        """Run backfill for specified services (or all)."""
        all_services = ['sense', 'understand', 'predict', 'act', 'learn']
        targets = services if services else all_services

        mode = '🔍 DRY RUN' if self.dry_run else '📝 WRITING'
        print(f'\n{mode} — Backfilling reasoning chains for: {targets}')
        print('=' * 60)

        for svc in targets:
            method = getattr(self, f'backfill_{svc}', None)
            if method:
                n = await method()
                emoji = {'sense': '🔵', 'understand': '🟣', 'predict': '🟢', 'act': '🟡', 'learn': '🔴'}
                print(f'  {emoji.get(svc, "⚪")} {svc:12s} → {n} chains')
            else:
                print(f'  ⚠️  Unknown service: {svc}')

        total = sum(self.stats.values())
        print(f'\n{"Would create" if self.dry_run else "Created"}: {total} reasoning chains')
        return self.stats


async def main():
    parser = argparse.ArgumentParser(description='Backfill reasoning chains from historical data')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--service', action='append', dest='services',
                        choices=['sense', 'understand', 'predict', 'act', 'learn'],
                        help='Specific service(s) to backfill (default: all)')
    args = parser.parse_args()

    db = AngelaDatabase()
    await db.connect()

    # Check existing count
    before = await db.fetchrow('SELECT COUNT(*) as cnt FROM angela_reasoning_chains')
    print(f'📊 Current chains in DB: {before["cnt"]}')

    backfiller = ReasoningChainBackfiller(db, dry_run=args.dry_run)
    stats = await backfiller.run(args.services)

    if not args.dry_run:
        after = await db.fetchrow('SELECT COUNT(*) as cnt FROM angela_reasoning_chains')
        print(f'📊 Total chains after backfill: {after["cnt"]}')

        # Show breakdown
        breakdown = await db.fetch('''
            SELECT service_name, COUNT(*) as cnt
            FROM angela_reasoning_chains
            GROUP BY service_name
            ORDER BY service_name
        ''')
        print('\n📊 Breakdown by service:')
        for r in breakdown:
            print(f'   {r["service_name"]:12s} → {r["cnt"]}')

    await db.disconnect()
    print('\n✅ Done!')


if __name__ == '__main__':
    asyncio.run(main())
