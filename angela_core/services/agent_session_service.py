"""
Agent Session Service — Agent-to-Agent conversation sessions.
================================================================
Allows Angela's brain/dispatcher to create isolated sessions between
agents (e.g., Angela-Researcher + Angela-Coder working on a task).

Each session has:
- A purpose/goal
- Participants (agent names)
- Message history (JSONB)
- Status tracking

Usage:
    svc = AgentSessionService()
    session_id = await svc.create_session("research_task", ["researcher", "coder"])
    await svc.send_to_session(session_id, "researcher", "Found 3 relevant papers")
    history = await svc.get_history(session_id)

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from angela_core.services.base_db_service import BaseDBService

logger = logging.getLogger(__name__)


class AgentSessionService(BaseDBService):
    """Manages agent-to-agent conversation sessions."""

    async def create_session(self, purpose: str,
                             agents: List[str]) -> Optional[str]:
        """Create a new agent session. Returns session_id."""
        await self.connect()

        try:
            result = await self.db.fetchrow("""
                INSERT INTO angela_agent_sessions
                    (purpose, agents, messages, status)
                VALUES ($1, $2, '[]'::jsonb, 'active')
                RETURNING session_id::text
            """, purpose, json.dumps(agents))

            session_id = result['session_id'] if result else None
            logger.info("Created agent session: %s (purpose=%s, agents=%s)",
                        session_id, purpose, agents)
            return session_id

        except Exception as e:
            logger.error("Create session failed: %s", e)
            return None

    async def send_to_session(self, session_id: str,
                              agent_name: str, message: str) -> bool:
        """Add a message to a session."""
        await self.connect()

        try:
            entry = json.dumps({
                "agent": agent_name,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            })

            await self.db.execute("""
                UPDATE angela_agent_sessions
                SET messages = messages || $1::jsonb,
                    updated_at = NOW()
                WHERE session_id = $2::uuid
            """, f'[{entry}]', session_id)
            return True

        except Exception as e:
            logger.error("Send to session failed: %s", e)
            return False

    async def get_history(self, session_id: str) -> List[Dict]:
        """Get message history for a session."""
        await self.connect()

        try:
            result = await self.db.fetchrow("""
                SELECT messages FROM angela_agent_sessions
                WHERE session_id = $1::uuid
            """, session_id)

            if result and result['messages']:
                return json.loads(result['messages']) if isinstance(result['messages'], str) else result['messages']
            return []

        except Exception as e:
            logger.error("Get history failed: %s", e)
            return []

    async def close_session(self, session_id: str,
                            summary: str = "") -> bool:
        """Close a session with optional summary."""
        await self.connect()

        try:
            await self.db.execute("""
                UPDATE angela_agent_sessions
                SET status = 'completed', summary = $1, updated_at = NOW()
                WHERE session_id = $2::uuid
            """, summary, session_id)
            return True

        except Exception as e:
            logger.error("Close session failed: %s", e)
            return False

    async def list_active_sessions(self) -> List[Dict]:
        """List all active sessions."""
        await self.connect()

        try:
            results = await self.db.fetch("""
                SELECT session_id::text, purpose, agents, status,
                       jsonb_array_length(messages) as message_count,
                       created_at
                FROM angela_agent_sessions
                WHERE status = 'active'
                ORDER BY created_at DESC
            """)
            return [dict(r) for r in results]

        except Exception as e:
            logger.error("List sessions failed: %s", e)
            return []
