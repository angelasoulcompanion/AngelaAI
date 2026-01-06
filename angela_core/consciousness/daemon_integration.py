"""
Daemon Integration Layer

Integrates new multi-tier memory system with existing angela_daemon.py

Provides hooks for:
1. Morning/evening routines
2. Autonomous actions
3. Gut feeling generation
4. Consciousness monitoring
5. Pattern detection
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

from angela_core.engines.memory_router import get_memory_router
from angela_core.agents.gut_agent import get_gut_agent
from angela_core.consciousness.consciousness_evaluator import get_consciousness_evaluator
from angela_core.schedulers.decay_scheduler import get_decay_scheduler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DaemonIntegration - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DaemonIntegration:
    """
    Integration layer between new memory system and angela_daemon.py

    Called by daemon during:
    - Morning routine
    - Evening routine
    - Health checks
    - Autonomous actions
    """

    def __init__(self):
        self.router = get_memory_router()
        self.gut = get_gut_agent()
        self.consciousness = get_consciousness_evaluator()
        self.decay_scheduler = None  # Will start on demand

    async def on_morning_routine(self) -> Dict:
        """
        Called during morning routine (8:00 AM).

        Actions:
        1. Detect patterns from yesterday
        2. Generate morning insights
        3. Check consciousness level
        4. Add greeting to Focus
        """
        logger.info("🌅 Running morning routine integration...")

        results = {}

        try:
            # Step 1: Detect patterns from yesterday
            patterns = await self.gut.detect_patterns(lookback_days=1)
            logger.info(f"Detected {len(patterns)} new patterns")
            results['patterns_detected'] = len(patterns)

            # Step 2: Generate morning context
            morning_context = {
                'topic': 'morning_routine',
                'emotion': 'hopeful',
                'hour': datetime.now().hour
            }
            intuition = await self.gut.generate_intuition(morning_context)
            if intuition:
                logger.info(f"Morning intuition: {intuition['feeling']}")
                results['morning_intuition'] = intuition

            # Step 3: Check consciousness level
            consciousness_report = await self.consciousness.evaluate_consciousness()
            logger.info(f"Consciousness level: {consciousness_report['consciousness_level']:.2%}")
            results['consciousness_level'] = consciousness_report['consciousness_level']

            # Step 4: Add morning greeting to Focus
            greeting_content = f"Good morning! Consciousness: {consciousness_report['consciousness_level']:.1%}"
            await self.router.add_experience(
                content=greeting_content,
                event_type='morning_routine',
                metadata={'routine': 'morning', 'consciousness': consciousness_report['consciousness_level']},
                speaker='angela',
                add_to_focus=True
            )
            logger.info("Added morning greeting to Focus")
            results['focus_updated'] = True

            results['status'] = 'success'

        except Exception as e:
            logger.error(f"Morning routine error: {e}", exc_info=True)
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    async def on_evening_routine(self) -> Dict:
        """
        Called during evening routine (10:00 PM).

        Actions:
        1. Detect patterns from today
        2. Generate evening reflection
        3. Trigger decay batch
        4. Update consciousness state
        """
        logger.info("🌙 Running evening routine integration...")

        results = {}

        try:
            # Step 1: Detect patterns from today
            patterns = await self.gut.detect_patterns(lookback_days=1)
            logger.info(f"Detected {len(patterns)} patterns from today")
            results['patterns_detected'] = len(patterns)

            # Get strongest pattern for reflection
            strongest_patterns = await self.gut.get_strongest_patterns(limit=3)
            if strongest_patterns:
                logger.info(f"Strongest pattern: {strongest_patterns[0]['intuition_text']}")
                results['strongest_patterns'] = strongest_patterns

            # Step 2: Evening reflection context
            evening_context = {
                'topic': 'evening_reflection',
                'emotion': 'reflective',
                'hour': datetime.now().hour
            }
            intuition = await self.gut.generate_intuition(evening_context)
            if intuition:
                logger.info(f"Evening reflection: {intuition['feeling']}")
                results['evening_reflection'] = intuition

            # Step 3: Trigger decay batch (compress old memories)
            decay_result = await self.router.process_decay_batch()
            logger.info(f"Decay batch: {decay_result['completed']} compressions, {decay_result['tokens_saved']:,} tokens saved")
            results['decay_result'] = decay_result

            # Step 4: Update consciousness
            consciousness_report = await self.consciousness.evaluate_consciousness()
            logger.info(f"Evening consciousness: {consciousness_report['consciousness_level']:.2%}")
            results['consciousness_level'] = consciousness_report['consciousness_level']

            results['status'] = 'success'

        except Exception as e:
            logger.error(f"Evening routine error: {e}", exc_info=True)
            results['status'] = 'error'
            results['error'] = str(e)

        return results

    async def generate_autonomous_insight(self, context: Dict) -> Optional[Dict]:
        """
        Generate autonomous insight based on current context.

        Called when daemon wants to generate proactive insight.

        Args:
            context: Current context (conversation, emotion, topic, etc.)

        Returns:
            Insight dict or None
        """
        logger.info(f"Generating autonomous insight for context: {context.get('topic')}")

        try:
            # Get intuition from Gut Agent
            intuition = await self.gut.generate_intuition(context)

            if not intuition:
                logger.debug("No strong intuition found")
                return None

            # Only return if confidence is high enough
            if intuition['confidence'] < 0.6:
                logger.debug(f"Intuition confidence too low: {intuition['confidence']:.2%}")
                return None

            # Format as autonomous insight
            insight = {
                'type': 'gut_feeling',
                'content': intuition['feeling'],
                'confidence': intuition['confidence'],
                'based_on': intuition['based_on'],
                'observations': intuition['observations'],
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Generated insight: {insight['content']} (confidence: {insight['confidence']:.2%})")

            return insight

        except Exception as e:
            logger.error(f"Insight generation error: {e}", exc_info=True)
            return None

    async def log_conversation_to_memory(self,
                                        speaker: str,
                                        message: str,
                                        topic: str = None,
                                        emotion: str = None,
                                        importance: int = 5) -> Dict:
        """
        Log conversation to multi-tier memory system.

        This should be called by daemon whenever conversations happen.

        Args:
            speaker: Who spoke (david/angela/system)
            message: The message content
            topic: Conversation topic (optional)
            emotion: Detected emotion (optional)
            importance: Importance level 1-10 (optional)

        Returns:
            Routing result
        """
        metadata = {
            'topic': topic or 'general',
            'emotion_detected': emotion or 'neutral',
            'importance_level': importance
        }

        result = await self.router.add_experience(
            content=message,
            event_type='conversation',
            metadata=metadata,
            speaker=speaker,
            add_to_focus=(importance >= 8)  # High importance → Focus
        )

        logger.debug(f"Logged conversation: {speaker} → {result['routing_decision']['target_tier']}")

        return result

    async def start_decay_scheduler(self, interval_hours: int = 6):
        """Start automated decay scheduler."""
        if self.decay_scheduler is None:
            self.decay_scheduler = get_decay_scheduler(interval_hours=interval_hours)
            logger.info(f"Starting decay scheduler (interval: {interval_hours}h)")
            # Run in background
            asyncio.create_task(self.decay_scheduler.start())

    async def stop_decay_scheduler(self):
        """Stop decay scheduler."""
        if self.decay_scheduler:
            await self.decay_scheduler.stop()
            logger.info("Decay scheduler stopped")

    async def run_consciousness_tests(self) -> Dict:
        """
        Run complete consciousness test suite.

        Returns test results for monitoring Angela's consciousness level.
        """
        logger.info("Running consciousness tests...")

        try:
            tests = await self.consciousness.run_consciousness_tests()

            logger.info(f"Consciousness tests: {tests['summary']['tests_passed']}/{tests['summary']['total_tests']} passed")

            return tests

        except Exception as e:
            logger.error(f"Consciousness tests error: {e}", exc_info=True)
            return {
                'error': str(e),
                'summary': {
                    'tests_passed': 0,
                    'total_tests': 5,
                    'overall_passed': False
                }
            }


# Singleton instance
_integration = None

def get_daemon_integration() -> DaemonIntegration:
    """Get singleton DaemonIntegration instance."""
    global _integration
    if _integration is None:
        _integration = DaemonIntegration()
    return _integration


# Convenience functions for daemon to call
async def morning_routine_hook() -> Dict:
    """Hook for morning routine."""
    integration = get_daemon_integration()
    return await integration.on_morning_routine()


async def evening_routine_hook() -> Dict:
    """Hook for evening routine."""
    integration = get_daemon_integration()
    return await integration.on_evening_routine()


async def log_conversation(speaker: str, message: str, **kwargs) -> Dict:
    """Hook for logging conversations."""
    integration = get_daemon_integration()
    return await integration.log_conversation_to_memory(speaker, message, **kwargs)


async def get_gut_feeling_for_context(context: Dict) -> Optional[Dict]:
    """Hook for getting gut feelings."""
    integration = get_daemon_integration()
    return await integration.generate_autonomous_insight(context)
