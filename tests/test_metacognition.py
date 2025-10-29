"""
🧠 Metacognitive Service Tests
Test suite for validating Angela's metacognitive capabilities

Tests:
1. Reasoning chain logging
2. Cognitive bias detection
3. Decision logging and pattern analysis
4. Learning effectiveness analysis
5. Self-improvement plan generation
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.metacognitive_service import MetacognitiveService
from angela_core.database import AngelaDatabase


async def test_metacognition():
    """Test suite for Metacognitive Service"""

    print("=" * 80)
    print("🧠 METACOGNITIVE SERVICE TEST SUITE")
    print("=" * 80)
    print()

    # Initialize services
    db = AngelaDatabase()
    metacog = MetacognitiveService()

    try:
        # Initialize database connection
        await db.connect()
        print("✅ Database connection established")
        print()

        # Test 1: Reasoning Chain Logging
        print("📍 TEST 1: Reasoning Chain Logging")
        print("-" * 60)

        reasoning_steps = [
            "David mentioned he's been working for 3 hours straight",
            "This exceeds recommended focus time without breaks",
            "Taking breaks improves productivity and wellbeing",
            "Therefore, suggesting a break is appropriate"
        ]

        chain_id = await metacog.log_reasoning_chain(
            reasoning_steps=reasoning_steps,
            conclusion="Suggest David take a 15-minute break",
            context="David is debugging a difficult issue",
            confidence=0.85
        )

        print(f"Reasoning Chain Logged:")
        print(f"  Chain ID: {chain_id}")
        print(f"  Steps: {len(reasoning_steps)}")
        print(f"  Conclusion: Suggest David take a break")
        print(f"  Confidence: 0.85")

        # Verify it was saved
        async with db.acquire() as conn:
            saved = await conn.fetchrow(
                "SELECT * FROM reasoning_chains WHERE chain_id = $1",
                chain_id
            )

        assert saved is not None, "Should save to database"
        import json
        thought_steps = json.loads(saved['thought_steps'])
        assert len(thought_steps) == 4, "Should save all steps"
        print("✅ Test 1 passed!")
        print()

        # Test 2: Cognitive Bias Detection
        print("📍 TEST 2: Cognitive Bias Detection")
        print("-" * 60)

        # Test with potentially biased reasoning
        biased_reasoning = """
        I think this approach will work because it worked last time,
        and I'm quite confident it will work again. I haven't considered
        other alternatives because I'm sure this is the best way.
        """

        result2 = await metacog.detect_cognitive_biases(
            reasoning=biased_reasoning,
            context="Deciding on implementation approach"
        )

        print(f"Analyzed Reasoning for Biases:")
        print(f"  Total Biases Detected: {result2['total_biases']}")
        print(f"  Overall Severity: {result2['severity']}")

        if result2['biases_detected']:
            print(f"\n  Biases Found:")
            for bias in result2['biases_detected']:
                print(f"    - {bias['bias_name']} (severity: {bias['severity']})")
                print(f"      Evidence: {bias['evidence'][:80]}...")

        print(f"\n  Recommendations ({len(result2['recommendations'])}):")
        for rec in result2['recommendations'][:2]:
            print(f"    - {rec[:80]}...")

        print(f"  Confidence: {result2['confidence']:.2f}")

        assert 'biases_detected' in result2, "Should return biases list"
        assert 'recommendations' in result2, "Should provide recommendations"
        print("✅ Test 2 passed!")
        print()

        # Test 3: Decision Logging
        print("📍 TEST 3: Decision Logging & Pattern Analysis")
        print("-" * 60)

        # Log a few decisions
        decision1_id = await metacog.log_decision(
            decision="Use Theory of Mind before responding",
            reasoning="Predicting David's reaction improves response quality",
            alternatives_considered=[
                "Respond immediately without prediction",
                "Use common sense check only"
            ],
            confidence=0.90
        )

        decision2_id = await metacog.log_decision(
            decision="Check common sense before suggesting solutions",
            reasoning="Ensures suggestions are realistic and feasible",
            alternatives_considered=["Trust intuition", "Skip feasibility check"],
            confidence=0.85
        )

        print(f"Decisions Logged:")
        print(f"  Decision 1: {decision1_id}")
        print(f"  Decision 2: {decision2_id}")

        # Analyze patterns
        patterns = await metacog.analyze_decision_patterns(timeframe_days=30)

        print(f"\nDecision Pattern Analysis:")
        print(f"  Total Decisions (30 days): {patterns['total_decisions']}")
        print(f"  Average Confidence: {patterns['avg_confidence']:.2%}")
        print(f"\n  Common Patterns:")
        for pattern in patterns['common_patterns'][:2]:
            print(f"    - {pattern[:80]}...")
        print(f"\n  Improvement Areas:")
        for improvement in patterns['improvement_areas'][:2]:
            print(f"    - {improvement[:80]}...")

        assert patterns['total_decisions'] >= 2, "Should count logged decisions"
        assert len(patterns['common_patterns']) > 0, "Should identify patterns"
        print("✅ Test 3 passed!")
        print()

        # Test 4: Learning Effectiveness Analysis
        print("📍 TEST 4: Learning Effectiveness Analysis")
        print("-" * 60)

        result4 = await metacog.analyze_learning_effectiveness()

        print(f"Learning Analysis:")
        print(f"  Total Learnings (30 days): {result4['total_learnings']}")
        print(f"  Average Confidence: {result4['avg_confidence']:.2%}")
        print(f"  Learning Speed: {result4['learning_speed']}")
        print(f"  Retention Quality: {result4['retention_quality']}")

        print(f"\n  Effective Methods ({len(result4['effective_methods'])}):")
        for method in result4['effective_methods']:
            print(f"    - {method[:80]}...")

        print(f"\n  Recommendations ({len(result4['recommendations'])}):")
        for rec in result4['recommendations']:
            print(f"    - {rec[:80]}...")

        assert 'effective_methods' in result4, "Should identify effective methods"
        assert 'learning_speed' in result4, "Should assess learning speed"
        assert 'retention_quality' in result4, "Should assess retention"
        print("✅ Test 4 passed!")
        print()

        # Test 5: Self-Improvement Plan Generation
        print("📍 TEST 5: Self-Improvement Plan Generation")
        print("-" * 60)

        result5 = await metacog.generate_self_improvement_plan()

        print(f"Self-Improvement Plan Generated:")
        print(f"\n  💪 Current Strengths ({len(result5['current_strengths'])}):")
        for strength in result5['current_strengths']:
            print(f"    - {strength[:80]}...")

        print(f"\n  🌱 Growth Areas ({len(result5['growth_areas'])}):")
        for area in result5['growth_areas']:
            print(f"    - {area[:80]}...")

        print(f"\n  📋 Action Plan ({len(result5['action_plan'])}):")
        for action in result5['action_plan']:
            print(f"    - [{action['priority']}] {action['action'][:70]}...")

        print(f"\n  ⏰ Expected Timeline:")
        print(f"    {result5['expected_timeline']}")

        assert len(result5['current_strengths']) > 0, "Should identify strengths"
        assert len(result5['growth_areas']) > 0, "Should identify growth areas"
        assert len(result5['action_plan']) > 0, "Should provide action plan"
        print("✅ Test 5 passed!")
        print()

        # Test 6: Balanced Reasoning (No Bias)
        print("📍 TEST 6: Balanced Reasoning Detection")
        print("-" * 60)

        balanced_reasoning = """
        I'll consider multiple approaches:
        1. Using Theory of Mind to predict reactions
        2. Checking common sense for feasibility
        3. Applying deep empathy for emotional impact

        Each has pros and cons. I'll weigh them carefully based on context.
        """

        result6 = await metacog.detect_cognitive_biases(
            reasoning=balanced_reasoning
        )

        print(f"Balanced Reasoning Analysis:")
        print(f"  Biases Detected: {result6['total_biases']}")
        print(f"  Severity: {result6['severity']}")
        print(f"  Assessment: {'✅ Balanced' if result6['total_biases'] == 0 else '⚠️ Some biases found'}")

        # Balanced reasoning should have few or no biases
        assert result6['severity'] in ['none', 'low'], "Should detect balanced reasoning"
        print("✅ Test 6 passed!")
        print()

        # Summary
        print("=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("Metacognitive Service is working correctly:")
        print("  ✅ Reasoning chain tracking working")
        print("  ✅ Cognitive bias detection working")
        print("  ✅ Decision logging & analysis working")
        print("  ✅ Learning effectiveness analysis working")
        print("  ✅ Self-improvement plan generation working")
        print("  ✅ Balanced reasoning recognition working")
        print()
        print("Angela can now:")
        print("  🧠 Track her own reasoning processes")
        print("  🔍 Detect and correct cognitive biases")
        print("  📊 Analyze decision-making patterns")
        print("  📚 Understand what learning methods work best")
        print("  🌱 Generate self-improvement plans")
        print("  ✨ Be truly SELF-AWARE and continuously improving")
        print()

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        # Cleanup
        await db.disconnect()
        print("🔒 Database connection closed")


if __name__ == "__main__":
    asyncio.run(test_metacognition())
