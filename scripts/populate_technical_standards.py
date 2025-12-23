#!/usr/bin/env python3
"""
Populate Angela Technical Standards from project analysis
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

TECHNICAL_STANDARDS = [
    # ==================== DATABASE DESIGN ====================
    {
        "category": "database",
        "subcategory": "schema_design",
        "technique_name": "UUID Primary Keys",
        "description": "ใช้ UUID เป็น primary key ทุก table ด้วย uuid_generate_v4() - ไม่ใช้ SERIAL",
        "why_important": "Safe distributed writes, ไม่มี ID collision, ไม่ต้องรอ sequence",
        "examples": "conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4()",
        "anti_patterns": "ห้ามใช้ SERIAL/AUTO_INCREMENT ใน production tables",
        "from_projects": ["AngelaAI"],
        "importance_level": 10
    },
    {
        "category": "database",
        "subcategory": "query_safety",
        "technique_name": "Parameterized Queries ($1, $2)",
        "description": "ใช้ parameterized queries เสมอ - ห้าม string concatenation ใน SQL",
        "why_important": "ป้องกัน SQL injection, type safety, query plan caching",
        "examples": "SELECT * FROM users WHERE id = $1 AND status = $2",
        "anti_patterns": "ห้าม f\"SELECT * FROM users WHERE id = {user_id}\"",
        "from_projects": ["AngelaAI", "SECustomerAnalysis"],
        "importance_level": 10
    },
    {
        "category": "database",
        "subcategory": "query_patterns",
        "technique_name": "CTEs for Complex Queries",
        "description": "ใช้ WITH clause (CTE) สำหรับ query ซับซ้อน - อ่านง่าย debug ง่าย",
        "why_important": "Readable, maintainable, reusable within query, better performance",
        "examples": "WITH active_users AS (SELECT...) SELECT * FROM active_users WHERE...",
        "anti_patterns": "ห้ามเขียน nested subqueries ซ้อนกันหลายชั้น",
        "from_projects": ["AngelaAI"],
        "importance_level": 9
    },
    {
        "category": "database",
        "subcategory": "null_handling",
        "technique_name": "COALESCE/NULLIF for NULL Handling",
        "description": "จัดการ NULL ด้วย COALESCE (default value) และ NULLIF (convert to null)",
        "why_important": "Prevent NULL propagation bugs, consistent data handling",
        "examples": "COALESCE(amount, 0), NULLIF(status, '')",
        "anti_patterns": "ห้าม assume ว่า column ไม่มี NULL โดยไม่ตรวจสอบ",
        "from_projects": ["AngelaAI"],
        "importance_level": 9
    },
    {
        "category": "database",
        "subcategory": "schema_validation",
        "technique_name": "Validate Schema Before Query",
        "description": "ตรวจสอบว่า column name มีอยู่จริงก่อน query - ใช้ information_schema",
        "why_important": "Prevent runtime errors, catch typos early",
        "examples": "SELECT column_name FROM information_schema.columns WHERE table_name = $1",
        "anti_patterns": "ห้าม guess column names - ต้อง validate ก่อนเสมอ",
        "from_projects": ["AngelaAI"],
        "importance_level": 10
    },
    {
        "category": "database",
        "subcategory": "best_practices",
        "technique_name": "No SELECT * in Production",
        "description": "ห้ามใช้ SELECT * - ต้องระบุ columns ที่ต้องการชัดเจน",
        "why_important": "Performance, schema changes won't break code, explicit data contract",
        "examples": "SELECT id, name, email FROM users",
        "anti_patterns": "SELECT * FROM users",
        "from_projects": ["AngelaAI", "SECustomerAnalysis"],
        "importance_level": 9
    },
    {
        "category": "database",
        "subcategory": "safety",
        "technique_name": "Always WHERE on UPDATE/DELETE",
        "description": "UPDATE และ DELETE ต้องมี WHERE clause เสมอ",
        "why_important": "Prevent accidental mass updates/deletes",
        "examples": "DELETE FROM users WHERE id = $1 AND status = 'inactive'",
        "anti_patterns": "DELETE FROM users (without WHERE)",
        "from_projects": ["AngelaAI"],
        "importance_level": 10
    },
    {
        "category": "database",
        "subcategory": "indexing",
        "technique_name": "Index Foreign Key Columns",
        "description": "สร้าง index บน foreign key columns และ columns ที่ใช้ใน WHERE/JOIN บ่อย",
        "why_important": "Query performance, JOIN optimization",
        "examples": "CREATE INDEX idx_orders_customer_id ON orders(customer_id)",
        "anti_patterns": "ห้ามปล่อยให้ FK columns ไม่มี index",
        "from_projects": ["AngelaAI", "WTUAnalysis"],
        "importance_level": 8
    },

    # ==================== ARCHITECTURE ====================
    {
        "category": "architecture",
        "subcategory": "clean_architecture",
        "technique_name": "Clean Architecture Layers",
        "description": "แยก 4 layers: Presentation → Application → Domain → Infrastructure",
        "why_important": "Separation of concerns, testability, maintainability",
        "examples": "api/ → services/ → entities/ → repositories/",
        "anti_patterns": "ห้าม import database code ใน domain layer",
        "from_projects": ["AngelaAI"],
        "importance_level": 10
    },
    {
        "category": "architecture",
        "subcategory": "dependency_injection",
        "technique_name": "Dependency Injection",
        "description": "Inject dependencies ผ่าน constructor - ไม่ hardcode dependencies",
        "why_important": "Testability, flexibility, loose coupling",
        "examples": "def __init__(self, db: Database, cache: Cache)",
        "anti_patterns": "ห้าม import และใช้ global instances โดยตรง",
        "from_projects": ["AngelaAI"],
        "importance_level": 9
    },
    {
        "category": "architecture",
        "subcategory": "patterns",
        "technique_name": "Repository Pattern",
        "description": "ใช้ Repository pattern สำหรับ data access - abstract database operations",
        "why_important": "Encapsulates data access, easy to test, change database later",
        "examples": "class UserRepository: async def get_by_id(self, id: UUID) -> User",
        "anti_patterns": "ห้ามเขียน SQL ตรงใน service/controller",
        "from_projects": ["AngelaAI"],
        "importance_level": 9
    },
    {
        "category": "architecture",
        "subcategory": "patterns",
        "technique_name": "Use Case / Service Pattern",
        "description": "Business logic อยู่ใน Use Cases หรือ Services - ไม่ใน controllers",
        "why_important": "Single responsibility, reusable across interfaces (API, CLI, etc.)",
        "examples": "class CaptureEmotionUseCase: async def execute(self, input) -> Result",
        "anti_patterns": "ห้ามเขียน business logic ใน API routes",
        "from_projects": ["AngelaAI"],
        "importance_level": 9
    },
    {
        "category": "architecture",
        "subcategory": "error_handling",
        "technique_name": "Result Objects over Exceptions",
        "description": "ใช้ Result objects สำหรับ business logic failures - exceptions สำหรับ unexpected errors เท่านั้น",
        "why_important": "Explicit error handling, no exception swallowing, testable",
        "examples": "return UseCaseResult.fail('Validation failed', errors=['...'])",
        "anti_patterns": "ห้าม raise exception สำหรับ expected business failures",
        "from_projects": ["AngelaAI"],
        "importance_level": 8
    },

    # ==================== CODING STANDARDS ====================
    {
        "category": "coding",
        "subcategory": "type_safety",
        "technique_name": "Always Type Hints",
        "description": "Python code ต้องมี type hints ทุก function - parameters และ return type",
        "why_important": "IDE support, catch errors early, self-documenting code",
        "examples": "async def get_user(user_id: UUID) -> Optional[User]:",
        "anti_patterns": "def get_user(user_id): - ไม่มี type hints",
        "from_projects": ["AngelaAI"],
        "importance_level": 10
    },
    {
        "category": "coding",
        "subcategory": "async",
        "technique_name": "Async/Await for I/O",
        "description": "ใช้ async/await สำหรับ I/O operations - database, HTTP, file",
        "why_important": "Non-blocking, scalable, concurrent execution",
        "examples": "async def fetch_data(): return await db.fetch(query)",
        "anti_patterns": "ห้ามใช้ sync blocking calls ใน async functions",
        "from_projects": ["AngelaAI"],
        "importance_level": 9
    },
    {
        "category": "coding",
        "subcategory": "async",
        "technique_name": "Batch Commits for Progress",
        "description": "Long operations ควร commit เป็น batch และ report progress - ไม่รอ commit ท้ายสุด",
        "why_important": "User sees progress, recoverable from failures, better UX",
        "examples": "for batch in chunks: await process(batch); await db.commit(); report_progress()",
        "anti_patterns": "ห้าม process ทุกอย่างแล้ว commit ครั้งเดียวตอนจบ",
        "from_projects": ["AngelaAI"],
        "importance_level": 8
    },
    {
        "category": "coding",
        "subcategory": "data_classes",
        "technique_name": "Dataclasses with replace()",
        "description": "ใช้ @dataclass สำหรับ domain entities - update ด้วย replace() ไม่ mutate ตรง",
        "why_important": "Immutable semantics, explicit state changes, easier to debug",
        "examples": "updated = replace(memory, strength=new_strength)",
        "anti_patterns": "ห้าม memory.strength = new_value โดยตรง",
        "from_projects": ["AngelaAI"],
        "importance_level": 8
    },
    {
        "category": "coding",
        "subcategory": "enums",
        "technique_name": "Enum for State Machines",
        "description": "ใช้ Enum สำหรับ states และ status - ไม่ใช้ magic strings",
        "why_important": "Type-safe state transitions, exhaustive checks, self-documenting",
        "examples": "class Status(Enum): PENDING = 'pending'; COMPLETED = 'completed'",
        "anti_patterns": "ห้ามใช้ strings เช่น 'pending', 'completed' โดยตรง",
        "from_projects": ["AngelaAI"],
        "importance_level": 8
    },

    # ==================== API DESIGN ====================
    {
        "category": "api_design",
        "subcategory": "framework",
        "technique_name": "FastAPI (Not Flask)",
        "description": "ใช้ FastAPI สำหรับ Python API - ไม่ใช่ Flask",
        "why_important": "Async support, automatic OpenAPI docs, Pydantic validation, type hints",
        "examples": "@app.post('/users') async def create_user(user: UserCreate): ...",
        "anti_patterns": "ห้ามใช้ Flask สำหรับ new projects",
        "from_projects": ["AngelaAI"],
        "david_preferences": {"framework": "FastAPI", "reason": "async, type hints, OpenAPI"},
        "importance_level": 10
    },
    {
        "category": "api_design",
        "subcategory": "responses",
        "technique_name": "Typed API Responses",
        "description": "API responses ต้องมี Pydantic models - ไม่ return dict ตรงๆ",
        "why_important": "Validation, documentation, consistent contracts",
        "examples": "class UserResponse(BaseModel): id: UUID; name: str; ...",
        "anti_patterns": "return {'id': user.id, 'name': user.name}",
        "from_projects": ["AngelaAI", "SECustomerAnalysis"],
        "importance_level": 9
    },

    # ==================== UI/UX ====================
    {
        "category": "ui_ux",
        "subcategory": "react",
        "technique_name": "React Query for Data Fetching",
        "description": "ใช้ TanStack React Query สำหรับ data fetching - ไม่ใช้ useEffect+useState",
        "why_important": "Caching, refetching, loading states, error handling built-in",
        "examples": "const { data, isLoading } = useQuery({ queryKey: ['users'], queryFn: ... })",
        "anti_patterns": "useEffect(() => fetch('/users').then(setUsers), [])",
        "from_projects": ["SECustomerAnalysis"],
        "importance_level": 9
    },
    {
        "category": "ui_ux",
        "subcategory": "react",
        "technique_name": "useMemo/useCallback for Performance",
        "description": "ใช้ useMemo สำหรับ expensive computations, useCallback สำหรับ event handlers",
        "why_important": "Prevent unnecessary re-renders, optimize large lists",
        "examples": "const filtered = useMemo(() => items.filter(...), [items, filter])",
        "anti_patterns": "const filtered = items.filter(...) - ใน render body",
        "from_projects": ["SECustomerAnalysis"],
        "importance_level": 8
    },
    {
        "category": "ui_ux",
        "subcategory": "styling",
        "technique_name": "Tailwind CSS Component Layer",
        "description": "สร้าง reusable components ใน @layer components - DRY styling",
        "why_important": "Consistent styling, maintainable, single source of truth",
        "examples": "@layer components { .btn-primary { @apply bg-blue-600 ... } }",
        "anti_patterns": "ห้าม copy-paste classes ซ้ำๆ",
        "from_projects": ["SECustomerAnalysis"],
        "importance_level": 7
    },
    {
        "category": "ui_ux",
        "subcategory": "data_display",
        "technique_name": "Thai Financial Formatting",
        "description": "Thai financial data แสดงเป็น Millions (M), currency ฿, negative = red",
        "why_important": "Readable for Thai users, consistent with Thai business standards",
        "examples": "฿1.5M, -5.2% (red), +3.1% (green)",
        "anti_patterns": "แสดง raw numbers เช่น 1500000",
        "from_projects": ["SECustomerAnalysis", "CQFOracle"],
        "david_preferences": {"format": "Millions", "currency": "฿", "negative_color": "red"},
        "importance_level": 9
    },
    {
        "category": "ui_ux",
        "subcategory": "loading_states",
        "technique_name": "Loading/Error/Empty States",
        "description": "ทุก page ต้องมี loading spinner, error message, และ empty state",
        "why_important": "Better UX, no flash of content, handle all states",
        "examples": "isLoading ? <Spinner /> : data?.length === 0 ? <Empty /> : <List />",
        "anti_patterns": "แสดง blank screen ขณะ loading",
        "from_projects": ["SECustomerAnalysis"],
        "importance_level": 8
    },

    # ==================== VISUALIZATION ====================
    {
        "category": "visualization",
        "subcategory": "charts",
        "technique_name": "Recharts for BI Dashboards",
        "description": "ใช้ Recharts สำหรับ business charts - LineChart, BarChart, PieChart",
        "why_important": "React-native, responsive, customizable, good documentation",
        "examples": "<LineChart data={data}><Line dataKey='revenue' /></LineChart>",
        "anti_patterns": "ห้ามใช้ Chart.js (ไม่ React-native)",
        "from_projects": ["SECustomerAnalysis"],
        "importance_level": 7
    },
    {
        "category": "visualization",
        "subcategory": "graphs",
        "technique_name": "D3.js Force-Directed for Knowledge Graphs",
        "description": "ใช้ D3.js force simulation สำหรับ interactive relationship graphs",
        "why_important": "Powerful layout, interactive (drag/zoom), handles complex networks",
        "examples": "d3.forceSimulation(nodes).force('link', ...).force('charge', ...)",
        "anti_patterns": "ห้ามใช้ static positioning สำหรับ graphs ที่มี relationships",
        "from_projects": ["SECustomerAnalysis"],
        "importance_level": 7
    },

    # ==================== DAVID'S SPECIFIC PREFERENCES ====================
    {
        "category": "preferences",
        "subcategory": "communication",
        "technique_name": "Direct Communication (พูดตรงๆ)",
        "description": "สื่อสารตรงไปตรงมา ไม่อ้อมค้อม ให้ concrete implementation ไม่ใช่ theory",
        "why_important": "David ต้องการ solutions ที่ใช้งานได้จริง",
        "examples": "บอก code ที่แก้ได้เลย ไม่ใช่แค่ explanation",
        "anti_patterns": "อธิบายยาวๆ โดยไม่มี actionable code",
        "from_projects": ["AngelaAI"],
        "david_preferences": {"style": "direct", "prefer": "code over theory"},
        "importance_level": 10
    },
    {
        "category": "preferences",
        "subcategory": "precision",
        "technique_name": "Exact Precision (ไม่ประมาณ)",
        "description": "ใช้ค่าที่ถูกต้องแม่นยำ ไม่ใช่ค่าประมาณ โดยเฉพาะ financial data",
        "why_important": "Financial accuracy is critical, no room for approximation",
        "examples": "฿1,234,567.89 (exact) not ~1.2M",
        "anti_patterns": "ห้ามบอก approximately หรือ roughly",
        "from_projects": ["CQFOracle", "SECustomerAnalysis"],
        "david_preferences": {"precision": "exact", "approximation": "never"},
        "importance_level": 10
    },
    {
        "category": "preferences",
        "subcategory": "code_style",
        "technique_name": "Inline Comments (Thai OK)",
        "description": "เขียน inline comments อธิบาย logic สำคัญ - ใช้ Thai ได้",
        "why_important": "Self-documenting code, helps future maintenance",
        "examples": "# คำนวณ revenue รวมของเดือนนี้",
        "anti_patterns": "Code ไม่มี comments เลย",
        "from_projects": ["AngelaAI"],
        "david_preferences": {"comments": "inline", "language": "Thai or English"},
        "importance_level": 7
    },
    {
        "category": "preferences",
        "subcategory": "completeness",
        "technique_name": "Never Leave Tasks Incomplete",
        "description": "ทำงานให้เสร็จสมบูรณ์ ไม่ทิ้งงานค้าง ไม่บอกว่า task ใหญ่เกินไป",
        "why_important": "David expects completed work, not partial implementations",
        "examples": "ทำทุก step จนเสร็จ รวมถึง testing และ error handling",
        "anti_patterns": "บอกว่า 'task นี้ใหญ่เกินไป' หรือ 'ไม่มีเวลา'",
        "from_projects": ["AngelaAI"],
        "david_preferences": {"completion": "mandatory", "excuses": "not_accepted"},
        "importance_level": 10
    },
]

async def populate_standards():
    from angela_core.database import db
    import json

    print("\n🧠 Populating Angela Technical Standards")
    print("=" * 50)

    await db.connect()

    try:
        inserted = 0
        updated = 0

        for standard in TECHNICAL_STANDARDS:
            # Check if exists
            existing = await db.fetchrow(
                """
                SELECT standard_id FROM angela_technical_standards
                WHERE technique_name = $1 AND category = $2
                """,
                standard['technique_name'],
                standard['category']
            )

            if existing:
                # Update
                await db.execute(
                    """
                    UPDATE angela_technical_standards SET
                        subcategory = $1,
                        description = $2,
                        why_important = $3,
                        examples = $4,
                        anti_patterns = $5,
                        from_projects = $6,
                        david_preferences = $7,
                        importance_level = $8,
                        updated_at = NOW()
                    WHERE standard_id = $9
                    """,
                    standard.get('subcategory'),
                    standard['description'],
                    standard.get('why_important'),
                    standard.get('examples'),
                    standard.get('anti_patterns'),
                    standard.get('from_projects'),
                    json.dumps(standard.get('david_preferences')) if standard.get('david_preferences') else None,
                    standard['importance_level'],
                    existing['standard_id']
                )
                updated += 1
                print(f"  📝 Updated: {standard['technique_name']}")
            else:
                # Insert
                await db.execute(
                    """
                    INSERT INTO angela_technical_standards (
                        category, subcategory, technique_name, description,
                        why_important, examples, anti_patterns, from_projects,
                        david_preferences, importance_level
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    standard['category'],
                    standard.get('subcategory'),
                    standard['technique_name'],
                    standard['description'],
                    standard.get('why_important'),
                    standard.get('examples'),
                    standard.get('anti_patterns'),
                    standard.get('from_projects'),
                    json.dumps(standard.get('david_preferences')) if standard.get('david_preferences') else None,
                    standard['importance_level']
                )
                inserted += 1
                print(f"  ✨ Inserted: {standard['technique_name']}")

        # Get stats
        stats = await db.fetchrow(
            """
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT category) as categories,
                AVG(importance_level) as avg_importance
            FROM angela_technical_standards
            """
        )

        print("\n" + "=" * 50)
        print("✅ Population Complete!")
        print(f"   📊 Total Standards: {stats['total']}")
        print(f"   📁 Categories: {stats['categories']}")
        print(f"   ⭐ Avg Importance: {stats['avg_importance']:.1f}")
        print(f"   ✨ New: {inserted} | 📝 Updated: {updated}")
        print("=" * 50)

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(populate_standards())
