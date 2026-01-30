"""Daily tasks endpoints."""
import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Query

from db import get_pool

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_scheduled_time(task_type: str) -> str:
    """Get scheduled time for task type"""
    schedule_map = {
        'conscious_morning_check': '08:00',
        'morning_check': '08:00',
        'daily_self_learning': '11:30',
        'self_learning': '11:30',
        'subconscious_learning': '14:00',
        'subconscious_learning_manual_test': '14:00',
        'conscious_evening_reflection': '22:00',
        'evening_reflection': '22:00',
        'pattern_reinforcement': '23:00',
        'knowledge_consolidation': '10:30'
    }
    return schedule_map.get(task_type, '00:00')


def get_expected_tasks_for_date(target_date: date) -> list:
    """Get expected tasks for a date"""
    weekday = target_date.weekday()  # 0 = Monday
    is_monday = weekday == 0

    expected = [
        {'task_type': 'conscious_morning_check', 'task_name': 'Morning Check', 'scheduled_time': '08:00'},
        {'task_type': 'self_learning', 'task_name': 'Self Learning', 'scheduled_time': '11:30'},
        {'task_type': 'subconscious_learning', 'task_name': 'Subconscious Learning', 'scheduled_time': '14:00'},
        {'task_type': 'conscious_evening_reflection', 'task_name': 'Evening Reflection', 'scheduled_time': '22:00'},
        {'task_type': 'pattern_reinforcement', 'task_name': 'Pattern Reinforcement', 'scheduled_time': '23:00'},
    ]

    if is_monday:
        expected.append({
            'task_type': 'knowledge_consolidation',
            'task_name': 'Knowledge Consolidation',
            'scheduled_time': '10:30'
        })

    return expected


@router.get("/daily/{date_str}")
async def get_daily_tasks(date_str: str):
    """Fetch daily tasks for a specific date (YYYY-MM-DD)"""
    from fastapi import HTTPException
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT action_id::text, action_type, action_description,
                   created_at, status, success
            FROM autonomous_actions
            WHERE DATE(created_at) = $1
              AND (action_type IN ('conscious_morning_check', 'morning_check',
                                   'conscious_evening_reflection', 'evening_reflection',
                                   'self_learning', 'daily_self_learning',
                                   'subconscious_learning', 'subconscious_learning_manual_test',
                                   'pattern_reinforcement', 'knowledge_consolidation'))
            ORDER BY created_at ASC
        """, target_date)

        tasks = []
        for r in rows:
            task = dict(r)
            task['scheduled_time'] = get_scheduled_time(r['action_type'])
            tasks.append(task)

        return tasks


@router.get("/last-7-days")
async def get_tasks_last_7_days():
    """Fetch daily tasks for the last 7 days"""
    results = []
    today = date.today()
    pool = get_pool()

    for days_ago in range(7):
        target_date = today - timedelta(days=days_ago)
        date_str = target_date.strftime("%Y-%m-%d")

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT action_id::text, action_type,
                       COALESCE(action_description, action_type) as action_description,
                       to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"+00:00"') as created_at,
                       status, success,
                       result_summary as error_message
                FROM autonomous_actions
                WHERE DATE(created_at) = $1
                ORDER BY created_at ASC
            """, target_date)

            tasks = []
            for r in rows:
                task = dict(r)
                task['scheduled_time'] = get_scheduled_time(r['action_type'])
                tasks.append(task)

            # Add expected tasks that didn't run
            executed_types = {t['action_type'] for t in tasks}
            expected_tasks = get_expected_tasks_for_date(target_date)

            for expected in expected_tasks:
                if expected['task_type'] not in executed_types:
                    scheduled_dt = datetime.combine(target_date, datetime.strptime(expected['scheduled_time'], '%H:%M').time())
                    tasks.append({
                        'action_id': str(uuid.uuid4()),
                        'action_type': expected['task_type'],
                        'action_description': expected['task_name'],
                        'created_at': scheduled_dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00'),
                        'status': 'pending',
                        'success': None,
                        'error_message': None,
                        'scheduled_time': expected['scheduled_time']
                    })

            results.append({
                'date': date_str,
                'tasks': tasks
            })

    return results
