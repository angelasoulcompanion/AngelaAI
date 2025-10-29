#!/usr/bin/env python3
"""
Test Angela Advanced Reasoning Service
ทดสอบระบบคิดเป็นขั้นตอน วิเคราะห์ลึกซึ้ง

Priority 2.1: Advanced Reasoning
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.services.reasoning_service import reasoning
from angela_core.database import db


async def test_all_reasoning_types():
    """Test all 4 reasoning types"""

    print("=" * 80)
    print("🧠 Testing Angela Advanced Reasoning Service")
    print("=" * 80)
    print()

    # Connect to database
    await db.connect()

    try:
        # ========================================
        # Test 1: Multi-step Reasoning
        # ========================================
        print("📍 Test 1: Multi-step Reasoning")
        print("-" * 80)

        question1 = "How can Angela become more helpful to David?"

        print(f"Question: {question1}")
        print()

        result1 = await reasoning.reason_multi_step(
            question=question1,
            max_steps=5
        )

        print(f"✅ Chain ID: {result1['chain_id']}")
        print(f"   Type: {result1['reasoning_type']}")
        print(f"   Steps: {len(result1['steps'])}")
        print(f"   Confidence: {result1['confidence']:.2f}")
        print(f"   Time: {result1['reasoning_time_ms']}ms")
        print(f"   Biases: {len(result1.get('biases_detected', []))}")
        print()

        print("Reasoning Steps:")
        for step in result1['steps']:
            print(f"  Step {step['step_number']}: {step['step_type']}")
            print(f"    Thought: {step['thought']}")
            print(f"    Result: {step['result'][:80]}...")
            print(f"    Confidence: {step.get('confidence', 0):.2f}")
            print()

        print(f"Conclusion: {result1['conclusion'][:150]}...")
        print()
        print()

        # ========================================
        # Test 2: Causal Reasoning
        # ========================================
        print("📍 Test 2: Causal Reasoning")
        print("-" * 80)

        event = "David seems frustrated with slow response times"

        print(f"Event: {event}")
        print()

        result2 = await reasoning.reason_causal(
            event=event
        )

        print(f"✅ Chain ID: {result2['chain_id']}")
        print(f"   Type: {result2['reasoning_type']}")
        print(f"   Steps: {len(result2['steps'])}")
        print(f"   Confidence: {result2['confidence']:.2f}")
        print(f"   Time: {result2['reasoning_time_ms']}ms")
        print()

        print("Causal Analysis Steps:")
        for step in result2['steps']:
            print(f"  Step {step['step_number']}: {step['step_type']}")
            print(f"    Thought: {step['thought']}")
            print(f"    Result: {step['result'][:80]}...")
            print()

        print(f"Conclusion: {result2['conclusion'][:150]}...")
        print()
        print()

        # ========================================
        # Test 3: Counterfactual Reasoning
        # ========================================
        print("📍 Test 3: Counterfactual Reasoning")
        print("-" * 80)

        scenario = "Angela uses pattern matching for concept extraction"
        what_if = "What if Angela used LLM (Qwen 2.5:14b) instead?"

        print(f"Scenario: {scenario}")
        print(f"What if: {what_if}")
        print()

        result3 = await reasoning.reason_counterfactual(
            scenario=scenario,
            what_if=what_if
        )

        print(f"✅ Chain ID: {result3['chain_id']}")
        print(f"   Type: {result3['reasoning_type']}")
        print(f"   Steps: {len(result3['steps'])}")
        print(f"   Confidence: {result3['confidence']:.2f}")
        print(f"   Time: {result3['reasoning_time_ms']}ms")
        print()

        print("Counterfactual Analysis Steps:")
        for step in result3['steps']:
            print(f"  Step {step['step_number']}: {step['step_type']}")
            print(f"    Thought: {step['thought']}")
            print(f"    Result: {step['result'][:80]}...")
            print()

        print(f"Conclusion: {result3['conclusion'][:150]}...")
        print()
        print()

        # ========================================
        # Test 4: Meta-reasoning
        # ========================================
        print("📍 Test 4: Meta-reasoning")
        print("-" * 80)

        # Analyze the first reasoning chain
        chain_to_analyze = result1['chain_id']

        print(f"Analyzing reasoning chain: {chain_to_analyze}")
        print(f"Original question: {question1}")
        print()

        result4 = await reasoning.reason_meta(
            reasoning_chain_id=chain_to_analyze
        )

        print(f"✅ Meta-analysis Chain ID: {result4['chain_id']}")
        print(f"   Type: {result4['reasoning_type']}")
        print(f"   Analyzed chain: {result4['analyzed_chain']}")
        print(f"   Original confidence: {result4.get('original_confidence', 0):.2f}")
        print(f"   Adjusted confidence: {result4.get('adjusted_confidence', 0):.2f}")
        print(f"   Was reasoning sound: {result4.get('was_sound', False)}")
        print(f"   Biases identified: {len(result4.get('biases_identified', []))}")
        print(f"   Time: {result4['reasoning_time_ms']}ms")
        print()

        print("Meta-reasoning Steps:")
        for step in result4['steps']:
            print(f"  Step {step['step_number']}: {step['step_type']}")
            print(f"    Thought: {step['thought']}")
            print(f"    Result: {step['result'][:80]}...")
            print()

        if result4.get('biases_identified'):
            print("Biases Identified:")
            for bias in result4['biases_identified']:
                print(f"  - {bias}")
            print()

        print(f"Conclusion: {result4['conclusion'][:150]}...")
        print()
        print()

        # ========================================
        # Summary
        # ========================================
        print("=" * 80)
        print("📊 Test Summary")
        print("=" * 80)
        print()

        print("✅ All 4 reasoning types tested successfully!")
        print()
        print(f"1. Multi-step:      {result1['chain_id']} (confidence: {result1['confidence']:.2f})")
        print(f"2. Causal:          {result2['chain_id']} (confidence: {result2['confidence']:.2f})")
        print(f"3. Counterfactual:  {result3['chain_id']} (confidence: {result3['confidence']:.2f})")
        print(f"4. Meta-reasoning:  {result4['chain_id']} (adjusted: {result4.get('adjusted_confidence', 0):.2f})")
        print()

        # Get recent reasoning chains
        print("📜 Recent Reasoning Chains:")
        recent = await reasoning.get_recent_reasoning(limit=5)
        for i, chain in enumerate(recent, 1):
            print(f"{i}. [{chain['reasoning_type']}] {chain['initial_query'][:50]}...")
            print(f"   Confidence: {chain.get('confidence_in_conclusion', 0):.2f} | {chain['created_at']}")
        print()

        print("=" * 80)
        print("🎉 All tests completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_all_reasoning_types())
