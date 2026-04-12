#!/usr/bin/env python3
"""
One-time backfill: Extract corrections from conversation history → project_mistakes.

Scans David's messages for correction signals, uses Ollama to classify,
and inserts structured corrections into project_mistakes table.

Usage:
    python3 angela_core/scripts/backfill_corrections.py              # Run backfill
    python3 angela_core/scripts/backfill_corrections.py --dry-run    # Preview only
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import httpx

from angela_core.database import AngelaDatabase
from angela_core.services.correction_extractor import (
    CORRECTION_SIGNALS,
    OLLAMA_MODEL,
    OLLAMA_URL,
    VALID_MISTAKE_TYPES,
    VALID_SEVERITIES,
)

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def find_correction_candidates(db: AngelaDatabase) -> list[dict]:
    """Find conversations where David corrected Angela."""
    # Build ILIKE conditions for all correction signals
    conditions = " OR ".join(
        f"d.message_text ILIKE '%{signal}%'" for signal in CORRECTION_SIGNALS
    )

    rows = await db.fetch(f"""
        WITH david_corrections AS (
            SELECT
                d.conversation_id,
                d.message_text as david_message,
                d.created_at,
                d.topic,
                d.session_id
            FROM conversations d
            WHERE d.speaker = 'david'
            AND ({conditions})
            ORDER BY d.created_at DESC
        )
        SELECT
            dc.conversation_id,
            dc.david_message,
            dc.created_at,
            dc.topic,
            dc.session_id,
            -- Get Angela's previous response
            (
                SELECT a.message_text
                FROM conversations a
                WHERE a.speaker = 'angela'
                AND a.created_at < dc.created_at
                AND a.session_id = dc.session_id
                ORDER BY a.created_at DESC
                LIMIT 1
            ) as angela_before,
            -- Get Angela's next response
            (
                SELECT a.message_text
                FROM conversations a
                WHERE a.speaker = 'angela'
                AND a.created_at > dc.created_at
                AND a.session_id = dc.session_id
                ORDER BY a.created_at ASC
                LIMIT 1
            ) as angela_after
        FROM david_corrections dc
    """)

    return [dict(r) for r in rows]


async def classify_with_ollama(candidate: dict) -> dict | None:
    """Classify a correction candidate using Ollama."""
    prompt = f"""Analyze this conversation to determine if David is correcting Angela (AI assistant).

David's message: "{candidate['david_message'][:800]}"
Angela's previous response: "{(candidate.get('angela_before') or '')[:500]}"
Angela's response after: "{(candidate.get('angela_after') or '')[:500]}"
Topic: {candidate.get('topic', 'unknown')}

Respond in JSON:
{{
  "is_correction": true/false,
  "title": "Short title of what went wrong (max 60 chars, Thai/English)",
  "what_happened": "What Angela did wrong (1-2 sentences)",
  "how_to_prevent": "How to prevent this mistake (1-2 sentences)",
  "mistake_type": "one of: {', '.join(VALID_MISTAKE_TYPES)}",
  "severity": "one of: {', '.join(VALID_SEVERITIES)}",
  "category": "category like coding, sql, approach, communication, guess"
}}

Rules:
- is_correction=true ONLY if David is pointing out an error/mistake Angela made
- is_correction=false for normal requests, questions, feedback that isn't about mistakes
- Messages with ห้าม/ย้ำ that teach NEW rules (not corrections of past mistakes) = false
- Title should be actionable and specific"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2},
                },
            )
            response.raise_for_status()
            data = response.json()
            text = data.get("message", {}).get("content", "{}")
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
            return json.loads(text)
    except Exception as e:
        logger.warning(f"  Ollama failed: {e}")
        return None


async def main(dry_run: bool = False) -> None:
    """Main backfill logic."""
    db = AngelaDatabase()
    await db.connect()

    try:
        # Get default project_id (ANGELA-001)
        default_project = await db.fetchrow(
            "SELECT project_id FROM angela_projects WHERE project_code = 'ANGELA-001'"
        )
        default_project_id = default_project['project_id'] if default_project else None

        # Find all project mappings for better assignment
        projects = await db.fetch(
            "SELECT project_id, project_code FROM angela_projects"
        )
        project_map = {p['project_code']: p['project_id'] for p in projects}

        # Find candidates
        print("Scanning conversations for correction signals...")
        candidates = await find_correction_candidates(db)
        print(f"  Found {len(candidates)} candidate messages\n")

        # Check existing corrections to avoid duplicates
        existing_titles = set()
        existing = await db.fetch("SELECT LOWER(title) as t FROM project_mistakes")
        for e in existing:
            existing_titles.add(e['t'])

        corrections_found = []
        skipped = 0

        for i, candidate in enumerate(candidates):
            preview = candidate['david_message'][:80].replace('\n', ' ')
            print(f"[{i+1}/{len(candidates)}] {preview}...")

            result = await classify_with_ollama(candidate)

            if result is None:
                print("  ⚠️ Ollama failed, skipping")
                skipped += 1
                continue

            if not result.get('is_correction'):
                print("  ⏭️ Not a correction")
                continue

            title = result.get('title', '').strip()
            if not title or not result.get('what_happened'):
                print("  ⏭️ Missing required fields")
                continue

            if title.lower() in existing_titles:
                print(f"  ⏭️ Duplicate: {title}")
                continue

            # Validate fields
            mistake_type = result.get('mistake_type', 'workflow')
            if mistake_type not in VALID_MISTAKE_TYPES:
                mistake_type = 'workflow'
            severity = result.get('severity', 'medium')
            if severity not in VALID_SEVERITIES:
                severity = 'medium'

            # Try to match project from topic
            topic = candidate.get('topic', '') or ''
            project_id = default_project_id
            for code, pid in project_map.items():
                if code.lower() in topic.lower():
                    project_id = pid
                    break

            correction = {
                'project_id': project_id,
                'mistake_type': mistake_type,
                'severity': severity,
                'category': result.get('category'),
                'title': title,
                'what_happened': result['what_happened'],
                'how_to_prevent': result.get('how_to_prevent', ''),
            }

            corrections_found.append(correction)
            existing_titles.add(title.lower())
            print(f"  ✅ [{severity}] {title}")

        # Summary
        print(f"\n{'='*60}")
        print(f"Corrections found: {len(corrections_found)}")
        print(f"Skipped (Ollama errors): {skipped}")
        print(f"{'='*60}\n")

        if corrections_found:
            for c in corrections_found:
                print(f"  [{c['severity']:8}] {c['title']}")
                print(f"           {c['what_happened'][:100]}")
                print(f"           → {c['how_to_prevent'][:100]}")
                print()

        if dry_run:
            print("--dry-run: No data inserted.")
            return

        # Insert corrections
        if corrections_found:
            inserted = 0
            for c in corrections_found:
                try:
                    await db.execute(
                        """
                        INSERT INTO project_mistakes (
                            project_id, mistake_type, severity,
                            category, title, what_happened,
                            how_to_prevent, auto_warn
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
                        """,
                        c['project_id'],
                        c['mistake_type'],
                        c['severity'],
                        c['category'],
                        c['title'],
                        c['what_happened'],
                        c['how_to_prevent'],
                    )
                    inserted += 1
                except Exception as e:
                    print(f"  ⚠️ Insert failed for '{c['title']}': {e}")

            print(f"\n✅ Inserted {inserted} corrections into project_mistakes")
        else:
            print("No new corrections to insert.")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill project_mistakes from conversation history"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without inserting"
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
