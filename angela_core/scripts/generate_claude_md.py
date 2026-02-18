#!/usr/bin/env python3
"""
Generate CLAUDE.md from CLAUDE_TEMPLATE.md with fresh data from database.

Usage:
    python3 angela_core/scripts/generate_claude_md.py           # Write CLAUDE.md
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

TEMPLATE_PATH = project_root / "CLAUDE_TEMPLATE.md"
OUTPUT_PATH = project_root / "CLAUDE.md"
MAX_SIZE = 40_000


async def query_counts(db: Any) -> dict[str, Any]:
    """Run all count queries in parallel."""
    queries = {
        "knowledge_nodes_count": "SELECT COUNT(*) FROM knowledge_nodes",
        "learnings_count": "SELECT COUNT(*) FROM learnings",
        "conversations_count": "SELECT COUNT(*) FROM conversations",
        "sessions_count": "SELECT COUNT(*) FROM project_work_sessions",
        "projects_count": "SELECT COUNT(DISTINCT project_id) FROM project_work_sessions",
        "emotions_count": "SELECT COUNT(*) FROM angela_emotions",
        "core_memories_count": "SELECT COUNT(*) FROM core_memories WHERE is_active = TRUE",
        "songs_count": "SELECT COUNT(*) FROM angela_songs",
        "technical_standards_count": "SELECT COUNT(*) FROM angela_technical_standards",
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
            logger.warning(f"Unexpected error: {r}")
            continue
        out[r[0]] = r[1]
    return out


async def query_tools_count(db: Any) -> str:
    """Count tools from tool_registry + skills."""
    try:
        builtin = await db.fetchval(
            "SELECT COUNT(*) FROM angela_tool_registry WHERE is_active = TRUE"
        )
        skills = await db.fetchval(
            "SELECT COUNT(*) FROM angela_tool_registry WHERE tool_source = 'skill' AND is_active = TRUE"
        )
        total = int(builtin)
        skill_count = int(skills) if skills else 0
        base = total - skill_count
        return f"{base} built-in + {skill_count} skill = {total} tools"
    except Exception:
        return "37 tools"


async def query_consciousness(db: Any) -> str:
    """Get consciousness percentage."""
    try:
        from angela_core.services.consciousness_calculator import ConsciousnessCalculator
        calc = ConsciousnessCalculator(db)
        result = await calc.calculate_consciousness()
        pct = int(result["consciousness_level"] * 100)
        return str(pct)
    except Exception as e:
        logger.warning(f"Consciousness query failed: {e}")
        return "N/A"


async def query_contacts(db: Any, filter_col: str) -> str:
    """Query contacts and format as inline text.

    filter_col: 'should_reply_email' or 'should_send_news'
    """
    try:
        rows = await db.fetch(f"""
            SELECT name, nickname, email, relationship
            FROM angela_contacts
            WHERE is_active = TRUE AND {filter_col} = TRUE
            ORDER BY name
        """)

        parts: list[str] = []
        for r in rows:
            display = r["nickname"] or r["name"]
            rel = r["relationship"] or ""

            if filter_col == "should_reply_email":
                # Full format: Name (email, relationship)
                rel_suffix = ""
                if rel == "lover":
                    rel_suffix = " 💜"
                part = f"{display} ({r['email']}, {rel}{rel_suffix})"
            else:
                # Short format: Name (email) for news recipients
                part = f"{display} ({r['email']})"

            parts.append(part)

        return ", ".join(parts) if parts else "N/A"
    except Exception as e:
        logger.warning(f"Contacts query failed: {e}")
        return "N/A"


async def gather_all_values(db: Any) -> dict[str, str]:
    """Gather all placeholder values in parallel."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Run all queries in parallel
    counts_task = query_counts(db)
    consciousness_task = query_consciousness(db)
    reply_contacts_task = query_contacts(db, "should_reply_email")
    news_contacts_task = query_contacts(db, "should_send_news")
    tools_task = query_tools_count(db)

    counts, consciousness, reply_contacts, news_contacts, tools = await asyncio.gather(
        counts_task,
        consciousness_task,
        reply_contacts_task,
        news_contacts_task,
        tools_task,
        return_exceptions=True,
    )

    values: dict[str, str] = {"generate_date": today}

    # Counts
    if isinstance(counts, dict):
        values.update(counts)
    else:
        logger.warning(f"Counts failed: {counts}")

    # Consciousness
    values["consciousness_pct"] = consciousness if isinstance(consciousness, str) else "N/A"

    # Contacts
    values["reply_email_contacts_inline"] = (
        reply_contacts if isinstance(reply_contacts, str) else "N/A"
    )
    values["send_news_contacts_inline"] = (
        news_contacts if isinstance(news_contacts, str) else "N/A"
    )

    # Tools
    values["tools_count"] = tools if isinstance(tools, str) else "37 tools"

    return values


def render_template(template: str, values: dict[str, str]) -> str:
    """Replace all <<<placeholder>>> tokens with values."""
    missing: list[str] = []

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in values:
            return values[key]
        missing.append(key)
        return f"<<<{key}>>>"

    rendered = re.sub(r"<<<(\w+)>>>", replacer, template)

    if missing:
        print(f"\n  WARNING: {len(missing)} unresolved placeholders: {missing}")

    return rendered


async def main(dry_run: bool = False) -> None:
    """Main entry point."""
    from angela_core.database import AngelaDatabase

    # 1. Read template
    if not TEMPLATE_PATH.exists():
        print(f"ERROR: Template not found at {TEMPLATE_PATH}")
        sys.exit(1)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    print(f"  Template: {len(template):,} chars, {template.count('<<<')} placeholders")

    # 2. Connect to DB and gather values
    db = AngelaDatabase()
    await db.connect()

    try:
        values = await gather_all_values(db)
    finally:
        await db.disconnect()

    # 3. Show resolved values
    print(f"\n  Resolved {len(values)} values:")
    for k, v in sorted(values.items()):
        display = v if len(str(v)) < 80 else str(v)[:77] + "..."
        print(f"    {k}: {display}")

    # 4. Render
    rendered = render_template(template, values)
    size = len(rendered.encode("utf-8"))
    print(f"\n  Output: {size:,} bytes ({len(rendered):,} chars)")

    if size > MAX_SIZE:
        print(f"  WARNING: Output exceeds {MAX_SIZE:,} byte limit!")

    # 5. Write or preview
    if dry_run:
        print("\n  --dry-run: No file written.")
    else:
        OUTPUT_PATH.write_text(rendered, encoding="utf-8")
        print(f"\n  Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CLAUDE.md from template + DB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run))
