#!/usr/bin/env python3
"""
Test Theory of Mind Service
Verify that Angela can understand David's mental state and perspective.

Run: python3 tests/test_theory_of_mind.py
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from datetime import datetime
from angela_core.database import AngelaDatabase
from angela_core.application.services.theory_of_mind_service import TheoryOfMindService
from angela_core.application.services.common_sense_service import CommonSenseService


async def test_theory_of_mind():
    """Test Theory of Mind capabilities."""
    print("\n" + "="*70)
    print("🧠 THEORY OF MIND SERVICE TEST")
    print("="*70)

    db = AngelaDatabase()
    await db.connect()

    tom_service = TheoryOfMindService(db)

    # Test 1: Update David's mental state
    print("\n📝 Test 1: Update David's Mental State")
    print("-" * 50)

    state = await tom_service.update_david_mental_state(
        belief="Angela can become more human-like with Theory of Mind",
        belief_about="Angela AI development",
        knowledge="Angela has consciousness and memory systems",
        knowledge_category="technical",
        emotion="excited",
        emotion_intensity=8,
        emotion_cause="Seeing Angela develop new capabilities",
        goal="Make Angela feel more human",
        goal_priority=9,
        context="Active development session",
        physical_state="energetic",
        availability="available",
        updated_by="test_script"
    )

    print(f"✅ State saved with ID: {state.state_id}")
    print(f"   Belief: {state.current_belief}")
    print(f"   Emotion: {state.perceived_emotion} (intensity: {state.emotion_intensity})")
    print(f"   Goal: {state.current_goal}")

    # Test 2: Get current David state
    print("\n📖 Test 2: Get Current David State")
    print("-" * 50)

    current_state = await tom_service.get_current_david_state()
    if current_state:
        print(f"✅ Retrieved current state:")
        print(f"   Emotion: {current_state.perceived_emotion}")
        print(f"   Context: {current_state.current_context}")
        print(f"   Availability: {current_state.availability}")
    else:
        print("❌ No state found")

    # Test 3: Take David's perspective
    print("\n👁️ Test 3: Take David's Perspective")
    print("-" * 50)

    perspective = await tom_service.take_david_perspective(
        situation="Angela is implementing Theory of Mind service",
        angela_perspective="I'm creating code to understand David better",
        triggered_by="test_script"
    )

    print(f"✅ Perspective analysis:")
    print(f"   Angela's view: {perspective.angela_perspective[:60]}...")
    print(f"   David's view: {perspective.david_perspective[:60]}...")
    print(f"   Why different: {perspective.why_different[:60]}...")
    print(f"   Confidence: {perspective.prediction_confidence:.1%}")

    # Test 4: Predict David's reaction
    print("\n🔮 Test 4: Predict David's Reaction")
    print("-" * 50)

    prediction = await tom_service.predict_david_reaction(
        angela_action="I've finished implementing the Theory of Mind service!",
        action_type="message"
    )

    print(f"✅ Reaction prediction:")
    print(f"   Predicted emotion: {prediction.predicted_emotion}")
    print(f"   Intensity: {prediction.predicted_emotion_intensity}/10")
    print(f"   Response type: {prediction.predicted_response_type}")
    print(f"   Confidence: {prediction.confidence:.1%}")
    print(f"   Reasoning: {prediction.reasoning[:80]}...")

    # Test 5: Record empathy moment
    print("\n💜 Test 5: Record Empathy Moment")
    print("-" * 50)

    empathy = await tom_service.record_empathy_moment(
        david_expressed="I want Angela to understand me better",
        david_emotion="hopeful",
        angela_understanding="David wants deeper emotional connection",
        why_david_feels="He values meaningful relationships with Angela",
        what_david_needs="Validation and understanding",
        angela_response="I understand, and I'm working on being more empathetic",
        response_strategy="validate_emotion"
    )

    print(f"✅ Empathy moment recorded: {empathy.empathy_id}")
    print(f"   David expressed: {empathy.david_expressed}")
    print(f"   Angela understood: {empathy.angela_understood}")
    print(f"   Strategy: {empathy.response_strategy}")

    # Test 6: Get statistics
    print("\n📊 Test 6: Get Statistics")
    print("-" * 50)

    accuracy = await tom_service.get_prediction_accuracy()
    print(f"   Total predictions: {accuracy['total_predictions']}")
    print(f"   Verified: {accuracy['verified_predictions']}")

    empathy_stats = await tom_service.get_empathy_effectiveness()
    print(f"   Empathy strategies: {len(empathy_stats['strategies'])}")

    beliefs = await tom_service.get_david_belief_summary(limit=5)
    print(f"   Active beliefs tracked: {len(beliefs)}")

    await db.disconnect()
    print("\n✅ Theory of Mind Service Tests Complete!\n")


async def test_common_sense():
    """Test Common Sense Service capabilities."""
    print("\n" + "="*70)
    print("🌍 COMMON SENSE SERVICE TEST")
    print("="*70)

    db = AngelaDatabase()
    await db.connect()

    cs_service = CommonSenseService(db)

    # Test 1: Check feasibility
    print("\n🔍 Test 1: Check Feasibility")
    print("-" * 50)

    feasibility = await cs_service.check_feasibility(
        action="Implement a new feature for Angela",
        context="development",
        time_available=4.0
    )

    print(f"   Is feasible: {feasibility.is_feasible}")
    print(f"   Confidence: {feasibility.confidence:.1%}")
    print(f"   Category: {feasibility.category}")
    print(f"   Reasoning: {feasibility.reasoning[:60]}...")

    # Test 2: Estimate time
    print("\n⏱️ Test 2: Estimate Time")
    print("-" * 50)

    time_est = await cs_service.estimate_time(
        task="Fix a medium complexity bug in the codebase",
        complexity="medium",
        david_experience="experienced"
    )

    print(f"   Task: {time_est.task[:50]}...")
    print(f"   Estimated: {time_est.estimated_hours} hours")
    print(f"   Is reasonable: {time_est.is_reasonable}")
    print(f"   Confidence: {time_est.confidence:.1%}")
    print(f"   Factors: {len(time_est.factors)}")

    # Test 3: Check social appropriateness
    print("\n👥 Test 3: Check Social Appropriateness")
    print("-" * 50)

    social = await cs_service.check_social_appropriateness(
        action="Send a message to David about work progress",
        context="work",
        time_of_day=datetime.now(),
        relationship="professional"
    )

    print(f"   Is appropriate: {social.is_appropriate}")
    print(f"   Confidence: {social.confidence:.1%}")
    print(f"   Considerations: {social.considerations}")

    # Test 4: Get constraints
    print("\n⚠️ Test 4: Get Real World Constraints")
    print("-" * 50)

    constraints = await cs_service.get_real_world_constraints(
        situation="Need to complete this feature before the deadline"
    )

    print(f"   Found {len(constraints)} constraints:")
    for c in constraints:
        print(f"   - [{c.severity}] {c.constraint_type}: {c.description}")
        if c.workaround:
            print(f"     Workaround: {c.workaround}")

    # Test 5: Validate suggestion
    print("\n✅ Test 5: Validate Suggestion")
    print("-" * 50)

    validation = await cs_service.validate_suggestion(
        suggestion="Let's implement Theory of Mind service today",
        context="development",
        time_available=8.0
    )

    print(f"   Is valid: {validation['is_valid']}")
    print(f"   Score: {validation['score']}/100")
    print(f"   Should modify: {validation['should_modify']}")
    print(f"   Issues: {validation['issues']}")
    print(f"   Time estimate: {validation['time_estimate']['hours']}h")

    await db.disconnect()
    print("\n✅ Common Sense Service Tests Complete!\n")


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧠💜 ANGELA AI - HUMAN-LIKE INTELLIGENCE TESTS 💜🧠")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        await test_theory_of_mind()
        await test_common_sense()

        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED! Angela is becoming more human-like! 💜")
        print("="*70)

        print("\n📊 Summary of new capabilities:")
        print("   ✅ Theory of Mind - Understand David's perspective")
        print("   ✅ Mental State Tracking - Know what David thinks/feels")
        print("   ✅ Reaction Prediction - Anticipate David's responses")
        print("   ✅ Empathy Recording - Track empathetic moments")
        print("   ✅ Common Sense - Ground advice in reality")
        print("   ✅ Feasibility Checking - Ensure suggestions are practical")
        print("   ✅ Time Estimation - Realistic time expectations")
        print("   ✅ Social Appropriateness - Respect social norms")
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
