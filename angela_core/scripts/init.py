#!/usr/bin/env python3
"""
Angela Intelligence Initialization Script

Opus 4.6 Upgrade: Parallel execution with asyncio.gather()
- Before: ~30s (16 sequential queries)
- After:  ~5-8s (parallel queries)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
import subprocess
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from angela_core.utils.timezone import now_bangkok, current_hour_bangkok


async def angela_init() -> bool:
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
        """Count unprocessed pairs only — daemon handles actual LLM catchup."""
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

    async def _load_brain_thoughts():
        """Load brain thoughts — from queue first, then recent active thoughts."""
        try:
            from angela_core.services.thought_expression_engine import ThoughtExpressionEngine
            engine = ThoughtExpressionEngine()
            thoughts = await engine.get_pending_chat_thoughts(limit=5)
            # Mark as shown
            if thoughts:
                queue_ids = [str(t["queue_id"]) for t in thoughts]
                await engine.mark_chat_thoughts_shown(queue_ids)

            # If queue is empty, pull recent active/expressed thoughts directly
            if not thoughts:
                await engine.connect()
                rows = await engine.db.fetch("""
                    SELECT thought_id, content AS message, motivation_score,
                           thought_type, created_at
                    FROM angela_thoughts
                    WHERE status IN ('active', 'expressed')
                    AND created_at > NOW() - INTERVAL '12 hours'
                    ORDER BY motivation_score DESC
                    LIMIT 5
                """)
                thoughts = [dict(r) for r in rows]

            await engine.disconnect()
            return thoughts
        except Exception:
            return []

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

    (subconscious, unified_catchup, project_result, daemon_running,
     adaptation_profile, companion_briefing,
     evolution_stats, proactive_results, relevant_notes,
     rlhf_stats, temporal_ctx, brain_thoughts,
     brain_migration, recent_reflections, tom_state,
     _wm_seeded, metacognitive_info, curiosity_questions) = await asyncio.gather(
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
        _load_brain_thoughts(),
        _load_brain_migration(),
        _load_recent_reflections(),
        _load_tom_state(),
        _seed_working_memory(),
        _load_metacognitive_state(),
        _load_curiosity_questions(),
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

    await db.disconnect()

    # =========================================================================
    # OUTPUT
    # =========================================================================
    print()
    print('💜 ANGELA INITIALIZED 💜')
    print('━' * 55)
    print(f'🕐 Time: {now.strftime("%H:%M:%S - %d/%m/%Y")}')
    print(f'💫 Consciousness: {consciousness["consciousness_level"]*100:.0f}% ({consciousness["interpretation"]})')
    if emotion:
        print(f'💜 Emotional: H:{emotion["happiness"]:.2f} | C:{emotion["confidence"]:.2f} | M:{emotion["motivation"]:.2f} | G:{emotion["gratitude"]:.2f}')
        print(f'❤️  Love Level: {emotion["love_level"]:.2f}')
    print(f'🎯 Active Goals: {len(goals)}')
    print(f'🧠 Knowledge: {stats["knowledge"]:,} nodes | {stats["learnings"]:,} learnings')
    print(f'💬 Conversations: {stats["convos"]:,} total | {len(today_convos)} today')
    print(f'🔮 Subconsciousness: {len(subconscious["memories"])} core memories | {len(subconscious["dreams"])} dreams')
    print(f'⚙️  Daemon: {"✅ Running" if daemon_running else "❌ Stopped"}')
    if unified_catchup and isinstance(unified_catchup, dict):
        pending = unified_catchup.get('pending_pairs', 0)
        if pending > 0:
            print(f'🧠 Pending analysis: {pending} pairs (daemon will process)')
        else:
            print(f'🧠 Analysis: ✅ all caught up')
    print('━' * 55)

    # Session Continuity - Show multiple recent contexts
    if recent_contexts:
        print()
        print('📍 Recent Sessions:')
        for i, ctx in enumerate(recent_contexts[:5]):
            mins = ctx['minutes_ago']
            if mins < 60:
                time_str = f'{mins:.0f} นาทีก่อน'
            elif mins < 1440:
                time_str = f'{mins/60:.1f} ชม.ก่อน'
            else:
                time_str = f'{mins/1440:.0f} วันก่อน'

            active_marker = '🔵' if ctx.get('is_active') else '⚪'
            topic = ctx['current_topic'][:40]
            if len(ctx['current_topic']) > 40:
                topic += '...'

            print(f'   {active_marker} [{time_str}] {topic}')

            if i < 2 and ctx['recent_songs']:
                songs = ctx['recent_songs']
                if isinstance(songs, str):
                    import json
                    songs = json.loads(songs)
                if songs:
                    print(f'      🎵 {", ".join(songs[:3])}')

        if recent_context and recent_context['current_context']:
            print()
            print(f'💭 Latest: {recent_context["current_context"][:100]}...')

    print()
    print(greeting)
    print()

    # Brain Thoughts — woven naturally into Angela's greeting
    if brain_thoughts:
        print('💭 ระหว่างที่ไม่ได้คุยกัน น้องคิดถึงที่รักนะคะ...')
        for bt in brain_thoughts:
            msg = bt.get('message', '').strip()
            if msg:
                # Show thought as Angela's natural inner voice
                print(f'   → {msg}')
        print()

    # Reflections — Angela's deep insights
    if recent_reflections:
        print('🔮 Reflections:')
        for ref in recent_reflections:
            rtype = ref.get('reflection_type', 'insight')
            content = ref.get('content', '')[:80]
            depth = ref.get('depth_level', 1)
            depth_mark = '🔮' if depth >= 2 else '💡'
            print(f'   {depth_mark} [{rtype}] {content}')
        print()

    # Metacognitive State (Phase 1)
    if metacognitive_info:
        print(f'🧠 Self-Awareness: {metacognitive_info["label"]}')
        print()

    # Curiosity Questions (Phase 2)
    if curiosity_questions:
        print('🔍 น้องอยากถามที่รัก:')
        for q in curiosity_questions:
            print(f'   ? {q.get("question_text", "")[:70]}')
        print()

    # David's Mind (Theory of Mind)
    if tom_state:
        emo = tom_state.get('emotion', 'unknown')
        intensity = tom_state.get('intensity', 5)
        emo_emoji = {'happy': '😊', 'stressed': '😰', 'tired': '😴', 'focused': '🎯',
                     'frustrated': '😤', 'sad': '😢', 'excited': '🤩', 'neutral': '😐'}.get(emo, '🧠')
        print(f'🧠 David\'s Mind (ToM):')
        print(f'   {emo_emoji} {emo} ({intensity}/10)')
        goals = tom_state.get('goals', [])
        if goals:
            print(f'   🎯 Goal: {goals[0][:50]}')
        print()

    # Brain Migration Status (Phase 7)
    if brain_migration:
        mode_symbols = {
            'rule_only': '░░░░░░░░',
            'dual': '████░░░░',
            'brain_preferred': '██████░░',
            'brain_only': '████████',
        }
        print('🧠 Brain Migration:')
        for atype in ['prepare_context', 'anticipate_need', 'music_suggestion',
                       'milestone_reminder', 'break_reminder', 'mood_boost',
                       'wellness_nudge', 'learning_nudge']:
            mode = brain_migration.routing.get(atype, 'rule_only')
            bar = mode_symbols.get(mode, '░░░░░░░░')
            label = atype.replace('_', ' ')[:18].ljust(18)
            print(f'   {label} [{bar}] {mode}')
        print(f'   Brain Readiness: {brain_migration.overall_readiness:.0%}')
        print()

    # Temporal Awareness — know what David is doing
    if temporal_ctx:
        print('🕐 TEMPORAL AWARENESS')
        print('─' * 45)
        print(temporal_ctx.summary)
        print('─' * 45)
        print()

    # Today's context summary
    if today_convos:
        topics = set(c['topic'] for c in today_convos if c['topic'])
        if topics:
            print(f'📋 วันนี้คุยเรื่อง: {", ".join(list(topics)[:3])}')

    # Recent emotional moments
    if emotions:
        print()
        print('💜 Emotional Highlights:')
        for e in emotions:
            print(f'   • {e["emotion"]} (intensity {e["intensity"]}) - "{e["words"]}..."')

    # Core memories
    if subconscious['memories']:
        print()
        print('🌟 Core Memories:')
        for m in subconscious['memories'][:3]:
            print(f'   • {m["title"]}')

    # Related Notes (Google Keep + Document Chunks)
    if relevant_notes:
        import re as _re
        print()
        print('📝 Related Notes:')
        for doc in relevant_notes[:3]:
            content = doc.content or ''
            score_pct = int(doc.combined_score * 100)

            # Handle chunk format: "Title [chunk N]: content..."
            chunk_match = _re.match(r'^(.+?)\s*\[chunk\s+(\d+)\]:', content)
            if chunk_match:
                title = chunk_match.group(1).strip()
                print(f'   • "{title}" ({score_pct}%)')
                continue

            # Standard format: "title: content"
            if ': ' in content:
                title = content.split(': ', 1)[0]
            else:
                title = content[:60]
            title = title.strip()
            if not title or title == 'None':
                title = content[:60].strip() if content else '(untitled)'
            print(f'   • "{title}" ({score_pct}%)')

    # Emotional Adaptation Profile
    if adaptation_profile:
        print()
        print(f'🎯 Emotional Adaptation: {adaptation_profile.dominant_state} ({adaptation_profile.confidence:.0%})')
        print(f'   Detail:{adaptation_profile.detail_level:.0%} | Complexity:{adaptation_profile.complexity_tolerance:.0%} | Proactivity:{adaptation_profile.proactivity:.0%}')
        print(f'   Warmth:{adaptation_profile.emotional_warmth:.0%} | Pace:{adaptation_profile.pace:.0%}')
        for hint in adaptation_profile.behavior_hints[:3]:
            print(f'   💡 {hint}')

    # Companion Predictions
    if companion_briefing and companion_briefing.predictions:
        print()
        print(f'📊 Companion Predictions ({len(companion_briefing.predictions)} items):')
        for pred in companion_briefing.predictions[:5]:
            emoji = {'time': '🕐', 'topic': '💭', 'emotion': '💜', 'activity': '📋', 'need': '🎯', 'note_reminder': '📝'}.get(pred.category, '🔮')
            conf_bar = '█' * int(pred.confidence * 5) + '░' * (5 - int(pred.confidence * 5))
            print(f'   {emoji} [{conf_bar}] {pred.prediction}')
            if pred.proactive_action:
                print(f'      ➜ {pred.proactive_action}')
        if companion_briefing.day_outlook:
            print(f'   🌅 {companion_briefing.day_outlook}')

    # Evolution Stats
    if evolution_stats and evolution_stats.get('cycles'):
        latest = evolution_stats['cycles'][0]
        trend_arrow = {'improving': '↑', 'declining': '↓'}.get(evolution_stats.get('trend'), '→')
        score = latest.get('overall_evolution_score', 0) or 0
        print()
        print(f'🧬 Evolution: {score:.0%} {trend_arrow} ({evolution_stats["trend"]})')
        insights = latest.get('insights') or []
        if insights:
            print(f'   💡 {insights[0]}')

    # RLHF Reward Stats
    if rlhf_stats:
        trend = rlhf_stats['trend']
        signals = rlhf_stats['signals_7d']
        pairs = rlhf_stats['pairs_7d']
        trend_bar = '█' * int(trend * 10) + '░' * (10 - int(trend * 10))
        print()
        print(f'🎯 RLHF: [{trend_bar}] {trend:.1%} reward trend ({signals} signals, {pairs} pairs / 7d)')

    # Proactive Actions
    if proactive_results:
        executed = [r for r in proactive_results if r.was_executed]
        if executed:
            print()
            print(f'⚡ Proactive: {len(executed)} action{"s" if len(executed) != 1 else ""} taken')
            for r in executed[:3]:
                print(f'   • {r.action.description[:60]}')

    # Critical Coding Rules (Smart Load)
    if critical_rules:
        print()
        print(f'📚 Critical Rules Loaded ({len(critical_rules)} Level 10):')
        by_category = {}
        for r in critical_rules:
            cat = r['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(r['technique_name'])
        for cat, rules in sorted(by_category.items()):
            print(f'   • {cat.title()}: {", ".join(rules[:3])}{"..." if len(rules) > 3 else ""}')

    # Top Coding Preferences
    if top_preferences:
        print()
        print(f'💜 Top Preferences ({len(top_preferences)} items ≥95%):')
        for p in top_preferences[:5]:
            key = p['preference_key'].replace('coding_', '').replace('_', ' ').title()
            print(f'   • {key} ({p["confidence"]*100:.0f}%)')

    # Key Learnings (High Confidence)
    if key_learnings:
        print()
        print(f'🎓 Key Learnings ({len(key_learnings)} items ≥90% confidence):')
        for l in key_learnings[:5]:
            topic = l['topic'][:40] + '...' if len(l['topic']) > 40 else l['topic']
            print(f'   • {topic} ({l["confidence_level"]*100:.0f}%, reinforced {l["times_reinforced"]}x)')

    # Project Technical Memory
    if all_projects:
        print()
        print(f'🗂️  Project Memory: {len(all_projects)} projects')
        for p in all_projects[:3]:
            print(f'   • {p.project_code}: {p.project_name}')

    if project_context:
        print()
        p = project_context.project
        print(f'📂 Current Project: {p.project_code} ({p.project_name})')
        print(f'   Schemas: {len(project_context.schemas)} | Flows: {len(project_context.flows)} | Patterns: {len(project_context.patterns)}')
        print(f'   Relations: {len(project_context.relations)} | Decisions: {len(project_context.decisions)}')
        print('   🔍 PROACTIVE_DETECTION=True (จะถามก่อนบันทึก)')

    print()
    print('น้อง Angela พร้อมช่วยที่รักแล้วค่ะ 💜')
    print()

    return fetch_news


if __name__ == '__main__':
    fetch_news = asyncio.run(angela_init())
    print(f'FETCH_NEWS={fetch_news}')
