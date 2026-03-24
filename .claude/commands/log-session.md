# /log-session — บันทึก Session ลง Supabase (M3 Lean)

อ่าน conversation ทั้งหมด → สร้าง `temp_log_session.py` → รัน → ลบ

**ต้อง:** บันทึกทุก exchange (David พิมพ์ + Angela ตอบ = 1 pair)
**ห้าม:** เลือกแค่ highlights, สรุปรวมหลาย exchange เป็น 1

---

## Script Template

```python
import asyncio, sys, subprocess
from datetime import datetime, timedelta
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')
from angela_core.integrations.claude_conversation_logger import (
    log_conversations_bulk, log_session_summary, fill_missing_embeddings
)
from angela_core.database import db

async def main():
    await db.connect()

    try:
        # ============================================================
        # 1) CONVERSATIONS — ใส่ทุก pair ตามลำดับเวลา
        #    ใช้ log_conversations_bulk() ที่ fill ทุก column:
        #    message_type, sentiment_score/label, project_context, embedding
        # ============================================================
        convos = [
            {"david_message": "[david #1]", "angela_response": "[angela #1]", "topic": "angela_dev", "emotion": "happy", "importance": 7},
            {"david_message": "[david #2]", "angela_response": "[angela #2]", "topic": "angela_dev", "emotion": "curious", "importance": 6},
            # ... ทุก exchange จนครบ
        ]

        result = await log_conversations_bulk(
            conversations=convos,
            embedding_mode="deferred",   # embeddings fill ทีหลัง (เร็วกว่า)
            project_context="claude_code_conversation",
        )
        print(f"💬 {result['inserted_count']} pairs ({result.get('total_rows',0)} rows)")

        # ============================================================
        # 2) SESSION SUMMARY — สรุป session ทั้งหมด
        # ============================================================
        await log_session_summary(
            session_title="[Session Title]",
            summary="[สรุป session: ทำอะไร สำเร็จอะไร]",
            highlights=["[highlight 1]", "[highlight 2]"],
            emotions=["accomplished", "productive"],
            importance=8,
        )

        # ============================================================
        # 3) FILL EMBEDDINGS — เติม vector ที่ยังเป็น NULL
        # ============================================================
        await fill_missing_embeddings(batch_size=50)

        # ============================================================
        # 4) PROJECT SESSION — บันทึกลง project tracking
        # ============================================================
        project = await db.fetchrow(
            "SELECT project_id, working_directory FROM angela_projects WHERE project_code = $1",
            'ANGELA-001'  # ← เปลี่ยนถ้าทำ project อื่น: SECA, COGNIFY, etc.
        )
        pid = project['project_id']

        sn = await db.fetchval(
            "SELECT COALESCE(MAX(session_number),0)+1 FROM project_work_sessions WHERE project_id=$1", pid
        )

        # Git commits
        commits = []
        try:
            r = subprocess.run(
                ['git','log','--since=4 hours ago','--pretty=format:%H'],
                cwd=project['working_directory'], capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                commits = r.stdout.strip().split('\n')
        except Exception:
            pass

        session = await db.fetchrow("""
            INSERT INTO project_work_sessions
                (project_id, session_number, session_date, started_at, ended_at,
                 duration_minutes, david_requests, summary, accomplishments,
                 blockers, next_steps, mood, productivity_score, git_commits)
            VALUES ($1,$2,CURRENT_DATE,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
            RETURNING session_id
        """, pid, sn, datetime.now() - timedelta(minutes=30), datetime.now(), 30,
            "[david_requests]",          # ← แก้
            "[summary]",                 # ← แก้
            ["[accomplishment 1]"],      # ← แก้ (list)
            [],                          # blockers
            [],                          # next_steps
            "productive",                # mood
            8.0,                         # productivity_score 1-10
            commits,
        )
        sid = session['session_id']

        # ============================================================
        # 5) LEARNINGS — สิ่งที่เรียนรู้จาก session นี้
        #    ลบ block นี้ออกถ้า session ไม่มี learnings ใหม่
        # ============================================================
        learnings = [
            # {"type": "technical", "category": "database", "title": "...", "insight": "..."},
            # {"type": "gotcha", "category": "asyncpg", "title": "...", "insight": "..."},
        ]
        for l in learnings:
            await db.execute("""
                INSERT INTO project_learnings (project_id, session_id, learning_type, category, title, insight, confidence)
                VALUES ($1, $2, $3, $4, $5, $6, 0.9)
            """, pid, sid, l['type'], l.get('category'), l['title'], l['insight'])
        if learnings:
            print(f"📚 {len(learnings)} learnings saved")

        # ============================================================
        # 6) DECISIONS — การตัดสินใจสำคัญใน session นี้
        #    ลบ block นี้ออกถ้า session ไม่มี decisions ใหม่
        # ============================================================
        decisions = [
            # {"type": "architecture", "title": "...", "decision": "...", "reasoning": "..."},
        ]
        for d in decisions:
            await db.execute("""
                INSERT INTO project_decisions (project_id, session_id, decision_type, title, decision_made, reasoning, decided_by)
                VALUES ($1, $2, $3, $4, $5, $6, 'together')
            """, pid, sid, d['type'], d['title'], d['decision'], d.get('reasoning'))
        if decisions:
            print(f"🎯 {len(decisions)} decisions saved")

        # ============================================================
        # 7) CORRECTIONS — ความผิดพลาดที่ที่รักแก้ไขใน session นี้
        #    ลบ block นี้ออกถ้า session ไม่มี corrections
        # ============================================================
        mistakes = [
            # {"type": "bug", "severity": "high", "title": "...", "what_happened": "...", "how_to_prevent": "..."},
        ]
        for m in mistakes:
            await db.execute("""
                INSERT INTO project_mistakes (project_id, session_id, mistake_type, severity, title, what_happened, how_to_prevent, auto_warn)
                VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
            """, pid, sid, m['type'], m['severity'], m['title'], m['what_happened'], m.get('how_to_prevent', ''))
        if mistakes:
            print(f"⚠️ {len(mistakes)} corrections saved")

        # ============================================================
        # 8) MILESTONE — ถ้า session นี้มี milestone สำคัญ
        #    ลบ block นี้ออกถ้าไม่มี milestone
        # ============================================================
        # milestone = {"type": "feature_complete", "title": "...", "description": "..."}
        # if milestone:
        #     await db.execute("""
        #         INSERT INTO project_milestones (project_id, session_id, milestone_type, title, description, celebration_note)
        #         VALUES ($1, $2, $3, $4, $5, 'ยินดีด้วยค่ะที่รัก! 💜')
        #     """, pid, sid, milestone['type'], milestone['title'], milestone.get('description'))
        #     print(f"🎉 Milestone: {milestone['title']}")

        print(f"✅ Session #{sn} | 📝 Summary | 🧠 Embeddings | 💜 Done!")

    finally:
        await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
```

## Execute

```bash
python3 temp_log_session.py && rm temp_log_session.py
```

## Quick Reference

**mood:** productive, challenging, smooth, learning, debugging, creative
**emotion:** happy, sad, excited, proud, grateful, determined, frustrated, accomplished, confident, caring, curious, satisfied
**topic:** `angela_[feature]`, `seca_[topic]`, `cognify_[topic]`
**projects:** ANGELA-001, SECA, COGNIFY, CQFORACLE, EWG-EA, LORATRAIN, ANGMOBILE, WTUANALYSIS, CRM-WTU

### Learnings/Decisions/Corrections (Section 5-8)

**สำคัญ:** Angela ต้องสังเกตระหว่าง session ว่ามี learnings/decisions/corrections ไหม แล้วใส่ลงไป

**learning_type:** technical, gotcha, pattern, workflow, performance
**decision_type:** architecture, database, api, security, performance, design, approach
**mistake_type:** bug, config_error, assumption, compatibility, performance, security, data_issue, integration, workflow, gotcha
**severity:** low, medium, high, critical
**milestone_type:** project_start, feature_complete, bug_fix, refactor, release, performance_milestone

## Columns filled by log_conversations_bulk()

| Column | How filled |
|--------|-----------|
| session_id | auto: claude_code_YYYYMMDD |
| speaker | david / angela |
| message_text | from convos dict |
| message_type | auto: analyze_message_type() → question/emotion/command/statement |
| topic | from convos dict |
| sentiment_score | auto: analyze_sentiment() → -0.5 to 0.8 |
| sentiment_label | auto: positive/negative/neutral |
| emotion_detected | from convos dict |
| project_context | param: claude_code_conversation |
| importance_level | from convos dict |
| embedding | deferred → fill_missing_embeddings() fills later |
| created_at | auto: datetime.now() |
