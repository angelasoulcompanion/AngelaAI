"""Meeting notes endpoints (CRUD + sync)."""
import re
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from db import get_pool
from helpers.calendar_helpers import calendar_create, calendar_update, calendar_delete
from helpers.things3_helpers import things3_complete_todo, things3_create_todo
from schemas import MeetingCreate, MeetingUpdate

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
| Test Case | Status | Notes |
|-----------|--------|-------|
| | | |

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
| Action | Owner | Due Date |
|--------|-------|----------|
| | | |

## 📝 Notes
-
"""
}


@router.get("/")
async def get_meetings(limit: int = Query(50, ge=1, le=200)):
    """Fetch all meeting notes ordered by date desc"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                mn.meeting_id::text, mn.things3_uuid, mn.title,
                mn.meeting_type, mn.location,
                mn.meeting_date, mn.time_range,
                mn.attendees, mn.agenda, mn.key_points,
                mn.decisions_made, mn.issues_risks, mn.next_steps,
                mn.personal_notes, mn.raw_notes, mn.project_name,
                mn.things3_status, mn.morning_notes,
                mn.afternoon_notes, mn.site_observations,
                mn.synced_at, mn.created_at, mn.updated_at,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE meeting_id = mn.meeting_id) as total_actions,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE meeting_id = mn.meeting_id AND is_completed = TRUE) as completed_actions
            FROM meeting_notes mn
            ORDER BY mn.meeting_date DESC NULLS LAST, mn.created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@router.get("/stats")
async def get_meeting_stats():
    """Fetch meeting statistics"""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM meeting_notes) as total_meetings,
                (SELECT COUNT(*) FROM meeting_notes
                 WHERE meeting_date >= date_trunc('month', CURRENT_DATE)) as this_month,
                (SELECT COUNT(*) FROM meeting_notes
                 WHERE meeting_date >= CURRENT_DATE) as upcoming,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE is_completed = FALSE) as open_actions,
                (SELECT COUNT(*) FROM meeting_action_items) as total_actions,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE is_completed = TRUE) as completed_actions,
                (SELECT COUNT(*) FROM meeting_notes
                 WHERE meeting_type = 'site_visit') as site_visits
        """)
        total = row['total_actions'] or 0
        completed = row['completed_actions'] or 0
        return {
            "total_meetings": row['total_meetings'] or 0,
            "this_month": row['this_month'] or 0,
            "upcoming": row['upcoming'] or 0,
            "open_actions": row['open_actions'] or 0,
            "total_actions": total,
            "completed_actions": completed,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0.0,
            "site_visits": row['site_visits'] or 0,
        }


@router.get("/action-items")
async def get_open_action_items():
    """Fetch all open (incomplete) action items across meetings"""
    pool = get_pool()
    async with pool.acquire() as conn:
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


@router.get("/upcoming")
async def get_upcoming_meetings(limit: int = Query(5, ge=1, le=50)):
    """Fetch upcoming meetings (nearest first, default 5)"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                mn.meeting_id::text, mn.things3_uuid, mn.title,
                mn.meeting_type, mn.location,
                mn.meeting_date, mn.time_range,
                mn.attendees, mn.agenda, mn.key_points,
                mn.decisions_made, mn.issues_risks, mn.next_steps,
                mn.personal_notes, mn.raw_notes, mn.project_name,
                mn.things3_status, mn.morning_notes,
                mn.afternoon_notes, mn.site_observations,
                mn.synced_at, mn.created_at, mn.updated_at,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE meeting_id = mn.meeting_id) as total_actions,
                (SELECT COUNT(*) FROM meeting_action_items
                 WHERE meeting_id = mn.meeting_id AND is_completed = TRUE) as completed_actions
            FROM meeting_notes mn
            WHERE mn.meeting_date >= CURRENT_DATE
              AND mn.things3_status = 'open'
            ORDER BY mn.meeting_date ASC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


@router.get("/project-breakdown")
async def get_meeting_project_breakdown():
    """Fetch meeting counts grouped by project"""
    pool = get_pool()
    async with pool.acquire() as conn:
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
async def get_meeting_locations():
    """Get unique locations from past meetings for autocomplete"""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT DISTINCT location
            FROM meeting_notes
            WHERE location IS NOT NULL AND location != ''
            ORDER BY location
        """)
        return [r['location'] for r in rows]


@router.post("/create")
async def create_meeting(body: MeetingCreate):
    """Create a new meeting via Things3 and Google Calendar"""
    # Validate date
    try:
        meeting_dt = datetime.strptime(body.meeting_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

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
        pool = get_pool()
        async with pool.acquire() as conn:
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
async def update_meeting(meeting_id: str, body: MeetingUpdate):
    """Update an existing meeting"""
    # Build dynamic UPDATE query
    updates = []
    params = []
    param_idx = 1

    if body.title is not None:
        updates.append(f"title = ${param_idx}")
        params.append(body.title)
        param_idx += 1

    if body.location is not None:
        updates.append(f"location = ${param_idx}")
        params.append(body.location)
        param_idx += 1

    if body.meeting_date is not None:
        try:
            meeting_dt = datetime.strptime(body.meeting_date, "%Y-%m-%d").date()
            updates.append(f"meeting_date = ${param_idx}")
            params.append(meeting_dt)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    if body.start_time is not None and body.end_time is not None:
        time_range = f"{body.start_time}-{body.end_time}"
        updates.append(f"time_range = ${param_idx}")
        params.append(time_range)
        param_idx += 1

    if body.meeting_type is not None:
        db_type = "site_visit" if body.meeting_type == "site_visit" else "meeting"
        updates.append(f"meeting_type = ${param_idx}")
        params.append(db_type)
        param_idx += 1

    if body.attendees is not None:
        updates.append(f"attendees = ${param_idx}")
        params.append(body.attendees)
        param_idx += 1

    if body.project_name is not None:
        updates.append(f"project_name = ${param_idx}")
        params.append(body.project_name if body.project_name else None)
        param_idx += 1

    if body.things3_status is not None:
        updates.append(f"things3_status = ${param_idx}")
        params.append(body.things3_status)
        param_idx += 1

    if body.notes is not None:
        updates.append(f"raw_notes = ${param_idx}")
        params.append(body.notes)
        param_idx += 1

    if not updates:
        return {"success": False, "error": "No fields to update"}

    updates.append("updated_at = NOW()")

    # Add meeting_id as last parameter
    params.append(meeting_id)

    query = f"""
        UPDATE meeting_notes
        SET {', '.join(updates)}
        WHERE meeting_id = ${param_idx}::uuid
        RETURNING meeting_id
    """

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
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

            # --- Sync to Things3 (complete old + create new) ---
            try:
                old_things3_search = f"📅 {old_meeting['title']}"
                things3_complete_todo(old_things3_search)

                new_title = body.title or old_meeting['title']
                new_location = body.location or old_meeting['location']
                new_time = (f"{body.start_time}-{body.end_time}"
                            if body.start_time and body.end_time
                            else old_meeting['time_range'])
                new_date = body.meeting_date or str(old_meeting['meeting_date'])

                things3_title = f"📅 {new_title} @{new_location} ({new_time})"
                things3_create_todo(things3_title, "", new_date)
            except Exception as e:
                print(f"⚠️ Things3 sync failed: {e}")

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
async def delete_meeting(meeting_id: str):
    """Delete a meeting and sync to Things3 + Google Calendar"""
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
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
async def sync_meetings_external():
    """Sync upcoming meetings to Things3 + Google Calendar."""
    results = {"synced": [], "failed": [], "already_synced": 0}

    try:
        pool = get_pool()
        async with pool.acquire() as conn:
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
async def get_meeting_detail(meeting_id: str):
    """Fetch single meeting with action items"""
    pool = get_pool()
    async with pool.acquire() as conn:
        meeting = await conn.fetchrow("""
            SELECT
                meeting_id::text, things3_uuid, title,
                meeting_type, location, meeting_date, time_range,
                attendees, agenda, key_points,
                decisions_made, issues_risks, next_steps,
                personal_notes, raw_notes, project_name,
                things3_status, morning_notes,
                afternoon_notes, site_observations,
                synced_at, created_at, updated_at
            FROM meeting_notes
            WHERE meeting_id = $1::uuid
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
