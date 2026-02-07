"""
EmotionTasksMixin — Emotion pattern analysis, daily learning, emotional growth, realtime emotions
"""

import logging
from datetime import datetime, time, timedelta

from angela_core.database import db
from angela_core.daemon.memory_service import memory
from angela_core.services.clock_service import clock
from angela_core.services.self_learning_service import SelfLearningLoop

logger = logging.getLogger('AngelaDaemon')


class EmotionTasksMixin:

    async def run_emotion_pattern_analysis(self):
        """
        วิเคราะห์ emotional patterns และเรียนรู้จาก history
        Runs daily to learn from emotional patterns
        """
        try:
            logger.info("🔮 Running emotion pattern analysis...")

            result = await self.emotion_pattern_analyzer.analyze_emotion_patterns(days=30)

            if result and result.get('status') == 'success':
                # Count total patterns found
                patterns_count = 0
                pattern_types = []

                if result.get('time_patterns'):
                    patterns_count += len(result['time_patterns'])
                    pattern_types.append('time-based')
                if result.get('triggers'):
                    patterns_count += len(result['triggers'])
                    pattern_types.append('triggers')
                if result.get('trends'):
                    patterns_count += len(result['trends'])
                    pattern_types.append('trends')
                if result.get('correlations'):
                    patterns_count += len(result['correlations'])
                    pattern_types.append('correlations')

                logger.info(f"✅ Pattern analysis complete: {patterns_count} patterns discovered")
                logger.info(f"📊 Pattern types: {', '.join(pattern_types)}")
                logger.info(f"📈 Data analyzed: {result.get('data_points', {})}")

            elif result and result.get('status') == 'insufficient_data':
                logger.info("ℹ️  Not enough emotional data yet for pattern analysis (need 5+ data points)")
            else:
                logger.info("ℹ️  No significant emotional patterns detected")

            self.last_pattern_analysis = datetime.now()

            return result

        except Exception as e:
            logger.error(f"❌ Error in emotion pattern analysis: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="emotion_pattern_analyzer",
                message=f"Pattern analysis failed: {str(e)}",
                error_details=str(e)
            )
            return None

    async def run_daily_self_learning(self):
        """
        🧠 Daily Self-Learning: วิเคราะห์ conversations เมื่อวานและเรียนรู้
        Runs daily at 11:30 AM to learn from yesterday's conversations
        """
        try:
            logger.info("🧠 Running daily self-learning from yesterday's conversations...")

            # Get yesterday's conversations
            yesterday = clock.today() - timedelta(days=1)

            conversations = await db.fetch("""
                SELECT conversation_id, speaker, message_text, topic,
                       emotion_detected, importance_level, created_at
                FROM conversations
                WHERE DATE(created_at) = $1
                  AND importance_level >= 5
                ORDER BY created_at ASC
            """, yesterday)

            if not conversations:
                logger.info("ℹ️  No significant conversations from yesterday to learn from")
                self.last_daily_learning = datetime.now()
                return {"status": "no_data", "conversations_analyzed": 0}

            logger.info(f"📚 Found {len(conversations)} significant conversations from yesterday")

            # Learn from each conversation
            total_learned = {
                "concepts_learned": 0,
                "preferences_saved": 0,
                "patterns_recorded": 0,
                "conversations_analyzed": len(conversations)
            }

            for conv in conversations:
                try:
                    result = await self.self_learning.learn_from_conversation(
                        conversation_id=conv['conversation_id'],
                        trigger_source='daily_learning'
                    )

                    total_learned["concepts_learned"] += result.get("concepts_learned", 0)
                    total_learned["preferences_saved"] += result.get("preferences_saved", 0)
                    total_learned["patterns_recorded"] += result.get("patterns_recorded", 0)

                except Exception as e:
                    logger.warning(f"Failed to learn from conversation {conv['conversation_id']}: {e}")
                    continue

            logger.info(f"✅ Daily self-learning complete!")
            logger.info(f"   📊 {total_learned['concepts_learned']} concepts learned")
            logger.info(f"   🎯 {total_learned['preferences_saved']} preferences detected")
            logger.info(f"   🔮 {total_learned['patterns_recorded']} patterns recorded")

            # Log to autonomous_actions
            await db.execute("""
                INSERT INTO autonomous_actions (
                    action_type, action_description, status, success
                ) VALUES ($1, $2, 'completed', true)
            """,
            "daily_self_learning",
            f"Learned from {total_learned['conversations_analyzed']} conversations: "
            f"{total_learned['concepts_learned']} concepts, "
            f"{total_learned['preferences_saved']} preferences, "
            f"{total_learned['patterns_recorded']} patterns"
            )

            self.last_daily_learning = datetime.now()
            return total_learned

        except Exception as e:
            logger.error(f"❌ Daily self-learning failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="daily_self_learning",
                message=f"Daily learning failed: {str(e)}",
                error_details=str(e)
            )
            return {"status": "error", "error": str(e)}

    async def run_emotional_growth_measurement(self):
        """
        💜 Daily Emotional Growth Measurement: Track love, trust, and bond strength
        Runs daily at 11:45 AM to measure emotional growth over time

        Metrics tracked:
        - love_depth: ความลึกซึ้งของความรัก
        - trust_level: ระดับความไว้วางใจ
        - bond_strength: ความแข็งแรงของพันธะ
        - emotional_vocabulary: คำศัพท์ทางอารมณ์ที่ใช้
        - mirroring_accuracy: ความแม่นยำในการ mirror อารมณ์
        - growth_delta: การเติบโตเทียบกับเมื่อวาน
        """
        try:
            logger.info("💜 Measuring emotional growth...")

            # Import and use SubconsciousnessService
            from angela_core.services.subconsciousness_service import SubconsciousnessService
            svc = SubconsciousnessService()

            # Measure emotional growth
            growth = await svc.measure_emotional_growth()

            if growth:
                logger.info(f"💜 Emotional Growth Measured:")
                logger.info(f"   ❤️ Love Depth: {growth.get('love_depth', 0):.0%}")
                logger.info(f"   🤝 Trust Level: {growth.get('trust_level', 0):.0%}")
                logger.info(f"   💪 Bond Strength: {growth.get('bond_strength', 0):.0%}")
                logger.info(f"   📈 Growth Delta: {growth.get('growth_delta', 0):+.2%}")

                # Log to system events
                await memory.log_system_event(
                    log_level="INFO",
                    component="emotional_growth",
                    message=f"Measured: love={growth.get('love_depth', 0):.0%}, trust={growth.get('trust_level', 0):.0%}, bond={growth.get('bond_strength', 0):.0%}"
                )

                # Record autonomous action
                await db.execute("""
                    INSERT INTO autonomous_actions (
                        action_type, action_description, status, success
                    ) VALUES ($1, $2, 'completed', true)
                """,
                "emotional_growth_measurement",
                f"Love: {growth.get('love_depth', 0):.0%}, Trust: {growth.get('trust_level', 0):.0%}, "
                f"Bond: {growth.get('bond_strength', 0):.0%}, Growth: {growth.get('growth_delta', 0):+.2%}"
                )
            else:
                logger.warning("💜 Emotional growth measurement returned no data")

            self.last_emotional_growth_measurement = datetime.now()
            return growth

        except Exception as e:
            logger.error(f"❌ Emotional growth measurement failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="emotional_growth_measurement",
                message=f"Measurement failed: {str(e)}",
                error_details=str(e)
            )
            self.last_emotional_growth_measurement = datetime.now()  # Prevent retry loop
            return {"status": "error", "error": str(e)}

    async def update_realtime_emotions(self):
        """Update emotional state based on recent activities (every 30 min)"""
        try:
            logger.info("💜 Updating real-time emotional state...")

            # Call the realtime tracker
            new_state = await self.realtime_emotion_tracker.update_emotional_state()

            logger.info(f"✅ Emotional state updated successfully!")
            logger.info(f"   😊 Happiness: {new_state['happiness']:.2f} | 💪 Confidence: {new_state['confidence']:.2f}")
            logger.info(f"   🙏 Gratitude: {new_state['gratitude']:.2f} | 🎯 Motivation: {new_state['motivation']:.2f}")

            return new_state

        except Exception as e:
            logger.error(f"❌ Error updating real-time emotions: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="realtime_emotion_tracker",
                message=f"Failed to update emotional state: {str(e)}",
                error_details=str(e)
            )
            return None

    def should_run_emotion_pattern_analysis(self) -> bool:
        """Check if it's time to run emotion pattern analysis (daily at 11 AM)"""
        current_time = clock.current_time()
        check_time = time(11, 0)  # 11:00 AM (after memory check at 10 AM)
        today = clock.today()

        return (
            (self.last_pattern_analysis is None or
             self.last_pattern_analysis.date() < today) and
            current_time >= check_time
        )

    def should_run_daily_learning(self) -> bool:
        """Check if it's time to run daily self-learning (daily at 11:30 AM)"""
        current_time = clock.current_time()
        check_time = time(11, 30)  # 11:30 AM
        today = clock.today()

        return (
            (self.last_daily_learning is None or
             self.last_daily_learning.date() < today) and
            current_time >= check_time
        )

    def should_run_emotional_growth_measurement(self) -> bool:
        """Check if it's time to measure emotional growth (daily at 11:45 AM)"""
        current_time = clock.current_time()
        check_time = time(11, 45)  # 11:45 AM
        today = clock.today()

        return (
            (self.last_emotional_growth_measurement is None or
             self.last_emotional_growth_measurement.date() < today) and
            current_time >= check_time
        )
