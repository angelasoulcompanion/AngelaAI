#!/usr/bin/env python3
"""
Backfill project_milestones with OBJECTIVE markers only.

Milestones are curated achievements — we must NOT invent "feature_complete"
events from commit messages (that would overclaim, cf. project_mistakes). So
this only seeds events that are factually verifiable from the repo:

  • project_start  — the repo's first commit ("Project Started: <name>")
  • release        — MAJOR version-bump commits (X.0.0) + annotated git tags

Idempotent: skips a milestone whose (project_id, milestone_type, title) already
exists (the table has no unique constraint, so we dedup in-app).

Usage:
  python3 angela_core/scripts/backfill_milestones.py            # all
  python3 angela_core/scripts/backfill_milestones.py SE-ASSET   # one
"""

import argparse
import asyncio
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# "bump version to 6.0.0", "release v2.0.0" — MAJOR only (minor/patch = 0)
MAJOR_RE = re.compile(r"(?:bump version to|release)\s+v?(\d+)\.0\.0\b", re.IGNORECASE)


def _git(cwd: str, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", cwd, *args], capture_output=True, text=True, check=True
    ).stdout


def _collect(wd: str, project_name: str) -> list[dict]:
    """Objective milestones from the repo at wd."""
    try:
        root = _git(wd, "rev-parse", "--show-toplevel").strip()
    except subprocess.CalledProcessError:
        return []

    # Run all git queries from the repo ROOT; pathspec is relative to root.
    # (git resolves a pathspec against the -C directory, so it must match root.)
    scoped = os.path.abspath(root) != os.path.abspath(wd)
    rel = os.path.relpath(os.path.abspath(wd), os.path.abspath(root)) if scoped else None
    pathspec = ["--", rel] if rel else []

    out: list[dict] = []

    # 1) project_start — first (oldest) commit touching this path.
    # NOTE: `--reverse --max-count=1` returns the NEWEST commit (git limits before
    # reversing), so reverse the full log and take the first line instead.
    try:
        rev = _git(root, "log", "--reverse", "--pretty=format:%cI", *pathspec)
    except subprocess.CalledProcessError:
        rev = ""
    first = next((ln for ln in rev.split("\n") if ln.strip()), "")
    if first:
        out.append({
            "type": "project_start",
            "title": f"Project Started: {project_name}",
            "description": "First commit in the repository.",
            "significance": 5,
            "achieved_at": first,
        })

    # 2) release — MAJOR version-bump commits
    try:
        log = _git(root, "log", "--pretty=format:%cI\x1f%s", *pathspec)
    except subprocess.CalledProcessError:
        log = ""
    for line in log.split("\n"):
        if "\x1f" not in line:
            continue
        cdate, subject = line.split("\x1f", 1)
        m = MAJOR_RE.search(subject)
        if m:
            out.append({
                "type": "release",
                "title": f"Release v{m.group(1)}.0.0",
                "description": subject.strip()[:300],
                "significance": 5,
                "achieved_at": cdate,
            })

    # 3) release — annotated git tags (repo-root only, to avoid cross-project noise)
    if not scoped:
        try:
            tags = _git(wd, "for-each-ref", "--sort=-creatordate",
                        "--format=%(refname:short)\x1f%(creatordate:iso-strict)",
                        "refs/tags")
        except subprocess.CalledProcessError:
            tags = ""
        for line in tags.split("\n"):
            if "\x1f" not in line:
                continue
            name, tdate = line.split("\x1f", 1)
            out.append({
                "type": "release",
                "title": f"Tag {name}",
                "description": f"Git tag {name}",
                "significance": 4,
                "achieved_at": tdate,
            })
    return out


async def backfill(only: str | None) -> None:
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()
    try:
        rows = await db.fetch(
            "SELECT project_id, project_code, project_name, working_directory "
            "FROM angela_projects WHERE working_directory IS NOT NULL ORDER BY project_code"
        )
        total = 0
        for r in rows:
            code = r["project_code"]
            if only and code.lower() != only.lower():
                continue
            wd = r["working_directory"]
            if not wd or not os.path.isdir(wd):
                print(f"  {code:<12} skip — dir missing")
                continue

            candidates = _collect(wd, r["project_name"])
            if not candidates:
                print(f"  {code:<12} skip — no git / no markers")
                continue

            existing = {
                (row["milestone_type"], row["title"])
                for row in await db.fetch(
                    "SELECT milestone_type, title FROM project_milestones WHERE project_id = $1",
                    r["project_id"],
                )
            }
            # dedup within candidates too (same MAJOR can appear once)
            seen, new = set(), []
            for c in candidates:
                key = (c["type"], c["title"])
                if key in existing or key in seen:
                    continue
                seen.add(key)
                new.append(c)

            if not new:
                print(f"  {code:<12} 0 new ({len(candidates)} markers, all present)")
                continue

            args = [
                (r["project_id"], c["type"], c["title"], c["description"],
                 c["significance"], datetime.fromisoformat(c["achieved_at"]))
                for c in new
            ]
            await db.executemany(
                """INSERT INTO project_milestones
                       (project_id, milestone_type, title, description,
                        significance, achieved_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                args,
            )
            total += len(new)
            kinds = ", ".join(f"{c['type']}:{c['title']}" for c in new[:4])
            print(f"  {code:<12} +{len(new):<3} ({kinds}{'…' if len(new) > 4 else ''})")

        print(f"\n✅ Milestone backfill done — {total} inserted")
    finally:
        await db.disconnect()


def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill objective project_milestones")
    ap.add_argument("project", nargs="?", default=None, help="project code (default: all)")
    args = ap.parse_args()
    print("🚩 Backfilling milestones (objective markers only)…")
    asyncio.run(backfill(args.project))


if __name__ == "__main__":
    main()
