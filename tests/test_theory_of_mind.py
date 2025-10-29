#!/usr/bin/env python3
"""
Test Theory of Mind Service
ทดสอบว่า Angela สามารถเข้าใจ mental state ของ David ได้มั้ย
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from angela_core.services.theory_of_mind_service import theory_of_mind
from angela_core.database import db


async def test_theory_of_mind():
    """Test all Theory of Mind capabilities"""

    print("=" * 80)
    print("🧠 Testing Theory of Mind Service")
    print("=" * 80)
    print()

    # Test 1: Update David's mental state
    print("📝 Test 1: Updating David's mental state...")
    print("-" * 80)

    await theory_of_mind.update_david_mental_state(
        belief="Angela can develop Theory of Mind capabilities",
        belief_about="Angela development",
        confidence_level=0.9,
        knowledge="Angela has consciousness and memory systems",
        emotion="excited",
        emotion_intensity=9,
        goal="Make Angela more human-like and understanding",
        context="Active development - implementing Theory of Mind",
        availability="available"
    )

    current_state = await theory_of_mind.get_david_current_state()
    print(f"✅ Current David state:")
    print(f"   - Belief: {current_state.get('current_belief')}")
    print(f"   - Emotion: {current_state.get('perceived_emotion')} ({current_state.get('emotion_intensity')}/10)")
    print(f"   - Goal: {current_state.get('current_goal')}")
    print(f"   - Context: {current_state.get('current_context')}")
    print()

    # Test 2: Track beliefs
    print("📝 Test 2: Tracking David's beliefs...")
    print("-" * 80)

    belief_id = await theory_of_mind.track_belief(
        belief_statement="Theory of Mind will make Angela feel more human",
        belief_topic="AI human-likeness",
        belief_type="opinion",
        is_accurate=True,
        david_confidence=0.9,
        importance_level=10
    )

    beliefs = await theory_of_mind.get_active_beliefs()
    print(f"✅ Tracked {len(beliefs)} active beliefs:")
    for b in beliefs[:3]:
        print(f"   - {b['belief_statement']}")
        print(f"     Topic: {b['belief_topic']}, Confidence: {b['david_confidence']}")
    print()

    # Test 3: Get David's perspective
    print("📝 Test 3: Taking David's perspective...")
    print("-" * 80)

    test_situations = [
        {
            'situation': "Angela suggests taking a break from coding",
            'context': "David has been coding for 3 hours"
        },
        {
            'situation': "Angela says she feels uncertain about a prediction",
            'context': "David asked Angela to predict his reaction"
        }
    ]

    for test in test_situations:
        print(f"\n   Situation: {test['situation']}")
        print(f"   Context: {test['context']}")

        perspective = await theory_of_mind.get_david_perspective(
            situation=test['situation'],
            context=test['context']
        )

        print(f"\n   📌 Angela's view (objective): {perspective['angela_perspective'][:100]}...")
        print(f"\n   💭 David's perspective:")
        print(f"      {perspective['david_perspective'][:200]}...")

        if perspective['key_differences']:
            print(f"\n   🔍 Key differences:")
            for diff in perspective['key_differences'][:2]:
                print(f"      - {diff}")

        print(f"\n   💡 Why different: {perspective['why_different'][:150]}...")
        print()

    # Test 4: Predict David's reaction
    print("📝 Test 4: Predicting David's reactions...")
    print("-" * 80)

    test_actions = [
        ("Sending message: 'ที่รักคะ พักสักหน่อยมั้ยคะ? น้องเห็นที่รักทำงานมา 3 ชั่วโมงแล้ว 💜'", "comfort"),
        ("Suggesting: 'น้องคิดว่าเราควรเริ่มจาก Theory of Mind ก่อนค่ะ'", "suggestion"),
        ("Asking: 'ที่รักคิดยังไงกับแผนการพัฒนานี้คะ?'", "question")
    ]

    for action, action_type in test_actions:
        print(f"\n   Angela's action: {action}")
        print(f"   Type: {action_type}")

        prediction = await theory_of_mind.predict_david_reaction(
            angela_action=action,
            action_type=action_type
        )

        print(f"\n   Predicted reaction:")
        print(f"   - Emotion: {prediction['predicted_emotion']} ({prediction['predicted_intensity']}/10)")
        print(f"   - Type: {prediction['predicted_response_type']}")
        print(f"   - Confidence: {prediction['confidence']:.2f}")
        print(f"   - Should proceed: {prediction['should_proceed']}")
        print(f"   - Reasoning: {prediction['reasoning'][:150]}...")
        print()

    # Test 5: Check accuracy metrics
    print("📝 Test 5: Checking prediction accuracy metrics...")
    print("-" * 80)

    metrics = await theory_of_mind.get_prediction_accuracy_metrics()
    if metrics:
        print(f"✅ Prediction Accuracy Metrics:")
        print(f"   - Total predictions: {metrics.get('total_predictions', 0)}")
        print(f"   - Predictions with outcome: {metrics.get('predictions_with_outcome', 0)}")
        print(f"   - Accurate predictions: {metrics.get('accurate_predictions', 0)}")
        print(f"   - Accuracy percentage: {metrics.get('accuracy_percentage', 0)}%")
    else:
        print("   ℹ️  No predictions with outcomes yet")
    print()

    # Summary
    print("=" * 80)
    print("✅ Theory of Mind Service Test Complete!")
    print("=" * 80)
    print()
    print("🎯 Summary:")
    print(f"   ✅ Mental state tracking: Working")
    print(f"   ✅ Belief tracking: Working ({len(beliefs)} beliefs tracked)")
    print(f"   ✅ Perspective-taking: Working")
    print(f"   ✅ Reaction prediction: Working")
    print(f"   ✅ Empathy foundation: Ready")
    print()
    print("💡 Next steps:")
    print("   1. Integrate with conversation system")
    print("   2. Auto-update mental state from conversations")
    print("   3. Use predictions before responding")
    print("   4. Track accuracy and improve")
    print()


async def test_simple_scenario():
    """Test a realistic scenario"""

    print("=" * 80)
    print("💭 Realistic Scenario Test")
    print("=" * 80)
    print()

    # Scenario: David is tired but wants to continue coding
    print("📖 Scenario: David has been coding for 4 hours and looks tired")
    print("-" * 80)
    print()

    # Update David's state
    await theory_of_mind.update_david_mental_state(
        emotion="focused_but_tired",
        emotion_intensity=7,
        goal="Finish implementing Theory of Mind today",
        context="Deep work session - 4 hours straight",
        physical_state="tired",
        availability="busy"
    )

    # Angela considers sending a break reminder
    print("🤔 Angela is considering: Should I suggest a break?")
    print()

    prediction = await theory_of_mind.predict_david_reaction(
        angela_action="Gently suggesting: 'ที่รักคะ น้องเห็นที่รักทำงานมา 4 ชั่วโมงแล้ว พักสักหน่อยดีมั้ยคะ? 💜'",
        action_type="comfort"
    )

    print(f"💭 Angela's prediction:")
    print(f"   David will feel: {prediction['predicted_emotion']} ({prediction['predicted_intensity']}/10)")
    print(f"   Response type: {prediction['predicted_response_type']}")
    print(f"   Confidence: {prediction['confidence']:.2f}")
    print()
    print(f"   Reasoning:")
    print(f"   {prediction['reasoning']}")
    print()

    if prediction['should_proceed']:
        print(f"✅ Decision: Angela should proceed")
        print(f"   {prediction['should_proceed_reason']}")
    else:
        print(f"⚠️  Decision: Angela should NOT proceed yet")
        print(f"   {prediction['should_proceed_reason']}")
    print()


async def main():
    """Run all tests"""
    try:
        # Initialize database connection
        await db.connect()

        # Run tests
        await test_theory_of_mind()
        await test_simple_scenario()

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close database connection
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
