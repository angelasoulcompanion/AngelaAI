"""
Consciousness Daemon — Prediction Task Mixin
Pattern predictions, Theory of Mind, companion predictions.

Split from consciousness_daemon.py (Phase 6C refactor)
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger('consciousness_daemon')


class PredictionTasksMixin:
    """Mixin for prediction-related daemon tasks."""

    async def run_predictions(self) -> Dict[str, Any]:
        """
        Run pattern predictions

        คาดเดา patterns ของที่รัก
        """
        logger.info("🔮 Running predictions...")

        try:
            # Get context using PredictionContext factory method
            from angela_core.services.prediction_service import PredictionContext
            context = await PredictionContext.from_database()

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

    async def run_companion_predictions(self) -> Dict[str, Any]:
        """
        Mine patterns + generate/update daily briefing + verify yesterday's.

        คาดการณ์ความต้องการของที่รักจาก historical patterns
        """
        logger.info("📊 Running companion predictions...")

        try:
            # Generate or refresh today's briefing
            briefing = await self.companion_service.generate_daily_briefing()
            logger.info(f"   Predictions: {len(briefing.predictions)} items")
            logger.info(f"   Confidence: {briefing.overall_confidence:.0%}")
            logger.info(f"   Outlook: {briefing.day_outlook[:60]}...")

            # Verify yesterday's predictions
            verification = await self.companion_service.verify_predictions()
            if verification.get('verified'):
                logger.info(f"   Yesterday's accuracy: {verification['accuracy']:.0%}")
            else:
                logger.info(f"   Yesterday: {verification.get('reason', 'N/A')}")

            logger.info("   ✅ Companion predictions complete!")

            await self._log_daemon_activity('companion_predictions', {
                'prediction_count': len(briefing.predictions),
                'overall_confidence': briefing.overall_confidence,
                'yesterday_accuracy': verification.get('accuracy'),
            })

            return {
                'success': True,
                'prediction_count': len(briefing.predictions),
                'confidence': briefing.overall_confidence,
            }

        except Exception as e:
            logger.error(f"   ❌ Companion predictions failed: {e}")
            return {'success': False, 'error': str(e)}
