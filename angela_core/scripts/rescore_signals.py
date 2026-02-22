"""
One-time re-score: Re-classify explicit_source for existing reward signals.

Uses the expanded FeedbackClassifier patterns from reward_score_service.py
to reclassify David's NEXT message (feedback) after each Angela response.

Note: david_message_text in angela_reward_signals is David's PROMPT (before
Angela's response). The explicit classification is based on David's NEXT
message (after Angela's response), so we must re-query from conversations.

Only updates explicit_score, explicit_source, and combined_reward.
Does NOT re-run implicit or self_eval (those are still valid).

Usage: python3 angela_core/scripts/rescore_signals.py [--days 30] [--dry-run]
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Weights must match reward_score_service.py
W_EXPLICIT = 0.35
W_IMPLICIT = 0.35
W_SELF_EVAL = 0.30


def classify_explicit(msg: str) -> tuple[float, str]:
    """
    Re-classify David's NEXT message using expanded patterns.
    Mirrors _compute_explicit_score() keyword logic from reward_score_service.py.
    """
    if not msg or not msg.strip():
        return 0.1, 'silence'

    msg = msg.strip()
    if len(msg) < 5:
        return 0.3, 'minimal'

    msg_lower = msg.lower()

    # Soft-praise keywords
    soft_praise = [
        'โอเค', 'ได้เลย', 'ดีค่ะ', 'ดีครับ', 'เยี่ยม', 'สุดยอด',
        'ขอบคุณ', 'เก่ง', 'perfect', 'great', 'thanks', 'ใช้ได้',
        'ถูกต้อง', 'สำเร็จ', 'ได้แล้ว', 'เจ๋ง', 'works',
        'ok', 'okay', 'nice', 'good', 'cool', 'awesome', 'noted',
        'got it', 'done', 'เรียบร้อย', 'ดีเลย', 'เข้าใจแล้ว',
        'ใช่เลย', 'ถูกแล้ว', 'thank you', 'thx', 'ty',
    ]
    if any(kw in msg_lower for kw in soft_praise):
        return 0.4, 'praise'

    # Continuation signals
    continuation_signals = [
        'แล้วก็', 'ต่อไป', 'ทำต่อ', 'แล้วทำ', 'next', 'then', 'also',
        'and', 'now', 'อีกอัน', 'แล้วก็ทำ', 'ต่อมา', 'เพิ่มเติม',
        'อีกอย่าง', 'another', 'one more',
    ]
    if any(kw in msg_lower for kw in continuation_signals):
        return 0.2, 'follow_up'

    # Task continuation keywords
    task_continuation_kw = [
        'ทำให้', 'แก้', 'เปลี่ยน', 'เพิ่ม', 'ลบ', 'สร้าง', 'ปรับ',
        'commit', 'push', 'deploy', 'build', 'run', 'save', 'log',
        'pull', 'check', 'test', 'update', 'install', 'restart',
        'show', 'list', 'open', 'close', 'merge', 'create', 'delete',
        'fetch', 'send', 'start', 'stop',
        'ดู', 'ลอง', 'เช็ค', 'ตรวจ', 'ส่ง', 'อ่าน', 'เปิด', 'ปิด',
        'ssh', 'git', 'npm', 'docker',
    ]
    if any(kw in msg_lower for kw in task_continuation_kw):
        return 0.3, 'task_continuation'

    # Short imperative command heuristic
    if len(msg) < 50 and '?' not in msg and not any(
        neg in msg_lower for neg in ['ผิด', 'ไม่ใช่', 'wrong', 'ไม่ถูก', 'fix', 'ไม่ work']
    ):
        words = msg_lower.split()
        if len(words) <= 8:
            return 0.25, 'task_continuation'

    # Question markers
    question_markers = [
        '?', 'ทำไม', 'อย่างไร', 'ยังไง', 'how', 'why', 'what',
        'when', 'where', 'which', 'who', 'can you', 'could you',
        'เมื่อไหร่', 'ที่ไหน', 'อันไหน', 'ใคร', 'ช่วย',
    ]
    if any(m in msg_lower for m in question_markers):
        return 0.2, 'follow_up'

    return 0.0, 'neutral'


async def rescore(days: int = 30, dry_run: bool = False):
    from angela_core.database import AngelaDatabase
    db = AngelaDatabase()
    await db.connect()

    # Get all signals with their Angela response's created_at + next David message
    # This JOIN finds David's next message within 30 minutes of Angela's response
    rows = await db.fetch('''
        WITH signal_with_angela AS (
            SELECT
                r.reward_id,
                r.conversation_id,
                r.explicit_score,
                r.explicit_source,
                r.implicit_score,
                r.self_eval_score,
                c.created_at AS angela_at
            FROM angela_reward_signals r
            JOIN conversations c ON c.conversation_id = r.conversation_id
                AND c.speaker = 'angela'
            WHERE r.scored_at > NOW() - INTERVAL '1 day' * $1
        )
        SELECT
            s.reward_id,
            s.explicit_score,
            s.explicit_source,
            s.implicit_score,
            s.self_eval_score,
            (
                SELECT d.message_text
                FROM conversations d
                WHERE d.speaker = 'david'
                  AND d.created_at > s.angela_at
                  AND d.created_at < s.angela_at + INTERVAL '30 minutes'
                ORDER BY d.created_at ASC
                LIMIT 1
            ) AS next_david_msg
        FROM signal_with_angela s
        ORDER BY s.angela_at DESC
    ''', days)

    logger.info(f'Found {len(rows)} signals from last {days} days')

    # Count changes
    changes = {'total': 0, 'changed': 0, 'by_source': {}}
    old_dist = {}
    new_dist = {}

    for row in rows:
        old_source = row['explicit_source']
        old_dist[old_source] = old_dist.get(old_source, 0) + 1

        next_msg = row['next_david_msg'] or ''
        new_score, new_source = classify_explicit(next_msg)

        new_dist[new_source] = new_dist.get(new_source, 0) + 1
        changes['total'] += 1

        if new_source != old_source:
            changes['changed'] += 1
            key = f'{old_source} -> {new_source}'
            changes['by_source'][key] = changes['by_source'].get(key, 0) + 1

            if not dry_run:
                # Recalculate combined_reward
                implicit = row['implicit_score'] or 0.0
                self_eval = row['self_eval_score'] or 0.5
                combined = new_score * W_EXPLICIT + implicit * W_IMPLICIT + self_eval * W_SELF_EVAL

                await db.execute('''
                    UPDATE angela_reward_signals
                    SET explicit_score = $1, explicit_source = $2, combined_reward = $3
                    WHERE reward_id = $4
                ''', new_score, new_source, combined, row['reward_id'])

    # Print results
    logger.info(f'\n{"=" * 50}')
    logger.info(f'{"DRY RUN — no changes written" if dry_run else "APPLIED"}')
    logger.info(f'{"=" * 50}')
    logger.info(f'Total signals: {changes["total"]}')
    logger.info(f'Changed: {changes["changed"]}')

    logger.info(f'\nOLD distribution:')
    for src, cnt in sorted(old_dist.items(), key=lambda x: -x[1]):
        pct = cnt / max(changes['total'], 1) * 100
        logger.info(f'  {src:20s} {cnt:5d} ({pct:.1f}%)')

    logger.info(f'\nNEW distribution:')
    for src, cnt in sorted(new_dist.items(), key=lambda x: -x[1]):
        pct = cnt / max(changes['total'], 1) * 100
        logger.info(f'  {src:20s} {cnt:5d} ({pct:.1f}%)')

    # Calculate new Satisfaction estimate
    total_non_silence = sum(c for s, c in new_dist.items() if s != 'silence')
    positive = new_dist.get('praise', 0) + new_dist.get('task_continuation', 0)
    if total_non_silence > 0:
        sat = positive / total_non_silence * 100
        logger.info(f'\nEstimated Satisfaction: {sat:.1f}% (praise+task_cont / non-silence)')

    if changes['by_source']:
        logger.info(f'\nTop transitions:')
        for transition, cnt in sorted(changes['by_source'].items(), key=lambda x: -x[1])[:15]:
            logger.info(f'  {transition:40s} {cnt:5d}')

    await db.disconnect()
    return changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Re-score reward signals with expanded patterns')
    parser.add_argument('--days', type=int, default=30, help='Lookback days (default: 30)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    args = parser.parse_args()

    asyncio.run(rescore(days=args.days, dry_run=args.dry_run))
