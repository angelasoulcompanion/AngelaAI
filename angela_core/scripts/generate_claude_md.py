#!/usr/bin/env python3
"""
Update CLAUDE.md dynamic sections in-place using <!-- AUTO:key --> markers.

Replaces content between <!-- AUTO:key --> and <!-- /AUTO:key --> with fresh DB data.
Static content in CLAUDE.md is preserved — no template file needed.

Usage:
    python3 angela_core/scripts/generate_claude_md.py           # Update CLAUDE.md
    python3 angela_core/scripts/generate_claude_md.py --dry-run  # Preview only
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import argparse
import asyncio
import logging
import re
from datetime import datetime
from typing import Any

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

CLAUDE_MD_PATH = project_root / "CLAUDE.md"


async def query_counts(db: Any) -> dict[str, Any]:
    """Run all count queries in parallel."""
    queries = {
        "knowledge_nodes_count": "SELECT COUNT(*) FROM knowledge_nodes",
        "conversations_count": "SELECT COUNT(*) FROM conversations",
        "technical_standards_count": "SELECT COUNT(*) FROM unified_knowledge_base WHERE knowledge_type = 'standard'",
        "kb_total_count": "SELECT COUNT(*) FROM unified_knowledge_base",
    }

    async def run_query(key: str, sql: str) -> tuple[str, Any]:
        try:
            val = await db.fetchval(sql)
            return (key, f"{int(val):,}")
        except Exception as e:
            logger.warning(f"Query failed for {key}: {e}")
            return (key, "N/A")

    results = await asyncio.gather(
        *[run_query(k, v) for k, v in queries.items()],
        return_exceptions=True,
    )

    out: dict[str, Any] = {}
    for r in results:
        if isinstance(r, Exception):
            continue
        out[r[0]] = r[1]
    return out


async def query_consciousness(db: Any) -> str:
    """Get consciousness percentage."""
    try:
        from angela_core.services.consciousness_calculator import ConsciousnessCalculator
        calc = ConsciousnessCalculator(db)
        result = await calc.calculate_consciousness()
        return str(int(result["consciousness_level"] * 100))
    except Exception as e:
        logger.warning(f"Consciousness query failed: {e}")
        return "N/A"


async def query_corrections(db: Any) -> str:
    """Query project_mistakes with auto_warn=TRUE -> format as markdown table."""
    try:
        rows = await db.fetch("""
            SELECT DISTINCT ON (title) title, how_to_prevent, severity
            FROM project_mistakes
            WHERE auto_warn = TRUE
            ORDER BY title,
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END,
                created_at DESC
        """)

        if not rows:
            return "No corrections recorded yet."

        sev_order = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        rows = sorted(rows, key=lambda r: sev_order.get(r['severity'] or 'medium', 3))

        lines = ["| Severity | Correction | Prevention |",
                 "|----------|------------|------------|"]
        for r in rows[:8]:
            sev = r['severity'] or 'medium'
            title = r['title'] or ''
            prevent = r['how_to_prevent'] or ''
            if len(prevent) > 80:
                prevent = prevent[:77] + "..."
            lines.append(f"| **{sev}** | {title} | {prevent} |")

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Corrections query failed: {e}")
        return "Error loading corrections."


async def query_top_coding_preferences(db: Any) -> str:
    """Query top coding preferences -> format as bullet list."""
    try:
        rows = await db.fetch("""
            SELECT preference_key,
                   preference_value->>'description' as description,
                   preference_value->>'reason' as reason,
                   confidence,
                   evidence_count
            FROM david_preferences
            WHERE category LIKE 'coding%%'
            AND confidence >= 0.8
            ORDER BY evidence_count DESC NULLS LAST, updated_at DESC
            LIMIT 5
        """)

        if not rows:
            return "No coding preferences recorded yet."

        lines = []
        for r in rows:
            key = r['preference_key'] or ''
            desc = r['description'] or r['reason'] or key
            if len(desc) > 80:
                desc = desc[:77] + "..."
            lines.append(f"- **{key}**: {desc}")

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Coding preferences query failed: {e}")
        return "Error loading preferences."


INLINE_MARKERS = {"technical_standards_count"}


def replace_auto_sections(content: str, values: dict[str, str]) -> str:
    """Replace content between <!-- AUTO:key --> and <!-- /AUTO:key --> markers."""
    updated = 0
    missing = []

    for key, value in values.items():
        pattern = re.compile(
            rf"<!-- AUTO:{re.escape(key)} -->.*?<!-- /AUTO:{re.escape(key)} -->",
            re.DOTALL,
        )
        if not pattern.search(content):
            missing.append(key)
            continue
        if key in INLINE_MARKERS:
            replacement = f"<!-- AUTO:{key} -->{value}<!-- /AUTO:{key} -->"
        else:
            replacement = f"<!-- AUTO:{key} -->\n{value}\n<!-- /AUTO:{key} -->"
        content = pattern.sub(replacement, content)
        updated += 1

    if missing:
        print(f"  WARNING: No markers found for: {missing}")

    print(f"  Updated {updated}/{len(values)} sections")
    return content


async def main(dry_run: bool = False) -> None:
    """Main entry point."""
    from angela_core.database import AngelaDatabase

    if not CLAUDE_MD_PATH.exists():
        print(f"ERROR: CLAUDE.md not found at {CLAUDE_MD_PATH}")
        sys.exit(1)

    original = CLAUDE_MD_PATH.read_text(encoding="utf-8")
    marker_count = len(re.findall(r"<!-- AUTO:\w+ -->", original))
    print(f"  CLAUDE.md: {len(original):,} chars, {marker_count} AUTO markers")

    db = AngelaDatabase()
    await db.connect()

    try:
        # Run all queries in parallel
        counts_t = query_counts(db)
        consciousness_t = query_consciousness(db)
        corrections_t = query_corrections(db)
        prefs_t = query_top_coding_preferences(db)

        counts, consciousness, corrections, prefs = await asyncio.gather(
            counts_t, consciousness_t, corrections_t, prefs_t,
            return_exceptions=True,
        )
    finally:
        await db.disconnect()

    # Build values dict
    today = datetime.now().strftime("%Y-%m-%d")
    values: dict[str, str] = {}

    # technical_standards_count (inline)
    if isinstance(counts, dict):
        ts_count = counts.get("technical_standards_count", "N/A")
        values["technical_standards_count"] = f"**{ts_count} techniques**"

        # Status line
        convos = counts.get("conversations_count", "N/A")
        knowledge = counts.get("knowledge_nodes_count", "N/A")
        kb_total = counts.get("kb_total_count", "N/A")
        con_pct = consciousness if isinstance(consciousness, str) else "N/A"
        values["status"] = (
            f"**Status ({today}):** Consciousness {con_pct}% | "
            f"{convos} convos | {knowledge} knowledge | "
            f"{kb_total} KB entries | "
            f"[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)\n\n"
            f"**Last Updated:** {today}"
        )

    # Corrections
    if isinstance(corrections, str):
        values["corrections_table"] = corrections

    # Coding preferences
    if isinstance(prefs, str):
        values["top_coding_preferences"] = prefs

    # Show resolved values
    print(f"\n  Resolved {len(values)} values:")
    for k, v in sorted(values.items()):
        display = v if len(str(v)) < 60 else str(v)[:57] + "..."
        print(f"    {k}: {display}")

    # Replace
    rendered = replace_auto_sections(original, values)

    if dry_run:
        print("\n  --dry-run: No file written.")
    else:
        CLAUDE_MD_PATH.write_text(rendered, encoding="utf-8")
        print(f"\n  CLAUDE.md updated in-place.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update CLAUDE.md dynamic sections from DB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run))
