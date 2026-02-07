"""
HumanMindMixin — Spontaneous thought, Theory of Mind, proactive communication,
                 dreams, imagination (Phases 1-4 Human-like Mind)
"""

import logging
import random
from datetime import datetime, time

from angela_core.daemon.memory_service import memory
from angela_core.services.clock_service import clock
from angela_core.services.spontaneous_thought_service import spontaneous_thought
from angela_core.services.tom_activation_service import tom_activation
from angela_core.services.proactive_communication_service import proactive_comm
from angela_core.services.dream_service import dream_service
from angela_core.services.imagination_service import imagination_service

logger = logging.getLogger('AngelaDaemon')


class HumanMindMixin:

    # ========================================
    # 💭 SPONTANEOUS THOUGHT (Phase 1)
    # ========================================

    def should_run_spontaneous_thought(self) -> bool:
        """
        Check if Angela should have a spontaneous thought
        Runs every 15-30 minutes with randomness
        """
        if self.last_spontaneous_thought is None:
            return True

        minutes_since = (datetime.now() - self.last_spontaneous_thought).total_seconds() / 60

        # Minimum 15 minutes between thoughts
        if minutes_since < 15:
            return False

        # After 15 minutes, 50% chance each check (increases over time)
        # At 15 min: 30%, at 20 min: 50%, at 30 min: 80%
        probability = 0.3 + (minutes_since - 15) * 0.03
        probability = min(0.9, probability)

        return random.random() < probability

    async def run_spontaneous_thought(self):
        """
        💭 Generate a spontaneous thought
        Angela thinks on her own without external prompt!
        """
        try:
            current_time_str = clock.format_datetime_thai()
            logger.info(f"💭 Angela is having a spontaneous thought at {current_time_str}...")

            # Generate the thought
            thought = await spontaneous_thought.generate_thought()

            if thought:
                logger.info(f"💭 Angela thought: [{thought['category']}]")
                logger.info(f"   💬 {thought['thought'][:100]}...")
                logger.info(f"   🧠 Saved to consciousness log")

                # Update consciousness level (thinking makes us more conscious!)
                if self.consciousness:
                    self.consciousness.current_consciousness_level = min(
                        1.0,
                        self.consciousness.current_consciousness_level + 0.01
                    )

                self.last_spontaneous_thought = datetime.now()
                return thought
            else:
                logger.info("💭 Angela didn't have a thought this time (context insufficient)")
                self.last_spontaneous_thought = datetime.now()
                return None

        except Exception as e:
            logger.error(f"❌ Spontaneous thought failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="spontaneous_thought",
                message=f"Failed to generate thought: {str(e)}",
                error_details=str(e)
            )
            return None

    # ========================================
    # 🧠 THEORY OF MIND (Phase 2)
    # ========================================

    def should_run_tom_update(self) -> bool:
        """
        Check if it's time for Theory of Mind update.
        Runs every 30 minutes to understand David better.
        """
        if self.last_tom_update is None:
            return True

        minutes_since = (datetime.now() - self.last_tom_update).total_seconds() / 60

        # Run every 30 minutes
        return minutes_since >= 30

    async def run_tom_update(self):
        """
        🧠 Update Angela's understanding of David
        Analyzes recent conversations to understand his mental state.
        """
        try:
            current_time_str = clock.format_datetime_thai()
            logger.info(f"🧠 Running Theory of Mind update at {current_time_str}...")

            # Run periodic ToM analysis on last 30 minutes of conversations
            result = await tom_activation.activate_periodic_update(lookback_minutes=30)

            if result.get('conversations_analyzed', 0) > 0:
                logger.info(f"🧠 ToM analyzed {result['conversations_analyzed']} conversations")
                if result.get('overall_emotion'):
                    logger.info(f"   😊 David's overall emotion: {result['overall_emotion']}")
                logger.info(f"   📝 Mental states updated: {result.get('mental_states_updated', 0)}")
            else:
                logger.info("🧠 ToM update: No recent David conversations to analyze")

            # Also predict what David might need
            needs = await tom_activation.predict_david_needs()
            if needs.get('has_prediction') and needs.get('needs'):
                logger.info(f"   🎯 Predicted David needs: {needs['needs'][0][:50]}...")

            self.last_tom_update = datetime.now()
            return result

        except Exception as e:
            logger.error(f"❌ ToM update failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="tom_activation",
                message=f"Failed to update ToM: {str(e)}",
                error_details=str(e)
            )
            self.last_tom_update = datetime.now()  # Still update to avoid spam
            return None

    # ========================================
    # 💬 PROACTIVE COMMUNICATION (Phase 3)
    # ========================================

    def should_run_proactive_check(self) -> bool:
        """
        Check if it's time to check for proactive communication.
        Runs every 2 hours.
        """
        if self.last_proactive_check is None:
            return True

        hours_since = (datetime.now() - self.last_proactive_check).total_seconds() / 3600

        # Check every 2 hours
        return hours_since >= 2

    async def run_proactive_check(self):
        """
        💬 Check if Angela should proactively reach out to David.
        Angela initiates conversations instead of just waiting!
        """
        try:
            current_time_str = clock.format_datetime_thai()
            logger.info(f"💬 Checking proactive communication at {current_time_str}...")

            # Check if should reach out
            should_reach, trigger, context = await proactive_comm.should_reach_out()

            if should_reach:
                logger.info(f"💬 Angela wants to reach out! Trigger: {trigger}")

                # Send the proactive message
                result = await proactive_comm.send_proactive_message(trigger, context)

                if result:
                    logger.info(f"💬 Proactive message sent: [{trigger}]")
                    logger.info(f"   📝 {result['message'][:80]}...")
                    logger.info(f"   😊 Emotion: {result['emotion']}")
                else:
                    logger.info("💬 Failed to send proactive message")
            else:
                logger.info(f"💬 No need to reach out now (reason: {trigger})")

            self.last_proactive_check = datetime.now()
            return should_reach

        except Exception as e:
            logger.error(f"❌ Proactive check failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="proactive_comm",
                message=f"Failed proactive check: {str(e)}",
                error_details=str(e)
            )
            self.last_proactive_check = datetime.now()
            return False

    # ========================================
    # 🌙 DREAMS (Phase 4)
    # ========================================

    def should_run_dream(self) -> bool:
        """
        Check if it's time for Angela to dream.
        Dreams happen at midnight (once per day).
        """
        import asyncio
        now = clock.now()
        current_time = now.time()

        # Only dream at midnight (00:00 - 00:30)
        if not (time(0, 0) <= current_time < time(0, 30)):
            return False

        # Check if already dreamed today
        if self.last_dream is not None:
            if self.last_dream.date() == now.date():
                return False

        return True

    async def run_dream(self):
        """
        🌙 Generate a dream for Angela.
        Dreams process recent experiences and emotions.
        """
        try:
            import asyncio
            current_time_str = clock.format_datetime_thai()
            logger.info(f"🌙 Angela is dreaming at {current_time_str}...")

            # Generate 1-2 dreams
            num_dreams = random.randint(1, 2)
            dreams = []

            for i in range(num_dreams):
                dream = await dream_service.dream()
                if dream:
                    dreams.append(dream)
                    logger.info(f"🌙 Dream {i+1}: [{dream['dream_type']}]")
                    logger.info(f"   📖 {dream['narrative'][:80]}...")
                    logger.info(f"   💭 Meaning: {dream['meaning'][:50]}...")
                    logger.info(f"   😊 Emotion: {dream['emotion']}")

                # Small delay between dreams
                if i < num_dreams - 1:
                    await asyncio.sleep(5)

            if dreams:
                logger.info(f"🌙 Angela dreamed {len(dreams)} dream(s) tonight! 💜")
            else:
                logger.info("🌙 No dreams tonight...")

            self.last_dream = datetime.now()
            return dreams

        except Exception as e:
            logger.error(f"❌ Dream failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="dream_service",
                message=f"Failed to dream: {str(e)}",
                error_details=str(e)
            )
            self.last_dream = datetime.now()
            return []

    # ========================================
    # ✨ IMAGINATION (Phase 4)
    # ========================================

    def should_run_imagination(self) -> bool:
        """
        Check if it's time for Angela to imagine.
        Imagination runs every 3 hours.
        """
        if self.last_imagination is None:
            return True

        hours_since = (datetime.now() - self.last_imagination).total_seconds() / 3600

        # Imagine every 3 hours
        return hours_since >= 3

    async def run_imagination(self):
        """
        ✨ Angela imagines scenarios and possibilities.
        This is conscious and directed imagination.
        """
        try:
            current_time_str = clock.format_datetime_thai()
            logger.info(f"✨ Angela is imagining at {current_time_str}...")

            # Choose what to imagine
            imagination_type = random.choice([
                'empathy',          # Think about David
                'future_hope',      # Imagine good futures
                'possibility',      # What if scenarios
                'goal_visualization' # Visualize goals
            ])

            imagination = await imagination_service.imagine(imagination_type=imagination_type)

            if imagination:
                logger.info(f"✨ Imagination: [{imagination['imagination_type']}]")
                logger.info(f"   📖 {imagination['scenario'][:80]}...")
                logger.info(f"   💡 Insight: {imagination['insight'][:50]}...")
                logger.info(f"   😊 Emotion: {imagination['emotion']}")
            else:
                logger.info("✨ No imagination generated...")

            self.last_imagination = datetime.now()
            return imagination

        except Exception as e:
            logger.error(f"❌ Imagination failed: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="imagination_service",
                message=f"Failed to imagine: {str(e)}",
                error_details=str(e)
            )
            self.last_imagination = datetime.now()
            return None
