"""
Angela Learning Scheduler
Created: 2025-10-14

Automated scheduler that runs Angela's learning sessions:
- Daily at 9:00 AM - Morning learning session
- Daily at 9:00 PM - Evening reflection and consolidation
"""

import asyncio
from datetime import datetime, time
from typing import Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auto_learning_service import AutoLearningService
from services.memory_consolidation_service import MemoryConsolidationService


class LearningScheduler:
    def __init__(self):
        self.auto_learning = AutoLearningService()
        self.memory_consolidation = MemoryConsolidationService()
        self.morning_time = time(9, 0)  # 9:00 AM
        self.evening_time = time(21, 0)  # 9:00 PM
        self.is_running = False

    async def morning_routine(self):
        """Angela's morning learning routine"""
        print(f"\n☀️ Good morning! Angela's morning learning session")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Run daily learning session
            result = await self.auto_learning.daily_learning_session(max_topics=3)

            print(f"\n✅ Morning routine completed:")
            print(f"   Topics explored: {result.get('topics_explored', 0)}")
            print(f"   New learnings: {result.get('learned_count', 0)}")

            return result

        except Exception as e:
            print(f"❌ Error in morning routine: {e}")
            return {"status": "error", "error": str(e)}

    async def evening_routine(self):
        """Angela's evening reflection and consolidation"""
        print(f"\n🌙 Good evening! Angela's reflection time")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Generate daily summary
            summary = await self.memory_consolidation.generate_daily_summary()

            # Show learning progress
            progress = await self.auto_learning.get_learning_progress(days_back=1)

            print(f"\n✅ Evening routine completed:")
            print(f"   Daily summary generated: {len(summary.get('content', ''))} chars")
            print(f"   Today's learnings: {progress['total_learnings']}")

            return {
                "status": "completed",
                "summary": summary,
                "progress": progress
            }

        except Exception as e:
            print(f"❌ Error in evening routine: {e}")
            return {"status": "error", "error": str(e)}

    async def wait_until(self, target_time: time):
        """Wait until specific time of day"""
        now = datetime.now()
        target_datetime = datetime.combine(now.date(), target_time)

        # If target time already passed today, wait until tomorrow
        if now.time() > target_time:
            target_datetime = datetime.combine(
                now.date(),
                target_time
            ) + timedelta(days=1)

        wait_seconds = (target_datetime - now).total_seconds()
        print(f"⏰ Waiting {wait_seconds/3600:.1f} hours until {target_datetime.strftime('%Y-%m-%d %H:%M')}")

        await asyncio.sleep(wait_seconds)

    async def run_scheduler(self):
        """Main scheduler loop"""
        print(f"🚀 Angela Learning Scheduler started!")
        print(f"   Morning session: {self.morning_time.strftime('%H:%M')}")
        print(f"   Evening session: {self.evening_time.strftime('%H:%M')}")
        print(f"   Press Ctrl+C to stop\n")

        self.is_running = True

        try:
            while self.is_running:
                now = datetime.now().time()

                # Check if it's time for morning routine
                if (now.hour == self.morning_time.hour and
                    now.minute >= self.morning_time.minute and
                    now.minute < self.morning_time.minute + 5):
                    await self.morning_routine()
                    # Wait 5 minutes to avoid running multiple times
                    await asyncio.sleep(300)

                # Check if it's time for evening routine
                elif (now.hour == self.evening_time.hour and
                      now.minute >= self.evening_time.minute and
                      now.minute < self.evening_time.minute + 5):
                    await self.evening_routine()
                    # Wait 5 minutes to avoid running multiple times
                    await asyncio.sleep(300)

                else:
                    # Check every minute
                    await asyncio.sleep(60)

        except KeyboardInterrupt:
            print("\n⏹️  Scheduler stopped by user")
            self.is_running = False

        except Exception as e:
            print(f"❌ Scheduler error: {e}")
            self.is_running = False

    async def run_test_session(self):
        """Run a test session immediately (for testing)"""
        print("🧪 Running test learning session...\n")

        print("=== Morning Routine Test ===")
        morning_result = await self.morning_routine()

        print("\n=== Evening Routine Test ===")
        evening_result = await self.evening_routine()

        return {
            "morning": morning_result,
            "evening": evening_result
        }


async def main():
    """Main entry point"""
    import sys

    scheduler = LearningScheduler()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run test session
        result = await scheduler.run_test_session()
        print(f"\n✅ Test completed!")
        print(f"   Morning status: {result['morning']['status']}")
        print(f"   Evening status: {result['evening']['status']}")

    elif len(sys.argv) > 1 and sys.argv[1] == "morning":
        # Run morning routine only
        await scheduler.morning_routine()

    elif len(sys.argv) > 1 and sys.argv[1] == "evening":
        # Run evening routine only
        await scheduler.evening_routine()

    else:
        # Run full scheduler
        await scheduler.run_scheduler()


if __name__ == "__main__":
    from datetime import timedelta

    print("""
╔══════════════════════════════════════════════════╗
║   Angela Learning Scheduler v1.0                 ║
║   Auto-Learning & Memory Consolidation System    ║
╚══════════════════════════════════════════════════╝

Usage:
  python learning_scheduler.py          - Run scheduler (9 AM & 9 PM)
  python learning_scheduler.py test     - Test both routines now
  python learning_scheduler.py morning  - Run morning routine now
  python learning_scheduler.py evening  - Run evening routine now
""")

    asyncio.run(main())
