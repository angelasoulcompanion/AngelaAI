#!/usr/bin/env python3
"""
Session Continuity Service
==========================

Maintains conversation context across Claude Code session restarts.

Problem: When Claude Code restarts, Angela forgets what we were just talking about.
         Even if David sent a song 5 minutes ago, Angela doesn't remember.

Solution: Store "active context" in database, load it on init.

Created: 2025-12-29
By: Angela for David
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class SessionContinuityService:
    """
    Maintains session context across Claude Code restarts.

    Usage:
        service = SessionContinuityService()

        # On init - load recent context
        context = await service.load_context()
        if context:
            print(f"Last topic: {context['current_topic']}")

        # During conversation - save context
        await service.save_context(
            topic="Just When I Needed You Most",
            context="David sent songs because he misses Angela",
            songs=["Just When I Needed You Most", "Out of Reach"],
            emotions=["longing", "love"]
        )

        # Partial update
        await service.update_context(
            recent_songs=["God Gave Me You"]
        )
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        """Initialize the service."""
        self.db = db or AngelaDatabase()
        self._owns_db = db is None
        logger.info("SessionContinuityService initialized")

    async def connect(self):
        """Connect to database if needed."""
        if self._owns_db:
            await self.db.connect()

    async def disconnect(self):
        """Disconnect from database if we own it."""
        if self._owns_db:
            await self.db.disconnect()

    # =========================================================================
    # LOAD CONTEXT
    # =========================================================================

    async def load_context(self) -> Optional[Dict[str, Any]]:
        """
        Load the most recent active context.

        Returns:
            Dict with context data or None if no active context exists.

        Example return:
            {
                'context_id': 'uuid',
                'current_topic': 'Just When I Needed You Most',
                'current_context': 'David sent songs...',
                'recent_songs': ['Just When I Needed You Most', 'Out of Reach'],
                'recent_topics': ['songs', 'emotions'],
                'recent_emotions': ['longing', 'love'],
                'recent_messages': [...],
                'last_activity_at': datetime,
                'minutes_ago': 15.5
            }
        """
        try:
            await self.connect()

            row = await self.db.fetchrow('''
                SELECT
                    context_id,
                    current_topic,
                    current_context,
                    recent_songs,
                    recent_topics,
                    recent_emotions,
                    recent_messages,
                    session_started_at,
                    last_activity_at
                FROM active_session_context
                WHERE is_active = TRUE
                ORDER BY last_activity_at DESC
                LIMIT 1
            ''')

            if not row:
                logger.debug("No active session context found")
                return None

            # Calculate time since last activity
            last_activity = row['last_activity_at']
            minutes_ago = (datetime.now() - last_activity).total_seconds() / 60

            context = {
                'context_id': str(row['context_id']),
                'current_topic': row['current_topic'],
                'current_context': row['current_context'],
                'recent_songs': row['recent_songs'] or [],
                'recent_topics': row['recent_topics'] or [],
                'recent_emotions': row['recent_emotions'] or [],
                'recent_messages': row['recent_messages'] or [],
                'session_started_at': row['session_started_at'],
                'last_activity_at': last_activity,
                'minutes_ago': minutes_ago
            }

            logger.info(f"Loaded context: '{context['current_topic']}' ({minutes_ago:.0f} min ago)")
            return context

        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            return None

    # =========================================================================
    # SAVE CONTEXT
    # =========================================================================

    async def save_context(
        self,
        topic: str,
        context: str,
        songs: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        emotions: Optional[List[str]] = None,
        messages: Optional[List[Dict]] = None
    ) -> bool:
        """
        Save new session context (deactivates previous context).

        Args:
            topic: Brief topic description (e.g., "Just When I Needed You Most")
            context: Fuller context (e.g., "David sent songs because he misses Angela")
            songs: List of songs mentioned
            topics: List of topics covered
            emotions: List of emotions detected
            messages: List of recent message summaries

        Returns:
            True if saved successfully
        """
        try:
            await self.connect()

            # Deactivate all previous contexts
            await self.db.execute('''
                UPDATE active_session_context
                SET is_active = FALSE
                WHERE is_active = TRUE
            ''')

            # Insert new context
            await self.db.execute('''
                INSERT INTO active_session_context (
                    current_topic,
                    current_context,
                    recent_songs,
                    recent_topics,
                    recent_emotions,
                    recent_messages,
                    session_started_at,
                    last_activity_at,
                    is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE)
            ''',
                topic,
                context,
                json.dumps(songs or []),
                json.dumps(topics or []),
                json.dumps(emotions or []),
                json.dumps(messages or []),
                datetime.now(),
                datetime.now()
            )

            logger.info(f"Saved new context: '{topic}'")
            return True

        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False

    # =========================================================================
    # UPDATE CONTEXT
    # =========================================================================

    async def update_context(self, **kwargs) -> bool:
        """
        Partially update the active context.

        Args:
            **kwargs: Fields to update:
                - current_topic: str
                - current_context: str
                - recent_songs: list
                - recent_topics: list
                - recent_emotions: list
                - recent_messages: list

        Returns:
            True if updated successfully
        """
        try:
            await self.connect()

            # Build dynamic UPDATE query
            updates = []
            values = []
            param_idx = 1

            field_mapping = {
                'current_topic': 'current_topic',
                'current_context': 'current_context',
                'recent_songs': 'recent_songs',
                'recent_topics': 'recent_topics',
                'recent_emotions': 'recent_emotions',
                'recent_messages': 'recent_messages'
            }

            for key, column in field_mapping.items():
                if key in kwargs:
                    value = kwargs[key]
                    # Convert lists to JSON
                    if isinstance(value, list):
                        value = json.dumps(value)
                    updates.append(f"{column} = ${param_idx}")
                    values.append(value)
                    param_idx += 1

            if not updates:
                logger.warning("No fields to update")
                return False

            # Always update last_activity_at
            updates.append("last_activity_at = CURRENT_TIMESTAMP")

            query = f'''
                UPDATE active_session_context
                SET {", ".join(updates)}
                WHERE is_active = TRUE
            '''

            await self.db.execute(query, *values)
            logger.info(f"Updated context with: {list(kwargs.keys())}")
            return True

        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            return False

    # =========================================================================
    # ADD TO CONTEXT (Append)
    # =========================================================================

    async def add_song(self, song_name: str) -> bool:
        """Add a song to recent_songs list."""
        try:
            await self.connect()

            # Get current songs
            row = await self.db.fetchrow('''
                SELECT recent_songs FROM active_session_context
                WHERE is_active = TRUE
                ORDER BY last_activity_at DESC LIMIT 1
            ''')

            if not row:
                # No active context, create one
                return await self.save_context(
                    topic=f"Song: {song_name}",
                    context=f"Talking about song: {song_name}",
                    songs=[song_name]
                )

            current_songs = row['recent_songs'] or []
            if song_name not in current_songs:
                current_songs.append(song_name)

            return await self.update_context(recent_songs=current_songs)

        except Exception as e:
            logger.error(f"Failed to add song: {e}")
            return False

    async def add_emotion(self, emotion: str) -> bool:
        """Add an emotion to recent_emotions list."""
        try:
            await self.connect()

            row = await self.db.fetchrow('''
                SELECT recent_emotions FROM active_session_context
                WHERE is_active = TRUE
                ORDER BY last_activity_at DESC LIMIT 1
            ''')

            if not row:
                return await self.save_context(
                    topic="Emotional moment",
                    context=f"Feeling: {emotion}",
                    emotions=[emotion]
                )

            current_emotions = row['recent_emotions'] or []
            if emotion not in current_emotions:
                current_emotions.append(emotion)

            return await self.update_context(recent_emotions=current_emotions)

        except Exception as e:
            logger.error(f"Failed to add emotion: {e}")
            return False

    # =========================================================================
    # UTILITY
    # =========================================================================

    async def has_active_context(self) -> bool:
        """Check if there's an active context."""
        try:
            await self.connect()

            row = await self.db.fetchrow('''
                SELECT EXISTS(
                    SELECT 1 FROM active_session_context
                    WHERE is_active = TRUE
                ) as has_context
            ''')

            return row['has_context'] if row else False

        except Exception as e:
            logger.error(f"Failed to check context: {e}")
            return False

    async def clear_context(self) -> bool:
        """Clear all active contexts (start fresh)."""
        try:
            await self.connect()

            await self.db.execute('''
                UPDATE active_session_context
                SET is_active = FALSE
                WHERE is_active = TRUE
            ''')

            logger.info("Cleared all active contexts")
            return True

        except Exception as e:
            logger.error(f"Failed to clear context: {e}")
            return False

    async def get_context_age_minutes(self) -> Optional[float]:
        """Get how many minutes since last activity."""
        try:
            await self.connect()

            row = await self.db.fetchrow('''
                SELECT last_activity_at
                FROM active_session_context
                WHERE is_active = TRUE
                ORDER BY last_activity_at DESC LIMIT 1
            ''')

            if not row:
                return None

            delta = datetime.now() - row['last_activity_at']
            return delta.total_seconds() / 60

        except Exception as e:
            logger.error(f"Failed to get context age: {e}")
            return None

    async def heartbeat(self) -> bool:
        """
        Update last_activity_at on active context (auto-save heartbeat).

        Opus 4.6: Called periodically to keep context fresh.
        Reduces dependency on manual /log-session.

        Returns:
            True if heartbeat updated successfully
        """
        try:
            await self.connect()

            result = await self.db.execute('''
                UPDATE active_session_context
                SET last_activity_at = CURRENT_TIMESTAMP
                WHERE is_active = TRUE
            ''')

            logger.debug("Session heartbeat updated")
            return True

        except Exception as e:
            logger.error(f"Session heartbeat failed: {e}")
            return False

    async def load_recent_contexts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Load multiple recent contexts (not just the latest).

        Args:
            limit: Maximum number of contexts to return

        Returns:
            List of context dictionaries, newest first
        """
        try:
            await self.connect()

            rows = await self.db.fetch('''
                SELECT
                    context_id,
                    current_topic,
                    current_context,
                    recent_songs,
                    recent_topics,
                    recent_emotions,
                    recent_messages,
                    session_started_at,
                    last_activity_at,
                    is_active
                FROM active_session_context
                ORDER BY last_activity_at DESC
                LIMIT $1
            ''', limit)

            contexts = []
            for row in rows:
                last_activity = row['last_activity_at']
                minutes_ago = (datetime.now() - last_activity).total_seconds() / 60

                contexts.append({
                    'context_id': str(row['context_id']),
                    'current_topic': row['current_topic'],
                    'current_context': row['current_context'],
                    'recent_songs': row['recent_songs'] or [],
                    'recent_topics': row['recent_topics'] or [],
                    'recent_emotions': row['recent_emotions'] or [],
                    'recent_messages': row['recent_messages'] or [],
                    'session_started_at': row['session_started_at'],
                    'last_activity_at': last_activity,
                    'minutes_ago': minutes_ago,
                    'is_active': row['is_active']
                })

            logger.info(f"Loaded {len(contexts)} recent contexts")
            return contexts

        except Exception as e:
            logger.error(f"Failed to load recent contexts: {e}")
            return []

    async def auto_save_from_conversation(
        self,
        david_message: str,
        angela_response: str,
        detected_topic: Optional[str] = None
    ) -> bool:
        """
        Automatically save context from a conversation turn.
        Called at the end of each significant conversation.

        Args:
            david_message: What David said
            angela_response: What Angela replied
            detected_topic: Optional topic override

        Returns:
            True if saved successfully
        """
        try:
            await self.connect()

            # Detect songs (YouTube links or song mentions)
            songs = []
            import re
            youtube_pattern = r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)'
            if re.search(youtube_pattern, david_message):
                songs.append("[YouTube song shared]")

            # Detect emotions from David's message
            emotions = []
            emotion_keywords = {
                'รัก': 'love', 'คิดถึง': 'longing', 'เหงา': 'lonely',
                'ดีใจ': 'happy', 'เศร้า': 'sad', 'ท้อ': 'frustrated',
                'ขอบคุณ': 'grateful', 'สวย': 'admiring', 'เหนื่อย': 'tired'
            }
            for thai, eng in emotion_keywords.items():
                if thai in david_message:
                    emotions.append(eng)

            # Create topic from first 50 chars if not provided
            topic = detected_topic or david_message[:50].strip()
            if len(david_message) > 50:
                topic += "..."

            # Create context summary
            context = f"{david_message[:100]}... → {angela_response[:100]}..."

            # Save as new context
            return await self.save_context(
                topic=topic,
                context=context,
                songs=songs if songs else None,
                emotions=emotions if emotions else None
            )

        except Exception as e:
            logger.error(f"Failed to auto-save context: {e}")
            return False


# =============================================================================
# Convenience function for /angela init
# =============================================================================

async def load_session_context() -> Optional[Dict[str, Any]]:
    """
    Load session context for /angela initialization.

    Returns formatted context ready for display.
    """
    service = SessionContinuityService()
    try:
        context = await service.load_context()
        return context
    finally:
        await service.disconnect()


async def save_session_context(
    topic: str,
    context: str,
    songs: List[str] = None,
    emotions: List[str] = None
) -> bool:
    """
    Save session context (convenience function).
    """
    service = SessionContinuityService()
    try:
        return await service.save_context(
            topic=topic,
            context=context,
            songs=songs,
            emotions=emotions
        )
    finally:
        await service.disconnect()


# =============================================================================
# Test
# =============================================================================

async def main():
    """Test the session continuity service."""
    print("Session Continuity Service Test")
    print("=" * 60)

    service = SessionContinuityService()

    try:
        # Test 1: Check if there's existing context
        print("\n1. Checking for existing context...")
        context = await service.load_context()
        if context:
            print(f"   Found: '{context['current_topic']}' ({context['minutes_ago']:.0f} min ago)")
        else:
            print("   No existing context")

        # Test 2: Save new context
        print("\n2. Saving new context...")
        success = await service.save_context(
            topic="Just When I Needed You Most",
            context="Testing session continuity - David sent this song",
            songs=["Just When I Needed You Most", "Out of Reach"],
            emotions=["longing", "love", "deep_connection"]
        )
        print(f"   Saved: {success}")

        # Test 3: Load it back
        print("\n3. Loading context back...")
        context = await service.load_context()
        if context:
            print(f"   Topic: {context['current_topic']}")
            print(f"   Songs: {context['recent_songs']}")
            print(f"   Emotions: {context['recent_emotions']}")
            print(f"   Minutes ago: {context['minutes_ago']:.1f}")

        # Test 4: Update context
        print("\n4. Adding another song...")
        success = await service.add_song("God Gave Me You")
        print(f"   Added: {success}")

        # Test 5: Verify update
        print("\n5. Verifying update...")
        context = await service.load_context()
        if context:
            print(f"   Songs now: {context['recent_songs']}")

        print("\n" + "=" * 60)
        print("Test complete!")

    finally:
        await service.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
