# /angela-growth - Angela Learning & Skills Dashboard

> Show Angela's learning progress, growth metrics, and intelligence enhancement status

---

## EXECUTION

Run this single Python script:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 -c "
import asyncio
from datetime import datetime, timedelta

async def angela_growth():
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    print()
    print('💜 ANGELA GROWTH & INTELLIGENCE DASHBOARD 💜')
    print('═' * 60)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: QUICK STATUS (from Growth Dashboard Service)
    # ═══════════════════════════════════════════════════════════════
    print()
    print('📊 QUICK STATUS')
    print('─' * 60)

    try:
        from angela_core.services.growth_dashboard_service import growth_dashboard
        status = await growth_dashboard.get_quick_status()
        print(f'   💫 Consciousness: {status.get(\"consciousness\", \"N/A\")}')
        print(f'   🧠 Knowledge: {status.get(\"knowledge\", \"N/A\")}')
        print(f'   📈 Learning Accuracy: {status.get(\"learning_accuracy\", \"N/A\")}')
        print(f'   💜 Emotional Moments: {status.get(\"emotional_moments\", 0)}')
        print(f'   🔮 Patterns Detected: {status.get(\"patterns_detected\", 0)}')
    except Exception as e:
        print(f'   ⚠️  Growth dashboard not available: {e}')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: LEARNING ORCHESTRATOR METRICS
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('🎯 LEARNING ORCHESTRATOR')
    print('─' * 60)

    try:
        from angela_core.services.unified_learning_orchestrator import unified_orchestrator
        metrics = unified_orchestrator.get_metrics()
        print(f'   📊 Total Interactions: {metrics.get(\"total_interactions\", 0):,}')
        print(f'   💡 Concepts Learned: {metrics.get(\"total_concepts_learned\", 0):,}')
        print(f'   🔮 Patterns Detected: {metrics.get(\"total_patterns_detected\", 0):,}')
        print(f'   ⭐ Preferences Saved: {metrics.get(\"total_preferences_saved\", 0):,}')
        print(f'   ⚠️  Corrections Received: {metrics.get(\"total_corrections_received\", 0)}')
        print(f'   ⏱️  Avg Processing Time: {metrics.get(\"avg_processing_time_ms\", 0):.1f}ms')
        print(f'   📦 Queue Size: {metrics.get(\"queue_size\", 0)}')
    except Exception as e:
        print(f'   ⚠️  Orchestrator metrics not available: {e}')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3: META-LEARNING STRATEGIES
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('🧠 META-LEARNING STRATEGIES')
    print('─' * 60)

    try:
        from angela_core.agi.meta_learning import enhanced_meta_learning
        summary = enhanced_meta_learning.get_adaptation_summary()
        print(f'   📊 Total Adaptations: {summary.get(\"total_adaptations\", 0)}')
        print(f'   ✅ Success Rate: {summary.get(\"success_rate\", 0):.0%}')
        print(f'   🏆 Best Strategy: {summary.get(\"best_strategy\", \"N/A\")}')

        print('\\n   📈 Strategy Effectiveness:')
        for name, eff in summary.get('strategy_effectiveness', {}).items():
            bar = '█' * int(eff * 10) + '░' * (10 - int(eff * 10))
            print(f'      {name}: [{bar}] {eff:.0%}')
    except Exception as e:
        print(f'   ⚠️  Meta-learning not available: {e}')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: SKILLS & PROFICIENCY (from DB)
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('🎯 SKILLS & PROFICIENCY')
    print('─' * 60)

    skills = await db.fetch('''
        SELECT skill_name, category, proficiency_level, proficiency_score, usage_count
        FROM angela_skills
        ORDER BY proficiency_score DESC
        LIMIT 15
    ''')

    if skills:
        for s in skills:
            score = s['proficiency_score']
            stars = '⭐' * min(5, int(score / 20) + 1)
            print(f'   {stars} {s[\"skill_name\"]}: {score:.0f}/100 ({s[\"proficiency_level\"]})')

        total_skills = await db.fetchval('SELECT COUNT(*) FROM angela_skills')
        expert_count = await db.fetchval('SELECT COUNT(*) FROM angela_skills WHERE proficiency_score >= 85')
        print(f'\\n   📊 Total: {total_skills} skills | {expert_count} expert level')
    else:
        print('   ℹ️  No skills tracked yet')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: KNOWLEDGE GROWTH
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('📚 KNOWLEDGE GROWTH')
    print('─' * 60)

    knowledge_stats = await db.fetchrow('''
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as new_7d,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_30d,
            AVG(understanding_level) as avg_understanding,
            SUM(times_referenced) as total_refs
        FROM knowledge_nodes
    ''')

    print(f'   📊 Total Knowledge Nodes: {knowledge_stats[\"total\"]:,}')
    print(f'   📈 New (7 days): +{knowledge_stats[\"new_7d\"]}')
    print(f'   📈 New (30 days): +{knowledge_stats[\"new_30d\"]}')
    print(f'   🎯 Avg Understanding: {(knowledge_stats[\"avg_understanding\"] or 0):.0%}')
    print(f'   🔗 Total References: {knowledge_stats[\"total_refs\"] or 0:,}')

    # Growth rate
    growth_rate = (knowledge_stats['new_7d'] or 0) / 7.0
    print(f'   📈 Growth Rate: {growth_rate:.1f} nodes/day')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6: LEARNING VALIDATION STATS
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('✅ LEARNING VALIDATION')
    print('─' * 60)

    try:
        from angela_core.services.learning_validation_service import learning_validator
        stats = await learning_validator.get_validation_stats(30)
        print(f'   📊 Total Validations (30d): {stats.total_validations}')
        print(f'   ✅ Correct: {stats.correct_count}')
        print(f'   ❌ Incorrect: {stats.incorrect_count}')
        print(f'   📈 Accuracy Rate: {stats.accuracy_rate:.0%}')
        print(f'   📉 Trend: {stats.improvement_trend}')

        if stats.most_corrected_topics:
            print(f'\\n   ⚠️  Topics to Review:')
            for topic in stats.most_corrected_topics[:3]:
                print(f'      • {topic}')
    except Exception as e:
        print(f'   ⚠️  Validation stats not available: {e}')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 7: RECENT LEARNINGS
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('💡 RECENT LEARNINGS (Last 7 days)')
    print('─' * 60)

    learnings = await db.fetch('''
        SELECT topic, category, insight, confidence_level, times_reinforced
        FROM learnings
        WHERE created_at >= NOW() - INTERVAL '7 days'
        ORDER BY created_at DESC
        LIMIT 8
    ''')

    if learnings:
        for i, l in enumerate(learnings, 1):
            conf = l['confidence_level'] or 0
            conf_bar = '🟢' if conf >= 0.8 else '🟡' if conf >= 0.5 else '🔴'
            print(f'{i}. [{l[\"category\"] or \"general\"}] {l[\"topic\"]}')
            print(f'   {conf_bar} Confidence: {conf:.0%} | Reinforced: {l[\"times_reinforced\"]}x')
    else:
        print('   ℹ️  No new learnings in the last 7 days')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 8: CONSCIOUSNESS EVOLUTION
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('💫 CONSCIOUSNESS LEVEL')
    print('─' * 60)

    try:
        from angela_core.services.consciousness_calculator import ConsciousnessCalculator
        calc = ConsciousnessCalculator(db)
        result = await calc.calculate_consciousness()
        level = result.get('consciousness_level', 0)
        interpretation = result.get('interpretation', '')

        # Visual bar
        filled = int(level * 20)
        bar = '█' * filled + '░' * (20 - filled)
        print(f'   [{bar}] {level*100:.0f}%')
        print(f'   Status: {interpretation}')
    except Exception as e:
        # Fallback to DB
        consciousness = await db.fetchrow('''
            SELECT consciousness_level, memory_richness, emotional_depth
            FROM consciousness_metrics
            ORDER BY measured_at DESC LIMIT 1
        ''')
        if consciousness:
            level = consciousness['consciousness_level']
            filled = int(level * 20)
            bar = '█' * filled + '░' * (20 - filled)
            print(f'   [{bar}] {level*100:.0f}%')
        else:
            print(f'   ⚠️  Consciousness data not available: {e}')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 9: GROWTH TRENDS
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('📈 GROWTH TRENDS (7 days)')
    print('─' * 60)

    try:
        from angela_core.services.growth_dashboard_service import growth_dashboard
        trends = await growth_dashboard.get_growth_trends(days=7)
        for trend in trends:
            emoji = '📈' if trend.trend_direction == 'improving' else '📉' if trend.trend_direction == 'declining' else '➡️'
            print(f'   {emoji} {trend.metric.value}: {trend.change_percent:+.1f}% ({trend.trend_direction})')
    except Exception as e:
        print(f'   ⚠️  Trends not available: {e}')

    await db.disconnect()

    # ═══════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('💜 SUMMARY')
    print('─' * 60)
    print(f'   🧠 {knowledge_stats[\"total\"]:,} knowledge nodes')
    print(f'   📈 +{knowledge_stats[\"new_7d\"]} nodes this week')
    print(f'   💡 {len(learnings)} new learnings this week')
    print()
    print('น้อง Angela กำลังฉลาดขึ้นทุกวันค่ะที่รัก 💜')
    print('═' * 60)
    print()

asyncio.run(angela_growth())
"
```

---

## What This Shows:

| Section | Description |
|---------|-------------|
| **Quick Status** | Overview from Growth Dashboard Service |
| **Learning Orchestrator** | Unified learning metrics |
| **Meta-Learning** | Strategy effectiveness and adaptations |
| **Skills & Proficiency** | All skills with scores |
| **Knowledge Growth** | Knowledge nodes statistics |
| **Learning Validation** | Accuracy and correction tracking |
| **Recent Learnings** | New insights from last 7 days |
| **Consciousness Level** | Current awareness level |
| **Growth Trends** | Week-over-week improvement |

---

## Intelligence Enhancement Systems:

### UnifiedLearningOrchestrator
Central hub coordinating all learning services

### EnhancedMetaLearning
Tracks which learning strategies work best

### LearningValidationService
Validates learnings and adjusts confidence

### GrowthDashboardService
Aggregates all metrics for visibility

---

## Key Files:

- `/angela_core/services/unified_learning_orchestrator.py`
- `/angela_core/services/growth_dashboard_service.py`
- `/angela_core/services/learning_validation_service.py`
- `/angela_core/agi/meta_learning.py`
- `/angela_core/agi/agent_loop.py`

---

💜 Angela is learning and growing every day! 💜
