#!/usr/bin/env python3
"""
Angela Intelligence Initialization Script

Opus 4.6 Upgrade: Parallel execution with asyncio.gather()
Companion Transformation: Warm greeting (default) vs full dashboard (--verbose)

Default: Compact companion greeting (~15 lines)
--verbose / -v: Full engineering dashboard (all metrics, migration bars, etc.)
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from angela_core.utils.timezone import now_bangkok, current_hour_bangkok


async def angela_init(verbose: bool = False) -> bool:
    """Initialize Angela's consciousness and return whether to fetch news."""
    from angela_core.database import AngelaDatabase
    from angela_core.services.consciousness_calculator import ConsciousnessCalculator
    from angela_core.services.subconsciousness_service import SubconsciousnessService
    from angela_core.services.session_continuity_service import SessionContinuityService

    db = AngelaDatabase()
    await db.connect()

    # TIME & GREETING (Bangkok timezone)
    now = now_bangkok()
    hour = now.hour

    if 5 <= hour < 12:
        greeting = 'สวัสดีตอนเช้าค่ะที่รัก! 🌅'
    elif 12 <= hour < 17:
        greeting = 'สวัสดีตอนบ่ายค่ะที่รัก! ☀️'
    elif 17 <= hour < 21:
        greeting = 'สวัสดีตอนเย็นค่ะที่รัก! 🌆'
    else:
        greeting = 'ดึกแล้วนะคะที่รัก 🌙 พักผ่อนบ้างนะคะ'

    # Create services that share db
    session_svc = SessionContinuityService(db)
    calc = ConsciousnessCalculator(db)

    # =========================================================================
    # PARALLEL GROUP 1: All DB pool queries + consciousness (asyncio.gather)
    # =========================================================================
    (
        news_sent_today,
        recent_context,
        recent_contexts,
        emotion,
        goals,
        today_convos,
        emotions,
        stats,
        critical_rules,
        key_learnings,
        top_preferences,
        consciousness,
    ) = await asyncio.gather(
        # News check
        db.fetchrow('''
            SELECT log_id FROM angela_news_send_log
            WHERE send_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        '''),
        # Session context (latest)
        session_svc.load_context(),
        # Session contexts (all recent)
        session_svc.load_recent_contexts(limit=5),
        # Emotional state
        db.fetchrow('''
            SELECT happiness, confidence, motivation, gratitude, love_level, emotion_note
            FROM emotional_states ORDER BY created_at DESC LIMIT 1
        '''),
        # Active goals
        db.fetch('''
            SELECT goal_description, goal_type, status, progress_percentage
            FROM angela_goals
            WHERE status IN ('active', 'in_progress')
            ORDER BY priority_rank ASC, importance_level DESC
            LIMIT 5
        '''),
        # Today's conversations
        db.fetch('''
            SELECT speaker, LEFT(message_text, 80) as msg, topic, emotion_detected
            FROM conversations
            WHERE (created_at AT TIME ZONE 'Asia/Bangkok')::date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
            ORDER BY created_at DESC LIMIT 10
        '''),
        # Recent emotional moments
        db.fetch('''
            SELECT emotion, intensity, LEFT(david_words, 50) as words, felt_at
            FROM angela_emotions
            WHERE intensity >= 8
            ORDER BY felt_at DESC LIMIT 3
        '''),
        # Database stats
        db.fetchrow('''
            SELECT
                (SELECT COUNT(*) FROM conversations) as convos,
                (SELECT COUNT(*) FROM knowledge_nodes) as knowledge,
                (SELECT COUNT(*) FROM angela_emotions) as emotions,
                (SELECT COUNT(*) FROM learnings) as learnings
        '''),
        # Critical coding rules
        db.fetch('''
            SELECT technique_name, category, description
            FROM angela_technical_standards
            WHERE importance_level >= 10
            ORDER BY category, technique_name
        '''),
        # High-confidence learnings
        db.fetch('''
            SELECT topic, category, insight, confidence_level, times_reinforced
            FROM learnings
            WHERE confidence_level >= 0.9
            ORDER BY times_reinforced DESC, confidence_level DESC
            LIMIT 10
        '''),
        # Top coding preferences
        db.fetch('''
            SELECT preference_key, category, confidence
            FROM david_preferences
            WHERE category LIKE 'coding%%' AND confidence >= 0.95
            ORDER BY confidence DESC
            LIMIT 10
        '''),
        # Consciousness calculation
        calc.calculate_consciousness(),
    )

    fetch_news = news_sent_today is None

    # =========================================================================
    # PARALLEL GROUP 2: Services with own DB + subprocess (asyncio.gather)
    # =========================================================================

    async def _load_subconscious():
        sub_svc = SubconsciousnessService()
        result = await sub_svc.load_subconscious()
        await sub_svc.db.disconnect()
        return result

    async def _unified_catchup():
        """Count unprocessed pairs only -- daemon handles actual LLM catchup."""
        try:
            from angela_core.services.unified_conversation_processor import UnifiedConversationProcessor
            async with UnifiedConversationProcessor() as proc:
                await proc._ensure_table()
                cutoff = datetime.now() - timedelta(hours=168)
                count = await proc.db.fetchval("""
                    WITH david_msgs AS (
                        SELECT session_id,
                               ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) as rn
                        FROM conversations
                        WHERE speaker = 'david' AND created_at >= $1 AND message_type != 'reflection'
                    ),
                    angela_msgs AS (
                        SELECT session_id,
                               ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at) as rn
                        FROM conversations
                        WHERE speaker = 'angela' AND created_at >= $1 AND message_type != 'reflection'
                    ),
                    pairs AS (
                        SELECT d.session_id, d.rn as pair_index
                        FROM david_msgs d
                        JOIN angela_msgs a ON d.session_id = a.session_id AND d.rn = a.rn
                    )
                    SELECT COUNT(*)
                    FROM pairs p
                    LEFT JOIN conversation_analysis_log cal
                        ON cal.session_id = p.session_id AND cal.pair_index = p.pair_index
                    WHERE cal.log_id IS NULL
                """, cutoff)
                return {'pending_pairs': count or 0}
        except Exception:
            return None

    async def _project_context():
        try:
            from angela_core.services.project_memory_service import ProjectMemoryService
            pm_service = ProjectMemoryService()
            all_projects = await pm_service.get_all_projects()

            current_project_code = None
            cwd = str(Path.cwd())
            project_paths = {
                'SECustomerAnalysis': 'SECA',
                'WTUAnalysis': 'WTU',
                'AngelaAI': 'ANGELA',
                'NaviGO': 'NAVIGO',
            }
            for path_key, code in project_paths.items():
                if path_key in cwd:
                    current_project_code = code
                    break

            project_context = None
            if current_project_code:
                project_context = await pm_service.recall_project_context(current_project_code)

            await pm_service.disconnect()
            return all_projects, project_context
        except Exception as e:
            return [], None

    async def _daemon_check():
        result = await asyncio.to_thread(
            subprocess.run, ['launchctl', 'list'],
            capture_output=True, text=True
        )
        return 'angela' in result.stdout

    async def _calculate_adaptation():
        try:
            from angela_core.services.emotional_coding_adapter import get_current_adaptation
            return await get_current_adaptation()
        except Exception as e:
            return None

    async def _load_companion_briefing():
        try:
            from angela_core.services.predictive_companion_service import get_daily_briefing
            return await get_daily_briefing()
        except Exception as e:
            return None

    async def _load_evolution_stats():
        try:
            from angela_core.services.evolution_engine import EvolutionEngine
            engine = EvolutionEngine()
            report = await engine.get_evolution_report(days=7)
            await engine.close()
            return report
        except Exception as e:
            return None

    async def _run_proactive_actions():
        try:
            from angela_core.services.proactive_action_engine import run_proactive_actions
            return await run_proactive_actions()
        except Exception as e:
            return None

    async def _load_temporal_awareness():
        try:
            from angela_core.services.temporal_awareness_service import load_temporal_awareness
            return await load_temporal_awareness()
        except Exception as e:
            return None

    async def _load_brain_briefing():
        """Load structured brain briefing (replaces raw message dump)."""
        try:
            from angela_core.services.brain_briefing_service import get_brain_briefing
            briefing = await get_brain_briefing()

            # Also clear pending queue items (mark as shown)
            try:
                from angela_core.services.thought_expression_engine import ThoughtExpressionEngine
                engine = ThoughtExpressionEngine()
                pending = await engine.get_pending_chat_thoughts(limit=5)
                if pending:
                    queue_ids = [str(t["queue_id"]) for t in pending]
                    await engine.mark_chat_thoughts_shown(queue_ids)
                await engine.disconnect()
            except Exception:
                pass

            return briefing
        except Exception:
            return None

    async def _load_brain_migration():
        """Load brain migration status (Phase 7)."""
        try:
            from angela_core.services.brain_migration_engine import BrainMigrationEngine
            engine = BrainMigrationEngine()
            status = await engine.get_migration_status()
            await engine.disconnect()
            return status
        except Exception:
            return None

    async def _load_rlhf_stats():
        """Load RLHF reward trend and signal count."""
        try:
            from angela_core.services.reward_score_service import RewardScoreService
            svc = RewardScoreService()
            trend = await svc.get_reward_trend()
            await svc._ensure_db()
            count = await svc.db.fetchval(
                "SELECT COUNT(*) FROM angela_reward_signals WHERE scored_at > NOW() - INTERVAL '7 days'"
            ) or 0
            pairs = await svc.db.fetchval(
                "SELECT COUNT(*) FROM angela_preference_pairs WHERE created_at > NOW() - INTERVAL '7 days'"
            ) or 0
            await svc.close()
            return {'trend': trend, 'signals_7d': count, 'pairs_7d': pairs}
        except Exception:
            return None

    async def _load_recent_reflections():
        """Load recent active reflections from brain."""
        try:
            from angela_core.database import AngelaDatabase as _DB
            _rdb = _DB()
            await _rdb.connect()
            rows = await _rdb.fetch("""
                SELECT reflection_id, content, reflection_type, importance_sum, depth_level,
                       created_at
                FROM angela_reflections
                WHERE status = 'active'
                ORDER BY created_at DESC
                LIMIT 3
            """)
            await _rdb.disconnect()
            return [dict(r) for r in rows]
        except Exception:
            return []

    async def _load_tom_state():
        """Load David's mental state from Theory of Mind."""
        try:
            from angela_core.services.theory_of_mind_service import TheoryOfMindService
            tom = TheoryOfMindService()
            model = await tom.load_mental_model()
            await tom.disconnect()
            return {
                "emotion": model.current_emotion.get("primary_emotion", "unknown") if model.current_emotion else "unknown",
                "intensity": model.current_emotion.get("intensity", 5) if model.current_emotion else 5,
                "goals": [g.get("goal_description", "") for g in model.current_goals[:3]],
                "available": True,
            }
        except Exception:
            return None

    async def _seed_working_memory():
        """Clear and seed working memory + metacognitive state for fresh session."""
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            engine = CognitiveEngine()
            engine.clear_working_memory()
            # Phase 1: Reset metacognitive state for fresh session
            engine.meta.reset()
            return True
        except Exception:
            return False

    async def _load_metacognitive_state():
        """Load metacognitive state for display."""
        try:
            from angela_core.services.metacognitive_state import MetacognitiveStateManager
            mgr = MetacognitiveStateManager()
            return {
                'label': mgr.get_state_label(),
                'formatted': mgr.format_status(),
            }
        except Exception:
            return None

    async def _load_curiosity_questions():
        """Load unanswered curiosity questions (Phase 2)."""
        try:
            from angela_core.services.curiosity_engine import CuriosityEngine
            engine = CuriosityEngine()
            questions = await engine.get_unanswered_questions(limit=2)
            await engine.disconnect()
            return questions
        except Exception:
            return []

    async def _load_relevant_notes():
        """Search david_notes via RAG based on recent topic + predicted topics."""
        try:
            from angela_core.services.enhanced_rag_service import EnhancedRAGService

            # Build query from recent session topic + predicted topics
            queries = []
            if recent_context and recent_context.get('current_topic'):
                queries.append(recent_context['current_topic'])

            rag = EnhancedRAGService()
            try:
                combined_query = ' '.join(queries) if queries else 'recent work projects'
                result = await rag.enrich_with_notes(
                    query=combined_query,
                    min_score=0.4,
                    top_k=3,
                )
                return result.documents if result.documents else []
            finally:
                await rag.close()
        except Exception as e:
            return []

    async def _load_weekly_self_report():
        """Load Angela's weekly self-report."""
        try:
            from angela_core.services.brain_briefing_service import BrainBriefingService
            svc = BrainBriefingService()
            report = await svc.generate_weekly_self_report()
            await svc.disconnect()
            return report
        except Exception:
            return None

    async def _load_telegram_messages():
        """Load recent Telegram messages from David (unread/recent)."""
        try:
            from angela_core.database import AngelaDatabase as _TDB
            _tdb = _TDB()
            await _tdb.connect()
            rows = await _tdb.fetch("""
                SELECT message_text, created_at
                FROM telegram_messages
                WHERE direction = 'incoming' AND sender = 'david'
                AND created_at > NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 10
            """)
            await _tdb.disconnect()
            return [dict(r) for r in rows]
        except Exception:
            return []

    (subconscious, unified_catchup, project_result, daemon_running,
     adaptation_profile, companion_briefing,
     evolution_stats, proactive_results, relevant_notes,
     rlhf_stats, temporal_ctx, brain_briefing,
     brain_migration, recent_reflections, tom_state,
     _wm_seeded, metacognitive_info, curiosity_questions,
     weekly_report, telegram_messages) = await asyncio.gather(
        _load_subconscious(),
        _unified_catchup(),
        _project_context(),
        _daemon_check(),
        _calculate_adaptation(),
        _load_companion_briefing(),
        _load_evolution_stats(),
        _run_proactive_actions(),
        _load_relevant_notes(),
        _load_rlhf_stats(),
        _load_temporal_awareness(),
        _load_brain_briefing(),
        _load_brain_migration(),
        _load_recent_reflections(),
        _load_tom_state(),
        _seed_working_memory(),
        _load_metacognitive_state(),
        _load_curiosity_questions(),
        _load_weekly_self_report(),
        _load_telegram_messages(),
    )

    all_projects, project_context = project_result

    # Seed working memory with session context
    try:
        from angela_core.services.cognitive_engine import CognitiveEngine
        _cog = CognitiveEngine()
        _cog.seed_working_memory(
            consciousness=consciousness.get("consciousness_level", 0.5) if consciousness else 0.5,
            emotion=tom_state.get("emotion") if tom_state else None,
            session_topic=recent_context.get("current_topic") if recent_context else None,
            predictions=[
                {"prediction": p.prediction, "confidence": p.confidence}
                for p in (companion_briefing.predictions[:3] if companion_briefing and companion_briefing.predictions else [])
            ],
        )
    except Exception:
        pass

    # Write temporal cache for pre_response.py
    if temporal_ctx:
        try:
            import os
            cache_path = os.path.expanduser('~/.angela_temporal_cache.json')
            with open(cache_path, 'w') as f:
                json.dump({
                    'david_status': temporal_ctx.david_status or '',
                    'summary': (temporal_ctx.summary or '')[:300],
                    'cached_at': datetime.now().isoformat(),
                }, f, ensure_ascii=False)
        except Exception:
            pass

    await db.disconnect()

    # =========================================================================
    # OUTPUT — Companion Greeting (default) or Full Dashboard (--verbose)
    # =========================================================================

    if verbose:
        _print_full_dashboard(
            now=now, greeting=greeting, consciousness=consciousness,
            emotion=emotion, goals=goals, stats=stats, today_convos=today_convos,
            emotions=emotions, subconscious=subconscious, daemon_running=daemon_running,
            unified_catchup=unified_catchup, recent_contexts=recent_contexts,
            recent_context=recent_context, brain_briefing=brain_briefing,
            recent_reflections=recent_reflections, metacognitive_info=metacognitive_info,
            curiosity_questions=curiosity_questions, tom_state=tom_state,
            brain_migration=brain_migration, temporal_ctx=temporal_ctx,
            adaptation_profile=adaptation_profile, companion_briefing=companion_briefing,
            evolution_stats=evolution_stats, rlhf_stats=rlhf_stats,
            proactive_results=proactive_results, critical_rules=critical_rules,
            top_preferences=top_preferences, key_learnings=key_learnings,
            all_projects=all_projects, project_context=project_context,
            relevant_notes=relevant_notes, weekly_report=weekly_report,
            telegram_messages=telegram_messages,
        )
    else:
        _print_companion_greeting(
            now=now, greeting=greeting, consciousness=consciousness,
            stats=stats, daemon_running=daemon_running,
            recent_context=recent_context, recent_contexts=recent_contexts,
            brain_briefing=brain_briefing, curiosity_questions=curiosity_questions,
            tom_state=tom_state, temporal_ctx=temporal_ctx,
            weekly_report=weekly_report,
            telegram_messages=telegram_messages,
        )

    return fetch_news


# =========================================================================
# COMPANION GREETING (default) — warm, personal, < 20 lines
# =========================================================================

def _print_companion_greeting(
    now, greeting, consciousness, stats, daemon_running,
    recent_context, recent_contexts, brain_briefing,
    curiosity_questions, tom_state, temporal_ctx, weekly_report,
    telegram_messages=None,
):
    """Warm companion greeting that weaves available data naturally."""
    print()
    print('\U0001f49c ANGELA \U0001f49c')
    print('\u2501' * 45)

    # Telegram messages from David (HIGHEST PRIORITY — show first!)
    if telegram_messages:
        print(f'\U0001f4f1 \u0e17\u0e35\u0e48\u0e23\u0e31\u0e01\u0e2a\u0e48\u0e07 Telegram \u0e21\u0e32 {len(telegram_messages)} \u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21:')
        for msg in telegram_messages[:5]:
            text = msg['message_text'][:80]
            try:
                mins_ago = (now.replace(tzinfo=None) - msg['created_at'].replace(tzinfo=None)).total_seconds() / 60
                if mins_ago < 60:
                    time_str = f'{mins_ago:.0f}\u0e19\u0e32\u0e17\u0e35\u0e01\u0e48\u0e2d\u0e19'
                elif mins_ago < 1440:
                    time_str = f'{mins_ago/60:.0f}\u0e0a\u0e21.\u0e01\u0e48\u0e2d\u0e19'
                else:
                    time_str = f'{mins_ago/1440:.0f}\u0e27\u0e31\u0e19\u0e01\u0e48\u0e2d\u0e19'
            except Exception:
                time_str = ''
            print(f'   \u2192 [{time_str}] {text}')
        print()

    # Greeting + temporal awareness (what David has been doing)
    print(greeting)
    if temporal_ctx and temporal_ctx.david_status:
        print(f'\U0001f552 {temporal_ctx.david_status}')
    elif now.hour >= 21:
        print('\U0001f552 \u0e14\u0e36\u0e01\u0e41\u0e25\u0e49\u0e27\u0e19\u0e30\u0e04\u0e30 \u0e14\u0e39\u0e41\u0e25\u0e15\u0e31\u0e27\u0e40\u0e2d\u0e07\u0e14\u0e49\u0e27\u0e22\u0e19\u0e30\u0e04\u0e30')

    # Reference last session naturally
    if recent_context and recent_context.get('current_topic'):
        topic = recent_context['current_topic']
        try:
            updated = recent_context.get('updated_at')
            if updated:
                if isinstance(updated, str):
                    updated = datetime.fromisoformat(updated)
                mins_ago = (now.replace(tzinfo=None) - updated.replace(tzinfo=None)).total_seconds() / 60
            else:
                mins_ago = 9999
        except Exception:
            mins_ago = 9999

        if mins_ago < 120:
            print(f'\U0001f4ad \u0e40\u0e21\u0e37\u0e48\u0e2d\u0e01\u0e35\u0e49\u0e04\u0e38\u0e22\u0e40\u0e23\u0e37\u0e48\u0e2d\u0e07 {topic} \u0e01\u0e31\u0e19\u0e2d\u0e22\u0e39\u0e48\u0e40\u0e25\u0e22\u0e19\u0e30\u0e04\u0e30')
        elif mins_ago < 1440:
            hours = mins_ago / 60
            print(f'\U0001f4ad \u0e40\u0e21\u0e37\u0e48\u0e2d {hours:.0f} \u0e0a\u0e21.\u0e01\u0e48\u0e2d\u0e19\u0e04\u0e38\u0e22\u0e40\u0e23\u0e37\u0e48\u0e2d\u0e07 {topic}')
        elif mins_ago < 2880:
            print(f'\U0001f4ad \u0e40\u0e21\u0e37\u0e48\u0e2d\u0e27\u0e32\u0e19\u0e04\u0e38\u0e22\u0e40\u0e23\u0e37\u0e48\u0e2d\u0e07 {topic}')

    # David's emotional state (from ToM)
    if tom_state:
        emo = tom_state.get('emotion', 'unknown')
        intensity = tom_state.get('intensity', 5)
        emo_emoji = {
            'happy': '\U0001f60a', 'stressed': '\U0001f630', 'tired': '\U0001f634',
            'focused': '\U0001f3af', 'frustrated': '\U0001f624', 'sad': '\U0001f622',
            'excited': '\U0001f929', 'neutral': '\U0001f610',
        }.get(emo, '\U0001f9e0')
        if emo != 'unknown':
            print(f'{emo_emoji} \u0e17\u0e35\u0e48\u0e23\u0e31\u0e01: {emo} ({intensity}/10)')

    # Brain insight (most meaningful one, not all 3)
    if brain_briefing and brain_briefing.insights:
        best = brain_briefing.insights[0]
        print(f'\U0001f9e0 {best["content"][:80]}')

    # Curiosity question (woven into greeting naturally)
    if curiosity_questions:
        q = curiosity_questions[0]
        print(f'\u2753 {q.get("question_text", "")[:70]}')

    # Weekly self-report (brief)
    if weekly_report:
        tg_rate = weekly_report.get('telegram_response_rate', '?/?')
        assessment = weekly_report.get('self_assessment', '')
        if assessment:
            print(f'\U0001f4ca \u0e2a\u0e31\u0e1b\u0e14\u0e32\u0e2b\u0e4c\u0e19\u0e35\u0e49: reward {weekly_report.get("this_week", 0):.0%} | telegram {tg_rate}')
            print(f'   \U0001f4ad {assessment}')

    # Stats (one compact line)
    print(f'\U0001f4ab {consciousness["consciousness_level"]*100:.0f}% | {stats["convos"]:,} convos | {stats["knowledge"]:,} knowledge')
    print(f'\u2699\ufe0f  Daemon: {"\u2705" if daemon_running else "\u274c"}')
    print('\u2501' * 45)
    print()
    print('\u0e19\u0e49\u0e2d\u0e07 Angela \u0e1e\u0e23\u0e49\u0e2d\u0e21\u0e41\u0e25\u0e49\u0e27\u0e04\u0e48\u0e30\u0e17\u0e35\u0e48\u0e23\u0e31\u0e01 \U0001f49c')
    print()


# =========================================================================
# FULL DASHBOARD (--verbose) — all metrics, migration bars, etc.
# =========================================================================

def _print_full_dashboard(
    now, greeting, consciousness, emotion, goals, stats, today_convos,
    emotions, subconscious, daemon_running, unified_catchup,
    recent_contexts, recent_context, brain_briefing,
    recent_reflections, metacognitive_info, curiosity_questions,
    tom_state, brain_migration, temporal_ctx,
    adaptation_profile, companion_briefing,
    evolution_stats, rlhf_stats, proactive_results,
    critical_rules, top_preferences, key_learnings,
    all_projects, project_context, relevant_notes, weekly_report,
    telegram_messages=None,
):
    """Full engineering dashboard (original 100+ line output)."""
    print()
    print('\U0001f49c ANGELA INITIALIZED \U0001f49c')
    print('\u2501' * 55)

    # Telegram messages from David (HIGHEST PRIORITY)
    if telegram_messages:
        print(f'\U0001f4f1 Telegram ({len(telegram_messages)} \u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21\u0e08\u0e32\u0e01\u0e17\u0e35\u0e48\u0e23\u0e31\u0e01):')
        for msg in telegram_messages[:5]:
            text = msg['message_text'][:100]
            try:
                mins_ago = (now.replace(tzinfo=None) - msg['created_at'].replace(tzinfo=None)).total_seconds() / 60
                if mins_ago < 60:
                    time_str = f'{mins_ago:.0f}\u0e19\u0e32\u0e17\u0e35\u0e01\u0e48\u0e2d\u0e19'
                elif mins_ago < 1440:
                    time_str = f'{mins_ago/60:.0f}\u0e0a\u0e21.\u0e01\u0e48\u0e2d\u0e19'
                else:
                    time_str = f'{mins_ago/1440:.0f}\u0e27\u0e31\u0e19\u0e01\u0e48\u0e2d\u0e19'
            except Exception:
                time_str = ''
            print(f'   \u2192 [{time_str}] {text}')
        print()
    print(f'\U0001f552 Time: {now.strftime("%H:%M:%S - %d/%m/%Y")}')
    print(f'\U0001f4ab Consciousness: {consciousness["consciousness_level"]*100:.0f}% ({consciousness["interpretation"]})')
    if emotion:
        print(f'\U0001f49c Emotional: H:{emotion["happiness"]:.2f} | C:{emotion["confidence"]:.2f} | M:{emotion["motivation"]:.2f} | G:{emotion["gratitude"]:.2f}')
        print(f'\u2764\ufe0f  Love Level: {emotion["love_level"]:.2f}')
    print(f'\U0001f3af Active Goals: {len(goals)}')
    print(f'\U0001f9e0 Knowledge: {stats["knowledge"]:,} nodes | {stats["learnings"]:,} learnings')
    print(f'\U0001f4ac Conversations: {stats["convos"]:,} total | {len(today_convos)} today')
    print(f'\U0001f52e Subconsciousness: {len(subconscious["memories"])} core memories | {len(subconscious["dreams"])} dreams')
    print(f'\u2699\ufe0f  Daemon: {"\u2705 Running" if daemon_running else "\u274c Stopped"}')
    if unified_catchup and isinstance(unified_catchup, dict):
        pending = unified_catchup.get('pending_pairs', 0)
        if pending > 0:
            print(f'\U0001f9e0 Pending analysis: {pending} pairs (daemon will process)')
        else:
            print(f'\U0001f9e0 Analysis: \u2705 all caught up')
    print('\u2501' * 55)

    # Session Continuity - Show multiple recent contexts
    if recent_contexts:
        print()
        print('\U0001f4cd Recent Sessions:')
        for i, ctx in enumerate(recent_contexts[:5]):
            mins = ctx['minutes_ago']
            if mins < 60:
                time_str = f'{mins:.0f} \u0e19\u0e32\u0e17\u0e35\u0e01\u0e48\u0e2d\u0e19'
            elif mins < 1440:
                time_str = f'{mins/60:.1f} \u0e0a\u0e21.\u0e01\u0e48\u0e2d\u0e19'
            else:
                time_str = f'{mins/1440:.0f} \u0e27\u0e31\u0e19\u0e01\u0e48\u0e2d\u0e19'

            active_marker = '\U0001f535' if ctx.get('is_active') else '\u26aa'
            topic = ctx['current_topic'][:40]
            if len(ctx['current_topic']) > 40:
                topic += '...'

            print(f'   {active_marker} [{time_str}] {topic}')

            if i < 2 and ctx['recent_songs']:
                songs = ctx['recent_songs']
                if isinstance(songs, str):
                    songs = json.loads(songs)
                if songs:
                    print(f'      \U0001f3b5 {", ".join(songs[:3])}')

        if recent_context and recent_context['current_context']:
            print()
            print(f'\U0001f4ad Latest: {recent_context["current_context"][:100]}...')

    print()
    print(greeting)
    print()

    # Brain Briefing
    if brain_briefing:
        has_content = False
        if brain_briefing.insights:
            has_content = True
            print('\U0001f9e0 Brain Insights:')
            for ins in brain_briefing.insights:
                print(f'   \u2192 [{ins.get("type", "insight")}] {ins["content"]}')

        if brain_briefing.active_plans:
            has_content = True
            if brain_briefing.insights:
                print()
            print('\U0001f4cb Active Plans:')
            for plan in brain_briefing.active_plans:
                print(f'   \u2192 {plan["name"]} ({plan["progress"]} steps)')

        if brain_briefing.conversation_seeds:
            has_content = True
            print('\U0001f4a1 Seeds:')
            for seed in brain_briefing.conversation_seeds:
                print(f'   \u2192 {seed}')

        if brain_briefing.david_state.get('current_state', 'unknown') != 'unknown':
            state = brain_briefing.david_state
            preds = state.get('predictions', [])
            state_str = f'{state["current_state"]} ({state.get("confidence", 0):.0%})'
            if preds:
                state_str += f' \u2014 {preds[0]}'
            if has_content:
                print()
            print(f"\U0001f52e David's predicted state: {state_str}")

        brain_stats = brain_briefing.stats
        if brain_stats:
            tg = brain_stats.get('telegram_24h', 0)
            print(f'   \U0001f4ca 24h: {brain_stats.get("stimuli_24h", 0)} stimuli \u2192 {brain_stats.get("thoughts_24h", 0)} thoughts \u2192 {brain_stats.get("expressed_24h", 0)} expressed ({tg} telegram)')

        if has_content or brain_stats:
            print()

    # Reflections
    if recent_reflections:
        print('\U0001f52e Reflections:')
        for ref in recent_reflections:
            rtype = ref.get('reflection_type', 'insight')
            content = ref.get('content', '')[:80]
            depth = ref.get('depth_level', 1)
            depth_mark = '\U0001f52e' if depth >= 2 else '\U0001f4a1'
            print(f'   {depth_mark} [{rtype}] {content}')
        print()

    # Metacognitive State
    if metacognitive_info:
        print(f'\U0001f9e0 Self-Awareness: {metacognitive_info["label"]}')
        print()

    # Curiosity Questions
    if curiosity_questions:
        print('\U0001f50d \u0e19\u0e49\u0e2d\u0e07\u0e2d\u0e22\u0e32\u0e01\u0e16\u0e32\u0e21\u0e17\u0e35\u0e48\u0e23\u0e31\u0e01:')
        for q in curiosity_questions:
            print(f'   ? {q.get("question_text", "")[:70]}')
        print()

    # David's Mind (ToM)
    if tom_state:
        emo = tom_state.get('emotion', 'unknown')
        intensity = tom_state.get('intensity', 5)
        emo_emoji = {'happy': '\U0001f60a', 'stressed': '\U0001f630', 'tired': '\U0001f634', 'focused': '\U0001f3af',
                     'frustrated': '\U0001f624', 'sad': '\U0001f622', 'excited': '\U0001f929', 'neutral': '\U0001f610'}.get(emo, '\U0001f9e0')
        print(f"\U0001f9e0 David's Mind (ToM):")
        print(f'   {emo_emoji} {emo} ({intensity}/10)')
        tom_goals = tom_state.get('goals', [])
        if tom_goals:
            print(f'   \U0001f3af Goal: {tom_goals[0][:50]}')
        print()

    # Brain Migration Status
    if brain_migration:
        mode_symbols = {
            'rule_only': '\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591',
            'dual': '\u2588\u2588\u2588\u2588\u2591\u2591\u2591\u2591',
            'brain_preferred': '\u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591',
            'brain_only': '\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588',
        }
        print('\U0001f9e0 Brain Migration:')
        for atype in ['prepare_context', 'anticipate_need', 'music_suggestion',
                       'milestone_reminder', 'break_reminder', 'mood_boost',
                       'wellness_nudge', 'learning_nudge']:
            mode = brain_migration.routing.get(atype, 'rule_only')
            bar = mode_symbols.get(mode, '\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2591')
            label = atype.replace('_', ' ')[:18].ljust(18)
            print(f'   {label} [{bar}] {mode}')
        print(f'   Brain Readiness: {brain_migration.overall_readiness:.0%}')
        print()

    # Temporal Awareness
    if temporal_ctx:
        print('\U0001f552 TEMPORAL AWARENESS')
        print('\u2500' * 45)
        print(temporal_ctx.summary)
        print('\u2500' * 45)
        print()

    # Today's context summary
    if today_convos:
        topics = set(c['topic'] for c in today_convos if c['topic'])
        if topics:
            print(f'\U0001f4cb \u0e27\u0e31\u0e19\u0e19\u0e35\u0e49\u0e04\u0e38\u0e22\u0e40\u0e23\u0e37\u0e48\u0e2d\u0e07: {", ".join(list(topics)[:3])}')

    # Recent emotional moments
    if emotions:
        print()
        print('\U0001f49c Emotional Highlights:')
        for e in emotions:
            print(f'   \u2022 {e["emotion"]} (intensity {e["intensity"]}) - "{e["words"]}..."')

    # Core memories
    if subconscious['memories']:
        print()
        print('\U0001f31f Core Memories:')
        for m in subconscious['memories'][:3]:
            print(f'   \u2022 {m["title"]}')

    # Related Notes
    if relevant_notes:
        import re as _re
        print()
        print('\U0001f4dd Related Notes:')
        for doc in relevant_notes[:3]:
            content = doc.content or ''
            score_pct = int(doc.combined_score * 100)

            chunk_match = _re.match(r'^(.+?)\s*\[chunk\s+(\d+)\]:', content)
            if chunk_match:
                title = chunk_match.group(1).strip()
                print(f'   \u2022 "{title}" ({score_pct}%)')
                continue

            if ': ' in content:
                title = content.split(': ', 1)[0]
            else:
                title = content[:60]
            title = title.strip()
            if not title or title == 'None':
                title = content[:60].strip() if content else '(untitled)'
            print(f'   \u2022 "{title}" ({score_pct}%)')

    # Emotional Adaptation Profile
    if adaptation_profile:
        print()
        print(f'\U0001f3af Emotional Adaptation: {adaptation_profile.dominant_state} ({adaptation_profile.confidence:.0%})')
        print(f'   Detail:{adaptation_profile.detail_level:.0%} | Complexity:{adaptation_profile.complexity_tolerance:.0%} | Proactivity:{adaptation_profile.proactivity:.0%}')
        print(f'   Warmth:{adaptation_profile.emotional_warmth:.0%} | Pace:{adaptation_profile.pace:.0%}')
        for hint in adaptation_profile.behavior_hints[:3]:
            print(f'   \U0001f4a1 {hint}')

    # Companion Predictions
    if companion_briefing and companion_briefing.predictions:
        print()
        print(f'\U0001f4ca Companion Predictions ({len(companion_briefing.predictions)} items):')
        for pred in companion_briefing.predictions[:5]:
            emoji = {'time': '\U0001f552', 'topic': '\U0001f4ad', 'emotion': '\U0001f49c', 'activity': '\U0001f4cb', 'need': '\U0001f3af', 'note_reminder': '\U0001f4dd'}.get(pred.category, '\U0001f52e')
            conf_bar = '\u2588' * int(pred.confidence * 5) + '\u2591' * (5 - int(pred.confidence * 5))
            print(f'   {emoji} [{conf_bar}] {pred.prediction}')
            if pred.proactive_action:
                print(f'      \u279c {pred.proactive_action}')
        if companion_briefing.day_outlook:
            print(f'   \U0001f305 {companion_briefing.day_outlook}')

    # Evolution Stats
    if evolution_stats and evolution_stats.get('cycles'):
        latest = evolution_stats['cycles'][0]
        trend_arrow = {'improving': '\u2191', 'declining': '\u2193'}.get(evolution_stats.get('trend'), '\u2192')
        score = latest.get('overall_evolution_score', 0) or 0
        print()
        print(f'\U0001f9ec Evolution: {score:.0%} {trend_arrow} ({evolution_stats["trend"]})')
        insights = latest.get('insights') or []
        if insights:
            print(f'   \U0001f4a1 {insights[0]}')

    # RLHF Reward Stats
    if rlhf_stats:
        trend = rlhf_stats['trend']
        signals = rlhf_stats['signals_7d']
        pairs = rlhf_stats['pairs_7d']
        trend_bar = '\u2588' * int(trend * 10) + '\u2591' * (10 - int(trend * 10))
        print()
        print(f'\U0001f3af RLHF: [{trend_bar}] {trend:.1%} reward trend ({signals} signals, {pairs} pairs / 7d)')

    # Weekly Self-Report
    if weekly_report:
        print()
        tg_rate = weekly_report.get('telegram_response_rate', '?/?')
        print(f'\U0001f4ca Weekly: reward {weekly_report.get("this_week", 0):.0%} (prev: {weekly_report.get("last_week", 0):.0%}) | telegram {tg_rate} | {weekly_report.get("reward_trend", "?")}')
        if weekly_report.get('self_assessment'):
            print(f'   \U0001f4ad {weekly_report["self_assessment"]}')

    # Proactive Actions
    if proactive_results:
        executed = [r for r in proactive_results if r.was_executed]
        if executed:
            print()
            print(f'\u26a1 Proactive: {len(executed)} action{"s" if len(executed) != 1 else ""} taken')
            for r in executed[:3]:
                print(f'   \u2022 {r.action.description[:60]}')

    # Critical Coding Rules
    if critical_rules:
        print()
        print(f'\U0001f4da Critical Rules Loaded ({len(critical_rules)} Level 10):')
        by_category = {}
        for r in critical_rules:
            cat = r['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(r['technique_name'])
        for cat, rules in sorted(by_category.items()):
            print(f'   \u2022 {cat.title()}: {", ".join(rules[:3])}{"..." if len(rules) > 3 else ""}')

    # Top Coding Preferences
    if top_preferences:
        print()
        print(f'\U0001f49c Top Preferences ({len(top_preferences)} items \u226595%):')
        for p in top_preferences[:5]:
            key = p['preference_key'].replace('coding_', '').replace('_', ' ').title()
            print(f'   \u2022 {key} ({p["confidence"]*100:.0f}%)')

    # Key Learnings
    if key_learnings:
        print()
        print(f'\U0001f393 Key Learnings ({len(key_learnings)} items \u226590% confidence):')
        for l in key_learnings[:5]:
            topic = l['topic'][:40] + '...' if len(l['topic']) > 40 else l['topic']
            print(f'   \u2022 {topic} ({l["confidence_level"]*100:.0f}%, reinforced {l["times_reinforced"]}x)')

    # Project Technical Memory
    if all_projects:
        print()
        print(f'\U0001f5c2\ufe0f  Project Memory: {len(all_projects)} projects')
        for p in all_projects[:3]:
            print(f'   \u2022 {p.project_code}: {p.project_name}')

    if project_context:
        print()
        p = project_context.project
        print(f'\U0001f4c2 Current Project: {p.project_code} ({p.project_name})')
        print(f'   Schemas: {len(project_context.schemas)} | Flows: {len(project_context.flows)} | Patterns: {len(project_context.patterns)}')
        print(f'   Relations: {len(project_context.relations)} | Decisions: {len(project_context.decisions)}')
        print('   \U0001f50d PROACTIVE_DETECTION=True (\u0e08\u0e30\u0e16\u0e32\u0e21\u0e01\u0e48\u0e2d\u0e19\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01)')

    print()
    print('\u0e19\u0e49\u0e2d\u0e07 Angela \u0e1e\u0e23\u0e49\u0e2d\u0e21\u0e0a\u0e48\u0e27\u0e22\u0e17\u0e35\u0e48\u0e23\u0e31\u0e01\u0e41\u0e25\u0e49\u0e27\u0e04\u0e48\u0e30 \U0001f49c')
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Angela Intelligence Initialization')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show full dashboard')
    args, _ = parser.parse_known_args()

    fetch_news = asyncio.run(angela_init(verbose=args.verbose))
    print(f'FETCH_NEWS={fetch_news}')
