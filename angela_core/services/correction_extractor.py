"""
CorrectionExtractor — Extract David's corrections from conversations → project_mistakes.

Uses keyword detection + Ollama to extract structured corrections.
"""

import json
import logging
from typing import Optional
from uuid import UUID

import httpx

from angela_core.services.base_db_service import BaseDBService

logger = logging.getLogger(__name__)

# Correction signal keywords (Thai + English)
CORRECTION_SIGNALS = [
    'ผิด', 'ไม่ถูก', 'แก้ให้', 'ห้าม', 'ย้ำ', 'ไม่ใช่แบบ',
    'wrong', 'fix this', 'approach ไม่', 'อันนี้ไม่', 'ไม่ต้อง',
    'อย่า', 'ไม่ควร', 'ทำใหม่', 'แก้ด้วย', 'ไม่ใช่อย่างนี้',
    'correction', 'mistake', 'ผิดแล้ว', 'ไม่ได้',
]

# Valid mistake_type values (from CHECK constraint)
VALID_MISTAKE_TYPES = [
    'bug', 'config_error', 'assumption', 'compatibility',
    'performance', 'security', 'data_issue', 'integration',
    'workflow', 'gotcha',
]

VALID_SEVERITIES = ['low', 'medium', 'high', 'critical']

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "scb10x/typhoon2.5-qwen3-4b"


class CorrectionExtractor(BaseDBService):
    """Extract corrections from David's messages and store in project_mistakes."""

    async def extract_from_session(
        self,
        conversations: list[dict],
        project_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
    ) -> list[dict]:
        """
        Scan session conversations for corrections.

        Args:
            conversations: List of dicts with keys:
                - david_message: str
                - angela_response: str
                - topic: str (optional)
            project_id: UUID of the project (falls back to ANGELA-001)
            session_id: UUID of the session (optional)

        Returns:
            List of corrections inserted into project_mistakes.
        """
        await self.connect()

        if project_id is None:
            row = await self.db.fetchrow(
                "SELECT project_id FROM angela_projects WHERE project_code = 'ANGELA-001'"
            )
            project_id = row['project_id'] if row else None

        if project_id is None:
            logger.warning("No project_id found, skipping correction extraction")
            return []

        # Find conversations with correction signals
        candidates = []
        for i, conv in enumerate(conversations):
            david_msg = conv.get('david_message', '')
            if self._has_correction_signal(david_msg):
                # Build context with previous Angela message if available
                angela_before = ''
                if i > 0:
                    angela_before = conversations[i - 1].get('angela_response', '')

                candidates.append({
                    'david_message': david_msg,
                    'angela_before': angela_before,
                    'angela_after': conv.get('angela_response', ''),
                    'topic': conv.get('topic', ''),
                    'index': i,
                })

        if not candidates:
            return []

        # Classify each candidate via Ollama
        corrections = []
        for candidate in candidates:
            result = await self._classify_correction(
                david_msg=candidate['david_message'],
                angela_before=candidate['angela_before'],
                angela_after=candidate['angela_after'],
            )

            if result and result.get('is_correction'):
                # Deduplicate: check if similar title already exists
                existing = await self.db.fetchval(
                    """
                    SELECT COUNT(*) FROM project_mistakes
                    WHERE LOWER(title) = LOWER($1)
                    """,
                    result['title'],
                )
                if existing > 0:
                    logger.info(f"Skipping duplicate correction: {result['title']}")
                    continue

                # Insert into project_mistakes
                row = await self.db.fetchrow(
                    """
                    INSERT INTO project_mistakes (
                        project_id, session_id, mistake_type, severity,
                        category, title, what_happened,
                        how_to_prevent, auto_warn
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE)
                    RETURNING mistake_id, title, severity
                    """,
                    project_id,
                    session_id,
                    result.get('mistake_type', 'workflow'),
                    result.get('severity', 'medium'),
                    result.get('category'),
                    result['title'],
                    result['what_happened'],
                    result.get('how_to_prevent', ''),
                )
                if row:
                    corrections.append(dict(row))
                    logger.info(f"Extracted correction: {row['title']}")

        return corrections

    def _has_correction_signal(self, text: str) -> bool:
        """Check if text contains correction signal keywords."""
        text_lower = text.lower()
        return any(signal in text_lower for signal in CORRECTION_SIGNALS)

    async def _classify_correction(
        self,
        david_msg: str,
        angela_before: str,
        angela_after: str,
    ) -> Optional[dict]:
        """
        Use Ollama to classify whether a message is a correction,
        and extract structured data.

        Returns:
            dict with keys: is_correction, title, what_happened,
            how_to_prevent, mistake_type, severity, category
            Or None if Ollama call fails.
        """
        prompt = f"""Analyze this conversation to determine if David is correcting Angela (AI assistant).

David's message: "{david_msg}"
Angela's previous response: "{angela_before[:500]}"
Angela's response after: "{angela_after[:500]}"

Respond in JSON:
{{
  "is_correction": true/false,
  "title": "Short title of what went wrong (max 60 chars)",
  "what_happened": "What Angela did wrong (1-2 sentences)",
  "how_to_prevent": "How to prevent this mistake (1-2 sentences)",
  "mistake_type": one of [{', '.join(VALID_MISTAKE_TYPES)}],
  "severity": one of [low, medium, high, critical],
  "category": "category like coding, sql, approach, communication"
}}

Rules:
- is_correction=true ONLY if David is pointing out an error/mistake Angela made
- is_correction=false for normal conversation, requests, questions
- Title should be actionable (e.g. "ห้าม guess lyrics — ต้อง search ก่อน")
- Keep everything concise"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.3},
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("message", {}).get("content", "{}")

                # Parse JSON, handle potential issues
                text = text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[-1].rsplit("```", 1)[0]

                result = json.loads(text)

                # Validate fields
                if result.get('is_correction'):
                    # Ensure valid mistake_type
                    if result.get('mistake_type') not in VALID_MISTAKE_TYPES:
                        result['mistake_type'] = 'workflow'
                    # Ensure valid severity
                    if result.get('severity') not in VALID_SEVERITIES:
                        result['severity'] = 'medium'
                    # Ensure required fields
                    if not result.get('title') or not result.get('what_happened'):
                        return None

                return result

        except Exception as e:
            logger.warning(f"Ollama correction classification failed: {e}")
            return None


async def extract_corrections(
    conversations: list[dict],
    project_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
) -> list[dict]:
    """Convenience function for use in log-session."""
    async with CorrectionExtractor() as extractor:
        return await extractor.extract_from_session(
            conversations, project_id, session_id
        )
