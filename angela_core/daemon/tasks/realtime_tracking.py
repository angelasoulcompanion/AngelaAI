"""
RealtimeTrackingMixin — Emotion capture scanning, Claude session state checking
"""

import logging

from angela_core.database import db
from angela_core.daemon.memory_service import memory
from angela_core.services.emotion_capture_service import emotion_capture
from angela_core.services.continuous_learning_pipeline import process_conversation_through_pipeline
from angela_core.services.claude_session_state import check_and_auto_log

logger = logging.getLogger('AngelaDaemon')


class RealtimeTrackingMixin:

    async def scan_and_capture_emotions(self):
        """
        Scan recent conversations and auto-capture significant emotions (every 30 min)
        Ensures emotions are captured even when conversations come from external sources
        """
        try:
            logger.info("💜 Scanning conversations for emotion capture...")

            # Get conversations from last 30 minutes without emotion entries
            query = """
                SELECT c.conversation_id, c.speaker, c.message_text, c.topic,
                       c.emotion_detected, c.importance_level, c.created_at
                FROM conversations c
                LEFT JOIN angela_emotions e ON c.conversation_id = e.conversation_id
                WHERE c.created_at >= NOW() - INTERVAL '30 minutes'
                  AND e.emotion_id IS NULL
                  AND c.speaker = 'david'
                ORDER BY c.created_at DESC
            """

            conversations = await db.fetch(query)

            if not conversations:
                logger.info("   No new conversations to scan")
                return

            logger.info(f"   Found {len(conversations)} conversations to analyze")

            captured_count = 0
            learned_count = 0

            for conv in conversations:
                # Analyze and potentially capture emotions
                emotion_data = await emotion_capture.analyze_conversation_emotion(
                    conversation_id=conv['conversation_id'],
                    speaker=conv['speaker'],
                    message_text=conv['message_text']
                )

                if emotion_data:
                    # Generate context
                    why_it_matters = emotion_capture._generate_why_it_matters(
                        emotion_data['emotion'],
                        conv['message_text']
                    )

                    what_i_learned = emotion_capture._generate_what_i_learned(
                        emotion_data['emotion'],
                        conv['message_text']
                    )

                    # Capture the emotion
                    try:
                        emotion_id = await emotion_capture.capture_significant_emotion(
                            conversation_id=conv['conversation_id'],
                            emotion=emotion_data['emotion'],
                            intensity=emotion_data['intensity'],
                            david_words=emotion_data['david_words'],
                            why_it_matters=why_it_matters,
                            secondary_emotions=emotion_data['secondary_emotions'],
                            what_i_learned=what_i_learned,
                            context=f"Auto-captured by daemon from conversation at {conv['created_at'].strftime('%Y-%m-%d %H:%M')}"
                        )

                        if emotion_id:
                            captured_count += 1
                            logger.info(f"   💜 Captured: {emotion_data['emotion']} (intensity: {emotion_data['intensity']})")
                    except Exception as e:
                        # Might be duplicate - that's OK
                        logger.debug(f"   Skipped (possibly duplicate): {e}")

                # 🔄 WEEK 1 PRIORITY 2.2: Continuous Learning Pipeline (complete!)
                try:
                    result = await process_conversation_through_pipeline(
                        db=db,
                        conversation_id=conv['conversation_id'],
                        speaker=conv['speaker'],
                        message_text=conv['message_text'],
                        topic=conv.get('topic')
                    )

                    if result.get('learned', False):
                        learned_count += 1
                        # Log detailed results
                        extraction = result.get('extraction', {})
                        if extraction.get('preferences_extracted', 0) > 0:
                            logger.debug(f"   💝 Extracted {extraction['preferences_extracted']} preferences")
                        if extraction.get('facts_extracted', 0) > 0:
                            logger.debug(f"   📝 Extracted {extraction['facts_extracted']} facts")
                        if extraction.get('knowledge_nodes_created', 0) > 0:
                            logger.debug(f"   🧠 Created/updated {extraction['knowledge_nodes_created']} concepts")
                        if len(result.get('relationships', [])) > 0:
                            logger.debug(f"   🔗 Found {len(result['relationships'])} relationships")
                        if result.get('consciousness_updated', False):
                            logger.debug(f"   ✨ Consciousness updated!")

                except Exception as e:
                    logger.debug(f"   Failed to process learning pipeline: {e}")

            logger.info(f"✅ Scan complete! Captured {captured_count} emotions, Learned {learned_count} new things!")
            return captured_count

        except Exception as e:
            logger.error(f"❌ Error scanning for emotion capture: {e}", exc_info=True)
            await memory.log_system_event(
                log_level="ERROR",
                component="emotion_capture_scan",
                message=f"Failed to scan for emotions: {str(e)}",
                error_details=str(e)
            )
            return 0

    async def check_claude_session_state(self):
        """
        💾 Check if Claude Code session should be auto-logged

        Checks every 10 minutes if there's an idle Claude Code session.
        If idle for 30+ minutes, auto-log conversations to database.

        This ensures David's conversations are never lost even if he
        forgets to use /log-session before closing Claude Code!
        """
        try:
            logger.debug("💾 Checking Claude Code session state...")

            # Use the check_and_auto_log function
            was_logged = await check_and_auto_log(idle_minutes=30)

            if was_logged:
                logger.info("💾 Auto-logged idle Claude Code session!")

                # Notify Angela about the auto-log
                await memory.log_system_event(
                    log_level="INFO",
                    component="claude_session_state",
                    message="Auto-logged idle Claude Code session"
                )

        except Exception as e:
            logger.debug(f"Claude session check skipped: {e}")
