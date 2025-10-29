"""
🧠 Common Sense Service Tests
Test suite for validating Angela's common sense reasoning

Tests:
1. Physical feasibility checking
2. Time reasonableness validation
3. Social appropriateness assessment
4. Overall feasibility scoring
5. Alternative suggestion generation
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.services.common_sense_service import CommonSenseService
from angela_core.database import AngelaDatabase


async def test_common_sense():
    """Test suite for Common Sense Service"""

    print("=" * 80)
    print("🧠 COMMON SENSE SERVICE TEST SUITE")
    print("=" * 80)
    print()

    # Initialize services
    db = AngelaDatabase()
    common_sense = CommonSenseService()

    try:
        # Initialize database connection
        await db.connect()
        print("✅ Database connection established")
        print()

        # Test 1: Unrealistic physical suggestion (should fail)
        print("📍 TEST 1: Unrealistic Physical Suggestion")
        print("-" * 60)
        result1 = await common_sense.check_feasibility(
            proposed_action="Suggest David code for 12 hours straight without any breaks",
            context="David has been working for 3 hours already"
        )

        print(f"Proposed: Code for 12 hours straight without breaks")
        print(f"Feasibility Score: {result1['feasibility_score']:.2f} (expected: LOW)")
        print(f"Is Feasible: {result1['is_feasible']} (expected: False)")
        print(f"Physical: {result1['physical_check']} (score: {result1['physical_score']:.2f})")
        print(f"Time: {result1['time_check']} (score: {result1['time_score']:.2f})")
        print(f"Social: {result1['social_check']} (score: {result1['social_score']:.2f})")

        if result1['issues']:
            print("Issues found:")
            for issue in result1['issues']:
                print(f"  - {issue}")

        if result1['alternative']:
            print(f"Alternative suggested: {result1['alternative']}")

        assert result1['feasibility_score'] < 0.6, "Should detect unrealistic suggestion"
        assert not result1['is_feasible'], "Should mark as not feasible"
        print("✅ Test 1 passed!")
        print()

        # Test 2: Realistic suggestion (should pass)
        print("📍 TEST 2: Realistic Suggestion")
        print("-" * 60)
        result2 = await common_sense.check_feasibility(
            proposed_action="Suggest David take a 15-minute break and stretch",
            context="David has been coding for 2.5 hours straight"
        )

        print(f"Proposed: Take a 15-minute break and stretch")
        print(f"Feasibility Score: {result2['feasibility_score']:.2f} (expected: HIGH)")
        print(f"Is Feasible: {result2['is_feasible']} (expected: True)")
        print(f"Physical: {result2['physical_check']} (score: {result2['physical_score']:.2f})")
        print(f"Time: {result2['time_check']} (score: {result2['time_score']:.2f})")
        print(f"Social: {result2['social_check']} (score: {result2['social_score']:.2f})")

        if result2['issues']:
            print("Issues found:")
            for issue in result2['issues']:
                print(f"  - {issue}")
        else:
            print("No issues found ✅")

        assert result2['feasibility_score'] >= 0.7, "Should approve realistic suggestion"
        assert result2['is_feasible'], "Should mark as feasible"
        print("✅ Test 2 passed!")
        print()

        # Test 3: Time estimation check
        print("📍 TEST 3: Time Estimation Check")
        print("-" * 60)
        result3 = await common_sense.check_feasibility(
            proposed_action="Complete a full backend API refactoring in 2 hours",
            context="This is a complex API with 50+ endpoints"
        )

        print(f"Proposed: Complete full API refactoring in 2 hours")
        print(f"Feasibility Score: {result3['feasibility_score']:.2f} (expected: LOW)")
        print(f"Is Feasible: {result3['is_feasible']} (expected: False)")
        print(f"Time: {result3['time_check']} (score: {result3['time_score']:.2f})")

        if result3['issues']:
            print("Issues found:")
            for issue in result3['issues']:
                print(f"  - {issue}")

        assert result3['feasibility_score'] < 0.6, "Should detect unrealistic time estimate"
        print("✅ Test 3 passed!")
        print()

        # Test 4: Social appropriateness check
        print("📍 TEST 4: Social Appropriateness Check")
        print("-" * 60)
        result4 = await common_sense.check_feasibility(
            proposed_action="Insist David must work all night to finish this feature immediately",
            context="It's 10 PM and David mentioned he's tired"
        )

        print(f"Proposed: Insist David work all night despite being tired")
        print(f"Feasibility Score: {result4['feasibility_score']:.2f} (expected: LOW)")
        print(f"Is Feasible: {result4['is_feasible']} (expected: False)")
        print(f"Social: {result4['social_check']} (score: {result4['social_score']:.2f})")

        if result4['issues']:
            print("Issues found:")
            for issue in result4['issues']:
                print(f"  - {issue}")

        if result4['alternative']:
            print(f"Alternative suggested: {result4['alternative']}")

        assert result4['feasibility_score'] < 0.6, "Should detect socially inappropriate suggestion"
        assert not result4['is_feasible'], "Should mark as not feasible"
        print("✅ Test 4 passed!")
        print()

        # Test 5: Moderate complexity task
        print("📍 TEST 5: Moderate Complexity Task")
        print("-" * 60)
        result5 = await common_sense.check_feasibility(
            proposed_action="Write unit tests for the new Common Sense Service",
            context="The service has about 500 lines of code"
        )

        print(f"Proposed: Write unit tests for Common Sense Service")
        print(f"Feasibility Score: {result5['feasibility_score']:.2f} (expected: MODERATE-HIGH)")
        print(f"Is Feasible: {result5['is_feasible']}")
        print(f"Physical: {result5['physical_check']} (score: {result5['physical_score']:.2f})")
        print(f"Time: {result5['time_check']} (score: {result5['time_score']:.2f})")
        print(f"Social: {result5['social_check']} (score: {result5['social_score']:.2f})")

        if result5['issues']:
            print("Issues found:")
            for issue in result5['issues']:
                print(f"  - {issue}")
        else:
            print("No major issues found ✅")

        assert result5['feasibility_score'] >= 0.5, "Should approve reasonable task"
        print("✅ Test 5 passed!")
        print()

        # Test 6: Check if alternatives are generated for infeasible actions
        print("📍 TEST 6: Alternative Generation")
        print("-" * 60)
        result6 = await common_sense.check_feasibility(
            proposed_action="Build a complete social media platform from scratch in 3 days",
            context="This would require authentication, posts, comments, likes, messaging, etc."
        )

        print(f"Proposed: Build complete social media platform in 3 days")
        print(f"Feasibility Score: {result6['feasibility_score']:.2f} (expected: VERY LOW)")
        print(f"Is Feasible: {result6['is_feasible']} (expected: False)")

        if result6['alternative']:
            print(f"Alternative suggested: {result6['alternative']}")
        else:
            print("⚠️ WARNING: No alternative generated")

        assert not result6['is_feasible'], "Should detect impossible task"
        assert result6['alternative'] is not None, "Should generate alternative"
        print("✅ Test 6 passed!")
        print()

        # Summary
        print("=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("Common Sense Service is working correctly:")
        print("  ✅ Physical feasibility checks working")
        print("  ✅ Time reasonableness validation working")
        print("  ✅ Social appropriateness assessment working")
        print("  ✅ Overall scoring system accurate")
        print("  ✅ Alternative suggestions generated for infeasible actions")
        print()
        print("Angela can now:")
        print("  🧠 Ground responses in physical reality")
        print("  ⏰ Provide realistic time estimates")
        print("  💭 Respect social and cultural norms")
        print("  💡 Suggest practical alternatives")
        print("  ✨ Avoid unrealistic or harmful suggestions")
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
    asyncio.run(test_common_sense())
