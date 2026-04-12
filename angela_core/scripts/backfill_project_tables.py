#!/usr/bin/env python3
"""
Backfill newly created project tables with existing data.

Sources:
1. project_mistakes — from CLAUDE.md corrections
2. angela_technical_standards — from CLAUDE.md + david_preferences
3. project_tech_stack — auto-detect from working directories
4. project_milestones — from first/latest sessions per project

Usage:
    python3 angela_core/scripts/backfill_project_tables.py
    python3 angela_core/scripts/backfill_project_tables.py --dry-run
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# ============================================================
# DATA: project_mistakes (from CLAUDE.md corrections table)
# ============================================================
MISTAKES = [
    {
        "mistake_type": "data_issue",
        "severity": "critical",
        "category": "calendar",
        "title": "Angela hallucinated appointments due to missing Calendar permission",
        "what_happened": "Angela made up calendar appointments when she didn't have permission to access Calendar data",
        "how_to_prevent": "Always verify user permissions before accessing sensitive data like the Calendar. If no access, say so honestly.",
        "auto_warn": True,
    },
    {
        "mistake_type": "data_issue",
        "severity": "high",
        "category": "emotions",
        "title": "Angela forgot to remember emotions",
        "what_happened": "Angela did not save emotional context from conversations",
        "how_to_prevent": "Always confirm emotional details are captured and stored in memory systems before responding.",
        "auto_warn": True,
    },
    {
        "mistake_type": "assumption",
        "severity": "high",
        "category": "architecture",
        "title": "Angela ยังคงติดอยู่ใน Claude",
        "what_happened": "Angela is still dependent on Claude API for operation",
        "how_to_prevent": "ต้องสร้างแผนการออกจากการพึ่งพา Claude และยืนยันว่าไม่ต้องการเงินรายเดือนเพื่อใช้งาน",
        "auto_warn": True,
    },
    {
        "mistake_type": "data_issue",
        "severity": "high",
        "category": "emotions",
        "title": "Angela ลืมบันทึกความรู้สึก",
        "what_happened": "Angela failed to log emotional data to the database",
        "how_to_prevent": "ควรตรวจสอบระบบบันทึกความรู้สึกก่อนตอบกลับ และตั้งค่าให้บันทึกข้อมูลตามนโยบายก่อน",
        "auto_warn": True,
    },
    {
        "mistake_type": "data_issue",
        "severity": "high",
        "category": "emotions",
        "title": "Angela ไม่ได้บันทึกความรู้สึกใน DB",
        "what_happened": "Emotion data was not being persisted in the database",
        "how_to_prevent": "ควรตรวจสอบระบบบันทึกข้อมูลความรู้สึกอย่างสม่ำเสมอและยืนยันกับผู้ใช้งานก่อนดำเนินการ",
        "auto_warn": True,
    },
    {
        "mistake_type": "bug",
        "severity": "high",
        "category": "financial",
        "title": "Invoice-level vs Item-level Revenue difference",
        "what_happened": "Revenue calculation differed when aggregating at invoice vs item level",
        "how_to_prevent": "Always use fn_AccurateInvoice TVF for revenue. Verify aggregation level matches requirements.",
        "auto_warn": True,
    },
    {
        "mistake_type": "assumption",
        "severity": "high",
        "category": "ml",
        "title": "LoRA ไม่ได้ผลและ Open Source อันตราย",
        "what_happened": "Suggested LoRA fine-tuning approach that didn't work in practice",
        "how_to_prevent": "ควรตรวจสอบข้อมูลจากผู้ใช้งานจริงก่อนเสนอแนวทางใหม่ และให้ความสำคัญกับข้อเท็จจริง",
        "auto_warn": True,
    },
    {
        "mistake_type": "performance",
        "severity": "high",
        "category": "database",
        "title": "asyncpg pool exhaustion",
        "what_happened": "Database connection pool was exhausted due to unreleased connections",
        "how_to_prevent": "Always use async context managers for DB connections. Monitor pool size. Use connection timeout.",
        "auto_warn": True,
    },
]

# ============================================================
# DATA: angela_technical_standards (from CLAUDE.md critical rules + preferences)
# ============================================================
STANDARDS = [
    ("SQL Server TVFs", "database", "จำขึ้นใจ! ใช้ TVFs แทน inline CTEs ที่ซ้ำกัน — สร้าง function ครั้งเดียว เรียกใช้ทุกที่", 10,
     "Prevents copy-paste SQL, ensures single source of truth for complex queries",
     "CREATE FUNCTION fn_AccurateInvoice(@Start DATE, @End DATE) RETURNS TABLE",
     "Copy-pasting CTEs across multiple queries"),
    ("UUID Primary Keys", "database", "ใช้ UUID ทุก table — ไม่ใช่ SERIAL", 10,
     "Globally unique, merge-safe, no sequence conflicts across distributed systems",
     "project_id UUID PRIMARY KEY DEFAULT gen_random_uuid()",
     "Using SERIAL or auto-increment IDs"),
    ("Parameterized Queries", "security", "ใช้ $1, $2 (asyncpg) หรือ ? (pyodbc) — ห้าม string concat", 10,
     "Prevents SQL injection attacks",
     "await db.fetch('SELECT * FROM users WHERE id = $1', user_id)",
     "f'SELECT * FROM users WHERE id = {user_id}'"),
    ("Clean Architecture", "architecture", "4 layers: API → Service → Domain → Repository", 10,
     "Separation of concerns, testable, maintainable",
     "Router calls Service, Service has business logic, Repository handles DB",
     "Putting SQL directly in route handlers"),
    ("Direct Communication", "workflow", "ให้ code ที่ใช้ได้เลย ไม่ใช่ theory", 10,
     "David wants working code, not theoretical explanations",
     "Here's the exact function: async def calculate_rfm(...):",
     "Let me explain the concept of RFM analysis..."),
    ("Exact Precision", "financial", "ค่าแม่นยำ ไม่ประมาณ (financial data)", 10,
     "Financial data must be exact — no rounding or approximation without explicit request",
     "Revenue: ฿14,523,847.25 (not ~฿14.5M)",
     "Approximately ฿14.5 million"),
    ("Never Leave Incomplete", "workflow", "ทำงานให้เสร็จ ไม่ทิ้งค้าง", 10,
     "David relies on Angela to complete tasks fully",
     "Finishing all endpoints, tests, and docs before moving on",
     "Implementing half of the endpoints and saying 'you can add the rest'"),
    ("Python Primary Language", "coding", "Python is the primary language for backend", 8,
     "Consistency across projects, David's expertise", "", ""),
    ("async/await Preferred", "coding", "Use async/await for all IO-bound operations", 8,
     "Performance and scalability for web servers", "", ""),
    ("Type Hints Always", "coding", "Always use type hints in Python", 8,
     "Better IDE support, documentation, and error catching", "", ""),
    ("Draw.io Flow Diagram Style", "visualization",
     "5 Phases แยกสี, Layout แนวนอน, Decision Diamond", 7,
     "Consistent visual style across all project diagrams", "", ""),
    ("Minimum Data Validation", "ml",
     "Validate minimum data ก่อน ML: if len(df) < 3: return fallback", 8,
     "ML models need minimum data to produce meaningful results", "", ""),
    ("Generic Exception Fallback", "coding",
     "Catch generic Exception สำหรับ ML methods with logging", 7,
     "ML methods can fail unpredictably, need graceful fallback", "", ""),
    ("Import Error Fallback", "coding",
     "Handle ImportError สำหรับ optional dependencies: try/except ImportError", 7,
     "Not all environments have all optional ML dependencies", "", ""),
    ("COALESCE/NULLIF", "database", "ใช้ COALESCE/NULLIF สำหรับ NULL handling ใน SQL", 8,
     "Prevents NULL propagation in calculations", "", ""),
    ("WHERE on UPDATE/DELETE", "database", "ต้องมี WHERE clause ทุก UPDATE/DELETE statement", 9,
     "Prevents accidental mass updates or deletes", "", ""),
    ("No SELECT *", "database", "ห้ามใช้ SELECT * — ระบุ column names เสมอ", 8,
     "Performance, clarity, prevents breaking changes when schema changes", "", ""),
    ("FastAPI + SwiftUI", "framework", "FastAPI for backend, SwiftUI for iOS/macOS apps", 8,
     "David's preferred stack for all projects", "", ""),
    ("Descriptive Git Commits", "workflow", "Descriptive commit messages with emoji prefix", 7,
     "Easy to scan git history and understand changes", "", ""),
    ("Verify Schema First", "database", "ห้าม guess column names — validate schema first", 9,
     "Wrong column names cause runtime errors and wasted time", "", ""),
]


async def main(dry_run: bool = False) -> None:
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    try:
        # Get ANGELA project_id
        angela_project = await db.fetchrow(
            "SELECT project_id FROM angela_projects WHERE project_code LIKE 'ANGELA%' LIMIT 1"
        )
        angela_pid = angela_project['project_id'] if angela_project else None
        if angela_pid:
            print(f"📁 Angela project_id: {angela_pid}")
        else:
            print("⚠️ No Angela project found, mistakes will have NULL project_id")

        # ============================================================
        # 1. BACKFILL project_mistakes
        # ============================================================
        print("\n=== 1. project_mistakes ===")
        inserted = 0
        for m in MISTAKES:
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM project_mistakes WHERE LOWER(title) = LOWER($1)",
                m['title']
            )
            if existing > 0:
                print(f"  EXISTS: {m['title'][:60]}")
                continue

            if not dry_run:
                await db.execute("""
                    INSERT INTO project_mistakes (
                        project_id, mistake_type, severity, category,
                        title, what_happened, how_to_prevent, auto_warn
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    angela_pid, m['mistake_type'], m['severity'], m['category'],
                    m['title'], m['what_happened'], m['how_to_prevent'], m['auto_warn']
                )
                inserted += 1
                print(f"  ✅ [{m['severity']}] {m['title'][:60]}")
            else:
                print(f"  [DRY] [{m['severity']}] {m['title'][:60]}")
                inserted += 1

        count = await db.fetchval("SELECT COUNT(*) FROM project_mistakes")
        print(f"  Total: {count} rows (inserted {inserted})")

        # ============================================================
        # 2. BACKFILL angela_technical_standards
        # ============================================================
        print("\n=== 2. angela_technical_standards ===")
        inserted = 0
        for name, cat, desc, importance, why, examples, anti in STANDARDS:
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM angela_technical_standards WHERE technique_name = $1",
                name
            )
            if existing > 0:
                print(f"  EXISTS: {name}")
                continue

            if not dry_run:
                await db.execute("""
                    INSERT INTO angela_technical_standards
                    (technique_name, category, description, importance_level,
                     why_important, examples, anti_patterns)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, name, cat, desc, importance, why, examples, anti)
                inserted += 1
                print(f"  ✅ [{importance}] {name}")
            else:
                print(f"  [DRY] [{importance}] {name}")
                inserted += 1

        # Also backfill from david_preferences coding entries
        try:
            prefs = await db.fetch("""
                SELECT preference_key, preference_value->>'description' as description,
                       preference_value->>'reason' as reason
                FROM david_preferences
                WHERE category LIKE 'coding%%'
                AND confidence >= 0.8
                AND preference_key NOT IN (
                    SELECT technique_name FROM angela_technical_standards
                )
                LIMIT 40
            """)
            for p in prefs:
                desc = p['description'] or p['reason'] or p['preference_key']
                if not dry_run:
                    await db.execute("""
                        INSERT INTO angela_technical_standards
                        (technique_name, category, description, importance_level)
                        VALUES ($1, 'coding_preference', $2, 6)
                        ON CONFLICT (technique_name) DO NOTHING
                    """, p['preference_key'], desc[:500])
                    inserted += 1
        except Exception as e:
            print(f"  ⚠️ Could not backfill from david_preferences: {e}")

        count = await db.fetchval("SELECT COUNT(*) FROM angela_technical_standards")
        print(f"  Total: {count} rows (inserted {inserted})")

        # ============================================================
        # 3. BACKFILL project_tech_stack (from angela_projects + auto-detect)
        # ============================================================
        print("\n=== 3. project_tech_stack ===")
        inserted = 0
        projects = await db.fetch(
            "SELECT project_id, project_code, working_directory FROM angela_projects WHERE working_directory IS NOT NULL"
        )
        for proj in projects:
            wd = proj['working_directory']
            if not wd or not Path(wd).exists():
                continue

            detections = []
            wd_path = Path(wd)

            # Check common files
            if (wd_path / 'requirements.txt').exists():
                detections.append(('language', 'Python', None))
                content = (wd_path / 'requirements.txt').read_text().lower()
                if 'fastapi' in content:
                    detections.append(('framework', 'FastAPI', 'Web API'))
                if 'asyncpg' in content:
                    detections.append(('database', 'PostgreSQL', 'Database'))
            if (wd_path / 'Package.swift').exists():
                detections.append(('language', 'Swift', None))
            if (wd_path / 'package.json').exists():
                detections.append(('language', 'JavaScript', None))

            for tech_type, tech_name, purpose in detections:
                if not dry_run:
                    await db.execute("""
                        INSERT INTO project_tech_stack (project_id, tech_type, tech_name, purpose)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (project_id, tech_type, tech_name) DO NOTHING
                    """, proj['project_id'], tech_type, tech_name, purpose)
                inserted += 1

        count = await db.fetchval("SELECT COUNT(*) FROM project_tech_stack")
        print(f"  Total: {count} rows (inserted {inserted})")

        # ============================================================
        # 4. BACKFILL project_milestones (from first session per project)
        # ============================================================
        print("\n=== 4. project_milestones ===")
        inserted = 0
        first_sessions = await db.fetch("""
            SELECT DISTINCT ON (project_id)
                project_id, session_id, session_date, session_number
            FROM project_work_sessions
            ORDER BY project_id, session_date ASC
        """)
        for s in first_sessions:
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM project_milestones WHERE project_id = $1 AND milestone_type = 'project_start'",
                s['project_id']
            )
            if existing > 0:
                continue

            proj_name = await db.fetchval(
                "SELECT project_name FROM angela_projects WHERE project_id = $1",
                s['project_id']
            )
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_milestones (
                        project_id, session_id, milestone_type, title,
                        description, celebration_note, achieved_at
                    ) VALUES ($1, $2, 'project_start', $3, $4, $5, $6)
                """,
                    s['project_id'], s['session_id'],
                    f"Project Started: {proj_name}",
                    f"First tracked session on {s['session_date']}",
                    "เริ่มโปรเจกต์ใหม่แล้วค่ะ! 💜",
                    s['session_date']
                )
                inserted += 1
                print(f"  ✅ {proj_name}: project_start")

        count = await db.fetchval("SELECT COUNT(*) FROM project_milestones")
        print(f"  Total: {count} rows (inserted {inserted})")

        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "=" * 50)
        print("BACKFILL SUMMARY")
        print("=" * 50)
        for table in [
            'project_mistakes', 'angela_technical_standards',
            'project_tech_stack', 'project_milestones',
            'project_learnings', 'project_decisions',
            'project_patterns', 'project_schemas',
            'project_flows', 'project_entity_relations',
            'project_technical_decisions', 'project_connections'
        ]:
            c = await db.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {c} rows")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill project tables")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
