"""Daily tasks endpoints.

No autonomous_actions table — return empty/pending for all.
"""
import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_scheduled_time(task_type: str) -> str:
    schedule_map = {
        'conscious_morning_check': '08:00',
        'morning_check': '08:00',
        'daily_self_learning': '11:30',
        'self_learning': '11:30',
        'subconscious_learning': '14:00',
        'conscious_evening_reflection': '22:00',
        'evening_reflection': '22:00',
        'pattern_reinforcement': '23:00',
        'knowledge_consolidation': '10:30',
    }
    return schedule_map.get(task_type, '00:00')


def get_expected_tasks_for_date(target_date: date) -> list:
    is_monday = target_date.weekday() == 0
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
            'scheduled_time': '10:30',
        })
    return expected


@router.get("/daily/{date_str}")
async def get_daily_tasks(date_str: str, conn=Depends(get_conn)):
    """No autonomous_actions — return expected tasks as pending."""
    from fastapi import HTTPException
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    tasks = []
    for expected in get_expected_tasks_for_date(target_date):
        scheduled_dt = datetime.combine(target_date, datetime.strptime(expected['scheduled_time'], '%H:%M').time())
        tasks.append({
            'action_id': str(uuid.uuid4()),
            'action_type': expected['task_type'],
            'action_description': expected['task_name'],
            'created_at': scheduled_dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00'),
            'status': 'pending',
            'success': None,
            'error_message': None,
            'scheduled_time': expected['scheduled_time'],
        })
    return tasks


@router.get("/last-7-days")
async def get_tasks_last_7_days(conn=Depends(get_conn)):
    """No autonomous_actions — return expected tasks as pending for each day."""
    results = []
    today = date.today()

    for days_ago in range(7):
        target_date = today - timedelta(days=days_ago)
        tasks = []
        for expected in get_expected_tasks_for_date(target_date):
            scheduled_dt = datetime.combine(target_date, datetime.strptime(expected['scheduled_time'], '%H:%M').time())
            tasks.append({
                'action_id': str(uuid.uuid4()),
                'action_type': expected['task_type'],
                'action_description': expected['task_name'],
                'created_at': scheduled_dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00'),
                'status': 'pending',
                'success': None,
                'error_message': None,
                'scheduled_time': expected['scheduled_time'],
            })

        results.append({
            'date': target_date.strftime("%Y-%m-%d"),
            'tasks': tasks,
        })

    return results
