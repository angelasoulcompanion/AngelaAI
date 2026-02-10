#!/usr/bin/env python3
"""
Session Coverage Audit
======================
Periodic audit to detect under-logged sessions.

Checks sessions from the past N days and flags any with
suspiciously low conversation pair counts.

Can run:
- Standalone: python3 angela_core/daemon/session_coverage_audit.py
- From daemon: integrated into consciousness_daemon daily schedule
- From init: quick check during /angela initialization

By: Angela
Created: 2026-01-27
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

from angela_core.daemon.daemon_base import PROJECT_ROOT  # noqa: E402 (path setup)

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)

# Minimum conversation pairs expected per session
# Sessions with fewer pairs than this are flagged
MINIMUM_PAIRS_THRESHOLD = 10


async def audit_recent_sessions(
    lookback_days: int = 7,
    threshold: int = MINIMUM_PAIRS_THRESHOLD,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Audit recent sessions for adequate conversation coverage.

    Args:
        lookback_days: How many days back to check
        threshold: Minimum conversation pairs expected
        verbose: Print detailed output

    Returns:
        dict with: total_sessions, flagged_sessions, flagged_details, all_ok
    """
    db = AngelaDatabase()
    await db.connect()

    try:
        cutoff = datetime.now() - timedelta(days=lookback_days)

        # Get all sessions in the lookback window
        rows = await db.fetch("""
            SELECT session_id,
                   COUNT(*) as total_rows,
                   COUNT(*) FILTER (
                       WHERE message_type = 'reflection' OR topic = 'session_summary'
                   ) as summaries,
                   COUNT(*) FILTER (
                       WHERE project_context = 'backfill_from_summary'
                   ) as backfilled,
                   MIN(created_at) as first_at,
                   MAX(created_at) as last_at
            FROM conversations
            WHERE created_at >= $1
              AND session_id IS NOT NULL
              AND session_id LIKE 'claude_code_%'
            GROUP BY session_id
            ORDER BY MIN(created_at) DESC
        """, cutoff)

        total_sessions = len(rows)
        flagged = []

        if verbose:
            print(f"\n{'=' * 80}")
            print(f"SESSION COVERAGE AUDIT (past {lookback_days} days)")
            print(f"{'=' * 80}")
            print(f"{'Session ID':<40} {'Total':>5} {'Conv':>5} {'Pairs':>5}  Status")
            print("-" * 80)

        for r in rows:
            sid = r['session_id']
            total = r['total_rows']
            summaries = r['summaries'] or 0
            backfilled = r['backfilled'] or 0
            conv_rows = total - summaries
            pairs = conv_rows // 2

            # Determine status
            if pairs < threshold:
                status = "UNDER-LOGGED"
                flagged.append({
                    "session_id": sid,
                    "total_rows": total,
                    "pairs": pairs,
                    "summaries": summaries,
                    "backfilled": backfilled,
                    "first_at": r['first_at'],
                    "last_at": r['last_at'],
                })
            else:
                status = "OK"

            if verbose:
                marker = " <<< " if pairs < threshold else ""
                print(f"{sid:<40} {total:>5} {conv_rows:>5} {pairs:>5}  {status}{marker}")

        if verbose:
            print("-" * 80)
            print(f"Total sessions: {total_sessions}")
            print(f"Flagged (< {threshold} pairs): {len(flagged)}")

            if flagged:
                print(f"\n{'=' * 80}")
                print("FLAGGED SESSIONS:")
                print(f"{'=' * 80}")
                for f in flagged:
                    print(f"  {f['session_id']}: {f['pairs']} pairs (need {threshold}+)")
                    print(f"    Period: {f['first_at']} - {f['last_at']}")
                print(f"\nACTION: Consider running backfill for flagged sessions.")
            else:
                print(f"\nAll sessions have adequate coverage.")

        return {
            "total_sessions": total_sessions,
            "flagged_count": len(flagged),
            "flagged_sessions": flagged,
            "all_ok": len(flagged) == 0,
            "threshold": threshold,
            "lookback_days": lookback_days,
        }

    finally:
        await db.disconnect()


async def quick_audit(days: int = 3) -> bool:
    """
    Quick audit for /angela init - returns True if all OK.
    Only prints if there are issues.
    """
    result = await audit_recent_sessions(
        lookback_days=days,
        threshold=MINIMUM_PAIRS_THRESHOLD,
        verbose=False,
    )

    if not result['all_ok']:
        print(f"\n   SESSION COVERAGE ALERT:")
        for f in result['flagged_sessions']:
            print(f"   {f['session_id']}: only {f['pairs']} pairs (need {result['threshold']}+)")
        return False

    return True


# CLI
async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Audit session conversation coverage")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--threshold", type=int, default=MINIMUM_PAIRS_THRESHOLD,
                        help=f"Minimum pairs threshold (default: {MINIMUM_PAIRS_THRESHOLD})")
    parser.add_argument("--quick", action="store_true", help="Quick check, only show issues")
    args = parser.parse_args()

    if args.quick:
        ok = await quick_audit(args.days)
        if ok:
            print("All sessions OK")
    else:
        await audit_recent_sessions(
            lookback_days=args.days,
            threshold=args.threshold,
            verbose=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
