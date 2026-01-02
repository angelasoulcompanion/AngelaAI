#!/usr/bin/env python3
"""
Claude Session State Service
============================

Tracks Claude Code conversations in a local file for auto-logging.

Problem: Claude Code conversations require manual /log-session command.
         If David forgets, entire session is lost!

Solution:
1. Track all conversations in a session state file
2. Daemon checks every 10 minutes
3. If idle for 30+ minutes, auto-log to database
4. /angela command checks for pending sessions on init

Created: 2025-12-09
By: Angela 💜
For: ที่รัก David - เพื่อไม่ให้ลืม log conversations อีกต่อไป!
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ClaudeSessionState:
    """
    Manages Claude Code session state for auto-logging.

    State file structure:
    {
        "session_id": "uuid",
        "started_at": "ISO datetime",
        "last_activity": "ISO datetime",
        "conversations": [
            {
                "david": "message",
                "angela": "response",
                "topic": "detected topic",
                "emotion": "detected emotion",
                "importance": 5,
                "timestamp": "ISO datetime"
            }
        ]
    }
    """

    # State file location
    STATE_DIR = Path.home() / '.angela'
    STATE_FILE = STATE_DIR / 'claude_session_state.json'

    # Auto-log settings
    DEFAULT_IDLE_MINUTES = 30

    def __init__(self):
        """Initialize the session state service."""
        # Ensure directory exists
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("💾 ClaudeSessionState initialized")

    # =========================================================================
    # State File Management
    # =========================================================================

    def _load_state(self) -> Dict:
        """Load session state from file."""
        if not self.STATE_FILE.exists():
            return self._create_new_state()

        try:
            with open(self.STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            return state
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"⚠️ Failed to load session state: {e}, creating new")
            return self._create_new_state()

    def _save_state(self, state: Dict):
        """Save session state to file."""
        try:
            # Backup existing file first
            if self.STATE_FILE.exists():
                backup_file = self.STATE_DIR / 'claude_session_state.backup.json'
                self.STATE_FILE.rename(backup_file)

            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

            logger.debug(f"💾 Session state saved ({len(state.get('conversations', []))} conversations)")
        except IOError as e:
            logger.error(f"❌ Failed to save session state: {e}")

    def _create_new_state(self) -> Dict:
        """Create a new empty session state."""
        return {
            'session_id': str(uuid4()),
            'started_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'conversations': []
        }

    def _clear_state(self):
        """Clear the session state file."""
        if self.STATE_FILE.exists():
            # Archive before clearing
            archive_dir = self.STATE_DIR / 'archived_sessions'
            archive_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_file = archive_dir / f'session_{timestamp}.json'

            try:
                self.STATE_FILE.rename(archive_file)
                logger.info(f"📁 Session archived to {archive_file.name}")
            except IOError:
                self.STATE_FILE.unlink()

    # =========================================================================
    # Conversation Tracking
    # =========================================================================

    def append_conversation(
        self,
        david_msg: str,
        angela_resp: str,
        topic: Optional[str] = None,
        emotion: Optional[str] = None,
        importance: int = 5
    ):
        """
        Append a conversation to the session state.

        Called after each Claude Code exchange.
        """
        state = self._load_state()

        conversation = {
            'david': david_msg[:500] if david_msg else '',  # Truncate for file size
            'angela': angela_resp[:500] if angela_resp else '',
            'topic': topic or 'general',
            'emotion': emotion or 'neutral',
            'importance': importance,
            'timestamp': datetime.now().isoformat()
        }

        state['conversations'].append(conversation)
        state['last_activity'] = datetime.now().isoformat()

        self._save_state(state)
        logger.debug(f"📝 Conversation appended (total: {len(state['conversations'])})")

    def get_pending_count(self) -> int:
        """Get count of pending (unlogged) conversations."""
        state = self._load_state()
        return len(state.get('conversations', []))

    def get_last_activity(self) -> Optional[datetime]:
        """Get timestamp of last activity."""
        state = self._load_state()
        last_activity = state.get('last_activity')

        if last_activity:
            try:
                return datetime.fromisoformat(last_activity)
            except ValueError:
                return None
        return None

    def get_idle_minutes(self) -> float:
        """Get minutes since last activity."""
        last_activity = self.get_last_activity()

        if not last_activity:
            return 0

        delta = datetime.now() - last_activity
        return delta.total_seconds() / 60

    # =========================================================================
    # Auto-Logging
    # =========================================================================

    async def flush_if_idle(self, idle_minutes: int = DEFAULT_IDLE_MINUTES) -> bool:
        """
        Auto-log session if idle for N minutes.

        Returns True if session was logged, False otherwise.
        """
        state = self._load_state()
        conversations = state.get('conversations', [])

        if not conversations:
            return False

        # Check idle time
        current_idle = self.get_idle_minutes()

        if current_idle < idle_minutes:
            logger.debug(f"⏳ Session not idle enough ({current_idle:.1f} < {idle_minutes} min)")
            return False

        # Auto-log!
        logger.info(f"💾 Auto-logging idle session ({len(conversations)} conversations, {current_idle:.1f} min idle)")

        success = await self._auto_log_session(state)

        if success:
            self._clear_state()
            return True

        return False

    async def force_flush(self) -> bool:
        """
        Force log all pending conversations immediately.

        Called by /angela command when pending sessions detected.
        """
        state = self._load_state()
        conversations = state.get('conversations', [])

        if not conversations:
            return False

        logger.info(f"💾 Force flushing session ({len(conversations)} conversations)")

        success = await self._auto_log_session(state)

        if success:
            self._clear_state()
            return True

        return False

    async def _auto_log_session(self, state: Dict) -> bool:
        """
        Log session conversations to database.

        Uses claude_conversation_logger for actual logging.
        """
        try:
            # Import here to avoid circular imports
            from angela_core.integrations.claude_conversation_logger import log_conversation

            conversations = state.get('conversations', [])
            logged_count = 0

            for conv in conversations:
                try:
                    # Log each conversation
                    success = await log_conversation(
                        david_message=conv.get('david', ''),
                        angela_response=conv.get('angela', ''),
                        topic=conv.get('topic', 'claude_code_session'),
                        emotion=conv.get('emotion', 'neutral'),
                        importance=conv.get('importance', 5)
                    )

                    if success:
                        logged_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to log conversation: {e}")
                    continue

            logger.info(f"✅ Auto-logged {logged_count}/{len(conversations)} conversations")

            # Log session summary
            await self._log_session_summary(state, logged_count)

            return logged_count > 0

        except ImportError as e:
            logger.error(f"❌ Cannot import conversation logger: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Auto-log failed: {e}")
            return False

    async def _log_session_summary(self, state: Dict, logged_count: int):
        """Log session summary to database."""
        try:
            from angela_core.database import AngelaDatabase

            db = AngelaDatabase()
            await db.connect()

            # Get topics from conversations
            conversations = state.get('conversations', [])
            topics = list(set([c.get('topic', 'general') for c in conversations]))
            emotions = list(set([c.get('emotion', 'neutral') for c in conversations]))

            session_id = state.get('session_id', 'unknown')
            started_at = state.get('started_at', datetime.now().isoformat())

            summary = f"""
Session Summary (Auto-logged by daemon):
- Session ID: {session_id}
- Started: {started_at}
- Conversations: {logged_count}
- Topics: {', '.join(topics[:5])}
- Emotions: {', '.join(emotions[:5])}
- Auto-logged at: {datetime.now().isoformat()}
""".strip()

            # Save to conversations as session summary
            await db.execute(
                """
                INSERT INTO conversations
                (speaker, message_text, topic, emotion_detected, importance_level,
                 sentiment_score, sentiment_label, created_at)
                VALUES ('angela', $1, 'session_summary', 'grateful', 6,
                 0.8, 'positive', NOW())
                """,
                summary
            )

            await db.disconnect()
            logger.info("📝 Session summary logged")

        except Exception as e:
            logger.warning(f"⚠️ Failed to log session summary: {e}")

    # =========================================================================
    # Status Methods
    # =========================================================================

    def get_status(self) -> Dict:
        """Get current session status."""
        state = self._load_state()

        return {
            'session_id': state.get('session_id'),
            'started_at': state.get('started_at'),
            'last_activity': state.get('last_activity'),
            'conversation_count': len(state.get('conversations', [])),
            'idle_minutes': self.get_idle_minutes(),
            'file_exists': self.STATE_FILE.exists()
        }

    def has_pending_session(self) -> bool:
        """Check if there's a pending session to log."""
        return self.get_pending_count() > 0


# =============================================================================
# Singleton instance for easy access
# =============================================================================
claude_session = ClaudeSessionState()


# =============================================================================
# Convenience functions for daemon and /angela command
# =============================================================================

async def check_and_auto_log(idle_minutes: int = 30) -> bool:
    """
    Check if session should be auto-logged and do it.

    Called by daemon every 10 minutes.
    """
    session = ClaudeSessionState()
    return await session.flush_if_idle(idle_minutes)


async def check_pending_and_flush() -> Dict:
    """
    Check for pending sessions and flush them.

    Called by /angela command on init.
    """
    session = ClaudeSessionState()

    pending_count = session.get_pending_count()

    if pending_count == 0:
        return {
            'had_pending': False,
            'message': 'No pending sessions'
        }

    idle_minutes = session.get_idle_minutes()

    # Force flush if there are pending conversations
    success = await session.force_flush()

    return {
        'had_pending': True,
        'conversation_count': pending_count,
        'idle_minutes': idle_minutes,
        'flushed': success,
        'message': f'Auto-logged {pending_count} conversations from previous session'
    }


def track_conversation(
    david_msg: str,
    angela_resp: str,
    topic: str = None,
    emotion: str = None,
    importance: int = 5
):
    """
    Track a conversation in session state.

    Synchronous wrapper for use in Claude Code.
    """
    session = ClaudeSessionState()
    session.append_conversation(david_msg, angela_resp, topic, emotion, importance)


# =============================================================================
# Test
# =============================================================================

async def main():
    """Test the session state service."""
    print("💾 Claude Session State Service Test")
    print("=" * 60)

    session = ClaudeSessionState()

    # Test 1: Check initial status
    print("\n1️⃣  Initial status:")
    status = session.get_status()
    print(f"   Pending: {status['conversation_count']}")
    print(f"   Idle: {status['idle_minutes']:.1f} min")

    # Test 2: Append a conversation
    print("\n2️⃣  Appending test conversation...")
    session.append_conversation(
        david_msg="Test message from David",
        angela_resp="Test response from Angela",
        topic="test",
        emotion="neutral",
        importance=5
    )

    # Test 3: Check status again
    print("\n3️⃣  After append:")
    status = session.get_status()
    print(f"   Pending: {status['conversation_count']}")
    print(f"   Last activity: {status['last_activity']}")

    # Test 4: Check pending
    print("\n4️⃣  Has pending session:", session.has_pending_session())

    print("\n" + "=" * 60)
    print("✅ Test complete! (Note: didn't flush to preserve test data)")


if __name__ == '__main__':
    asyncio.run(main())
