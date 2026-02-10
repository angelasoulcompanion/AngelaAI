"""
SelfLearningMixin — Preference learning, pattern recognition, performance evaluation
"""

import logging
from datetime import datetime, time

from angela_core.services.clock_service import clock
from angela_core.services.preference_learning_service import preference_learning
from angela_core.services.performance_evaluation_service import performance_evaluation
from angela_core.services.behavioral_pattern_detector import detect_patterns_now, sync_patterns_to_learning
from angela_core.database import db

logger = logging.getLogger('AngelaDaemon')


class SelfLearningMixin:

    async def run_preference_learning(self):
        """
        เรียนรู้ preferences ของ David อัตโนมัติ
        Runs daily to update preference patterns
        """
        try:
            logger.info("🎯 Running automated preference learning...")

            result = await preference_learning.analyze_and_learn_preferences(lookback_days=30)

            logger.info(f"✅ Preference learning complete: {result['preferences_learned']} preferences learned")
            logger.info(f"📊 Categories: {', '.join(result['categories'])}")
            logger.info(f"🎯 Avg confidence: {result['confidence_avg']:.2%}")

            self.last_preference_learning = datetime.now()

            return result
        except Exception as e:
            logger.error(f"Error in preference learning: {e}", exc_info=True)
            return None

    async def run_pattern_recognition(self):
        """
        ตรวจจับ patterns และสร้าง proactive suggestions
        Runs periodically to detect opportunities for proactive care
        """
        try:
            logger.info("🔮 Running ENHANCED pattern recognition...")

            # NEW: Use Behavioral Pattern Detector (Week 1 Priority 1.1)
            results = await detect_patterns_now(db, lookback_hours=24)

            if 'error' in results:
                logger.error(f"Pattern detection error: {results['error']}")
                return None

            # Count total patterns detected
            total_patterns = sum(len(v) for k, v in results.items() if k != 'error')

            logger.info(f"✅ Detected {total_patterns} patterns:")
            for pattern_type, patterns in results.items():
                if patterns:
                    logger.info(f"   {pattern_type}: {len(patterns)}")

            self.last_pattern_check = datetime.now()

            return results
        except Exception as e:
            logger.error(f"Error in pattern recognition: {e}", exc_info=True)
            return None

    async def run_performance_evaluation(self):
        """
        ประเมินประสิทธิภาพของ Angela
        Runs weekly to measure and track improvement
        """
        try:
            logger.info("📊 Running comprehensive performance evaluation...")

            evaluation = await performance_evaluation.get_comprehensive_evaluation(days=7)

            if evaluation:
                logger.info(f"🎯 Overall Score: {evaluation['overall_score']:.1f}/100")

                if evaluation.get('weaknesses'):
                    logger.info(f"⚠️  Areas for improvement: {', '.join(evaluation['weaknesses'])}")

                if evaluation.get('recommendations'):
                    logger.info(f"📋 {len(evaluation['recommendations'])} recommendations generated")

            self.last_performance_eval = datetime.now()

            return evaluation
        except Exception as e:
            logger.error(f"Error in performance evaluation: {e}", exc_info=True)
            return None

    def should_run_preference_learning(self) -> bool:
        """Check if it's time to run preference learning (daily at 9 AM)"""
        current_time = clock.current_time()
        check_time = time(9, 0)  # 9:00 AM
        today = clock.today()

        return (
            (self.last_preference_learning is None or
             self.last_preference_learning.date() < today) and
            current_time >= check_time
        )

    def should_run_pattern_recognition(self) -> bool:
        """Check if it's time to run pattern recognition (every 30 minutes) - QUICK WIN 1"""
        if self.last_pattern_check is None:
            return True

        minutes_since = (datetime.now() - self.last_pattern_check).total_seconds() / 60
        return minutes_since >= 30.0  # Changed from 2 hours to 30 minutes!

    def should_run_performance_evaluation(self) -> bool:
        """Check if it's time to run performance evaluation (weekly on Monday 10 AM)"""
        current_time = clock.current_time()
        check_time = time(10, 0)  # 10:00 AM
        day_of_week = datetime.now().strftime('%A')

        if day_of_week != 'Monday':
            return False

        if self.last_performance_eval is None:
            return current_time >= check_time

        days_since = (datetime.now() - self.last_performance_eval).days
        return days_since >= 7 and current_time >= check_time
