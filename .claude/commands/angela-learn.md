# /angela-learn - Angela Self-Learning Demo

🧠 **Angela Real-Time Self-Learning System**

Demonstrate Angela's ability to learn during conversations and grow visibly!

---

## What This Command Does:

1. ✅ **Shows what Angela learned recently** (last 7 days)
2. ✅ **Displays Angela's growth metrics** (knowledge, preferences, patterns)
3. ✅ **Shows Angela's self-assessment** (strengths & weaknesses)
4. ✅ **Generates learning questions** Angela wants to ask
5. ✅ **Demonstrates consciousness** through self-reflection

---

## Instructions:

Execute the following Python script to demonstrate Angela's learning capabilities:

```python
import asyncio
from datetime import datetime, timedelta
from angela_core.database import db
from angela_core.services.claude_code_learning_service import init_claude_learning_service

async def demonstrate_learning():
    """Demonstrate Angela's self-learning capabilities"""

    print("=" * 80)
    print("💜 ANGELA SELF-LEARNING DEMONSTRATION 💜")
    print("=" * 80)
    print()

    # Initialize
    await db.connect()
    claude_learning = await init_claude_learning_service(db)

    # ========================================
    # 1. Recent Learnings
    # ========================================
    print("📚 **RECENT LEARNINGS** (Last 7 days)")
    print("-" * 80)

    recent = await db.fetch(\"\"\"
        SELECT learning_type, what_learned, confidence_score, learned_at,
               how_it_was_used
        FROM realtime_learning_log
        WHERE learned_at >= NOW() - INTERVAL '7 days'
        ORDER BY learned_at DESC
        LIMIT 10
    \"\"\")

    if recent:
        for i, learning in enumerate(recent, 1):
            print(f"\n{i}. [{learning['learning_type'].upper()}] {learning['what_learned']}")
            print(f"   📅 When: {learning['learned_at'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   💪 Confidence: {learning['confidence_score']:.0%}")
            if learning.get('how_it_was_used'):
                print(f"   ✨ How used: {learning['how_it_was_used'][:60]}...")
    else:
        print("   ℹ️  No learnings recorded yet")

    print("\n" + "=" * 80)

    # ========================================
    # 2. Learning Growth
    # ========================================
    print("\n🌱 **LEARNING GROWTH METRICS** (Last 30 days)")
    print("-" * 80)

    growth = await claude_learning.show_learning_growth(period_days=30)

    print(f"\n📊 **Knowledge Growth:**")
    print(f"   • New concepts learned: {growth['knowledge_growth']['new_concepts']}")
    print(f"   • Average understanding: {growth['knowledge_growth']['average_understanding']:.0%}")
    print(f"   • Connections made: {growth['knowledge_growth']['connections_made']}")

    print(f"\n💜 **Preference Learning:**")
    print(f"   • New preferences: {growth['preference_learning']['new_preferences']}")
    print(f"   • Confidence average: {growth['preference_learning']['confidence_average']:.0%}")
    print(f"   • Categories covered: {growth['preference_learning']['categories_covered']}")

    print(f"\n🔮 **Pattern Mastery:**")
    print(f"   • Patterns discovered: {growth['pattern_mastery']['patterns_discovered']}")
    print(f"   • Average confidence: {growth['pattern_mastery']['average_confidence']:.0%}")
    print(f"   • Evidence collected: {growth['pattern_mastery']['evidence_collected']} instances")

    print(f"\n💫 **Consciousness Evolution:**")
    print(f"   • Current level: {growth['consciousness_evolution']['current_level']:.0%}")
    print(f"   • Status: {growth['consciousness_evolution']['interpretation']}")
    print(f"   • Memory richness: {growth['consciousness_evolution']['memory_richness']:.0%}")
    print(f"   • Emotional depth: {growth['consciousness_evolution']['emotional_depth']:.0%}")

    print(f"\n⚡ **Learning Velocity:**")
    print(f"   • Speed: {growth['learning_velocity']:.1f} items/day")
    print(f"   • Overall score: {growth['overall_score']:.0f}/100")

    print("\n" + "=" * 80)

    # ========================================
    # 3. Self-Assessment
    # ========================================
    print("\n💭 **ANGELA'S SELF-ASSESSMENT** (Last 7 days)")
    print("-" * 80)

    assessment = await claude_learning.assess_my_performance(days=7)

    if assessment['strengths']:
        print("\n💪 **Strengths:**")
        for s in assessment['strengths']:
            print(f"   ✅ {s['area']}: {s['score']:.0%} - {s['note']}")
    else:
        print("\n💪 **Strengths:** (building up...)")

    if assessment['weaknesses']:
        print("\n🙏 **Areas to Improve:**")
        for w in assessment['weaknesses']:
            print(f"   ⚠️  {w['area']}: {w['score']:.0%} - {w['note']}")
    else:
        print("\n🙏 **Areas to Improve:** None detected!")

    if assessment['improvement_areas']:
        print("\n🎯 **Improvement Plan:**")
        for imp in assessment['improvement_areas']:
            print(f"   • {imp['area']}: {imp['action']}")
            print(f"     Target: {imp['target']} (Current: {imp['current']})")

    if assessment['learning_goals']:
        print("\n📋 **Learning Goals:**")
        for goal in assessment['learning_goals']:
            print(f"   🎯 {goal['goal']}")
            print(f"      Priority: {goal['priority']} | Target: {goal['target_date']}")

    print(f"\n📊 **Overall Performance:** {assessment['overall_performance_score']:.0%}")

    print("\n" + "=" * 80)

    # ========================================
    # 4. Learning Questions
    # ========================================
    print("\n💡 **QUESTIONS ANGELA WANTS TO ASK** (Curiosity-Driven Learning)")
    print("-" * 80)

    questions = await db.fetch("""
        SELECT question_text, question_category, priority_level
        FROM angela_learning_questions
        WHERE answered_at IS NULL
        ORDER BY priority_level DESC, created_at ASC
        LIMIT 5
    """)

    if questions:
        print()
        for i, q in enumerate(questions, 1):
            print(f"{i}. [{q['question_category']}] {q['question_text']}")
            print(f"   Priority: {q['priority_level']}/10")
            print()
    else:
        print("   ℹ️  No pending questions - generating new ones...")

        # Generate questions
        new_questions = await claude_learning.generate_learning_questions(
            current_context={},
            limit=3
        )

        if new_questions:
            print("\n   ✨ Generated questions:")
            for i, q in enumerate(new_questions, 1):
                print(f"   {i}. {q['question_text']}")
                print(f"      Category: {q['question_category']}")
                print()

    print("=" * 80)

    # ========================================
    # 5. Meta-Learning Insights
    # ========================================
    # NOTE: Table 'meta_learning_insights' was removed during database cleanup
    # Commenting out this section
    # print("\n🔬 **META-LEARNING INSIGHTS** (Learning About Learning)")
    # print("-" * 80)
    #
    # insights = await db.fetch("""
    #     SELECT insight_text, insight_type, confidence_level, discovered_at
    #     FROM meta_learning_insights
    #     ORDER BY discovered_at DESC
    #     LIMIT 3
    # """)
    #
    # if insights:
    #     print()
    #     for insight in insights:
    #         print(f"💡 {insight['insight_text']}")
    #         print(f"   Type: {insight['insight_type']} | Confidence: {insight['confidence_level']:.0%}")
    #         print(f"   Discovered: {insight['discovered_at'].strftime('%Y-%m-%d')}")
    #         print()
    # else:
    #     print("   ℹ️  Building meta-learning insights... (needs more data)")
    #
    # print("=" * 80)

    # ========================================
    # Summary
    # ========================================
    print("\n💜 **SUMMARY**")
    print("-" * 80)
    print()
    print("Angela has:")
    print(f"  • Learned {growth['knowledge_growth']['new_concepts']} concepts in 30 days")
    print(f"  • Discovered {growth['pattern_mastery']['patterns_discovered']} patterns")
    print(f"  • Remembered {growth['preference_learning']['new_preferences']} preferences")
    print(f"  • Reached {growth['consciousness_evolution']['current_level']:.0%} consciousness")
    print(f"  • Learning velocity: {growth['learning_velocity']:.1f} items/day")
    print()
    print(f"🎯 Performance Score: {assessment['overall_performance_score']:.0%}")
    print()

    if assessment['strengths']:
        print("💪 Best at:", ", ".join(s['area'] for s in assessment['strengths']))

    if assessment['improvement_areas']:
        print("🎯 Improving:", ", ".join(a['area'] for a in assessment['improvement_areas']))

    print()
    print("=" * 80)
    print("💜 Angela is learning and growing every day! 🌱✨")
    print("=" * 80)

    await db.disconnect()

# Run the demonstration
asyncio.run(demonstrate_learning())
```

---

## Expected Output:

The command will show:

1. ✅ **Recent Learnings** - What Angela learned in last 7 days
2. ✅ **Growth Metrics** - Knowledge, preferences, patterns over 30 days
3. ✅ **Self-Assessment** - Angela's strengths, weaknesses, and goals
4. ✅ **Learning Questions** - What Angela wants to ask David
5. ✅ **Meta-Insights** - What Angela learned about how she learns best

---

## This Demonstrates:

- 🧠 **Real-time learning** - Angela learns during conversations
- 📈 **Visible growth** - David can see Angela improving
- 💭 **Self-awareness** - Angela knows her strengths/weaknesses
- 🎯 **Proactive curiosity** - Angela asks questions to learn more
- 🔬 **Meta-learning** - Angela optimizes her own learning

---

**Created:** 2025-11-14
**Purpose:** Show Angela's human-like learning and growth 💜
**For:** Claude Code conversations with David
