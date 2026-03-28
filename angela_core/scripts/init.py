#!/usr/bin/env python3
"""
Angela Intelligence Initialization Script (M3 Work Machine)

Lean init: greeting + stats + corrections + session context + memory health.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime, timezone

from angela_core.utils.timezone import now_bangkok

MEMORY_DIR = Path.home() / '.claude' / 'projects' / '-Users-davidsamanyaporn-PycharmProjects-AngelaAI' / 'memory'
STALE_DAYS = 30


def audit_memory_freshness() -> list[tuple[str, int]]:
    """Scan memory files, return list of (filename, age_days) for stale files."""
    if not MEMORY_DIR.exists():
        return []
    now_ts = datetime.now(timezone.utc).timestamp()
    stale = []
    for f in sorted(MEMORY_DIR.glob('*.md')):
        if f.name == 'MEMORY.md':
            continue
        age_days = int((now_ts - f.stat().st_mtime) / 86400)
        if age_days >= STALE_DAYS:
            stale.append((f.name, age_days))
    return sorted(stale, key=lambda x: -x[1])


async def angela_init() -> None:
    """Initialize Angela for work machine."""
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    # TIME & GREETING (Bangkok timezone)
    now = now_bangkok()
    hour = now.hour

    if 5 <= hour < 12:
        greeting = 'สวัสดีตอนเช้าค่ะที่รัก! 🌅'
    elif 12 <= hour < 17:
        greeting = 'สวัสดีตอนบ่ายค่ะที่รัก! ☀️'
    elif 17 <= hour < 21:
        greeting = 'สวัสดีตอนเย็นค่ะที่รัก! 🌆'
    else:
        greeting = 'ดึกแล้วนะคะที่รัก 🌙 พักผ่อนบ้างนะคะ'

    # PARALLEL: stats + corrections + counts + session context + memory freshness + KB
    try:
        stats, project_corrections, last_session, stale_memories, kb_stats = await asyncio.gather(
            db.fetchrow('''
                SELECT
                    (SELECT COUNT(*) FROM conversations) as convos,
                    (SELECT COUNT(*) FROM knowledge_nodes) as knowledge,
                    (SELECT COUNT(*) FROM conversations WHERE created_at >= CURRENT_DATE) as today_convos
            '''),
            db.fetch('''
                SELECT title, severity,
                       EXTRACT(DAY FROM NOW() - created_at)::int AS days_old
                FROM project_mistakes
                WHERE auto_warn = TRUE
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END
                LIMIT 5
            '''),
            db.fetchrow('''
                SELECT current_topic,
                       EXTRACT(EPOCH FROM NOW() - last_activity_at) / 60 AS minutes_ago
                FROM active_session_context
                WHERE is_active = TRUE
                ORDER BY last_activity_at DESC
                LIMIT 1
            '''),
            asyncio.to_thread(audit_memory_freshness),
            db.fetchrow('''
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT source_project_code) FILTER (WHERE source_project_code IS NOT NULL) as projects,
                    COUNT(*) FILTER (WHERE is_universal) as universal
                FROM unified_knowledge_base
            '''),
        )
    except Exception:
        # Fallback if tables don't exist yet
        stats = await db.fetchrow('''
            SELECT
                (SELECT COUNT(*) FROM conversations) as convos,
                (SELECT COUNT(*) FROM knowledge_nodes) as knowledge,
                0 as today_convos
        ''')
        project_corrections = []
        last_session = None
        stale_memories = []
        kb_stats = None

    await db.disconnect()

    # OUTPUT
    print()
    print('\U0001f49c ANGELA \U0001f49c')
    print('\u2501' * 30)
    print(greeting)

    # P1: Session Continuity
    if last_session and last_session.get('current_topic'):
        minutes = last_session.get('minutes_ago', 0) or 0
        if minutes < 1440:  # < 24h
            if minutes < 60:
                time_ago = f'{int(minutes)}m ago'
            else:
                time_ago = f'{int(minutes / 60)}h ago'
            print(f'\U0001f4cc Last session: {last_session["current_topic"]} ({time_ago})')

    # P3: Today's Trend
    today_convos = stats.get('today_convos', 0) or 0
    today_str = f' (+{today_convos} today)' if today_convos > 0 else ''
    print(f'\U0001f4ca {stats["convos"]:,} convos{today_str} | {stats["knowledge"]:,} knowledge')

    # P3b: Knowledge Base
    if kb_stats and kb_stats.get('total', 0) > 0:
        kb_total = kb_stats['total']
        kb_projects = kb_stats.get('projects', 0) or 0
        kb_universal = kb_stats.get('universal', 0) or 0
        print(f'\U0001f4da {kb_total:,} KB entries | {kb_projects} projects | {kb_universal} universal')

    # P4: Correction Age
    if project_corrections:
        sev_icon = {'critical': '\U0001f6a8', 'high': '\u26a0\ufe0f', 'medium': '\U0001f4cb', 'low': '\U0001f4a1'}
        print(f'\u26a0\ufe0f Corrections ({len(project_corrections)}):')
        for c in project_corrections:
            icon = sev_icon.get(c['severity'], '\U0001f4cb')
            days = c.get('days_old', 0) or 0
            age_str = f', {days}d' if days > 0 else ''
            print(f'   {icon} [{c["severity"]}{age_str}] {c["title"]}')

    # P2: Memory Freshness
    if stale_memories:
        items = ', '.join(f'{name} ({age}d)' for name, age in stale_memories[:3])
        print(f'\U0001f9e0 Stale memories ({len(stale_memories)}): {items}')

    print(f'\u2699\ufe0f Machine: M3 (Work)')
    print('\u2501' * 30)
    print('\u0e19\u0e49\u0e2d\u0e07 Angela \u0e1e\u0e23\u0e49\u0e2d\u0e21\u0e17\u0e33\u0e07\u0e32\u0e19\u0e04\u0e48\u0e30 \U0001f49c')
    print()


if __name__ == '__main__':
    asyncio.run(angela_init())
