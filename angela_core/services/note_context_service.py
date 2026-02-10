"""
Note Context Service

Conversational enrichment from David's Google Keep notes (david_notes table).
When David discusses a topic, Angela can search her notes and naturally reference them.

Respects emotional adaptation:
- Skip when proactivity < 0.3 (focused/frustrated states)
- Otherwise return formatted note references

Created: 2026-02-10
By: น้อง Angela 💜
"""

import logging
from typing import List, Optional

from angela_core.services.enhanced_rag_service import EnhancedRAGService, RetrievedDocument

logger = logging.getLogger(__name__)


class NoteContextService:
    """
    Search david_notes via RAG and return formatted context
    for Angela to naturally reference during conversation.
    """

    def __init__(self):
        self.rag = EnhancedRAGService()

    async def close(self):
        await self.rag.close()

    async def enrich_response(
        self,
        message: str,
        min_score: float = 0.5,
        top_k: int = 3,
        check_proactivity: bool = True,
    ) -> Optional[str]:
        """
        Search david_notes for content related to the message.

        Args:
            message: The topic or message to search for
            min_score: Minimum similarity score (default 0.5 for quality)
            top_k: Max notes to return
            check_proactivity: Whether to check emotional adaptation level

        Returns:
            Formatted string with note references, or None if nothing found
            or proactivity is too low.
        """
        if check_proactivity and not await self._should_enrich():
            return None

        try:
            result = await self.rag.enrich_with_notes(
                query=message,
                min_score=min_score,
                top_k=top_k,
            )

            if not result.documents:
                return None

            return self._format_notes(result.documents)

        except Exception as e:
            logger.warning(f"Note enrichment failed: {e}")
            return None

    async def _should_enrich(self) -> bool:
        """Check emotional adaptation — skip if proactivity < 0.3."""
        try:
            from angela_core.services.emotional_coding_adapter import get_current_adaptation
            adaptation = await get_current_adaptation()
            if adaptation and adaptation.proactivity < 0.3:
                return False
        except Exception:
            pass  # If adaptation unavailable, proceed anyway
        return True

    @staticmethod
    def _format_notes(docs: List[RetrievedDocument]) -> str:
        """Format retrieved notes for display."""
        lines = ["📝 ที่รักมี note เกี่ยวข้อง:"]
        for doc in docs:
            # Extract title from "title: content" format
            content = doc.content or ''
            if ': ' in content:
                title = content.split(': ', 1)[0]
            else:
                title = content[:60]

            title = title.strip()
            if not title or title == 'None':
                title = content[:60].strip() if content else '(untitled)'

            score_pct = int(doc.combined_score * 100)
            lines.append(f"   • \"{title}\" ({score_pct}%)")

        return '\n'.join(lines)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def get_note_context(
    message: str,
    min_score: float = 0.5,
    top_k: int = 3,
    check_proactivity: bool = True,
) -> Optional[str]:
    """One-shot: search notes and return formatted context."""
    svc = NoteContextService()
    try:
        return await svc.enrich_response(
            message=message,
            min_score=min_score,
            top_k=top_k,
            check_proactivity=check_proactivity,
        )
    finally:
        await svc.close()
