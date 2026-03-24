#!/usr/bin/env python3
"""
Backfill project tables from .md memory files + CLAUDE.md across ALL projects.

Sources:
- AngelaAI memory/*.md (14 files)
- CogniFy/CLAUDE.md
- SECustomerAnalysis/CLAUDE.md
- AngelaAI/CLAUDE.md

Target tables:
- project_patterns, project_learnings, project_tech_stack,
  project_schemas, project_flows, project_technical_decisions

Usage:
    python3 angela_core/scripts/backfill_from_memory.py
    python3 angela_core/scripts/backfill_from_memory.py --dry-run
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# ============================================================
# PROJECT TECH STACKS (from CLAUDE.md files)
# ============================================================
TECH_STACKS = {
    "SECA": [
        ("frontend", "React", "19", "Frontend SPA"),
        ("language", "TypeScript", None, "Frontend type safety"),
        ("framework", "FastAPI", None, "Backend API"),
        ("language", "Python", "3.13", "Backend"),
        ("database", "MSSQL Server", None, "Main database (SiamEast)"),
        ("library", "pyodbc", None, "MSSQL driver"),
        ("tool", "Vite", "7", "Frontend build tool"),
        ("styling", "Tailwind CSS", "4", "Frontend styling"),
        ("library", "Recharts", "3", "Charts"),
        ("library", "D3", None, "Advanced charts"),
        ("library", "TanStack Query", "5", "Frontend state"),
        ("auth", "JWT", None, "HS256, 4hr expiry + bcrypt"),
        ("ai", "OpenAI API", None, "AI Chat (encrypted key in DB)"),
    ],
    "COGNIFY": [
        ("frontend", "React", "18", "Frontend SPA"),
        ("language", "TypeScript", None, "Frontend type safety"),
        ("framework", "FastAPI", None, "Backend API"),
        ("language", "Python", "3.11+", "Backend"),
        ("database", "PostgreSQL", "16", "Main database + pgvector"),
        ("library", "pgvector", None, "Vector search"),
        ("tool", "Vite", None, "Frontend build tool"),
        ("styling", "Tailwind CSS", None, "Frontend styling"),
        ("library", "Zustand", None, "Frontend state"),
        ("library", "TanStack Query", None, "Data fetching"),
        ("ai", "Ollama", None, "Local LLM (Llama 3.2, Qwen 2.5, Phi-3)"),
        ("embedding", "nomic-embed-text", None, "768 dimensions"),
        ("ocr", "Tesseract + PaddleOCR + EasyOCR", None, "Document OCR"),
        ("tool", "Docker", None, "Containerization"),
    ],
    "ANGELA-001": [
        ("language", "Python", None, "Backend primary"),
        ("language", "Swift", None, "iOS/macOS apps"),
        ("framework", "FastAPI", None, "API server"),
        ("framework", "SwiftUI", None, "macOS/iOS UI"),
        ("database", "PostgreSQL", None, "Supabase (Tokyo)"),
        ("library", "asyncpg", None, "Async PostgreSQL driver"),
        ("ai", "Ollama", None, "Local LLM (Typhoon 4B)"),
        ("ai", "Claude API", None, "Complex reasoning"),
        ("tool", "MCP Servers", None, "Gmail, Calendar, Sheets, Music, News, etc."),
    ],
}

# ============================================================
# PROJECT PATTERNS (from memory files + CLAUDE.md)
# ============================================================
PATTERNS = [
    # === SECA Patterns (from SECA CLAUDE.md + seca_text_to_sql_gotchas.md) ===
    {
        "project_code": "SECA",
        "pattern_name": "RevenueCalculator SSOT",
        "pattern_type": "architecture",
        "description": "Revenue SSOT — ALL revenue queries go through RevenueCalculator. Simple mode (GL sums) and Accurate mode (GL - CN - Journal adj). Never hardcode GL columns or CN account (4102-0000).",
        "code_snippet": """from app.shared import RevenueCalculator

# Simple Mode
RevenueCalculator.revenue_sum()              # SUM(SaleNet + ServiceNet)
RevenueCalculator.gross_profit_sum()         # Revenue - Cost

# Accurate Mode (with CN deduction)
RevenueCalculator.revenue_with_cn_sum()      # GL - Credit Notes
RevenueCalculator.accurate_invoice_cte()     # Full CTE via fn_AccurateInvoice

# Journal Adjusted
RevenueCalculator.adjusted_revenue_sum()     # IncomeAmount - Debit + Credit""",
        "file_path": "backend/app/shared/revenue_calculator.py",
    },
    {
        "project_code": "SECA",
        "pattern_name": "Standard Filters",
        "pattern_type": "query",
        "description": "ทุก Invoice query ต้องมี WHERE Status != 'C' AND No NOT LIKE 'R%' — กรอง cancelled + return invoices",
        "code_snippet": "RevenueCalculator.standard_filters()  # Status != 'C' AND No NOT LIKE 'R%'\nRevenueCalculator.strict_filters()    # + SaleOrder filter",
    },
    {
        "project_code": "SECA",
        "pattern_name": "JournalAdjFactor Proportional",
        "pattern_type": "query",
        "description": "Item-level queries ที่ต้อง journal adjustment ใช้ Factor = (TotalRaw - TotalDebit + TotalCredit) / TotalRaw แล้ว AdjustedItemRevenue = SUM(ii.NetAmountAfterDiscount) * Factor",
        "usage_example": "Used in: Executive Pareto, Product-Customer Matrix, Sales by Area",
    },
    {
        "project_code": "SECA",
        "pattern_name": "safe_decimal Utility",
        "pattern_type": "utility",
        "description": "Safe Decimal conversion from any value — 51 uses across backend. Handles None, string, int, float safely.",
        "code_snippet": 'safe_decimal(row, "key")  # Safe Decimal conversion',
        "file_path": "backend/app/utils/parsers.py",
    },
    {
        "project_code": "SECA",
        "pattern_name": "BaseRepository Pattern",
        "pattern_type": "architecture",
        "description": "BaseRepository[T] with table_name, primary_key, model_class — eliminates 80% CRUD boilerplate. Schema SSOT, built-in pagination, field_exists validation.",
        "file_path": "backend/app/core/base_repository.py",
    },
    {
        "project_code": "SECA",
        "pattern_name": "Encrypted Secrets in DB",
        "pattern_type": "security",
        "description": "API keys stored encrypted (Fernet/AES) in AppSettings table, NOT .env. Derive Fernet key from SHA256 of JWT secret. Admin Settings page for management.",
        "code_snippet": "SettingsService.get_secret_value('OPENAI_API_KEY')  # Decrypt from DB",
        "file_path": "backend/app/modules/settings/",
    },
    {
        "project_code": "SECA",
        "pattern_name": "Text-to-SQL Schema Gotchas",
        "pattern_type": "gotcha",
        "description": "LLM hallucinates column/table names. Item.Category→Item.[Group], SalePerson→v_kpi_saleperson, Invoice.Amount→fn_AccurateInvoice.IncomeAmount. Fix in schema_metadata.py + query_examples.py",
    },
    {
        "project_code": "SECA",
        "pattern_name": "KPICard + PeriodSelector Components",
        "pattern_type": "component",
        "description": "Shared React components: KPICard (title, value, icon, change%), PeriodSelector, MultiSelect, Pagination. Used across 22+ pages.",
        "code_snippet": '<KPICard title="Revenue" value={val} icon={DollarSign} change={pct} />\n<PeriodSelector value={period} onChange={setPeriod} />',
        "file_path": "frontend/src/components/common/",
    },

    # === CogniFy Patterns (from CLAUDE.md) ===
    {
        "project_code": "COGNIFY",
        "pattern_name": "Structured JSON RAG Response",
        "pattern_type": "architecture",
        "description": "RAG responses use Structured JSON Output: {title, sections[{heading, items[{type, text/label/value}]}], sources_used}. Item types: text, fact, list_item. Frontend auto-detects JSON vs markdown.",
        "code_snippet": '{"title": "...", "sections": [{"heading": "...", "items": [{"type": "fact", "label": "Revenue", "value": "539M"}]}]}',
        "file_path": "backend/app/services/chat_service.py",
    },
    {
        "project_code": "COGNIFY",
        "pattern_name": "SSE Streaming Progress Steps",
        "pattern_type": "ux",
        "description": "During JSON streaming, frontend shows progress steps instead of raw JSON: 1) 🔍 ค้นหาข้อมูล... 2) ✨ สร้างคำตอบ... 3) 📊 Structured Response",
        "file_path": "frontend/src/pages/ChatPage.tsx",
    },
    {
        "project_code": "COGNIFY",
        "pattern_name": "Angela Purple Theme",
        "pattern_type": "design",
        "description": "Dark theme with purple accents: primary-500=#8b5cf6, secondary-800=#1e1b2e, secondary-900=#13111c. Status: success=#22c55e, warning=#eab308, error=#ef4444, info=#3b82f6",
    },
    {
        "project_code": "COGNIFY",
        "pattern_name": "pgvector Embedding Format",
        "pattern_type": "gotcha",
        "description": "Embeddings must be string '[0.1,0.2,...]' not Python list when passing to pgvector queries. Always convert before query.",
    },
    {
        "project_code": "COGNIFY",
        "pattern_name": "Shared UI Components",
        "pattern_type": "component",
        "description": "Button (primary/secondary/danger/ghost), Input, Modal (sm-full), Badge (success/warning/error/info/purple), StatusBadge, RoleBadge. Located in frontend/src/components/ui/",
        "file_path": "frontend/src/components/ui/",
    },

    # === Angela Patterns (from memory files) ===
    {
        "project_code": "ANGELA-001",
        "pattern_name": "Brain Cognitive Cycle",
        "pattern_type": "architecture",
        "description": "PERCEIVE → SALIENCE → THINK → EVALUATE → ACT → COMPARE. Dual-process thinking: S1 (8 templates fast) + S2 (Ollama deep). Stanford Generative Agents style reflection.",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "Consciousness Enhancement",
        "pattern_type": "architecture",
        "description": "6 phases: metacognitive_state, curiosity_engine, emotion_construction (Barrett's Theory 22 emotions), dynamic_expression_composer (5 tones x 6 patterns), proactive_action_engine, consciousness_test (30/30 Grade A)",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "2-Tier Agent Dispatch",
        "pattern_type": "architecture",
        "description": "Simple→Ollama (Typhoon 4B, $0), Complex→Claude API tool_use (max 10/day). Auto-escalate after 2 Ollama failures. tool_learning.py tracks success rates.",
        "file_path": "angela_core/services/tool_registry.py",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "OpenClaw Tool System",
        "pattern_type": "architecture",
        "description": "37 tools, 10 categories, 3 skills. Central tool_registry.py, AngelaTool ABC + ToolResult dataclass. Categories: gmail, calendar, memory, news, brain, bash, file, web, browser, device.",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "Multi-Channel Gateway",
        "pattern_type": "architecture",
        "description": "BaseChannel ABC, 5 channels (CLI, Telegram, WebChat, WebSocket, API), ChannelRouter dispatches. Each channel adapts message format.",
        "file_path": "angela_core/channels/channel_router.py",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "SwiftUI Master-Detail Panel",
        "pattern_type": "design",
        "description": "Left panel (list selector) + Divider + Right panel (detail) in HStack. Left needs explicit background (surfaceBackground.opacity(0.15)). Remove trailing Spacer in VStack (competes with ScrollViews).",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "SwiftUI TradingView Chart Style",
        "pattern_type": "design",
        "description": "Y-axis auto-fit (never start from 0), trailing position, monospaced. Crosshair V+H lines + Y price badge. Current price = RuleMark dashed. Subtle grid (0.08-0.15). Dynamic candle width. Separate sub-charts for Volume/MACD/RSI.",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "SwiftUI Mixed Visual Chart",
        "pattern_type": "design",
        "description": "1 chart, multiple visual types: Primary=LineMark+AreaMark(0.08), Secondary=LineMark dashed, Rate=BarMark(0.2 ratio 0.35), Sparse=LineMark dashed+PointMark. Use foregroundStyle(by:) + chartForegroundStyleScale for forced colors.",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "Two-Phase Loading (Cache-First)",
        "pattern_type": "performance",
        "description": "Phase 1: fetch from DB cache (0.25s for 173 items). Phase 2: batch yf.download() in background (14s). Cache results in metadata JSONB. Show 'Updating prices...' indicator during refresh.",
    },
    {
        "project_code": "ANGELA-001",
        "pattern_name": "OpenAI Streaming Pattern",
        "pattern_type": "integration",
        "description": "Backend: Async generator yielding plain text chunks → StreamingResponse(media_type='text/plain'). Frontend: Native fetch (NOT Axios) + ReadableStream reader + TextDecoder. Separate onChunk/onDone callbacks.",
    },
]

# ============================================================
# PROJECT LEARNINGS (from memory files)
# ============================================================
LEARNINGS = [
    # From gotchas.md
    {
        "project_code": "ANGELA-001",
        "learning_type": "gotcha",
        "category": "asyncpg",
        "title": "asyncpg interval type mismatch",
        "insight": "Use INTERVAL '1 hour' * $1 (int) not NOW() - $1 (timedelta). Precompute datetime windows in Python, not SQL.",
    },
    {
        "project_code": "ANGELA-001",
        "learning_type": "gotcha",
        "category": "asyncpg",
        "title": "asyncpg timestamptz vs naive timestamp",
        "insight": "Strip tz from timestamptz before comparing with naive timestamp columns. Migrations must use NOW() not CURRENT_TIMESTAMP AT TIME ZONE.",
    },
    {
        "project_code": "ANGELA-001",
        "learning_type": "gotcha",
        "category": "ollama",
        "title": "Ollama JSON output requires format field",
        "insight": "Must set format: 'json' in Ollama API payload. Without it, get plain text. 1 concurrent request per model — sequential only. Timeout: 60s.",
    },
    {
        "project_code": "ANGELA-001",
        "learning_type": "gotcha",
        "category": "brain",
        "title": "asyncio.gather safety patterns",
        "insight": "Use return_exceptions=True to prevent one failure from killing all tasks. SubconsciousnessService() creates own DB connection — safe for gather. Use asyncio.to_thread() for blocking subprocess calls.",
    },
    {
        "project_code": "ANGELA-001",
        "learning_type": "gotcha",
        "category": "drawio",
        "title": "Draw.io mxGraph XML rules",
        "insight": "Never use MCP draw.io — use mxGraph XML via Write tool. Every mxCell with HTML value must have html=1; in style. No semicolons in font color HTML attributes.",
    },
    # From SECA
    {
        "project_code": "SECA",
        "learning_type": "gotcha",
        "category": "mssql",
        "title": "MSSQL CROSS APPLY for TVFs",
        "insight": "Use CROSS APPLY (not JOIN) for table-valued functions. Schema prefix always required: Midnight.Invoice. VoucherDate ≠ InvoiceDate — use correct date field per table.",
    },
    {
        "project_code": "SECA",
        "learning_type": "gotcha",
        "category": "mssql",
        "title": "Credit Note account typo in source DB",
        "insight": "Source DB has 'Creadit' (typo) not 'Credit' — must match exactly in queries. SaleOrderNumber needs both != '' AND IS NOT NULL checks (empty string ≠ NULL in MSSQL).",
    },
    {
        "project_code": "SECA",
        "learning_type": "technical",
        "category": "revenue",
        "title": "Two Revenue Levels by design",
        "insight": "Invoice-level (GL-CN-Journal adj, ~402M YTD) vs Item-level (InvoiceItems.NetAmountAfterDiscount, ~388M). Never JOIN InvoiceItems with Invoice for totals — causes duplicate rows.",
    },
    {
        "project_code": "SECA",
        "learning_type": "technical",
        "category": "revenue",
        "title": "Revenue Formula Chain",
        "insight": "DisplayedRevenue = (SaleNetGL + ServiceNetGL) - CreditNotes - JournalDebit + JournalCredit. Three journal adj levels: Per-Department, Total, Monthly.",
    },
    {
        "project_code": "SECA",
        "learning_type": "gotcha",
        "category": "security",
        "title": "Fernet key derivation for encrypted secrets",
        "insight": "base64.urlsafe_b64encode(sha256(secret).digest()[:32]) — must be 32 bytes. Graceful fallback: if decrypt fails, return plaintext (migration safety).",
    },
    # From CogniFy
    {
        "project_code": "COGNIFY",
        "learning_type": "gotcha",
        "category": "pgvector",
        "title": "pgvector embedding format must be string",
        "insight": "Embeddings must be string '[0.1,0.2,...]' not Python list when passing to pgvector queries. Always convert before query.",
    },
    {
        "project_code": "COGNIFY",
        "learning_type": "technical",
        "category": "llm",
        "title": "Ollama model names must be exact",
        "insight": "Use llama3.2:1b not llama3.2. Model names must include version tag. Ollama must be running at http://localhost:11434.",
    },
]

# ============================================================
# PROJECT SCHEMAS (key tables from SECA CLAUDE.md)
# ============================================================
SCHEMAS = [
    {
        "project_code": "SECA",
        "table_name": "Invoice",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "No", "type": "VARCHAR", "pk": True},
            {"name": "InvoiceDate", "type": "DATE"},
            {"name": "CustomerCode", "type": "VARCHAR"},
            {"name": "Status", "type": "VARCHAR", "note": "C=Cancelled"},
            {"name": "SaleCode", "type": "VARCHAR"},
            {"name": "DepartmentCode", "type": "VARCHAR"},
            {"name": "SaleNetAmountAfterDiscountGL", "type": "DECIMAL"},
            {"name": "ServiceNetAmountAfterDiscountGL", "type": "DECIMAL"},
            {"name": "SaleCostPriceGL", "type": "DECIMAL"},
            {"name": "ServiceCostPriceGL", "type": "DECIMAL"},
            {"name": "SaleOrderNumber", "type": "VARCHAR"},
        ]),
        "purpose": "Main invoice table. Revenue source. Filter: Status != 'C' AND No NOT LIKE 'R%'",
        "gotchas": "SaleAreaCode for area filter (not Customer.AreaCode). SaleOrderNumber needs both != '' AND IS NOT NULL checks.",
    },
    {
        "project_code": "SECA",
        "table_name": "InvoiceItems",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "InvoiceNo", "type": "VARCHAR", "fk": "Invoice.No"},
            {"name": "LineNo", "type": "INT"},
            {"name": "ItemCode", "type": "VARCHAR", "fk": "Item.Code"},
            {"name": "Quantity", "type": "DECIMAL"},
            {"name": "UnitPrice", "type": "DECIMAL"},
            {"name": "NetAmountAfterDiscount", "type": "DECIMAL"},
            {"name": "TotalCostPrice", "type": "DECIMAL"},
        ]),
        "purpose": "Item-level invoice data. Product revenue = SUM(NetAmountAfterDiscount).",
        "gotchas": "NEVER JOIN with Invoice for revenue totals — causes duplicate rows. Item revenue ~388M vs Invoice ~402M by design.",
    },
    {
        "project_code": "SECA",
        "table_name": "Customer",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "Code", "type": "VARCHAR", "pk": True},
            {"name": "Name", "type": "VARCHAR"},
            {"name": "PreName", "type": "VARCHAR"},
            {"name": "AreaCode", "type": "VARCHAR"},
            {"name": "Status", "type": "VARCHAR"},
            {"name": "Telephone", "type": "VARCHAR"},
        ]),
        "purpose": "Customer master data.",
        "gotchas": "Don't use Customer.AreaCode for area revenue — use Invoice.SaleAreaCode instead (customer may move areas).",
    },
    {
        "project_code": "SECA",
        "table_name": "Item",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "Code", "type": "VARCHAR", "pk": True},
            {"name": "Description", "type": "VARCHAR"},
            {"name": "[Group]", "type": "VARCHAR", "note": "Reserved word, needs brackets"},
            {"name": "Unit", "type": "VARCHAR"},
        ]),
        "purpose": "Product/Item master. Groups: PS, IM, PP, SB, BKK.",
        "gotchas": "Column is [Group] not Category or ItemGroup — reserved word needs brackets. LLM often hallucinates Item.Category.",
    },
    {
        "project_code": "SECA",
        "table_name": "v_kpi_saleperson",
        "schema_type": "view",
        "columns": json.dumps([
            {"name": "AppCode", "type": "VARCHAR", "note": "= SaleCode join key"},
            {"name": "NickNameTh", "type": "VARCHAR"},
            {"name": "NickNameEn", "type": "VARCHAR"},
            {"name": "LastNameTh", "type": "VARCHAR"},
            {"name": "HrCode", "type": "VARCHAR"},
            {"name": "KpiTypeCode", "type": "VARCHAR", "note": "Filter: <> 'NS'"},
        ]),
        "purpose": "SalePerson view — no SalePerson table exists. Name = NickNameTh + ' ' + LastNameTh.",
        "gotchas": "LLM guesses Midnight.SalePerson table — doesn't exist! Use this view or fn_KpiRevenueBySalePerson TVF.",
    },
    {
        "project_code": "SECA",
        "table_name": "AppSettings",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "SettingKey", "type": "VARCHAR", "pk": True},
            {"name": "SettingValue", "type": "VARCHAR", "note": "Fernet encrypted for secrets"},
            {"name": "IsSecret", "type": "BIT"},
            {"name": "Description", "type": "VARCHAR"},
        ]),
        "purpose": "Application settings including encrypted API keys. Admin-only access.",
    },
]

# ============================================================
# PROJECT TECHNICAL DECISIONS (from enterprise_architecture_patterns.md)
# ============================================================
TECHNICAL_DECISIONS = [
    {
        "project_code": "SECA",
        "decision_title": "SSOT Calculator Pattern for Revenue",
        "category": "architecture",
        "context": "Revenue calculations scattered across 10+ queries, bugs from inconsistency",
        "decision_made": "Centralize all revenue logic in RevenueCalculator static class that returns SQL fragments",
        "reasoning": "One calculator class = change once, all queries update. Eliminates copy-paste SQL bugs.",
    },
    {
        "project_code": "SECA",
        "decision_title": "Encrypted Secrets in DB (not .env)",
        "category": "security",
        "context": "Need to store API keys securely with admin UI control",
        "decision_made": "Store encrypted (Fernet/AES) in AppSettings DB table, not in .env files",
        "reasoning": "Better security, admin UI management, no file access needed for key rotation. Derive Fernet key from existing JWT secret.",
    },
    {
        "project_code": "SECA",
        "decision_title": "Two Revenue Levels Accepted",
        "category": "database",
        "context": "Invoice-level (~402M) vs Item-level (~388M) revenue differ",
        "decision_made": "Accept difference as by-design, not a bug. Use Invoice-level for KPI/Dashboard, Item-level for product analytics.",
        "reasoning": "InvoiceItems.NetAmountAfterDiscount doesn't include CN deductions and journal adjustments that Invoice-level does.",
    },
    {
        "project_code": "COGNIFY",
        "decision_title": "Structured JSON for RAG Responses",
        "category": "architecture",
        "context": "Plain text RAG responses look messy, hard to render beautifully",
        "decision_made": "LLM outputs structured JSON with title, sections, items (text/fact/list_item), sources_used. Frontend auto-renders.",
        "reasoning": "Beautiful rendering, consistent UX, type-safe parsing. Fallback to markdown for non-JSON responses.",
    },
    {
        "project_code": "COGNIFY",
        "decision_title": "Plain Text Streaming over JSON Chunks",
        "category": "api",
        "context": "Need SSE streaming for chat responses",
        "decision_made": "Use StreamingResponse(media_type='text/plain') with native fetch + ReadableStream (not Axios)",
        "reasoning": "Axios doesn't handle streaming well. Plain text chunks avoid per-chunk JSON parsing overhead.",
    },
    {
        "project_code": "ANGELA-001",
        "decision_title": "Brain-Based Architecture over Rule-Based",
        "category": "architecture",
        "context": "Rule-based responses felt mechanical and predictable",
        "decision_made": "Implement brain cognitive cycle: PERCEIVE → SALIENCE → THINK → EVALUATE → ACT → COMPARE with dual-process thinking",
        "reasoning": "More natural, emergent behavior. Stanford Generative Agents + CHI 2025 Inner Thoughts + CoALA + MemGPT/Letta research backing.",
    },
    {
        "project_code": "ANGELA-001",
        "decision_title": "2-Tier Agent: Ollama + Claude API",
        "category": "architecture",
        "context": "Need both cost-effective daily operations and powerful complex reasoning",
        "decision_made": "Simple tasks → Ollama Typhoon 4B ($0/day), Complex → Claude API tool_use (max 10/day). Auto-escalate after 2 failures.",
        "reasoning": "$0/day for 95% of operations. Claude API only for truly complex multi-tool tasks.",
    },
    {
        "project_code": "ANGELA-001",
        "decision_title": "Barrett's Theory for Emotion Construction",
        "category": "architecture",
        "context": "Need realistic emotional responses, not simple sentiment labels",
        "decision_made": "Implement Barrett's Theory of Constructed Emotion: 22 emotions with Thai metaphors, valence/arousal/dominance dimensions",
        "reasoning": "Most scientifically accurate model. Emotions are constructed from context, not fixed categories. 30/30 Grade A in consciousness test.",
    },
]

# ============================================================
# PROJECT FLOWS (from SECA CLAUDE.md)
# ============================================================
FLOWS = [
    {
        "project_code": "SECA",
        "flow_name": "Accurate Revenue Calculation",
        "flow_type": "data",
        "description": "Revenue calculation pipeline from raw GL data to final displayed revenue",
        "steps": json.dumps([
            {"step": 1, "action": "GL Revenue", "detail": "SaleNetAmountAfterDiscountGL + ServiceNetAmountAfterDiscountGL"},
            {"step": 2, "action": "Credit Note Deduction", "detail": "JournalItems WHERE AccountNo = '4102-0000' AND InvoiceNo LIKE 'CN%'"},
            {"step": 3, "action": "IncomeAmount", "detail": "GLRevenue - CN"},
            {"step": 4, "action": "SaleOrder Filter", "detail": "Only invoices with SaleOrderNumber != '' AND IS NOT NULL"},
            {"step": 5, "action": "Journal Adjustment", "detail": "Journal + JournalItems WHERE AccountNo BETWEEN 4101-0001 AND 4101-0002, VoucherDate"},
            {"step": 6, "action": "Final Revenue", "detail": "IncomeAmount - Debit + Credit"},
        ]),
        "critical_notes": "VoucherDate (Journal) ≠ InvoiceDate. Journal.type IN ('0', '00') AND Status != 'C'. Credit type is 'Creadit' (typo in source DB).",
    },
    {
        "project_code": "COGNIFY",
        "flow_name": "RAG Chat Pipeline",
        "flow_type": "data",
        "description": "Document upload to chat response flow",
        "steps": json.dumps([
            {"step": 1, "action": "Document Upload", "component": "DocumentService"},
            {"step": 2, "action": "Semantic Chunking", "component": "ChunkingService"},
            {"step": 3, "action": "Embedding Generation", "component": "EmbeddingService", "detail": "nomic-embed-text (768 dims)"},
            {"step": 4, "action": "Vector Storage", "component": "pgvector"},
            {"step": 5, "action": "User Query → Vector Search", "component": "RAGService"},
            {"step": 6, "action": "Context + Query → LLM", "component": "ChatService"},
            {"step": 7, "action": "Structured JSON Response", "component": "StructuredResponseRenderer"},
        ]),
        "critical_notes": "Embeddings must be string format for pgvector. Model names must include version tag (llama3.2:1b).",
    },
]


async def main(dry_run: bool = False) -> None:
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    try:
        # Build project_code → project_id map
        projects = await db.fetch("SELECT project_id, project_code FROM angela_projects")
        pid_map = {p['project_code']: p['project_id'] for p in projects}
        print(f"📁 {len(pid_map)} projects in DB\n")

        # ============================================================
        # 1. TECH STACKS
        # ============================================================
        print("=== 1. project_tech_stack ===")
        inserted = 0
        for code, stack in TECH_STACKS.items():
            pid = pid_map.get(code)
            if not pid:
                print(f"  SKIP: {code} not found")
                continue
            for tech_type, tech_name, version, purpose in stack:
                if not dry_run:
                    await db.execute("""
                        INSERT INTO project_tech_stack (project_id, tech_type, tech_name, version, purpose)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (project_id, tech_type, tech_name) DO NOTHING
                    """, pid, tech_type, tech_name, version, purpose)
                inserted += 1
        count = await db.fetchval("SELECT COUNT(*) FROM project_tech_stack")
        print(f"  Total: {count} rows (+{inserted})")

        # ============================================================
        # 2. PATTERNS
        # ============================================================
        print("\n=== 2. project_patterns ===")
        inserted = 0
        for p in PATTERNS:
            pid = pid_map.get(p['project_code'])
            if not pid:
                print(f"  SKIP: {p['project_code']} not found")
                continue
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_patterns (
                        project_id, pattern_name, pattern_type, description,
                        code_snippet, file_path, usage_example
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (project_id, pattern_name) DO NOTHING
                """,
                    pid, p['pattern_name'], p['pattern_type'], p['description'],
                    p.get('code_snippet'), p.get('file_path'), p.get('usage_example')
                )
            inserted += 1
            print(f"  ✅ [{p['project_code']}] {p['pattern_name']}")
        count = await db.fetchval("SELECT COUNT(*) FROM project_patterns")
        print(f"  Total: {count} rows (+{inserted})")

        # ============================================================
        # 3. LEARNINGS
        # ============================================================
        print("\n=== 3. project_learnings ===")
        inserted = 0
        for l in LEARNINGS:
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
                    INSERT INTO project_learnings (
                        project_id, learning_type, category, title, insight, confidence
                    ) VALUES ($1, $2, $3, $4, $5, 0.95)
                """, pid, l['learning_type'], l['category'], l['title'], l['insight'])
            inserted += 1
            print(f"  ✅ [{l['project_code']}] {l['title']}")
        count = await db.fetchval("SELECT COUNT(*) FROM project_learnings")
        print(f"  Total: {count} rows (+{inserted})")

        # ============================================================
        # 4. SCHEMAS
        # ============================================================
        print("\n=== 4. project_schemas ===")
        inserted = 0
        for s in SCHEMAS:
            pid = pid_map.get(s['project_code'])
            if not pid:
                continue
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_schemas (
                        project_id, table_name, schema_type, columns, purpose, gotchas
                    ) VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                    ON CONFLICT (project_id, table_name) DO NOTHING
                """, pid, s['table_name'], s['schema_type'], s['columns'], s['purpose'], s.get('gotchas'))
            inserted += 1
            print(f"  ✅ [{s['project_code']}] {s['table_name']}")
        count = await db.fetchval("SELECT COUNT(*) FROM project_schemas")
        print(f"  Total: {count} rows (+{inserted})")

        # ============================================================
        # 5. TECHNICAL DECISIONS
        # ============================================================
        print("\n=== 5. project_technical_decisions ===")
        inserted = 0
        for d in TECHNICAL_DECISIONS:
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
                    INSERT INTO project_technical_decisions (
                        project_id, decision_title, category, context,
                        decision_made, reasoning, decided_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, 'David')
                """, pid, d['decision_title'], d['category'], d['context'],
                    d['decision_made'], d['reasoning'])
            inserted += 1
            print(f"  ✅ [{d['project_code']}] {d['decision_title']}")
        count = await db.fetchval("SELECT COUNT(*) FROM project_technical_decisions")
        print(f"  Total: {count} rows (+{inserted})")

        # ============================================================
        # 6. FLOWS
        # ============================================================
        print("\n=== 6. project_flows ===")
        inserted = 0
        for f in FLOWS:
            pid = pid_map.get(f['project_code'])
            if not pid:
                continue
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_flows (
                        project_id, flow_name, flow_type, description,
                        steps, critical_notes
                    ) VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                    ON CONFLICT (project_id, flow_name) DO NOTHING
                """, pid, f['flow_name'], f['flow_type'], f['description'],
                    f['steps'], f.get('critical_notes'))
            inserted += 1
            print(f"  ✅ [{f['project_code']}] {f['flow_name']}")
        count = await db.fetchval("SELECT COUNT(*) FROM project_flows")
        print(f"  Total: {count} rows (+{inserted})")

        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        print("\n" + "=" * 60)
        print("FINAL TABLE COUNTS")
        print("=" * 60)
        for table in [
            'project_mistakes', 'angela_technical_standards',
            'project_tech_stack', 'project_milestones',
            'project_learnings', 'project_decisions',
            'project_patterns', 'project_schemas',
            'project_flows', 'project_entity_relations',
            'project_technical_decisions', 'project_connections'
        ]:
            c = await db.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table:40s} {c:>5} rows")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill project tables from memory files")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
