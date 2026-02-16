"""Meeting notes endpoints (CRUD + sync)."""
import re
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from db import get_conn, get_pool
from helpers import DynamicUpdate, parse_date
from helpers.calendar_helpers import calendar_create, calendar_update, calendar_delete
from helpers.things3_helpers import things3_complete_todo, things3_create_todo
from schemas import ActionItemCreate, ActionItemUpdate, MeetingCreate, MeetingUpdate

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

# Meeting Type Templates
MEETING_TEMPLATES = {
    "standard": """## 📋 วาระการประชุม
-

## 👥 ผู้เข้าร่วม
-

## 📝 Key Points
-

## ✅ Next Steps
-
""",
    "site_visit": """## 🌅 Morning Notes
-

## 🌆 Afternoon Notes
-

## 👀 Site Observations
-

## 📝 Key Findings
-

## ✅ Next Steps
-
""",
    "testing": """## 🎯 Test Scope
-

## 📊 Test Results
- [ ]

## 🐛 Issues Found
-

## ✅ Next Steps
-
""",
    "bod": """## 📋 Formal Agenda
1.

## 📜 Resolutions
-

## ✅ Action Items
- [ ]

## 📝 Notes
-
"""
}

# Shared column list for meeting queries (used in get_meetings, get_upcoming, get_detail)
_MEETING_COLUMNS = """mn.meeting_id::text, mn.things3_uuid, mn.title,
    mn.meeting_type, mn.location,
    mn.meeting_date, mn.time_range,
    mn.attendees, mn.agenda, mn.key_points,
    mn.decisions_made, mn.issues_risks, mn.next_steps,
    mn.personal_notes, mn.raw_notes, mn.project_name,
    mn.things3_status, mn.morning_notes,
    mn.afternoon_notes, mn.site_observations,
    mn.synced_at, mn.created_at, mn.updated_at"""

_MEETING_ACTION_COUNTS = """(SELECT COUNT(*) FROM meeting_action_items
     WHERE meeting_id = mn.meeting_id) as total_actions,
    (SELECT COUNT(*) FROM meeting_action_items
     WHERE meeting_id = mn.meeting_id AND is_completed = TRUE) as completed_actions"""


@router.get("/")
async def get_meetings(limit: int = Query(50, ge=1, le=200), conn=Depends(get_conn)):
    """Fetch all meeting notes ordered by date desc"""
    rows = await conn.fetch(f"""
        SELECT {_MEETING_COLUMNS}, {_MEETING_ACTION_COUNTS}
        FROM meeting_notes mn
        ORDER BY mn.meeting_date DESC NULLS LAST, mn.created_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/stats")
async def get_meeting_stats(conn=Depends(get_conn)):
    """Fetch meeting statistics"""
    row = await conn.fetchrow("""
        SELECT
            (SELECT COUNT(*) FROM meeting_notes) as total_meetings,
            (SELECT COUNT(*) FROM meeting_notes
             WHERE meeting_date >= date_trunc('month', CURRENT_DATE)) as this_month,
            (SELECT COUNT(*) FROM meeting_notes
             WHERE meeting_date >= CURRENT_DATE) as upcoming,
            (SELECT COUNT(*) FROM meeting_notes
             WHERE things3_status = 'open') as open_meetings,
            (SELECT COUNT(*) FROM meeting_notes
             WHERE things3_status = 'completed') as completed_meetings,
            (SELECT COUNT(*) FROM meeting_notes
             WHERE meeting_type = 'site_visit') as site_visits
    """)
    total = row['total_meetings'] or 0
    completed = row['completed_meetings'] or 0
    return {
        "total_meetings": total,
        "this_month": row['this_month'] or 0,
        "upcoming": row['upcoming'] or 0,
        "open_meetings": row['open_meetings'] or 0,
        "completed_meetings": completed,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0.0,
        "site_visits": row['site_visits'] or 0,
    }


@router.get("/action-items")
async def get_open_action_items(conn=Depends(get_conn)):
    """Fetch all open (incomplete) action items across meetings"""
    rows = await conn.fetch("""
        SELECT
            ai.action_id::text, ai.meeting_id::text,
            ai.action_text, ai.assignee, ai.due_date,
            ai.is_completed, ai.completed_at, ai.priority,
            ai.created_at,
            mn.title as meeting_title,
            mn.meeting_date,
            mn.project_name
        FROM meeting_action_items ai
        JOIN meeting_notes mn ON ai.meeting_id = mn.meeting_id
        WHERE ai.is_completed = FALSE
        ORDER BY ai.priority ASC, mn.meeting_date DESC NULLS LAST
    """)
    return [dict(r) for r in rows]


@router.post("/action-items")
async def create_action_item(body: ActionItemCreate, conn=Depends(get_conn)):
    """Create a new action item for a meeting"""
    action_id = str(uuid.uuid4())
    due = parse_date(body.due_date, "due_date") if body.due_date else None

    await conn.execute("""
        INSERT INTO meeting_action_items
            (action_id, meeting_id, action_text, assignee, due_date, priority, is_completed, created_at)
        VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, FALSE, NOW())
    """, action_id, body.meeting_id, body.action_text, body.assignee, due, body.priority)

    return {"success": True, "action_id": action_id}


@router.put("/action-items/{action_id}")
async def update_action_item(action_id: str, body: ActionItemUpdate, conn=Depends(get_conn)):
    """Update an existing action item"""
    b = DynamicUpdate()

    if body.action_text is not None:
        b.add("action_text", body.action_text)
    if body.assignee is not None:
        b.add("assignee", body.assignee if body.assignee else None)
    if body.due_date is not None:
        b.add("due_date", parse_date(body.due_date, "due_date") if body.due_date else None)
    if body.priority is not None:
        b.add("priority", body.priority)
    if body.is_completed is not None:
        b.add("is_completed", body.is_completed)
        b.add_literal("completed_at = NOW()" if body.is_completed else "completed_at = NULL")

    if not b.has_updates:
        return {"success": False, "error": "No fields to update"}

    query, params = b.build("meeting_action_items", "action_id", action_id,
                            cast="::uuid", returning="action_id::text, is_completed")

    row = await conn.fetchrow(query, *params)
    if not row:
        return {"success": False, "error": "Action item not found"}
    return {"success": True, "action_id": row['action_id'], "is_completed": row['is_completed']}


@router.put("/action-items/{action_id}/toggle")
async def toggle_action_item(action_id: str, conn=Depends(get_conn)):
    """Toggle action item completion status"""
    row = await conn.fetchrow("""
        UPDATE meeting_action_items
        SET is_completed = NOT is_completed,
            completed_at = CASE WHEN is_completed THEN NULL ELSE NOW() END
        WHERE action_id = $1::uuid
        RETURNING action_id::text, is_completed
    """, action_id)

    if not row:
        raise HTTPException(status_code=404, detail="Action item not found")

    return {"success": True, "action_id": row['action_id'], "is_completed": row['is_completed']}


@router.delete("/action-items/{action_id}")
async def delete_action_item(action_id: str, conn=Depends(get_conn)):
    """Delete an action item"""
    result = await conn.execute("""
        DELETE FROM meeting_action_items
        WHERE action_id = $1::uuid
    """, action_id)

    if "DELETE 1" in result:
        return {"success": True, "deleted": True}
    return {"success": False, "error": "Action item not found"}


@router.get("/{meeting_id}/action-items")
async def get_meeting_action_items(meeting_id: str, conn=Depends(get_conn)):
    """Fetch action items for a specific meeting"""
    rows = await conn.fetch("""
        SELECT
            ai.action_id::text, ai.meeting_id::text,
            ai.action_text, ai.assignee, ai.due_date,
            ai.is_completed, ai.completed_at, ai.priority,
            ai.created_at,
            mn.title as meeting_title,
            mn.meeting_date,
            mn.project_name
        FROM meeting_action_items ai
        JOIN meeting_notes mn ON ai.meeting_id = mn.meeting_id
        WHERE ai.meeting_id = $1::uuid
        ORDER BY ai.is_completed ASC, ai.priority ASC
    """, meeting_id)
    return [dict(r) for r in rows]


@router.get("/upcoming")
async def get_upcoming_meetings(limit: int = Query(5, ge=1, le=50), conn=Depends(get_conn)):
    """Fetch upcoming meetings (nearest first, default 5)"""
    rows = await conn.fetch(f"""
        SELECT {_MEETING_COLUMNS}, {_MEETING_ACTION_COUNTS}
        FROM meeting_notes mn
        WHERE mn.meeting_date >= CURRENT_DATE
          AND mn.things3_status = 'open'
        ORDER BY mn.meeting_date ASC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/project-breakdown")
async def get_meeting_project_breakdown(conn=Depends(get_conn)):
    """Fetch meeting counts grouped by project"""
    rows = await conn.fetch("""
        SELECT
            COALESCE(NULLIF(project_name, ''), 'No Project') as project_name,
            COUNT(*) as meeting_count,
            COUNT(*) FILTER (WHERE things3_status = 'open') as open_count,
            COUNT(*) FILTER (WHERE things3_status = 'completed') as completed_count,
            COUNT(*) FILTER (WHERE meeting_type = 'site_visit') as site_visit_count
        FROM meeting_notes
        GROUP BY COALESCE(NULLIF(project_name, ''), 'No Project')
        ORDER BY meeting_count DESC
    """)
    return [dict(r) for r in rows]


@router.get("/locations")
async def get_meeting_locations(conn=Depends(get_conn)):
    """Get unique locations from past meetings for autocomplete"""
    rows = await conn.fetch("""
        SELECT DISTINCT location
        FROM meeting_notes
        WHERE location IS NOT NULL AND location != ''
        ORDER BY location
    """)
    return [r['location'] for r in rows]


@router.post("/create")
async def create_meeting(body: MeetingCreate, conn=Depends(get_conn)):
    """Create a new meeting via Things3 and Google Calendar"""
    meeting_dt = parse_date(body.meeting_date, "meeting_date")

    # Validate time
    try:
        start_parts = body.start_time.split(":")
        end_parts = body.end_time.split(":")
        int(start_parts[0]); int(start_parts[1])
        int(end_parts[0]); int(end_parts[1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

    # Generate Things3 title with emoji
    time_str = f"{body.start_time}-{body.end_time}"
    things3_title = f"📅 {body.title} @{body.location} ({time_str})"

    # Get template notes
    template_notes = MEETING_TEMPLATES.get(body.meeting_type, MEETING_TEMPLATES["standard"])

    # Add header with details
    header = f"""# {body.title}
📅 Date: {body.meeting_date}
🕐 Time: {time_str}
📍 Location: {body.location}
"""
    if body.project_name:
        header += f"📁 Project: {body.project_name}\n"
    if body.attendees:
        header += f"👥 Attendees: {', '.join(body.attendees)}\n"

    full_notes = header + "\n---\n\n" + template_notes

    # Generate meeting ID
    meeting_id = str(uuid.uuid4())

    # --- Sync to Things3 via x-callback-url ---
    try:
        things3_create_todo(things3_title, full_notes, body.meeting_date, body.project_name)
    except Exception as e:
        print(f"⚠️ Things3 call failed: {e}")

    # --- Sync to Google Calendar ---
    calendar_event_id = None
    calendar_success = False
    try:
        calendar_event_id = calendar_create(
            title=body.title,
            date_str=body.meeting_date,
            start_time=body.start_time,
            end_time=body.end_time,
            location=body.location
        )
        calendar_success = calendar_event_id is not None
    except Exception as e:
        print(f"⚠️ Calendar creation failed: {e}")

    # --- Insert into database ---
    try:
        db_meeting_type = "site_visit" if body.meeting_type == "site_visit" else "meeting"

        await conn.execute("""
            INSERT INTO meeting_notes
                (meeting_id, things3_uuid, title, meeting_type, location,
                 meeting_date, time_range, attendees, project_name,
                 things3_status, raw_notes, calendar_event_id,
                 created_at, updated_at, synced_at)
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, 'open', $10, $11, NOW(), NOW(), NOW())
        """,
            meeting_id,
            meeting_id,
            body.title,
            db_meeting_type,
            body.location,
            meeting_dt,
            time_str,
            body.attendees,
            body.project_name,
            full_notes,
            calendar_event_id
        )
    except Exception as e:
        print(f"⚠️ Database insert failed: {e}")
        return {
            "success": False,
            "error": f"Database insert failed: {str(e)}"
        }

    return {
        "success": True,
        "meeting_id": meeting_id,
        "things3_title": things3_title,
        "calendar_created": calendar_success
    }


@router.put("/{meeting_id}")
async def update_meeting(meeting_id: str, body: MeetingUpdate, conn=Depends(get_conn)):
    """Update an existing meeting"""
    b = DynamicUpdate()

    if body.title is not None:
        b.add("title", body.title)
    if body.location is not None:
        b.add("location", body.location)
    if body.meeting_date is not None:
        b.add("meeting_date", parse_date(body.meeting_date, "meeting_date"))
    if body.start_time is not None and body.end_time is not None:
        b.add("time_range", f"{body.start_time}-{body.end_time}")
    if body.meeting_type is not None:
        b.add("meeting_type", "site_visit" if body.meeting_type == "site_visit" else "meeting")
    if body.attendees is not None:
        b.add("attendees", body.attendees)
    if body.project_name is not None:
        b.add("project_name", body.project_name if body.project_name else None)
    if body.things3_status is not None:
        b.add("things3_status", body.things3_status)
    if body.notes is not None:
        b.add("raw_notes", body.notes)

    # Structured note fields
    for field_name, body_attr in [
        ("agenda", body.agenda), ("key_points", body.key_points),
        ("decisions_made", body.decisions_made), ("issues_risks", body.issues_risks),
        ("next_steps", body.next_steps), ("personal_notes", body.personal_notes),
        ("morning_notes", body.morning_notes), ("afternoon_notes", body.afternoon_notes),
        ("site_observations", body.site_observations),
    ]:
        if body_attr is not None:
            b.add(field_name, body_attr if body_attr else None)

    if not b.has_updates:
        return {"success": False, "error": "No fields to update"}

    b.add_literal("updated_at = NOW()")
    query, params = b.build("meeting_notes", "meeting_id", meeting_id,
                            cast="::uuid", returning="meeting_id")

    try:
        # Fetch old meeting data before updating (for sync)
        old_meeting = await conn.fetchrow("""
            SELECT title, location, time_range, meeting_date, calendar_event_id
            FROM meeting_notes WHERE meeting_id = $1::uuid
        """, meeting_id)

        if not old_meeting:
            return {"success": False, "error": "Meeting not found"}

        result = await conn.fetchrow(query, *params)
        if not result:
            return {"success": False, "error": "Update failed"}

        # --- Sync to Things3 (only when title/location/time/date/status actually change) ---
        old_title = old_meeting['title']
        old_location = old_meeting['location'] or ''
        old_time = old_meeting['time_range'] or ''
        old_date = str(old_meeting['meeting_date']) if old_meeting['meeting_date'] else ''
        new_time_str = (f"{body.start_time}-{body.end_time}"
                       if body.start_time and body.end_time else None)

        things3_changed = (
            (body.title and body.title != old_title)
            or (body.location and body.location != old_location)
            or (new_time_str and new_time_str != old_time)
            or (body.meeting_date and body.meeting_date != old_date)
        )

        if body.things3_status == "completed":
            try:
                things3_complete_todo(f"📅 {old_title}")
            except Exception as e:
                print(f"⚠️ Things3 complete failed: {e}")
        elif things3_changed:
            try:
                # Title/location/time/date changed — complete old + create new
                things3_complete_todo(f"📅 {old_title}")

                new_title = body.title or old_title
                new_location = body.location or old_location
                new_time = new_time_str or old_time
                new_date = body.meeting_date or old_date

                things3_title = f"📅 {new_title} @{new_location} ({new_time})"
                things3_create_todo(things3_title, "", new_date)
            except Exception as e:
                print(f"⚠️ Things3 sync failed: {e}")
        # else: only notes/structured fields changed — skip Things3

        # --- Sync to Google Calendar ---
        cal_id = old_meeting['calendar_event_id']
        if cal_id:
            try:
                cal_kwargs: dict[str, str] = {}
                if body.title:
                    cal_kwargs['summary'] = body.title
                if body.location:
                    cal_kwargs['location'] = body.location
                if body.meeting_date:
                    cal_kwargs['date'] = body.meeting_date
                if body.start_time:
                    cal_kwargs['start_time'] = body.start_time
                if body.end_time:
                    cal_kwargs['end_time'] = body.end_time
                if cal_kwargs:
                    if ('start_time' in cal_kwargs or 'end_time' in cal_kwargs) and 'date' not in cal_kwargs:
                        cal_kwargs['date'] = str(old_meeting['meeting_date'])
                    calendar_update(cal_id, **cal_kwargs)
            except Exception as e:
                print(f"⚠️ Calendar update failed: {e}")

        return {"success": True, "meeting_id": meeting_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, conn=Depends(get_conn)):
    """Delete a meeting and sync to Things3 + Google Calendar"""
    try:
        meeting = await conn.fetchrow("""
            SELECT title, calendar_event_id
            FROM meeting_notes WHERE meeting_id = $1::uuid
        """, meeting_id)

        if meeting:
            try:
                things3_complete_todo(f"📅 {meeting['title']}")
            except Exception as e:
                print(f"⚠️ Things3 complete failed: {e}")

            if meeting['calendar_event_id']:
                try:
                    calendar_delete(meeting['calendar_event_id'])
                except Exception as e:
                    print(f"⚠️ Calendar delete failed: {e}")

        await conn.execute("""
            DELETE FROM meeting_action_items
            WHERE meeting_id = $1::uuid
        """, meeting_id)

        result = await conn.execute("""
            DELETE FROM meeting_notes
            WHERE meeting_id = $1::uuid
        """, meeting_id)

        if "DELETE 1" in result:
            return {"success": True, "deleted": True}
        else:
            return {"success": False, "error": "Meeting not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/sync-external")
async def sync_meetings_external(conn=Depends(get_conn)):
    """Sync upcoming meetings to Things3 + Google Calendar."""
    results = {"synced": [], "failed": [], "already_synced": 0}

    try:
        rows = await conn.fetch("""
            SELECT meeting_id::text, title, location, meeting_date,
                   time_range, calendar_event_id, project_name
            FROM meeting_notes
            WHERE meeting_date >= CURRENT_DATE
              AND things3_status = 'open'
            ORDER BY meeting_date ASC
        """)

        for row in rows:
            mid = row['meeting_id']
            title = row['title']
            location = row['location'] or ''
            date_str = str(row['meeting_date'])
            time_range = row['time_range'] or ''

            times = re.findall(r'\d{1,2}:\d{2}', time_range)
            start_time = times[0] if len(times) >= 1 else "09:00"
            end_time = times[1] if len(times) >= 2 else "10:00"
            if end_time <= start_time:
                h = int(start_time.split(':')[0])
                end_time = f"{min(h + 1, 23):02d}:{start_time.split(':')[1]}"

            entry = {"meeting_id": mid, "title": title, "date": date_str,
                     "things3": False, "calendar": False}

            try:
                t3_title = f"📅 {title} @{location} ({time_range})"
                things3_create_todo(t3_title, "", date_str, row['project_name'])
                entry["things3"] = True
            except Exception as e:
                entry["things3_error"] = str(e)

            if row['calendar_event_id']:
                results["already_synced"] += 1
                entry["calendar"] = True
                entry["calendar_note"] = "already exists"
            else:
                try:
                    event_id = calendar_create(
                        title=title, date_str=date_str,
                        start_time=start_time, end_time=end_time,
                        location=location
                    )
                    if event_id:
                        await conn.execute("""
                            UPDATE meeting_notes
                            SET calendar_event_id = $1, updated_at = NOW()
                            WHERE meeting_id = $2::uuid
                        """, event_id, mid)
                        entry["calendar"] = True
                except Exception as e:
                    entry["calendar_error"] = str(e)

            if entry["things3"] or entry["calendar"]:
                results["synced"].append(entry)
            else:
                results["failed"].append(entry)

        results["total"] = len(rows)
        results["success"] = True
        return results
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/{meeting_id}")
async def get_meeting_detail(meeting_id: str, conn=Depends(get_conn)):
    """Fetch single meeting with action items"""
    meeting = await conn.fetchrow(f"""
        SELECT {_MEETING_COLUMNS.replace('mn.', '')}
        FROM meeting_notes mn
        WHERE mn.meeting_id = $1::uuid
    """, meeting_id)

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    result = dict(meeting)

    actions = await conn.fetch("""
        SELECT
            action_id::text, meeting_id::text,
            action_text, assignee, due_date,
            is_completed, completed_at, priority, created_at
        FROM meeting_action_items
        WHERE meeting_id = $1::uuid
        ORDER BY is_completed ASC, priority ASC
    """, meeting_id)

    result['action_items'] = [dict(a) for a in actions]
    return result
