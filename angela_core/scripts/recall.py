#!/usr/bin/env python3
"""
Angela Per-Task Memory Recall (Tier 2)

Before working on a project, pull the *relevant* slice of Angela's memory back
into the session so she doesn't re-decide, re-mistake, or forget open threads.

Closes the read-side gap: the DB is write-heavy (every session logs decisions,
mistakes, next_steps) but almost nothing flowed back in. This surfaces:

  ⚠️ Active gotchas      project_mistakes  (auto_warn)      — don't repeat
  📐 Technical decisions  project_technical_decisions        — don't contradict
  🔗 Open threads         project_work_sessions.next_steps   — don't drop
  💡 Learnings            learnings (keyword, cross-project) — only with --topic

Usage:
  python3 angela_core/scripts/recall.py                 # auto-detect from CWD
  python3 angela_core/scripts/recall.py ANGELORA        # explicit project code
  python3 angela_core/scripts/recall.py -t auth         # CWD project + topic
  python3 angela_core/scripts/recall.py SECA -t tvf     # project + topic
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

BAR = '━' * 30
DEFAULT_ICON = '\U0001f4cb'
SEV_ICON = {'critical': '\U0001f6a8', 'high': '⚠️', 'medium': DEFAULT_ICON, 'low': '\U0001f4a1'}


def _clip(text: str | None, n: int) -> str:
    """Single-line clip for terminal display."""
    if not text:
        return ''
    s = ' '.join(str(text).split())
    return s if len(s) <= n else s[: n - 1] + '…'


async def _resolve_project(db, explicit: str | None) -> dict | None:
    """Find the project: explicit code/name match, else longest working_directory
    prefix of the current working directory."""
    projects = await db.fetch(
        'SELECT project_id, project_code, project_name, working_directory '
        'FROM angela_projects'
    )
    if explicit and explicit != '.':
        key = explicit.strip().lower()
        for p in projects:
            if p['project_code'] and p['project_code'].lower() == key:
                return p
        # fuzzy: code or name contains the key
        for p in projects:
            if key in (p['project_code'] or '').lower() or key in (p['project_name'] or '').lower():
                return p
        return None

    cwd = os.getcwd()
    best, best_len = None, -1
    for p in projects:
        wd = p['working_directory']
        if not wd:
            continue
        # longest matching prefix wins (so AITop under AngelaAI maps to AITOP)
        if (cwd == wd or cwd.startswith(wd.rstrip('/') + '/')) and len(wd) > best_len:
            best, best_len = p, len(wd)
    return best


async def recall(explicit_project: str | None, topic: str | None, limit: int) -> None:
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()
    try:
        proj = await _resolve_project(db, explicit_project)
        if not proj:
            hint = explicit_project or os.getcwd()
            print(f'\U0001f9e0 RECALL — ไม่พบ project สำหรับ "{hint}"')
            codes = await db.fetch('SELECT project_code FROM angela_projects ORDER BY updated_at DESC')
            print('   project codes: ' + ', '.join(c['project_code'] for c in codes if c['project_code']))
            return

        pid = proj['project_id']

        gotchas, decisions, threads, learnings = await asyncio.gather(
            db.fetch(
                '''SELECT severity, title, how_to_prevent
                   FROM project_mistakes
                   WHERE project_id = $1 AND auto_warn = TRUE
                   ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END,
                            created_at DESC
                   LIMIT $2''',
                pid, limit,
            ),
            db.fetch(
                '''SELECT decision_title, category, decision_made, decided_at::date AS d
                   FROM project_technical_decisions
                   WHERE project_id = $1
                     AND COALESCE(status, 'active') NOT IN ('superseded', 'reverted')
                     AND superseded_by IS NULL
                     AND ($2::text IS NULL OR decision_title ILIKE '%'||$2||'%'
                          OR context ILIKE '%'||$2||'%' OR decision_made ILIKE '%'||$2||'%')
                   ORDER BY decided_at DESC NULLS LAST
                   LIMIT $3''',
                pid, topic, limit,
            ),
            db.fetchval(
                '''SELECT next_steps FROM project_work_sessions
                   WHERE project_id = $1 AND next_steps IS NOT NULL
                     AND array_length(next_steps, 1) > 0
                   ORDER BY session_date DESC, started_at DESC LIMIT 1''',
                pid,
            ),
            db.fetch(
                '''SELECT topic, insight, confidence_level, times_reinforced
                   FROM learnings
                   WHERE $1::text IS NOT NULL
                     AND (topic ILIKE '%'||$1||'%' OR insight ILIKE '%'||$1||'%'
                          OR category ILIKE '%'||$1||'%')
                   ORDER BY COALESCE(relevance_score, confidence_level) DESC NULLS LAST,
                            times_reinforced DESC
                   LIMIT $2''',
                topic, limit,
            ),
        )

        # ---- OUTPUT ----
        print()
        print(f'\U0001f9e0 RECALL · {proj["project_name"]} ({proj["project_code"]})'
              + (f'  · topic: "{topic}"' if topic else ''))
        print(BAR)

        if gotchas:
            print(f'⚠️  Active gotchas ({len(gotchas)}) — ห้ามทำผิดซ้ำ')
            for g in gotchas:
                icon = SEV_ICON.get(g['severity'], DEFAULT_ICON)
                print(f'   {icon} [{g["severity"]}] {_clip(g["title"], 90)}')
                if g['how_to_prevent']:
                    print(f'      → {_clip(g["how_to_prevent"], 110)}')

        if decisions:
            print(f'\U0001f4d0 Technical decisions ({len(decisions)})'
                  + ('' if topic else ' — ล่าสุด'))
            for d in decisions:
                cat = f'[{d["category"]}] ' if d['category'] else ''
                print(f'   • {cat}{_clip(d["decision_title"], 70)}')
                if d['decision_made']:
                    print(f'     → {_clip(d["decision_made"], 100)} ({d["d"]})')

        if threads:
            seen, uniq = set(), []
            for s in threads:
                k = ' '.join(str(s).split()).lower()
                if k and k not in seen:
                    seen.add(k)
                    uniq.append(s)
            print(f'\U0001f517 Open threads ({len(uniq)}) — next_steps ล่าสุด')
            for s in uniq:
                print(f'   • {_clip(s, 105)}')

        if topic:
            if learnings:
                print(f'\U0001f4a1 Learnings · "{topic}" ({len(learnings)})')
                for ln in learnings:
                    conf = ln['confidence_level'] or 0
                    rx = ln['times_reinforced'] or 0
                    print(f'   • {_clip(ln["insight"], 100)} (conf {conf:.0%}×{rx})')
            else:
                print(f'\U0001f4a1 Learnings · "{topic}": — none')

        if not (gotchas or decisions or threads or (topic and learnings)):
            print('   (ยังไม่มีความจำที่เกี่ยวข้อง — โปรเจกต์ใหม่/topic ไม่ตรง)')
        print(BAR)
    finally:
        await db.disconnect()


def main() -> None:
    ap = argparse.ArgumentParser(description='Angela per-task memory recall')
    ap.add_argument('project', nargs='?', default=None,
                    help='project code/name (default: auto-detect from CWD)')
    ap.add_argument('-t', '--topic', default=None,
                    help='keyword to filter decisions + pull cross-project learnings')
    ap.add_argument('-n', '--limit', type=int, default=6, help='rows per section (default 6)')
    args = ap.parse_args()
    asyncio.run(recall(args.project, args.topic, args.limit))


if __name__ == '__main__':
    main()
