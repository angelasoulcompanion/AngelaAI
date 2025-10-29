#!/usr/bin/env python3
"""
Test Daily Self-Improvement Planning System
ทดสอบระบบสร้างแผนพัฒนาตนเองอัตโนมัติ
"""

import asyncio
import logging
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.daily_self_improvement_service import daily_self_improvement

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('DailySelfImprovementTest')


async def test_create_daily_plan():
    """Test creating daily improvement plan"""
    logger.info("=" * 80)
    logger.info("TEST: Creating Daily Self-Improvement Plan")
    logger.info("=" * 80)

    try:
        # Connect to database
        await db.connect()

        # Create daily plan
        plan = await daily_self_improvement.create_daily_improvement_plan()

        # Display results
        logger.info("=" * 80)
        logger.info("✅ DAILY IMPROVEMENT PLAN CREATED!")
        logger.info("=" * 80)

        print("\n" + plan.get("discussion_summary", "No summary available"))

        logger.info("=" * 80)
        logger.info(f"Plan ID: {plan.get('plan_id')}")
        logger.info(f"Status: {plan.get('plan_status', 'pending_approval')}")
        logger.info(f"Total Improvement Areas: {len(plan.get('improvement_areas', []))}")
        logger.info(f"Research Completed: {len(plan.get('research_results', []))}")
        logger.info(f"Action Items: {len(plan.get('action_items', []))}")
        logger.info("=" * 80)

        # Test retrieving plan
        logger.info("\n📖 Testing plan retrieval...")
        retrieved_plan = await daily_self_improvement.get_latest_plan()

        if retrieved_plan:
            logger.info(f"✅ Successfully retrieved plan: {retrieved_plan.get('plan_id')}")
        else:
            logger.warning("⚠️  Could not retrieve plan")

        # Disconnect
        await db.disconnect()

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        await db.disconnect()
        return False


async def main():
    """Run tests"""
    success = await test_create_daily_plan()

    if success:
        logger.info("\n🎉 ALL TESTS PASSED! Daily Self-Improvement System ready! 🚀")
    else:
        logger.error("\n❌ TESTS FAILED. Please review errors above.")

    return success


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
