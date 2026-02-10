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
import subprocess
from datetime import datetime

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

    async def _learning_catchup():
        try:
            from angela_core.services.session_learning_processor import SessionLearningProcessor
            slp = SessionLearningProcessor()
            result = await slp.process_unprocessed_conversations(hours_back=48, limit=50)
            await slp.disconnect()
            return result
        except Exception as e:
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

    (subconscious, learning_catchup, project_result, daemon_running,
     adaptation_profile, companion_briefing,
     evolution_stats, proactive_results, relevant_notes) = await asyncio.gather(
        _load_subconscious(),
        _learning_catchup(),
        _project_context(),
        _daemon_check(),
        _calculate_adaptation(),
        _load_companion_briefing(),
        _load_evolution_stats(),
        _run_proactive_actions(),
        _load_relevant_notes(),
    )

    all_projects, project_context = project_result

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
    if learning_catchup and learning_catchup['processed'] > 0:
        print(f'🧠 Learning catch-up: {learning_catchup["processed"]} pairs → '
              f'{learning_catchup["total_concepts"]} concepts, '
              f'{learning_catchup["total_patterns"]} patterns')
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

    # Related Notes (Google Keep)
    if relevant_notes:
        print()
        print('📝 Related Notes (Google Keep):')
        for doc in relevant_notes[:3]:
            content = doc.content or ''
            if ': ' in content:
                title = content.split(': ', 1)[0]
            else:
                title = content[:60]
            title = title.strip()
            if not title or title == 'None':
                title = content[:60].strip() if content else '(untitled)'
            score_pct = int(doc.combined_score * 100)
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
