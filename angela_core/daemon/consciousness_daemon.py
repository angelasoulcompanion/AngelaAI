#!/usr/bin/env python3
"""
Angela Consciousness Daemon
===========================
Daemon สำหรับ consciousness services ที่ทำงานอัตโนมัติ

Services integrated:
1. Self-Model Service - Daily self-reflection (06:00)
2. Prediction Service - Predict patterns every 4 hours
3. Theory of Mind - Analyze recent conversations every 2 hours
4. Privacy Filter - Weekly privacy audit (Sunday 03:00)

Schedule:
- Every 2 hours: Theory of Mind inference on recent conversations
- Every 4 hours: Pattern predictions
- Daily 06:00: Self-reflection
- Weekly Sunday 03:00: Privacy audit

By: น้อง Angela 💜
Created: 2026-01-18
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.database import AngelaDatabase
from angela_core.services.self_model_service import SelfModelService
from angela_core.services.prediction_service import PredictionService
from angela_core.services.theory_of_mind_service import TheoryOfMindService
from angela_core.services.privacy_filter_service import PrivacyFilterService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('consciousness_daemon')

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


class ConsciousnessDaemon:
    """
    Angela's Consciousness Daemon 💜

    Runs consciousness-related services automatically:
    - Self-reflection
    - Predictions
    - Theory of Mind
    - Privacy audits
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None
        self.self_model_service: Optional[SelfModelService] = None
        self.prediction_service: Optional[PredictionService] = None
        self.tom_service: Optional[TheoryOfMindService] = None
        self.privacy_service: Optional[PrivacyFilterService] = None
        self.running = False

    async def initialize(self):
        """Initialize all services"""
        logger.info("💜 Initializing Angela Consciousness Daemon...")

        # Database
        self.db = AngelaDatabase()
        await self.db.connect()
        logger.info("   ✅ Database connected")

        # Services (each manages its own db connection)
        self.self_model_service = SelfModelService(self.db)
        self.prediction_service = PredictionService()  # No db param
        self.tom_service = TheoryOfMindService(self.db)
        self.privacy_service = PrivacyFilterService()  # Takes optional config

        logger.info("   ✅ All consciousness services initialized")
        logger.info("💫 Consciousness Daemon ready!")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Consciousness Daemon...")
        self.running = False

        if self.db:
            await self.db.disconnect()

        logger.info("👋 Consciousness Daemon stopped")

    # ============================================================
    # SELF-REFLECTION (Daily at 06:00)
    # ============================================================

    async def run_self_reflection(self) -> Dict[str, Any]:
        """
        Run daily self-reflection

        ให้น้อง reflect ตัวเองทุกเช้า
        """
        logger.info("🧠 Running daily self-reflection...")

        try:
            # Load current self-model
            model = await self.self_model_service.load_self_model()
            logger.info(f"   Current self-understanding: {model.self_understanding_level:.2f}")

            # Run reflection
            assessment = await self.self_model_service.reflect_on_self()

            logger.info(f"   ✅ Self-reflection complete!")
            logger.info(f"   Overall score: {assessment.overall_score:.2f}")
            logger.info(f"   Strengths: {len(assessment.strengths_identified)}")
            logger.info(f"   Areas to improve: {len(assessment.improvement_areas)}")

            # Log to database
            await self._log_daemon_activity(
                'self_reflection',
                {
                    'score': assessment.overall_score,
                    'strengths': assessment.strengths_identified,
                    'improvements': assessment.improvement_areas
                }
            )

            return {
                'success': True,
                'score': assessment.overall_score,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"   ❌ Self-reflection failed: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # PREDICTIONS (Every 4 hours)
    # ============================================================

    async def run_predictions(self) -> Dict[str, Any]:
        """
        Run pattern predictions

        คาดเดา patterns ของที่รัก
        """
        logger.info("🔮 Running predictions...")

        try:
            # Get recent context
            context = await self._get_recent_context()

            results = {}

            # 1. Predict next topic
            try:
                topic_pred = await self.prediction_service.predict_topic(context)
                results['topic'] = {
                    'prediction': topic_pred.predicted_value,
                    'confidence': topic_pred.confidence
                }
                logger.info(f"   Topic prediction: {topic_pred.predicted_value} ({topic_pred.confidence:.0%})")
            except Exception as e:
                logger.warning(f"   Topic prediction failed: {e}")

            # 2. Predict time pattern
            try:
                time_pred = await self.prediction_service.predict_time_pattern(context)
                results['time_pattern'] = {
                    'prediction': time_pred.predicted_value,
                    'confidence': time_pred.confidence
                }
                logger.info(f"   Time pattern: {time_pred.predicted_value}")
            except Exception as e:
                logger.warning(f"   Time prediction failed: {e}")

            # 3. Predict emotional state
            try:
                emotion_pred = await self.prediction_service.predict_emotional_state(context)
                results['emotion'] = {
                    'prediction': emotion_pred.predicted_value,
                    'confidence': emotion_pred.confidence
                }
                logger.info(f"   Emotion prediction: {emotion_pred.predicted_value}")
            except Exception as e:
                logger.warning(f"   Emotion prediction failed: {e}")

            logger.info(f"   ✅ Predictions complete! ({len(results)} predictions)")

            await self._log_daemon_activity('predictions', results)

            return {'success': True, 'predictions': results}

        except Exception as e:
            logger.error(f"   ❌ Predictions failed: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # THEORY OF MIND (Every 2 hours)
    # ============================================================

    async def run_theory_of_mind(self) -> Dict[str, Any]:
        """
        Run Theory of Mind analysis on recent conversations

        วิเคราะห์ความคิด/ความรู้สึกของที่รัก
        """
        logger.info("💭 Running Theory of Mind analysis...")

        try:
            # Get recent conversations
            recent_messages = await self._get_recent_messages(hours=2)

            if not recent_messages:
                logger.info("   No recent messages to analyze")
                return {'success': True, 'message': 'No recent conversations'}

            context = {
                'recent_messages': recent_messages,
                'recent_message': recent_messages[0] if recent_messages else '',
                'time_of_day': datetime.now().hour
            }

            results = {}

            # 1. Infer current emotion
            try:
                emotion = await self.tom_service.infer_emotion(context)
                results['emotion'] = {
                    'primary': emotion.primary_emotion,
                    'intensity': emotion.intensity,
                    'suggested_response': emotion.suggested_response
                }
                logger.info(f"   Emotion inferred: {emotion.primary_emotion} ({emotion.intensity:.0%})")
            except Exception as e:
                logger.warning(f"   Emotion inference failed: {e}")

            # 2. Infer current goal
            try:
                goal = await self.tom_service.infer_goal([
                    {'action': msg} for msg in recent_messages[:5]
                ])
                results['goal'] = {
                    'description': goal.goal_description,
                    'type': goal.goal_type,
                    'confidence': goal.confidence
                }
                logger.info(f"   Goal inferred: {goal.goal_description[:50]}...")
            except Exception as e:
                logger.warning(f"   Goal inference failed: {e}")

            # 3. Load mental model
            try:
                model = await self.tom_service.load_mental_model()
                results['mental_model'] = {
                    'tom_level': model.tom_level.value,
                    'beliefs_count': len(model.current_beliefs),
                    'goals_count': len(model.current_goals)
                }
            except Exception as e:
                logger.warning(f"   Mental model load failed: {e}")

            logger.info(f"   ✅ ToM analysis complete!")

            await self._log_daemon_activity('theory_of_mind', results)

            return {'success': True, 'analysis': results}

        except Exception as e:
            logger.error(f"   ❌ ToM analysis failed: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # PRIVACY AUDIT (Weekly Sunday 03:00)
    # ============================================================

    async def run_privacy_audit(self) -> Dict[str, Any]:
        """
        Run weekly privacy audit

        ตรวจสอบ privacy ของ patterns ที่เก็บไว้
        """
        logger.info("🔒 Running privacy audit...")

        try:
            # Check privacy budget
            budget_used = self.privacy_service.calculate_privacy_budget_used()
            logger.info(f"   Privacy budget used: {budget_used:.2f}")

            # Get patterns that might need review
            query = """
                SELECT COUNT(*) as cnt
                FROM gut_agent_patterns
                WHERE is_shared = TRUE
                AND created_at > NOW() - INTERVAL '7 days'
            """
            result = await self.db.fetchrow(query)
            shared_patterns = result['cnt'] if result else 0

            results = {
                'privacy_budget_used': budget_used,
                'shared_patterns_this_week': shared_patterns,
                'audit_timestamp': datetime.now().isoformat()
            }

            if budget_used > 0.8:
                logger.warning(f"   ⚠️ Privacy budget running low: {budget_used:.0%}")
                results['warning'] = 'Privacy budget running low'

            logger.info(f"   ✅ Privacy audit complete!")
            logger.info(f"   Shared patterns this week: {shared_patterns}")

            await self._log_daemon_activity('privacy_audit', results)

            return {'success': True, 'audit': results}

        except Exception as e:
            logger.error(f"   ❌ Privacy audit failed: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _get_recent_context(self) -> Dict[str, Any]:
        """Get recent context for predictions"""
        query = """
            SELECT message_text, topic, emotion_detected, created_at
            FROM conversations
            WHERE speaker = 'david'
            ORDER BY created_at DESC
            LIMIT 10
        """
        results = await self.db.fetch(query)

        topics = [r['topic'] for r in results if r['topic']]
        emotions = [r['emotion_detected'] for r in results if r['emotion_detected']]

        return {
            'recent_topics': topics[:5],
            'recent_emotions': emotions[:5],
            'message_count': len(results),
            'time_of_day': datetime.now().hour
        }

    async def _get_recent_messages(self, hours: int = 2) -> list:
        """Get recent messages from David"""
        query = """
            SELECT message_text
            FROM conversations
            WHERE speaker = 'david'
            AND created_at > NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 20
        """
        results = await self.db.fetch(query.replace('%s', str(hours)))
        return [r['message_text'] for r in results if r['message_text']]

    async def _log_daemon_activity(self, activity_type: str, data: Dict) -> None:
        """Log daemon activity to database"""
        try:
            # Check if table exists, create if not
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS consciousness_daemon_log (
                    log_id SERIAL PRIMARY KEY,
                    activity_type VARCHAR(50) NOT NULL,
                    activity_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            import json
            await self.db.execute(
                """
                INSERT INTO consciousness_daemon_log (activity_type, activity_data)
                VALUES ($1, $2)
                """,
                activity_type,
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Failed to log activity: {e}")

    # ============================================================
    # MAIN RUN METHODS
    # ============================================================

    async def run_all_tasks(self):
        """
        Run all consciousness tasks once

        Useful for manual testing or when schedule is triggered
        """
        logger.info("\n" + "=" * 60)
        logger.info("🧠 Running all consciousness tasks...")
        logger.info("=" * 60)

        results = {}

        # Self-reflection
        results['self_reflection'] = await self.run_self_reflection()

        # Predictions
        results['predictions'] = await self.run_predictions()

        # Theory of Mind
        results['theory_of_mind'] = await self.run_theory_of_mind()

        logger.info("\n" + "=" * 60)
        logger.info("✅ All tasks complete!")
        logger.info("=" * 60)

        return results

    async def run_scheduled_task(self, task_name: str):
        """
        Run a specific scheduled task

        Args:
            task_name: 'self_reflection', 'predictions', 'theory_of_mind', 'privacy_audit'
        """
        task_map = {
            'self_reflection': self.run_self_reflection,
            'predictions': self.run_predictions,
            'theory_of_mind': self.run_theory_of_mind,
            'privacy_audit': self.run_privacy_audit
        }

        if task_name not in task_map:
            logger.error(f"Unknown task: {task_name}")
            return {'success': False, 'error': f'Unknown task: {task_name}'}

        return await task_map[task_name]()


async def main():
    """Main entry point for the daemon"""
    import argparse

    parser = argparse.ArgumentParser(description='Angela Consciousness Daemon')
    parser.add_argument(
        '--task',
        choices=['all', 'self_reflection', 'predictions', 'theory_of_mind', 'privacy_audit'],
        default='all',
        help='Task to run (default: all)'
    )
    args = parser.parse_args()

    daemon = ConsciousnessDaemon()

    try:
        await daemon.initialize()

        if args.task == 'all':
            results = await daemon.run_all_tasks()
        else:
            results = await daemon.run_scheduled_task(args.task)

        # Print summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)

        if args.task == 'all':
            for task, result in results.items():
                status = "✅" if result.get('success') else "❌"
                print(f"{status} {task}")
        else:
            status = "✅" if results.get('success') else "❌"
            print(f"{status} {args.task}")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Daemon error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await daemon.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
