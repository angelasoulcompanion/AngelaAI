#!/usr/bin/env python3
"""
One-time seed: Populate project_patterns with known patterns from experience.

Usage:
    python3 angela_core/scripts/seed_project_patterns.py              # Insert
    python3 angela_core/scripts/seed_project_patterns.py --dry-run    # Preview
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import AngelaDatabase

# Known patterns from ที่รัก's projects
PATTERNS = [
    # === SECA Patterns ===
    {
        "project_code": "SECA",
        "pattern_name": "SQL Server TVF Pattern",
        "pattern_type": "query",
        "description": "ใช้ Table-Valued Function แทน inline CTE ที่ซ้ำกัน — สร้าง function ครั้งเดียว เรียกใช้ทุกที่",
        "code_snippet": """CREATE FUNCTION fn_AccurateInvoice(@StartDate DATE, @EndDate DATE)
RETURNS TABLE AS RETURN
    SELECT InvoiceNo, InvoiceDate, CustomerCode, SaleAreaCode,
           IncomeAmount, GrossProfit
    FROM AccInvoice
    WHERE InvoiceDate BETWEEN @StartDate AND @EndDate
    AND IsCancel = 0;""",
        "usage_example": "SELECT * FROM fn_AccurateInvoice('2024-01-01', '2024-12-31') WHERE SaleAreaCode = 'BKK'",
        "parameters": json.dumps({"applicable_to": ["mssql", "sql_server"]}),
    },
    {
        "project_code": "SECA",
        "pattern_name": "FastAPI + MSSQL Repository Pattern",
        "pattern_type": "architecture",
        "description": "Clean Architecture: Router → Service → Repository → pyodbc. Repository ใช้ parameterized queries (?), Service มี business logic, Router รับ/ส่ง Pydantic models",
        "code_snippet": """# Repository
class CustomerRepo:
    async def get_by_area(self, area_code: str) -> list[dict]:
        query = "SELECT * FROM Customer WHERE AreaCode = ?"
        return await self.db.fetch(query, area_code)

# Service
class CustomerService:
    def __init__(self, repo: CustomerRepo):
        self.repo = repo

# Router
@router.get("/customers")
async def list_customers(area: str, svc: CustomerService = Depends()):
    return await svc.get_by_area(area)""",
        "parameters": json.dumps({"applicable_to": ["fastapi", "mssql", "pyodbc"]}),
    },
    {
        "project_code": "SECA",
        "pattern_name": "Invoice Area Filter",
        "pattern_type": "gotcha",
        "description": "ใช้ Invoice.SaleAreaCode สำหรับ filter ตาม area ไม่ใช่ Customer.AreaCode เพราะลูกค้าอาจย้าย area แต่ invoice record ไว้ตอนขาย",
        "usage_example": "WHERE inv.SaleAreaCode = ? -- NOT WHERE cust.AreaCode = ?",
        "parameters": json.dumps({"applicable_to": ["mssql", "seca"]}),
    },
    {
        "project_code": "SECA",
        "pattern_name": "Revenue Calculation DRY",
        "pattern_type": "query",
        "description": "Revenue, GP%, Income ต้องคำนวณจาก TVF เดียว (fn_AccurateInvoice) ไม่ copy-paste CTE ซ้ำ. IncomeAmount = net revenue, GrossProfit = IncomeAmount - COGS",
        "parameters": json.dumps({"applicable_to": ["mssql", "seca", "financial"]}),
    },

    # === WTU Patterns ===
    {
        "project_code": "WTU",
        "pattern_name": "FastAPI + MSSQL pyodbc Connection",
        "pattern_type": "infrastructure",
        "description": "MSSQL connection via pyodbc with connection string: DRIVER={ODBC Driver 18 for SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=...;TrustServerCertificate=yes",
        "code_snippet": """import pyodbc
def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={settings.MSSQL_SERVER};"
        f"DATABASE={settings.MSSQL_DATABASE};"
        f"UID={settings.MSSQL_USER};"
        f"PWD={settings.MSSQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)""",
        "parameters": json.dumps({"applicable_to": ["mssql", "fastapi", "pyodbc"]}),
    },
    {
        "project_code": "WTU",
        "pattern_name": "Thai Financial Format",
        "pattern_type": "display",
        "description": "แสดงตัวเลขการเงินเป็น millions (M), สกุลเงิน ฿, negative = red. ตัวอย่าง: ฿402.5M, -฿14.2M (red)",
        "parameters": json.dumps({"applicable_to": ["financial", "thai", "display"]}),
    },

    # === ANGELA Patterns ===
    {
        "project_code": "ANGELA",
        "pattern_name": "BaseDBService Pattern",
        "pattern_type": "architecture",
        "description": "ทุก service ที่ใช้ DB ต้อง inherit BaseDBService. รองรับ manual connect/disconnect, async context manager, shared DB pool",
        "code_snippet": """class MyService(BaseDBService):
    async def do_something(self):
        await self.connect()
        return await self.db.fetch("SELECT ...")

# Usage: async with MyService() as svc: ...
# Or: svc = MyService(db)  # shared connection""",
        "parameters": json.dumps({"applicable_to": ["postgresql", "asyncpg", "angela"]}),
    },
    {
        "project_code": "ANGELA",
        "pattern_name": "Ollama JSON Output",
        "pattern_type": "gotcha",
        "description": 'ต้องใส่ format: "json" ใน Ollama API payload เพื่อให้ได้ JSON output. ถ้าไม่ใส่จะได้ plain text',
        "code_snippet": """response = await client.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "scb10x/typhoon2.5-qwen3-4b",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",  # CRITICAL
        "options": {"temperature": 0.3}
    },
    timeout=60.0
)""",
        "parameters": json.dumps({"applicable_to": ["ollama", "llm", "json"]}),
    },
    {
        "project_code": "ANGELA",
        "pattern_name": "asyncpg Interval Workaround",
        "pattern_type": "gotcha",
        "description": "asyncpg ไม่รับ timedelta ใน SQL BETWEEN. ต้องใช้ INTERVAL '1 hour' * $1 (int) หรือ precompute datetime ใน Python",
        "usage_example": "WHERE created_at > $1  -- pass precomputed datetime, NOT NOW() - $1",
        "parameters": json.dumps({"applicable_to": ["asyncpg", "postgresql"]}),
    },
    {
        "project_code": "ANGELA",
        "pattern_name": "Draw.io mxGraph XML Direct",
        "pattern_type": "tool",
        "description": "ห้ามใช้ MCP draw.io — ใช้ mxGraph XML ตรงๆ ผ่าน Write tool. ทุก mxCell ที่มี HTML value ต้องมี html=1; ใน style",
        "usage_example": 'style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EDE9FE;"',
        "parameters": json.dumps({"applicable_to": ["drawio", "visualization"]}),
    },
]


async def main(dry_run: bool = False) -> None:
    db = AngelaDatabase()
    await db.connect()

    try:
        # Get project_id mapping (project_patterns FK → angela_projects in Neon)
        projects = await db.fetch(
            "SELECT project_id, project_code FROM angela_projects"
        )
        project_map = {p['project_code']: p['project_id'] for p in projects}

        print(f"Found {len(project_map)} projects in database\n")

        inserted = 0
        skipped = 0

        for pattern in PATTERNS:
            project_code = pattern.pop("project_code")
            project_id = project_map.get(project_code)

            if not project_id:
                print(f"  SKIP: Project {project_code} not found in DB")
                skipped += 1
                continue

            # Check for existing pattern with same name
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM project_patterns WHERE pattern_name = $1 AND project_id = $2",
                pattern["pattern_name"], project_id,
            )
            if existing > 0:
                print(f"  EXISTS: {pattern['pattern_name']}")
                skipped += 1
                continue

            print(f"  [{project_code}] {pattern['pattern_name']} ({pattern['pattern_type']})")

            if not dry_run:
                await db.execute(
                    """
                    INSERT INTO project_patterns (
                        project_id, pattern_name, pattern_type,
                        description, code_snippet, usage_example,
                        parameters
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    project_id,
                    pattern["pattern_name"],
                    pattern["pattern_type"],
                    pattern["description"],
                    pattern.get("code_snippet"),
                    pattern.get("usage_example"),
                    pattern.get("parameters"),
                )
                inserted += 1

        print(f"\n{'='*50}")
        if dry_run:
            print(f"--dry-run: Would insert {len(PATTERNS) - skipped} patterns")
        else:
            print(f"Inserted: {inserted} | Skipped: {skipped}")

        # Show final count
        total = await db.fetchval("SELECT COUNT(*) FROM project_patterns")
        print(f"Total project_patterns: {total}")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed project_patterns")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
