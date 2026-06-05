#!/usr/bin/env python3
"""
Backfill project_git_commits from real git history.

Most projects logged 0 commits (only ANGELA-001 logs via /log-session), so the
AITop Projects page showed "No commits". This reads each project's actual
`git log` and upserts into project_git_commits — idempotent via the
(project_id, commit_hash) unique constraint, so it's safe to re-run.

For a project whose working_directory is the repo root → whole repo history.
For a sub-directory of a shared repo (AITop/Pythia under AngelaAI) → only
commits touching that sub-path, so the project gets its own scoped slice.

Usage:
  python3 angela_core/scripts/backfill_git_commits.py            # all projects
  python3 angela_core/scripts/backfill_git_commits.py ANGELORA   # one project
  python3 angela_core/scripts/backfill_git_commits.py --limit 500
"""

import argparse
import asyncio
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

REC = "\x01"   # commit-record marker
SEP = "\x02"   # field separator


def _git(cwd: str, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", cwd, *args],
        capture_output=True, text=True, check=True,
    ).stdout


def _parse_commits(wd: str, limit: int) -> list[dict]:
    """Return commits from `git log` scoped to wd (sub-path aware)."""
    try:
        root = _git(wd, "rev-parse", "--show-toplevel").strip()
    except subprocess.CalledProcessError:
        return []  # not a git repo

    pretty = f"--pretty=format:{REC}%H{SEP}%an{SEP}%cI{SEP}%s"
    cmd = ["log", f"--max-count={limit}", "--numstat", "--date=iso-strict", pretty]
    if os.path.abspath(root) != os.path.abspath(wd):
        rel = os.path.relpath(os.path.abspath(wd), os.path.abspath(root))
        cmd += ["--", rel]  # only commits touching this sub-path

    try:
        out = _git(root, *cmd)
    except subprocess.CalledProcessError:
        return []

    commits: list[dict] = []
    cur: dict | None = None
    for line in out.split("\n"):
        if line.startswith(REC):
            if cur:
                commits.append(cur)
            h, author, cdate, subject = line[1:].split(SEP, 3)
            cur = {
                "hash": h, "author": author, "date": cdate, "message": subject,
                "files": 0, "ins": 0, "dels": 0,
            }
        elif line.strip() and cur is not None and "\t" in line:
            added, deleted, *_ = line.split("\t")
            cur["files"] += 1
            cur["ins"] += int(added) if added.isdigit() else 0
            cur["dels"] += int(deleted) if deleted.isdigit() else 0
    if cur:
        commits.append(cur)
    return commits


async def backfill(only: str | None, limit: int) -> None:
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()
    try:
        rows = await db.fetch(
            "SELECT project_id, project_code, working_directory FROM angela_projects "
            "WHERE working_directory IS NOT NULL ORDER BY project_code"
        )
        total_inserted = 0
        for r in rows:
            code = r["project_code"]
            if only and code.lower() != only.lower():
                continue
            wd = r["working_directory"]
            if not wd or not os.path.isdir(wd):
                print(f"  {code:<12} skip — dir missing ({wd})")
                continue

            commits = _parse_commits(wd, limit)
            if not commits:
                print(f"  {code:<12} skip — not a git repo / no commits")
                continue

            existing = {
                row["commit_hash"] for row in await db.fetch(
                    "SELECT commit_hash FROM project_git_commits WHERE project_id = $1",
                    r["project_id"],
                )
            }
            new = [c for c in commits if c["hash"] not in existing]
            if not new:
                print(f"  {code:<12} 0 new ({len(commits)} in repo, all present)")
                continue

            args = [
                (
                    r["project_id"], c["hash"], c["message"][:2000], c["author"],
                    c["files"], c["ins"], c["dels"],
                    datetime.fromisoformat(c["date"]),
                )
                for c in new
            ]
            await db.executemany(
                """INSERT INTO project_git_commits
                       (project_id, commit_hash, commit_message, author,
                        files_changed, insertions, deletions, committed_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   ON CONFLICT (project_id, commit_hash) DO NOTHING""",
                args,
            )
            total_inserted += len(new)
            print(f"  {code:<12} +{len(new):<4} commits  ({len(commits)} scanned)")

        print(f"\n✅ Backfill done — {total_inserted} commits inserted")
    finally:
        await db.disconnect()


def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill project_git_commits from git log")
    ap.add_argument("project", nargs="?", default=None, help="project code (default: all)")
    ap.add_argument("--limit", type=int, default=2000, help="max commits per project")
    args = ap.parse_args()
    print("🔨 Backfilling git commits…")
    asyncio.run(backfill(args.project, args.limit))


if __name__ == "__main__":
    main()
