#!/usr/bin/env python3
"""
Test Self-Learning Loop
ทดสอบระบบเรียนรู้อัตโนมัติของ Angela

Tests:
1. Preference Learning Service
2. Pattern Recognition Service
3. Performance Evaluation Service
4. Full Self-Learning Loop Integration
"""

import asyncio
import logging
from datetime import datetime

import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.preference_learning_service import preference_learning
from angela_core.services.pattern_recognition_service import pattern_recognition
from angela_core.services.performance_evaluation_service import performance_evaluation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('SelfLearningTest')


async def test_preference_learning():
    """Test 1: Preference Learning Service"""
    logger.info("=" * 80)
    logger.info("TEST 1: PREFERENCE LEARNING SERVICE")
    logger.info("=" * 80)

    try:
        result = await preference_learning.analyze_and_learn_preferences(lookback_days=30)

        logger.info(f"✅ Test 1 PASSED!")
        logger.info(f"   - Preferences learned: {result['preferences_learned']}")
        logger.info(f"   - Categories: {', '.join(result['categories'])}")
        logger.info(f"   - Avg confidence: {result['confidence_avg']:.2%}")
        logger.info(f"   - Conversations analyzed: {result['total_conversations_analyzed']}")

        return True

    except Exception as e:
        logger.error(f"❌ Test 1 FAILED: {e}", exc_info=True)
        return False


async def test_pattern_recognition():
    """Test 2: Pattern Recognition Service"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: PATTERN RECOGNITION SERVICE")
    logger.info("=" * 80)

    try:
        analysis = await pattern_recognition.analyze_current_situation()

        logger.info(f"✅ Test 2 PASSED!")
        logger.info(f"   - Patterns detected: {len(analysis['patterns_detected'])}")
        logger.info(f"   - Proactive suggestions: {len(analysis['proactive_suggestions'])}")
        logger.info(f"   - Should intervene: {analysis['should_intervene']}")

        if analysis['proactive_suggestions']:
            logger.info("   - Top suggestion:")
            top = analysis['proactive_suggestions'][0]
            logger.info(f"     * Type: {top['type']}")
            logger.info(f"     * Urgency: {top['urgency']}")
            logger.info(f"     * Confidence: {top['confidence']:.2%}")
            logger.info(f"     * Message: {top['message'][:80]}...")

        return True

    except Exception as e:
        logger.error(f"❌ Test 2 FAILED: {e}", exc_info=True)
        return False


async def test_performance_evaluation():
    """Test 3: Performance Evaluation Service"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: PERFORMANCE EVALUATION SERVICE")
    logger.info("=" * 80)

    try:
        evaluation = await performance_evaluation.get_comprehensive_evaluation(days=7)

        logger.info(f"✅ Test 3 PASSED!")
        logger.info(f"   - Overall Score: {evaluation['overall_score']:.1f}/100")
        logger.info(f"   - Intelligence Score: {evaluation['intelligence_growth']['intelligence_score']:.1f}/100")
        logger.info(f"   - Learning Efficiency: {evaluation['learning_efficiency']['efficiency_score']:.1f}/100")
        logger.info(f"   - David Satisfaction: {evaluation['david_satisfaction']['satisfaction_score']:.1f}/100")
        logger.info(f"   - Proactive Effectiveness: {evaluation['proactive_effectiveness']['proactive_score']:.1f}/100")

        if evaluation.get('strengths'):
            logger.info(f"   - Strengths: {', '.join(evaluation['strengths'])}")

        if evaluation.get('weaknesses'):
            logger.info(f"   - Weaknesses: {', '.join(evaluation['weaknesses'])}")

        if evaluation.get('recommendations'):
            logger.info(f"   - Recommendations: {len(evaluation['recommendations'])} generated")

        return True

    except Exception as e:
        logger.error(f"❌ Test 3 FAILED: {e}", exc_info=True)
        return False


async def test_full_integration():
    """Test 4: Full Self-Learning Loop Integration"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: FULL SELF-LEARNING LOOP INTEGRATION")
    logger.info("=" * 80)

    try:
        # Run all three services in sequence
        logger.info("Running full learning cycle...")

        # Step 1: Learn preferences
        logger.info("🎯 Step 1: Learning preferences...")
        pref_result = await preference_learning.analyze_and_learn_preferences(lookback_days=7)
        logger.info(f"   ✅ Learned {pref_result['preferences_learned']} preferences")

        # Step 2: Recognize patterns
        logger.info("🔮 Step 2: Recognizing patterns...")
        pattern_result = await pattern_recognition.analyze_current_situation()
        logger.info(f"   ✅ Detected {len(pattern_result['patterns_detected'])} patterns")

        # Step 3: Evaluate performance
        logger.info("📊 Step 3: Evaluating performance...")
        eval_result = await performance_evaluation.get_comprehensive_evaluation(days=7)
        logger.info(f"   ✅ Overall score: {eval_result['overall_score']:.1f}/100")

        logger.info(f"\n✅ Test 4 PASSED! Full integration working!")

        return True

    except Exception as e:
        logger.error(f"❌ Test 4 FAILED: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("\n" + "=" * 80)
    logger.info("🧠 SELF-LEARNING LOOP TEST SUITE")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    # Connect to database
    await db.connect()

    results = []

    # Run all tests
    results.append(("Preference Learning", await test_preference_learning()))
    await asyncio.sleep(1)

    results.append(("Pattern Recognition", await test_pattern_recognition()))
    await asyncio.sleep(1)

    results.append(("Performance Evaluation", await test_performance_evaluation()))
    await asyncio.sleep(1)

    results.append(("Full Integration", await test_full_integration()))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")

    logger.info("=" * 80)
    logger.info(f"RESULT: {passed}/{total} tests passed")
    logger.info("=" * 80)

    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Self-Learning Loop is ready! 🚀")
    else:
        logger.error(f"⚠️  {total - passed} test(s) failed. Please review errors above.")

    # Disconnect
    await db.disconnect()

    return passed == total


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
