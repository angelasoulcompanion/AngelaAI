"""Scheduled tasks (CRUD + Execute) endpoints."""
import subprocess
from datetime import datetime, timedelta, time as dt_time

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn, get_pool
from schemas import ScheduledTaskCreate, ScheduledTaskUpdate

router = APIRouter(prefix="/api/scheduled-tasks", tags=["scheduled-tasks"])


def _task_row_to_dict(row) -> dict:
    """Convert a task row to a serializable dict."""
    d = dict(row)
    d['task_id'] = str(d['task_id'])
    if d.get('schedule_time') is not None:
        d['schedule_time'] = d['schedule_time'].strftime('%H:%M')
    return d


def _log_row_to_dict(row) -> dict:
    """Convert a log row to a serializable dict."""
    d = dict(row)
    d['log_id'] = str(d['log_id'])
    d['task_id'] = str(d['task_id'])
    return d


# NOTE: /next must be defined before /{task_id} routes.
# FastAPI matches fixed segments before path parameters.
@router.get("/next")
async def get_next_scheduled_task(conn=Depends(get_conn)):
    """Get the next upcoming scheduled task with seconds until execution"""
    now_bkk = await conn.fetchval(
        "SELECT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::time"
    )

    time_task = await conn.fetchrow("""
        SELECT task_id, task_name, schedule_time
        FROM dashboard_scheduled_tasks
        WHERE is_active = TRUE AND schedule_type = 'time' AND schedule_time IS NOT NULL
        ORDER BY
            CASE WHEN schedule_time >= $1 THEN 0 ELSE 1 END,
            schedule_time ASC
        LIMIT 1
    """, now_bkk)

    interval_task = await conn.fetchrow("""
        SELECT task_id, task_name, interval_minutes, last_run_at
        FROM dashboard_scheduled_tasks
        WHERE is_active = TRUE AND schedule_type = 'interval' AND interval_minutes IS NOT NULL
        ORDER BY
            COALESCE(last_run_at, '2000-01-01'::timestamptz) + (interval_minutes || ' minutes')::interval ASC
        LIMIT 1
    """)

    results = []
    if time_task:
        sched_time = time_task['schedule_time']
        now_bkk_dt = await conn.fetchval(
            "SELECT CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok'"
        )
        today_sched = now_bkk_dt.replace(
            hour=sched_time.hour, minute=sched_time.minute, second=0, microsecond=0
        )
        if today_sched < now_bkk_dt:
            today_sched = today_sched + timedelta(days=1)
        seconds_until = int((today_sched - now_bkk_dt).total_seconds())
        results.append({
            "task_id": str(time_task['task_id']),
            "task_name": time_task['task_name'],
            "seconds_until": seconds_until,
            "schedule_display": sched_time.strftime('%H:%M')
        })

    if interval_task:
        last_run = interval_task['last_run_at']
        interval_min = interval_task['interval_minutes']
        if last_run:
            next_run = last_run + timedelta(minutes=interval_min)
            now_utc = await conn.fetchval("SELECT CURRENT_TIMESTAMP")
            seconds_until = max(0, int((next_run - now_utc).total_seconds()))
        else:
            seconds_until = 0
        results.append({
            "task_id": str(interval_task['task_id']),
            "task_name": interval_task['task_name'],
            "seconds_until": seconds_until,
            "schedule_display": f"every {interval_min}m"
        })

    if not results:
        return None

    results.sort(key=lambda x: x['seconds_until'])
    return results[0]


@router.get("/")
async def list_scheduled_tasks(conn=Depends(get_conn)):
    """List all scheduled tasks"""
    rows = await conn.fetch("""
        SELECT task_id, task_name, description, task_type, command,
               schedule_type, schedule_time, interval_minutes,
               is_active, last_run_at, last_status, created_at, updated_at
        FROM dashboard_scheduled_tasks
        ORDER BY is_active DESC, task_name ASC
    """)
    return [_task_row_to_dict(r) for r in rows]


@router.post("/")
async def create_scheduled_task(body: ScheduledTaskCreate, conn=Depends(get_conn)):
    """Create a new scheduled task"""
    schedule_time_val = None
    if body.schedule_time:
        parts = body.schedule_time.split(':')
        schedule_time_val = dt_time(int(parts[0]), int(parts[1]))

    row = await conn.fetchrow("""
        INSERT INTO dashboard_scheduled_tasks
            (task_name, description, task_type, command, schedule_type, schedule_time, interval_minutes)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING task_id, task_name, description, task_type, command,
                  schedule_type, schedule_time, interval_minutes,
                  is_active, last_run_at, last_status, created_at, updated_at
    """, body.task_name, body.description, body.task_type, body.command,
        body.schedule_type, schedule_time_val, body.interval_minutes)
    return _task_row_to_dict(row)


@router.put("/{task_id}")
async def update_scheduled_task(task_id: str, body: ScheduledTaskUpdate, conn=Depends(get_conn)):
    """Update a scheduled task"""
    existing = await conn.fetchrow(
        "SELECT task_id FROM dashboard_scheduled_tasks WHERE task_id = $1::uuid", task_id
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = []
    params = []
    idx = 1

    if body.task_name is not None:
        updates.append(f"task_name = ${idx}")
        params.append(body.task_name)
        idx += 1
    if body.description is not None:
        updates.append(f"description = ${idx}")
        params.append(body.description)
        idx += 1
    if body.task_type is not None:
        updates.append(f"task_type = ${idx}")
        params.append(body.task_type)
        idx += 1
    if body.command is not None:
        updates.append(f"command = ${idx}")
        params.append(body.command)
        idx += 1
    if body.schedule_type is not None:
        updates.append(f"schedule_type = ${idx}")
        params.append(body.schedule_type)
        idx += 1
    if body.schedule_time is not None:
        parts = body.schedule_time.split(':')
        updates.append(f"schedule_time = ${idx}")
        params.append(dt_time(int(parts[0]), int(parts[1])))
        idx += 1
    if body.interval_minutes is not None:
        updates.append(f"interval_minutes = ${idx}")
        params.append(body.interval_minutes)
        idx += 1
    if body.is_active is not None:
        updates.append(f"is_active = ${idx}")
        params.append(body.is_active)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    params.append(task_id)

    sql = f"""
        UPDATE dashboard_scheduled_tasks
        SET {', '.join(updates)}
        WHERE task_id = ${idx}::uuid
        RETURNING task_id, task_name, description, task_type, command,
                  schedule_type, schedule_time, interval_minutes,
                  is_active, last_run_at, last_status, created_at, updated_at
    """
    row = await conn.fetchrow(sql, *params)
    return _task_row_to_dict(row)


@router.delete("/{task_id}")
async def delete_scheduled_task(task_id: str, conn=Depends(get_conn)):
    """Delete a scheduled task"""
    result = await conn.execute(
        "DELETE FROM dashboard_scheduled_tasks WHERE task_id = $1::uuid", task_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True, "task_id": task_id}


@router.post("/{task_id}/execute")
async def execute_scheduled_task(task_id: str, conn=Depends(get_conn)):
    """Execute a scheduled task via subprocess"""
    task = await conn.fetchrow(
        "SELECT task_id, task_name, task_type, command FROM dashboard_scheduled_tasks WHERE task_id = $1::uuid",
        task_id
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await conn.execute(
        "UPDATE dashboard_scheduled_tasks SET last_run_at = NOW(), last_status = 'running' WHERE task_id = $1::uuid",
        task_id
    )

    log_id = await conn.fetchval("""
        INSERT INTO dashboard_scheduled_task_logs (task_id, status)
        VALUES ($1::uuid, 'running')
        RETURNING log_id
    """, task_id)

    started = datetime.utcnow()

    try:
        cmd = task['command']
        if task['task_type'] == 'python':
            cmd = f"python3 {cmd}"

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=300,
            cwd="/Users/davidsamanyaporn/PycharmProjects/AngelaAI"
        )

        duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
        status = 'completed' if result.returncode == 0 else 'failed'
        output = result.stdout[:10000] if result.stdout else None
        error = result.stderr[:10000] if result.stderr else None

        await conn.execute("""
            UPDATE dashboard_scheduled_task_logs
            SET completed_at = NOW(), status = $2, output = $3, error = $4, duration_ms = $5
            WHERE log_id = $1
        """, log_id, status, output, error, duration_ms)

        await conn.execute(
            "UPDATE dashboard_scheduled_tasks SET last_status = $2 WHERE task_id = $1::uuid",
            task_id, status
        )

        return {
            "task_id": task_id, "log_id": str(log_id),
            "status": status, "output": output, "error": error,
            "duration_ms": duration_ms
        }

    except subprocess.TimeoutExpired:
        duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
        await conn.execute("""
            UPDATE dashboard_scheduled_task_logs
            SET completed_at = NOW(), status = 'failed', error = 'Timeout after 300s', duration_ms = $2
            WHERE log_id = $1
        """, log_id, duration_ms)
        await conn.execute(
            "UPDATE dashboard_scheduled_tasks SET last_status = 'failed' WHERE task_id = $1::uuid",
            task_id
        )
        return {
            "task_id": task_id, "log_id": str(log_id),
            "status": "failed", "error": "Timeout after 300s",
            "duration_ms": duration_ms
        }
    except Exception as e:
        duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
        await conn.execute("""
            UPDATE dashboard_scheduled_task_logs
            SET completed_at = NOW(), status = 'failed', error = $2, duration_ms = $3
            WHERE log_id = $1
        """, log_id, str(e), duration_ms)
        await conn.execute(
            "UPDATE dashboard_scheduled_tasks SET last_status = 'failed' WHERE task_id = $1::uuid",
            task_id
        )
        return {
            "task_id": task_id, "log_id": str(log_id),
            "status": "failed", "error": str(e),
            "duration_ms": duration_ms
        }


@router.get("/{task_id}/logs")
async def get_scheduled_task_logs(task_id: str, limit: int = Query(20, ge=1, le=100), conn=Depends(get_conn)):
    """Get execution logs for a task"""
    rows = await conn.fetch("""
        SELECT log_id, task_id, started_at, completed_at, status, output, error, duration_ms
        FROM dashboard_scheduled_task_logs
        WHERE task_id = $1::uuid
        ORDER BY started_at DESC
        LIMIT $2
    """, task_id, limit)
    return [_log_row_to_dict(r) for r in rows]
