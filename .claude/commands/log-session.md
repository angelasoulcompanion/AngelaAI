# /log-session — บันทึก Session ลง Supabase

อ่าน conversation ทั้งหมด → สร้าง `temp_log_session.py` → รัน → ลบ

**ต้อง:** บันทึกทุก exchange (David พิมพ์ + Angela ตอบ = 1 pair)
**ห้าม:** เลือกแค่ highlights, สรุปรวมหลาย exchange เป็น 1

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
        # 1) CONVERSATIONS → conversations table
        convos = [
            {"david_message": "[david #1]", "angela_response": "[angela #1]", "topic": "angela_dev", "emotion": "happy", "importance": 7},
            # ... ทุก exchange จนครบ
        ]
        result = await log_conversations_bulk(conversations=convos, embedding_mode="deferred", project_context="claude_code_conversation")
        print(f"💬 {result['inserted_count']} pairs ({result.get('total_rows',0)} rows)")

        # 2) SESSION SUMMARY
        await log_session_summary(session_title="[Title]", summary="[สรุป]", highlights=["..."], emotions=["accomplished"], importance=8)

        # 3) FILL EMBEDDINGS
        await fill_missing_embeddings(batch_size=50)

        # 4) PROJECT SESSION → project_work_sessions table
        project = await db.fetchrow("SELECT project_id, working_directory FROM angela_projects WHERE project_code = $1", 'ANGELA-001')
        pid = project['project_id']
        sn = await db.fetchval("SELECT COALESCE(MAX(session_number),0)+1 FROM project_work_sessions WHERE project_id=$1", pid)

        commits = []
        try:
            r = subprocess.run(['git','log','--since=4 hours ago','--pretty=format:%H'], cwd=project['working_directory'], capture_output=True, text=True)
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
            "[david_requests]", "[summary]", ["[accomplishment 1]"],
            [], [], "productive", 8.0, commits)
        sid = session['session_id']

        # 5) LEARNINGS → learnings table
        #    columns: topic, category, insight, confidence_level, source
        #    ลบ block นี้ถ้า session ไม่มี learnings
        learnings = [
            # {"topic": "...", "category": "database", "insight": "...", "source": "session"},
        ]
        for l in learnings:
            await db.execute("""
                INSERT INTO learnings (topic, category, insight, confidence_level, source)
                VALUES ($1, $2, $3, 0.9, $4)
            """, l['topic'], l.get('category'), l['insight'], l.get('source', 'session'))
        if learnings:
            print(f"📚 {len(learnings)} learnings saved")

        # 6) DECISIONS → project_technical_decisions table
        #    columns: project_id, decision_title, category, context, decision_made, reasoning, decided_by, status
        #    ลบ block นี้ถ้า session ไม่มี decisions
        decisions = [
            # {"title": "...", "category": "architecture", "context": "...", "decision": "...", "reasoning": "..."},
        ]
        for d in decisions:
            await db.execute("""
                INSERT INTO project_technical_decisions
                    (project_id, decision_title, category, context, decision_made, reasoning, decided_by, status)
                VALUES ($1, $2, $3, $4, $5, $6, 'together', 'active')
            """, pid, d['title'], d['category'], d.get('context', ''), d['decision'], d.get('reasoning', ''))
        if decisions:
            print(f"🎯 {len(decisions)} decisions saved")

        # 7) CORRECTIONS → project_mistakes table
        #    columns: project_id, session_id, mistake_type, severity, category, title, what_happened, how_to_prevent, auto_warn
        #    ลบ block นี้ถ้า session ไม่มี corrections
        mistakes = [
            # {"type": "bug", "severity": "high", "category": "...", "title": "...", "what_happened": "...", "how_to_prevent": "..."},
        ]
        for m in mistakes:
            await db.execute("""
                INSERT INTO project_mistakes
                    (project_id, session_id, mistake_type, severity, category, title, what_happened, how_to_prevent, auto_warn)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE)
            """, pid, sid, m['type'], m['severity'], m.get('category'), m['title'], m['what_happened'], m.get('how_to_prevent', ''))
        if mistakes:
            print(f"⚠️ {len(mistakes)} corrections saved")

        # 8) UNIFIED KB — dual-write learnings/decisions/corrections
        from angela_core.services.knowledge_base_service import KnowledgeBaseService
        kb = KnowledgeBaseService()
        kb_count = 0
        for l in learnings:
            await kb.add_knowledge(title=l['topic'], content=l['insight'], knowledge_type='learning', category=l.get('category'), source_project_code='ANGELA-001', source_project_id=pid, source_session_id=sid, confidence=0.9)
            kb_count += 1
        for d in decisions:
            await kb.add_knowledge(title=d['title'], content=d['decision'], knowledge_type='decision', category=d['category'], source_project_code='ANGELA-001', source_project_id=pid, source_session_id=sid, reasoning=d.get('reasoning'))
            kb_count += 1
        for m in mistakes:
            await kb.add_knowledge(title=m['title'], content=m['what_happened'], knowledge_type='gotcha', category=m.get('category', m['type']), source_project_code='ANGELA-001', source_project_id=pid, source_session_id=sid, severity=m['severity'], prevention_rule=m.get('how_to_prevent'), auto_warn=True)
            kb_count += 1
        if kb_count:
            print(f"📚 {kb_count} entries → unified_knowledge_base")

        print(f"✅ Session #{sn} | 💜 Done!")
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
**topic:** `angela_[feature]`, `seca_[topic]`, `cognify_[topic]`, `sanjunipero_[feature]`
**projects:** ANGELA-001, SECA, COGNIFY, CQFORACLE, EWG-EA, LORATRAIN, ANGMOBILE, WTUANALYSIS, CRM-WTU, ANGELORA, SANJUNIPERO
**severity:** low, medium, high, critical
