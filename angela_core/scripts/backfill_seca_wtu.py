#!/usr/bin/env python3
"""
Backfill project tables for SECA + WTU from deep codebase analysis.

Covers: tech_stack, patterns, learnings, schemas, flows,
        technical_decisions, entity_relations

Usage:
    python3 angela_core/scripts/backfill_seca_wtu.py
    python3 angela_core/scripts/backfill_seca_wtu.py --dry-run
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ============================================================
# SECA TECH STACK (exact versions from package.json + requirements.txt)
# ============================================================
SECA_TECH_STACK = [
    ("frontend", "React", "19.2.0", "UI framework"),
    ("language", "TypeScript", "5.9.3", "Frontend type safety"),
    ("tool", "Vite", "7.2.4", "Frontend build tool"),
    ("styling", "Tailwind CSS", "4.1.17", "Utility-first CSS"),
    ("library", "TanStack Query", "5.90.11", "State management (15min stale, 1hr gc)"),
    ("library", "Recharts", "3.5.1", "Charts"),
    ("library", "D3", "7.9.0", "Advanced visualization"),
    ("library", "Axios", "1.13.2", "HTTP client"),
    ("library", "React Router", "7.9.6", "Routing"),
    ("library", "Lucide React", "0.555.0", "Icons"),
    ("library", "date-fns", "4.1.0", "Date utilities"),
    ("framework", "FastAPI", ">=0.115.0", "Backend API"),
    ("language", "Python", "3.13", "Backend"),
    ("database", "MSSQL Server", None, "Host: 203.150.33.48, DB: SiamEast, Schema: Midnight"),
    ("library", "pyodbc", ">=5.2.0", "MSSQL ODBC driver 17"),
    ("library", "Pydantic", ">=2.10.0", "Validation"),
    ("auth", "python-jose", ">=3.3.0", "JWT HS256, 4hr expiry"),
    ("auth", "bcrypt", ">=4.2.0", "Password hashing"),
    ("ai", "OpenAI", ">=2.0.0", "AI Chat streaming"),
    ("library", "openpyxl", ">=3.1.5", "Excel export"),
    ("library", "ReportLab", ">=4.2.0", "PDF generation"),
]

# ============================================================
# WTU TECH STACK (exact versions)
# ============================================================
WTU_TECH_STACK = [
    ("frontend", "React", "19.2.0", "UI framework"),
    ("language", "TypeScript", "5.9.3", "Frontend type safety"),
    ("tool", "Vite", "7.2.4", "Frontend build tool"),
    ("styling", "Tailwind CSS", "4.1.17", "Utility-first CSS"),
    ("library", "TanStack Query", "5.90.11", "State management"),
    ("library", "Recharts", "3.5.1", "Charts"),
    ("library", "Axios", "1.13.2", "HTTP client"),
    ("library", "React Router", "7.9.6", "Routing"),
    ("library", "Zustand", "5.0.10", "Frontend state management"),
    ("library", "Lucide React", "0.555.0", "Icons"),
    ("library", "clsx", "2.1.1", "Conditional classnames"),
    ("library", "date-fns", "4.1.0", "Date utilities"),
    ("framework", "FastAPI", ">=0.115.0", "Backend API"),
    ("language", "Python", "3.13+", "Backend"),
    ("database", "MSSQL Server", None, "pymssql, PooledDB (min5/max20/total50)"),
    ("library", "pymssql", ">=2.3.0", "MSSQL driver (macOS preferred)"),
    ("library", "Pydantic", ">=2.10.0", "Validation"),
    ("auth", "python-jose", ">=3.3.0", "JWT HS256, 60min access + 7d refresh"),
    ("auth", "passlib+bcrypt", ">=1.7.4", "Password hashing"),
    ("library", "openpyxl", ">=3.1.2", "Excel export"),
    ("library", "ReportLab", ">=4.2.0", "PDF export"),
    ("library", "scikit-learn", ">=1.4.0", "ML models"),
    ("library", "pandas", ">=2.2.0", "Data preprocessing"),
    ("library", "DBUtils", None, "Connection pooling (PooledDB)"),
]

# ============================================================
# SECA PATTERNS
# ============================================================
SECA_PATTERNS = [
    {
        "name": "InvoiceCalculator SSOT",
        "type": "architecture",
        "description": "Invoice-level calculations for payment/AR. NetAmountAfterVat (incl VAT), ReceiveAmount (paid), RemainAmount (outstanding). Methods: revenue_sum(), paid_sum(), outstanding_sum(), payment_rate(), avg_order_value().",
        "file_path": "backend/app/shared/invoice_calculator.py",
    },
    {
        "name": "KpiSalePersonCalculator SSOT",
        "type": "architecture",
        "description": "KPI SalePerson revenue (Accurate Mode). Uses fn_KpiRevenueBySalePerson TVF. 23 columns from v_kpi_saleperson view. Handles XX distribution + SERV→SB mapping.",
        "file_path": "backend/app/shared/kpi_saleperson_calculator.py",
    },
    {
        "name": "ForecastingEngine SSOT",
        "type": "architecture",
        "description": "12-month revenue forecasting. 4 methods: moving_average (3-month MA ±20%), linear_regression (±25%), growth_rate (±15%), prophet (Facebook). Returns ForecastPoint with actual/forecast/bounds.",
        "file_path": "backend/app/shared/forecasting_engine.py",
    },
    {
        "name": "QueryBuilder",
        "type": "utility",
        "description": "SQL query builder with WHERE, ORDER BY, pagination. Used by BaseRepository for flexible filtering. Prevents SQL injection.",
        "file_path": "backend/app/core/query_builder.py",
    },
    {
        "name": "QueryTimer",
        "type": "utility",
        "description": "Performance monitoring context manager. Track query timing for every major query. Frontend shows QueryBreakdownDisplay.",
        "file_path": "backend/app/core/query_timer.py",
    },
    {
        "name": "ExcelStyleFactory",
        "type": "utility",
        "description": "Excel export styling. apply_header_row(), currency formatting, Thai date formatting. Used across all export endpoints.",
        "file_path": "backend/app/utils/excel_styles.py",
    },
    {
        "name": "date_utils DRY Functions",
        "type": "utility",
        "description": "format_date(), format_thai_date(DD/MM/YYYY), get_date_range(period), format_period_name('this_year'→'This Year'), get_previous_period(start, end, 'yoy'|'mom'). SSOT for all date operations.",
        "file_path": "backend/app/utils/date_utils.py",
    },
    {
        "name": "currency_utils DRY Functions",
        "type": "utility",
        "description": "calculate_growth_pct(current, previous), calculate_growth_index(), format_currency(amount, '฿'), format_baht(), format_compact(1.5M/500K), parse_currency('฿1,234.56'→Decimal). SSOT for financial formatting.",
        "file_path": "backend/app/utils/currency.py",
    },
    {
        "name": "Department Color Mapping",
        "type": "design",
        "description": "BKK=blue, BD=indigo, DIG=cyan, IM=emerald, PS=violet, PRC=amber, NonSale=slate. getDepartmentColor() returns Tailwind classes. CHART_COLORS: #8b5cf6, #3b82f6, #10b981, #f59e0b, #ef4444, #ec4899, #06b6d4, #84cc16.",
        "file_path": "frontend/src/utils/colors.ts",
    },
    {
        "name": "GP% Color Coding",
        "type": "design",
        "description": "GP% >= 20%: green-600, 10-20%: amber-600, < 10%: red-500. Positive values: emerald-600, Negative: red-600. Applied consistently across all tables.",
    },
    {
        "name": "DataStates Component",
        "type": "component",
        "description": "Unified loading/error state handler. Wraps any data display with consistent skeleton/error UI. Used across all list pages.",
        "file_path": "frontend/src/components/common/DataStates.tsx",
    },
    {
        "name": "SearchInput Component",
        "type": "component",
        "description": "Reusable search box with debounce. Icon prefix, placeholder, onChange handler. Used in customer/product/saleperson lists.",
        "file_path": "frontend/src/components/common/SearchInput.tsx",
    },
]

# ============================================================
# WTU PATTERNS
# ============================================================
WTU_PATTERNS = [
    {
        "name": "Multi-University Database Manager",
        "type": "architecture",
        "description": "UniversityDatabaseManager manages separate MSSQL connections per university (WTU→WTUDataWarehouse, NTU→NTUDataWarehouse). Runtime DB selection via X-University header. Single codebase, multiple deployments.",
        "file_path": "backend/database.py",
    },
    {
        "name": "PooledDB Connection Pool",
        "type": "infrastructure",
        "description": "DBUtils PooledDB wraps pymssql. min=5, maxcached=20, maxconnections=50, blocking=True. Eliminates ~275ms connection overhead per query. Warm-up on app startup.",
        "file_path": "backend/database.py",
    },
    {
        "name": "ThreadPoolExecutor Async Wrapper",
        "type": "infrastructure",
        "description": "50 workers wrap sync pymssql calls for FastAPI async. fetch_all(), fetch_one(), fetch_value(), execute() all use asyncio.to_thread(). 6 parallel queries: ~500ms vs ~5000ms sequential.",
        "file_path": "backend/database.py",
    },
    {
        "name": "pymssql Placeholder Conversion",
        "type": "gotcha",
        "description": "pymssql uses %s not ? for placeholders. database.py auto-converts ? → %s so service code uses ? consistently. Never use %s directly in service code.",
        "file_path": "backend/database.py",
    },
    {
        "name": "University Config SSOT",
        "type": "architecture",
        "description": "UNIVERSITY_CONFIG dict: WTU={code, name, database: WTUDataWarehouse}, NTU={code, name, database: NTUDataWarehouse}. All university-specific logic reads from this.",
        "file_path": "backend/config.py",
    },
    {
        "name": "Status/Level Label Mappings",
        "type": "architecture",
        "description": "Student status: A=ปกติ, G=จบการศึกษา, R=พ้นสภาพ, L=ลาพักการศึกษา, W=ถอนชื่อ, D=พักการศึกษา. Level: 1=ปริญญาเอก, 2=ปริญญาโท, 3=ปริญญาตรี, 4=ประกาศนียบัตร, 5=อนุปริญญา.",
    },
    {
        "name": "Teacher Enum Mappings",
        "type": "architecture",
        "description": "DegreeLevel, TeacherTitle, TeacherStatus, TeacherType enums with name_thai property. TeacherStatus.ACTIVE and ON_LEAVE both is_active=True. Raw values stored separately from mapped display values.",
    },
    {
        "name": "Status Color Mapping SSOT",
        "type": "design",
        "description": "Centralized in colors.ts. Excellent=green-500, Good=blue-500, Average=amber-500, BelowAverage=orange-500, Poor=red-500. Score>=80:green, >=60:blue, >=40:amber, <40:red. Risk: High=red, Medium=amber, Low=green.",
        "file_path": "frontend/src/utils/colors.ts",
    },
    {
        "name": "UniversityContext + localStorage",
        "type": "frontend",
        "description": "Must update localStorage BEFORE setting React state — API interceptor reads from localStorage. queryClient.resetQueries() on switch clears AND refetches. X-University header sent on every request.",
    },
    {
        "name": "Auth Token Flow",
        "type": "security",
        "description": "JWT access (60min) + refresh (7d). Token includes type field ('access'/'refresh'). Stored localStorage. 401 → clear + redirect /login. Default admin: admin/admin123 created on first startup.",
    },
    {
        "name": "MSSQL Pagination Pattern",
        "type": "query",
        "description": "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY for MSSQL pagination. Always with ORDER BY clause. Max export: 10,000 records.",
    },
]

# ============================================================
# SECA SCHEMAS (additional to existing ones)
# ============================================================
SECA_SCHEMAS = [
    {
        "table_name": "Journal",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "JournalNo", "type": "VARCHAR", "pk": True},
            {"name": "VoucherDate", "type": "DATE", "note": "NOT InvoiceDate for journal adj"},
            {"name": "type", "type": "VARCHAR", "note": "Valid: '0', '00'"},
            {"name": "Status", "type": "VARCHAR", "note": "Filter: != 'C'"},
        ]),
        "purpose": "Journal entries for revenue adjustments. Links to JournalItems.",
        "gotchas": "Use VoucherDate NOT InvoiceDate. type IN ('0', '00') AND Status != 'C'. Journal.type is lowercase.",
    },
    {
        "table_name": "JournalItems",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "JournalNo", "type": "VARCHAR", "fk": "Journal.JournalNo"},
            {"name": "Amount", "type": "DECIMAL"},
            {"name": "AccountNo", "type": "VARCHAR", "note": "4102-0000=CN, 4101-0001~0002=adj"},
            {"name": "InvoiceNo", "type": "VARCHAR"},
            {"name": "type", "type": "VARCHAR", "note": "Debit or Creadit (typo!)"},
        ]),
        "purpose": "Journal line items. CN deduction (AccountNo=4102-0000) + dept adjustments (4101-0001~0002).",
        "gotchas": "Credit type is 'Creadit' (TYPO in source DB, must match exactly). CN items have InvoiceNo LIKE 'CN%'.",
    },
    {
        "table_name": "Users",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "Id", "type": "UUID", "pk": True, "note": "OUTPUT INSERTED.Id"},
            {"name": "Username", "type": "VARCHAR", "unique": True},
            {"name": "Email", "type": "VARCHAR", "unique": True},
            {"name": "FullName", "type": "VARCHAR"},
            {"name": "Role", "type": "VARCHAR", "note": "admin, editor, user"},
            {"name": "IsActive", "type": "BIT"},
            {"name": "CreatedAt", "type": "DATETIME2"},
        ]),
        "purpose": "Dashboard user accounts. JWT auth (HS256, 4hr). Use OUTPUT INSERTED.Id not SCOPE_IDENTITY().",
        "gotchas": "MSSQL: use OUTPUT INSERTED.Id for INSERT RETURNING, NOT SCOPE_IDENTITY() (UUID PK).",
    },
]

# ============================================================
# WTU SCHEMAS
# ============================================================
WTU_SCHEMAS = [
    {
        "table_name": "wtu_dashboard_users",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "user_id", "type": "INT IDENTITY(1,1)", "pk": True},
            {"name": "username", "type": "NVARCHAR(50)", "unique": True},
            {"name": "email", "type": "NVARCHAR(100)", "unique": True},
            {"name": "password_hash", "type": "NVARCHAR(255)"},
            {"name": "full_name", "type": "NVARCHAR(100)"},
            {"name": "role", "type": "NVARCHAR(20)", "note": "CHECK: admin, viewer"},
            {"name": "is_active", "type": "BIT", "default": "1"},
            {"name": "created_at", "type": "DATETIME2"},
            {"name": "last_login", "type": "DATETIME2"},
        ]),
        "purpose": "Dashboard user accounts. Default admin created on first startup (admin/admin123).",
        "gotchas": "Uses INT IDENTITY not UUID. Indexes on username and email for lookup.",
    },
    {
        "table_name": "DimStudent",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "Id", "type": "VARCHAR", "pk": True, "note": "StudentCode"},
            {"name": "NameThai", "type": "NVARCHAR"},
            {"name": "LastNameThai", "type": "NVARCHAR"},
            {"name": "NameEng", "type": "NVARCHAR"},
            {"name": "LastNameEng", "type": "NVARCHAR"},
            {"name": "Status", "type": "CHAR(1)", "note": "A/G/R/L/W/D"},
            {"name": "LevelId", "type": "INT", "note": "1=PhD, 2=Master, 3=Bachelor, 4=Cert, 5=Diploma"},
            {"name": "DeptCode", "type": "VARCHAR"},
            {"name": "StartYear", "type": "INT", "note": "Buddhist Era year"},
        ]),
        "purpose": "Student master data. Bilingual Thai/English names. Status codes map to Thai labels.",
        "gotchas": "StartYear uses Buddhist Era (BE = CE + 543). Status labels must be mapped via SSOT dict.",
    },
    {
        "table_name": "DimTeacher",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "teacher_id", "type": "INT", "pk": True},
            {"name": "name_thai", "type": "NVARCHAR"},
            {"name": "surname_thai", "type": "NVARCHAR"},
            {"name": "title", "type": "NVARCHAR", "note": "Raw value, needs mapping"},
            {"name": "status", "type": "NVARCHAR", "note": "Raw value, needs mapping"},
            {"name": "teacher_type", "type": "NVARCHAR", "note": "Raw value, needs mapping"},
            {"name": "old_education", "type": "NVARCHAR", "note": "Raw degree, needs mapping"},
            {"name": "department_ukey", "type": "INT"},
            {"name": "division_ukey", "type": "INT"},
            {"name": "campus_id", "type": "INT"},
        ]),
        "purpose": "Teacher master data. Raw values stored separately — use enum mappings for display.",
        "gotchas": "Raw title/status/type/education values need Config*Mapping tables. LLM-matched data has confidence scores.",
    },
]

# ============================================================
# SECA ENTITY RELATIONS
# ============================================================
SECA_RELATIONS = [
    ("Customer", "Invoice", "1:N", "Customer.Code = Invoice.CustomerCode", "Customer has many Invoices"),
    ("Invoice", "InvoiceItems", "1:N", "Invoice.No = InvoiceItems.InvoiceNo", "Invoice has many Items (NEVER JOIN for revenue totals!)"),
    ("Item", "InvoiceItems", "1:N", "Item.Code = InvoiceItems.ItemCode", "Item appears in many InvoiceItems"),
    ("Invoice", "JournalItems", "1:N", "Invoice.No = JournalItems.InvoiceNo", "Invoice links to Journal entries (CN + adj)"),
    ("Journal", "JournalItems", "1:N", "Journal.JournalNo = JournalItems.JournalNo", "Journal has many line items"),
    ("v_kpi_saleperson", "Invoice", "1:N", "v_kpi_saleperson.AppCode = Invoice.SaleCode", "SalePerson (view) links to Invoices via SaleCode"),
]

# ============================================================
# WTU ENTITY RELATIONS
# ============================================================
WTU_RELATIONS = [
    ("DimStudent", "DimStudentStatus", "N:1", "DimStudent.Status = DimStudentStatus.StatusCode", "Student status lookup"),
    ("DimStudent", "DimLevel", "N:1", "DimStudent.LevelId = DimLevel.LevelId", "Student education level"),
    ("DimStudent", "DimDepartment", "N:1", "DimStudent.DeptCode = DimDepartment.DeptCode", "Student department"),
    ("DimDepartment", "DimDivision", "N:1", "DimDepartment.DivisionUKey = DimDivision.UKey", "Department belongs to Division"),
    ("DimDivision", "DimFacultyType", "N:1", "DimDivision.FacultyTypeId = DimFacultyType.Id", "Division belongs to Faculty Type"),
    ("DimDivision", "DimCampus", "N:1", "DimDivision.CampusId = DimCampus.Id", "Division belongs to Campus"),
    ("DimTeacher", "DimDepartment", "N:1", "DimTeacher.department_ukey = DimDepartment.UKey", "Teacher belongs to Department"),
]

# ============================================================
# LEARNINGS (gotchas from deep analysis)
# ============================================================
EXTRA_LEARNINGS = [
    {
        "project_code": "SECA",
        "learning_type": "gotcha",
        "category": "mssql",
        "title": "MSSQL OUTPUT INSERTED for UUID PKs",
        "insight": "Use OUTPUT INSERTED.Id not SCOPE_IDENTITY() for UUID primary keys in MSSQL. SCOPE_IDENTITY() only works with IDENTITY columns.",
    },
    {
        "project_code": "SECA",
        "learning_type": "gotcha",
        "category": "revenue",
        "title": "XX Invoice distribution by DepartmentCode",
        "insight": "SaleCode='XX' (no salesperson) invoices distributed by Invoice.DepartmentCode. SERV department mapped to SB in KPI reports. Must handle in all revenue aggregations.",
    },
    {
        "project_code": "SECA",
        "learning_type": "technical",
        "category": "architecture",
        "title": "SECA 4 SSOT Calculators",
        "insight": "RevenueCalculator (89KB), InvoiceCalculator (265 lines), KpiSalePersonCalculator (432 lines), ForecastingEngine (440 lines). ALL revenue queries MUST go through these — never hardcode GL columns.",
    },
    {
        "project_code": "SECA",
        "learning_type": "technical",
        "category": "frontend",
        "title": "SECA Primary Color Palette",
        "insight": "Primary blue: 50:#eff6ff → 900:#1e3a8a. Success:#10b981, Warning:#f59e0b, Danger:#ef4444. Chart: #8b5cf6,#3b82f6,#10b981,#f59e0b,#ef4444,#ec4899,#06b6d4,#84cc16.",
    },
    {
        "project_code": "WTUANALYSIS",
        "learning_type": "gotcha",
        "category": "database",
        "title": "pymssql uses %s not ? placeholders",
        "insight": "pymssql uses %s (not ?) for SQL placeholders. database.py auto-converts ? → %s. Never use %s directly in service code — always use ? for portability.",
    },
    {
        "project_code": "WTUANALYSIS",
        "learning_type": "gotcha",
        "category": "frontend",
        "title": "University switch: localStorage before React state",
        "insight": "Must update localStorage BEFORE setting React state on university switch — API interceptor reads from localStorage. Then queryClient.resetQueries() clears AND refetches active queries.",
    },
    {
        "project_code": "WTUANALYSIS",
        "learning_type": "technical",
        "category": "performance",
        "title": "PooledDB + ThreadPool eliminates connection overhead",
        "insight": "PooledDB (min5/max20/total50) eliminates ~275ms connection overhead per query. ThreadPoolExecutor (50 workers) wraps sync pymssql for async. 6 parallel queries: ~500ms vs ~5000ms.",
    },
    {
        "project_code": "WTUANALYSIS",
        "learning_type": "gotcha",
        "category": "auth",
        "title": "JWT token type field must be verified",
        "insight": "JWT tokens include 'type' field: 'access' vs 'refresh'. Must verify type='access' for API endpoints. Refresh token has 7-day expiry. Default admin created on first startup.",
    },
    {
        "project_code": "WTUANALYSIS",
        "learning_type": "technical",
        "category": "data",
        "title": "Buddhist Era year conversion",
        "insight": "WTU data uses Buddhist Era years (BE = CE + 543). StartYear, academic year fields all in BE. Must convert for display or comparison with CE dates.",
    },
    {
        "project_code": "WTUANALYSIS",
        "learning_type": "gotcha",
        "category": "data",
        "title": "Teacher raw values need enum mapping",
        "insight": "DimTeacher stores raw title/status/type/education values. Must use Config*Mapping tables for display. LLM-matched data includes confidence scores. ACTIVE and ON_LEAVE both count as is_active.",
    },
]

# ============================================================
# TECHNICAL DECISIONS
# ============================================================
EXTRA_DECISIONS = [
    {
        "project_code": "SECA",
        "decision_title": "4 SSOT Calculators for Domain Logic",
        "category": "architecture",
        "context": "Revenue, invoice, KPI, forecast logic scattered across repositories",
        "decision_made": "Create 4 centralized Calculator classes (RevenueCalculator, InvoiceCalculator, KpiSalePersonCalculator, ForecastingEngine) that return SQL fragments",
        "reasoning": "Single source of truth for all business calculations. Change once, all queries update. Prevents copy-paste SQL bugs.",
    },
    {
        "project_code": "SECA",
        "decision_title": "Department Color Mapping in Frontend",
        "category": "design",
        "context": "Need consistent department colors across all charts and tables",
        "decision_made": "Centralize in colors.ts: getDepartmentColor() returns Tailwind classes. CHART_COLORS array for Recharts.",
        "reasoning": "SSOT for visual consistency. Add new department → change one file.",
    },
    {
        "project_code": "WTUANALYSIS",
        "decision_title": "Multi-University Architecture",
        "category": "architecture",
        "context": "Need to support WTU and NTU from single codebase",
        "decision_made": "UniversityDatabaseManager with per-university MSSQL connections. X-University header for API selection. UniversityContext + localStorage on frontend.",
        "reasoning": "Single deployment, no code duplication. Add new university = add config entry.",
    },
    {
        "project_code": "WTUANALYSIS",
        "decision_title": "pymssql over pyodbc for macOS",
        "category": "infrastructure",
        "context": "pyodbc requires ODBC Driver installation which is problematic on macOS",
        "decision_made": "Use pymssql (pure Python) instead of pyodbc. Auto-convert ? → %s placeholders.",
        "reasoning": "No system-level driver installation needed. Works out of box on macOS.",
    },
    {
        "project_code": "WTUANALYSIS",
        "decision_title": "PooledDB + ThreadPool for Performance",
        "category": "performance",
        "context": "Sequential pymssql queries too slow (5s for 6 queries)",
        "decision_made": "PooledDB for connection reuse + ThreadPoolExecutor(50) for parallel execution",
        "reasoning": "Eliminates 275ms connection overhead. 6 parallel queries: 500ms vs 5000ms (10x improvement).",
    },
    {
        "project_code": "WTUANALYSIS",
        "decision_title": "Primary Blue Theme (not Purple)",
        "category": "design",
        "context": "University dashboard needs professional academic look",
        "decision_made": "Primary blue palette (#3b82f6 main) with status-based color coding. Same Tailwind scale as SECA.",
        "reasoning": "Blue conveys trust/professionalism for academic setting. Consistent color system with SECA project.",
    },
]

# ============================================================
# FLOWS
# ============================================================
EXTRA_FLOWS = [
    {
        "project_code": "SECA",
        "flow_name": "Authentication Flow",
        "flow_type": "auth",
        "description": "JWT-based authentication with HS256, 4hr expiry",
        "steps": json.dumps([
            {"step": 1, "action": "Login", "detail": "POST /api/users/login with username/password"},
            {"step": 2, "action": "Verify", "detail": "verify_token() checks bcrypt hash"},
            {"step": 3, "action": "Token", "detail": "JWT (HS256, 4hr) returned to frontend"},
            {"step": 4, "action": "Auth", "detail": "HTTPBearer + get_current_user() on each request"},
            {"step": 5, "action": "Admin", "detail": "require_admin() for Settings endpoint"},
        ]),
    },
    {
        "project_code": "WTUANALYSIS",
        "flow_name": "University Switch Flow",
        "flow_type": "data",
        "description": "Multi-university database switching at runtime",
        "steps": json.dumps([
            {"step": 1, "action": "User selects university", "detail": "UniversityContext.switchUniversity('NTU')"},
            {"step": 2, "action": "Update localStorage", "detail": "MUST update BEFORE React state (API interceptor reads it)"},
            {"step": 3, "action": "Reset queries", "detail": "queryClient.resetQueries() clears AND refetches active queries"},
            {"step": 4, "action": "Set state", "detail": "setCurrentUniversity(newUniversity)"},
            {"step": 5, "action": "API header", "detail": "Interceptor sends X-University header on all requests"},
            {"step": 6, "action": "Backend routing", "detail": "get_database(university) → separate MSSQL connection"},
        ]),
        "critical_notes": "localStorage must update BEFORE React state. queryClient.resetQueries() clears AND refetches.",
    },
    {
        "project_code": "WTUANALYSIS",
        "flow_name": "Student Hierarchy Query",
        "flow_type": "data",
        "description": "Student data with full organizational hierarchy",
        "steps": json.dumps([
            {"step": 1, "action": "DimStudent", "detail": "Base student record"},
            {"step": 2, "action": "JOIN DimStudentStatus", "detail": "Status label (Thai)"},
            {"step": 3, "action": "JOIN DimLevel", "detail": "Education level description"},
            {"step": 4, "action": "JOIN DimDepartment", "detail": "Department info"},
            {"step": 5, "action": "JOIN DimDivision", "detail": "Faculty division"},
            {"step": 6, "action": "JOIN DimCampus", "detail": "Campus location"},
        ]),
    },
]


async def _upsert_tech(db, pid, stack, project_code, dry_run):
    count = 0
    for tech_type, tech_name, version, purpose in stack:
        if not dry_run:
            await db.execute("""
                INSERT INTO project_tech_stack (project_id, tech_type, tech_name, version, purpose)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (project_id, tech_type, tech_name) DO UPDATE SET version = $4, purpose = $5
            """, pid, tech_type, tech_name, version, purpose)
        count += 1
    return count


async def _upsert_patterns(db, pid, patterns, project_code, dry_run):
    count = 0
    for p in patterns:
        if not dry_run:
            await db.execute("""
                INSERT INTO project_patterns (project_id, pattern_name, pattern_type, description, code_snippet, file_path, usage_example)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (project_id, pattern_name) DO UPDATE SET description = $4, file_path = $6
            """, pid, p['name'], p['type'], p['description'], p.get('code_snippet'), p.get('file_path'), p.get('usage_example'))
        count += 1
        print(f"  ✅ [{project_code}] {p['name']}")
    return count


async def main(dry_run: bool = False) -> None:
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    try:
        projects = await db.fetch("SELECT project_id, project_code FROM angela_projects")
        pid_map = {p['project_code']: p['project_id'] for p in projects}

        seca_pid = pid_map.get('SECA')
        wtu_pid = pid_map.get('WTUANALYSIS')

        if not seca_pid:
            print("❌ SECA project not found!")
            return
        if not wtu_pid:
            print("❌ WTUANALYSIS project not found!")
            return

        print(f"📁 SECA: {str(seca_pid)[:8]}...")
        print(f"📁 WTU: {str(wtu_pid)[:8]}...")

        # === 1. TECH STACKS ===
        print("\n=== 1. project_tech_stack ===")
        c1 = await _upsert_tech(db, seca_pid, SECA_TECH_STACK, "SECA", dry_run)
        c2 = await _upsert_tech(db, wtu_pid, WTU_TECH_STACK, "WTU", dry_run)
        total = await db.fetchval("SELECT COUNT(*) FROM project_tech_stack")
        print(f"  SECA: +{c1}, WTU: +{c2} | Total: {total}")

        # === 2. PATTERNS ===
        print("\n=== 2. project_patterns ===")
        await _upsert_patterns(db, seca_pid, SECA_PATTERNS, "SECA", dry_run)
        await _upsert_patterns(db, wtu_pid, WTU_PATTERNS, "WTU", dry_run)
        total = await db.fetchval("SELECT COUNT(*) FROM project_patterns")
        print(f"  Total: {total}")

        # === 3. SCHEMAS ===
        print("\n=== 3. project_schemas ===")
        for s in SECA_SCHEMAS:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_schemas (project_id, table_name, schema_type, columns, purpose, gotchas)
                    VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                    ON CONFLICT (project_id, table_name) DO NOTHING
                """, seca_pid, s['table_name'], s['schema_type'], s['columns'], s['purpose'], s.get('gotchas'))
            print(f"  ✅ [SECA] {s['table_name']}")

        for s in WTU_SCHEMAS:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_schemas (project_id, table_name, schema_type, columns, purpose, gotchas)
                    VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                    ON CONFLICT (project_id, table_name) DO NOTHING
                """, wtu_pid, s['table_name'], s['schema_type'], s['columns'], s['purpose'], s.get('gotchas'))
            print(f"  ✅ [WTU] {s['table_name']}")

        total = await db.fetchval("SELECT COUNT(*) FROM project_schemas")
        print(f"  Total: {total}")

        # === 4. ENTITY RELATIONS ===
        print("\n=== 4. project_entity_relations ===")
        for from_t, to_t, rel_type, join_cond, name in SECA_RELATIONS:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_entity_relations (project_id, from_table, to_table, relation_type, join_condition, relation_name)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (project_id, from_table, to_table, relation_type) DO NOTHING
                """, seca_pid, from_t, to_t, rel_type, join_cond, name)
            print(f"  ✅ [SECA] {from_t} → {to_t}")

        for from_t, to_t, rel_type, join_cond, name in WTU_RELATIONS:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_entity_relations (project_id, from_table, to_table, relation_type, join_condition, relation_name)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (project_id, from_table, to_table, relation_type) DO NOTHING
                """, wtu_pid, from_t, to_t, rel_type, join_cond, name)
            print(f"  ✅ [WTU] {from_t} → {to_t}")

        total = await db.fetchval("SELECT COUNT(*) FROM project_entity_relations")
        print(f"  Total: {total}")

        # === 5. LEARNINGS ===
        print("\n=== 5. project_learnings ===")
        for l in EXTRA_LEARNINGS:
            pid = pid_map.get(l['project_code'])
            if not pid:
                continue
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM project_learnings WHERE project_id = $1 AND title = $2",
                pid, l['title']
            )
            if existing > 0:
                continue
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_learnings (project_id, learning_type, category, title, insight, confidence)
                    VALUES ($1, $2, $3, $4, $5, 0.95)
                """, pid, l['learning_type'], l['category'], l['title'], l['insight'])
            print(f"  ✅ [{l['project_code']}] {l['title']}")

        total = await db.fetchval("SELECT COUNT(*) FROM project_learnings")
        print(f"  Total: {total}")

        # === 6. TECHNICAL DECISIONS ===
        print("\n=== 6. project_technical_decisions ===")
        for d in EXTRA_DECISIONS:
            pid = pid_map.get(d['project_code'])
            if not pid:
                continue
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM project_technical_decisions WHERE project_id = $1 AND decision_title = $2",
                pid, d['decision_title']
            )
            if existing > 0:
                continue
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_technical_decisions (project_id, decision_title, category, context, decision_made, reasoning, decided_by)
                    VALUES ($1, $2, $3, $4, $5, $6, 'David')
                """, pid, d['decision_title'], d['category'], d['context'], d['decision_made'], d['reasoning'])
            print(f"  ✅ [{d['project_code']}] {d['decision_title']}")

        total = await db.fetchval("SELECT COUNT(*) FROM project_technical_decisions")
        print(f"  Total: {total}")

        # === 7. FLOWS ===
        print("\n=== 7. project_flows ===")
        for f in EXTRA_FLOWS:
            pid = pid_map.get(f['project_code'])
            if not pid:
                continue
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_flows (project_id, flow_name, flow_type, description, steps, critical_notes)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                    ON CONFLICT (project_id, flow_name) DO NOTHING
                """, pid, f['flow_name'], f['flow_type'], f['description'], f['steps'], f.get('critical_notes'))
            print(f"  ✅ [{f['project_code']}] {f['flow_name']}")

        total = await db.fetchval("SELECT COUNT(*) FROM project_flows")
        print(f"  Total: {total}")

        # === FINAL SUMMARY ===
        print("\n" + "=" * 60)
        print("FINAL COUNTS (ALL PROJECTS)")
        print("=" * 60)
        for table in [
            'project_tech_stack', 'project_patterns', 'project_schemas',
            'project_entity_relations', 'project_learnings',
            'project_technical_decisions', 'project_flows',
            'project_mistakes', 'angela_technical_standards',
            'project_milestones',
        ]:
            c = await db.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table:40s} {c:>5} rows")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill SECA + WTU project data")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
