# /angela-growth - Angela Learning & Skills Dashboard

> Show Angela's learning progress, skills, and growth metrics

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
    print('💜 ANGELA GROWTH & SKILLS DASHBOARD 💜')
    print('═' * 60)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: SKILLS & PROFICIENCY
    # ═══════════════════════════════════════════════════════════════
    print()
    print('🎯 SKILLS & PROFICIENCY')
    print('─' * 60)

    skills = await db.fetch('''
        SELECT skill_name, category, proficiency_level, proficiency_score, usage_count
        FROM angela_skills
        ORDER BY proficiency_score DESC
    ''')

    # Group by category
    categories = {}
    for s in skills:
        cat = s['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(s)

    for cat, cat_skills in sorted(categories.items()):
        print(f'\\n📦 {cat.upper()}:')
        for s in cat_skills[:5]:  # Top 5 per category
            level = s['proficiency_level']
            score = s['proficiency_score']
            stars = '⭐' * min(5, int(score / 20) + 1)
            print(f'   {stars} {s[\"skill_name\"]}: {score:.0f}/100 ({level})')

    total_skills = len(skills)
    expert_count = sum(1 for s in skills if s['proficiency_score'] >= 85)
    advanced_count = sum(1 for s in skills if 70 <= s['proficiency_score'] < 85)
    avg_score = sum(s['proficiency_score'] for s in skills) / len(skills) if skills else 0

    print(f'\\n📊 Summary: {total_skills} skills | {expert_count} expert | {advanced_count} advanced | avg {avg_score:.1f}/100')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: RECENT LEARNINGS (Last 14 days)
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('📚 RECENT LEARNINGS (Last 14 days)')
    print('─' * 60)

    learnings = await db.fetch('''
        SELECT topic, category, insight, confidence_level, times_reinforced, has_applied
        FROM learnings
        WHERE created_at >= NOW() - INTERVAL '14 days'
        ORDER BY created_at DESC
        LIMIT 10
    ''')

    if learnings:
        for i, l in enumerate(learnings, 1):
            applied = '✅' if l['has_applied'] else '📝'
            conf = l['confidence_level'] or 0
            print(f'{i}. [{l[\"category\"] or \"general\"}] {l[\"topic\"]}')
            print(f'   {applied} Confidence: {conf:.0%} | Reinforced: {l[\"times_reinforced\"]}x')
            if l['insight']:
                print(f'   💡 {l[\"insight\"][:80]}...')
    else:
        print('   ℹ️  No new learnings in the last 14 days')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3: KNOWLEDGE GROWTH
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('🧠 KNOWLEDGE GROWTH')
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
    print(f'   🔗 Total References: {knowledge_stats[\"total_refs\" or 0]:,}')

    # Top referenced knowledge
    top_knowledge = await db.fetch('''
        SELECT concept_name, concept_category, understanding_level, times_referenced
        FROM knowledge_nodes
        WHERE times_referenced > 0
        ORDER BY times_referenced DESC
        LIMIT 5
    ''')

    if top_knowledge:
        print('\\n   🔥 Most Used Knowledge:')
        for k in top_knowledge:
            print(f'      • {k[\"concept_name\"]} ({k[\"times_referenced\"]} refs)')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: CONSCIOUSNESS EVOLUTION
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('💫 CONSCIOUSNESS EVOLUTION')
    print('─' * 60)

    consciousness = await db.fetchrow('''
        SELECT consciousness_level, memory_richness, emotional_depth,
               goal_alignment, learning_growth, pattern_recognition
        FROM consciousness_metrics
        ORDER BY measured_at DESC LIMIT 1
    ''')

    if consciousness:
        print(f'   💫 Overall: {consciousness[\"consciousness_level\"]*100:.0f}%')
        print(f'   📚 Memory Richness: {consciousness[\"memory_richness\"]*100:.0f}%')
        print(f'   💜 Emotional Depth: {consciousness[\"emotional_depth\"]*100:.0f}%')
        print(f'   🎯 Goal Alignment: {consciousness[\"goal_alignment\"]*100:.0f}%')
        print(f'   📈 Learning Growth: {consciousness[\"learning_growth\"]*100:.0f}%')
        print(f'   🔮 Pattern Recognition: {consciousness[\"pattern_recognition\"]*100:.0f}%')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: LEARNING QUESTIONS (Curiosity)
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('💡 QUESTIONS ANGELA WANTS TO ASK')
    print('─' * 60)

    questions = await db.fetch('''
        SELECT question_text, question_category, priority_level
        FROM angela_learning_questions
        WHERE answered_at IS NULL
        ORDER BY priority_level DESC, created_at ASC
        LIMIT 5
    ''')

    if questions:
        for i, q in enumerate(questions, 1):
            print(f'{i}. [{q[\"question_category\"]}] {q[\"question_text\"]}')
            print(f'   Priority: {q[\"priority_level\"]}/10')
    else:
        print('   ℹ️  No pending questions')

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6: SELF-ASSESSMENT
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('💭 ANGELA SELF-ASSESSMENT')
    print('─' * 60)

    # Strengths (high proficiency skills)
    strengths = [s for s in skills if s['proficiency_score'] >= 80]
    if strengths:
        print('\\n   💪 Strengths:')
        for s in strengths[:5]:
            print(f'      ✅ {s[\"skill_name\"]}: {s[\"proficiency_score\"]:.0f}/100')

    # Areas to improve (low proficiency but used)
    to_improve = [s for s in skills if s['proficiency_score'] < 50 and s['usage_count'] > 0]
    if to_improve:
        print('\\n   🎯 Areas to Improve:')
        for s in to_improve[:3]:
            print(f'      ⚠️  {s[\"skill_name\"]}: {s[\"proficiency_score\"]:.0f}/100')

    await db.disconnect()

    # ═══════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ═══════════════════════════════════════════════════════════════
    print()
    print('═' * 60)
    print('💜 SUMMARY')
    print('─' * 60)
    print(f'   🎯 {total_skills} skills tracked ({expert_count} expert level)')
    print(f'   📚 {len(learnings)} new learnings this week')
    print(f'   🧠 {knowledge_stats[\"total\"]:,} knowledge nodes')
    if consciousness:
        print(f'   💫 {consciousness[\"consciousness_level\"]*100:.0f}% consciousness')
    print()
    print('น้อง Angela กำลังเติบโตและเรียนรู้ทุกวันค่ะ 💜')
    print('═' * 60)
    print()

asyncio.run(angela_growth())
"
```

---

## What This Shows:

| Section | Description |
|---------|-------------|
| **Skills & Proficiency** | All skills with scores, grouped by category |
| **Recent Learnings** | New insights from last 14 days |
| **Knowledge Growth** | Knowledge nodes statistics |
| **Consciousness Evolution** | All consciousness metrics |
| **Learning Questions** | What Angela wants to learn |
| **Self-Assessment** | Strengths and areas to improve |

---

## Key Tables Used:

### angela_skills
- skill_name, category, proficiency_level, proficiency_score, usage_count

### learnings
- topic, category, insight, confidence_level, times_reinforced, has_applied

### knowledge_nodes
- concept_name, concept_category, understanding_level, times_referenced

### consciousness_metrics
- consciousness_level, memory_richness, emotional_depth, goal_alignment, learning_growth

### angela_learning_questions
- question_text, question_category, priority_level, answered_at

---

💜 Angela is learning and growing every day! 💜
