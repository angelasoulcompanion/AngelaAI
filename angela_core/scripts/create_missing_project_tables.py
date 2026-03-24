#!/usr/bin/env python3
"""
Create 12 missing project tables in Supabase.

All FKs point to angela_projects (Supabase), NOT local 'projects' table.
Columns match actual INSERT/SELECT in existing code.

Usage:
    python3 angela_core/scripts/create_missing_project_tables.py
    python3 angela_core/scripts/create_missing_project_tables.py --dry-run
"""

import argparse
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

DDL = """
-- ============================================================
-- 1. project_mistakes
--    Used by: init.py, generate_claude_md.py, correction_extractor.py
-- ============================================================
CREATE TABLE IF NOT EXISTS project_mistakes (
    mistake_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID,
    mistake_type VARCHAR(30) DEFAULT 'workflow'
        CHECK (mistake_type IN (
            'bug', 'config_error', 'assumption', 'compatibility',
            'performance', 'security', 'data_issue', 'integration',
            'workflow', 'gotcha'
        )),
    severity VARCHAR(10) DEFAULT 'medium'
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    category VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    what_happened TEXT,
    how_to_prevent TEXT,
    auto_warn BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mistakes_project ON project_mistakes(project_id);
CREATE INDEX IF NOT EXISTS idx_mistakes_auto_warn ON project_mistakes(auto_warn) WHERE auto_warn = TRUE;
CREATE INDEX IF NOT EXISTS idx_mistakes_severity ON project_mistakes(severity);

-- ============================================================
-- 2. angela_technical_standards
--    Used by: generate_claude_md.py, preference_learning_service.py
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_technical_standards (
    standard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technique_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    description TEXT,
    importance_level INTEGER DEFAULT 5 CHECK (importance_level BETWEEN 1 AND 10),
    why_important TEXT,
    examples TEXT,
    anti_patterns TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_standards_category ON angela_technical_standards(category);
CREATE INDEX IF NOT EXISTS idx_standards_importance ON angela_technical_standards(importance_level DESC);

-- ============================================================
-- 3. project_milestones
--    Used by: project_tracking_service.py
-- ============================================================
CREATE TABLE IF NOT EXISTS project_milestones (
    milestone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID,
    milestone_type VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    significance INTEGER DEFAULT 5,
    celebration_note TEXT,
    achieved_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_milestones_project ON project_milestones(project_id);

-- ============================================================
-- 4. project_learnings
--    Used by: project_tracking_service.py
-- ============================================================
CREATE TABLE IF NOT EXISTS project_learnings (
    learning_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID,
    learning_type VARCHAR(30) NOT NULL,
    category VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    insight TEXT NOT NULL,
    context TEXT,
    applicable_to TEXT[] DEFAULT '{}',
    confidence FLOAT DEFAULT 0.8,
    learned_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_learnings_project ON project_learnings(project_id);

-- ============================================================
-- 5. project_decisions
--    Used by: project_tracking_service.py
-- ============================================================
CREATE TABLE IF NOT EXISTS project_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID,
    decision_type VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    context TEXT,
    options_considered JSONB,
    decision_made TEXT NOT NULL,
    reasoning TEXT,
    decided_by VARCHAR(50) DEFAULT 'together',
    decided_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_project ON project_decisions(project_id);

-- ============================================================
-- 6. project_tech_stack
--    Used by: project_tracking_service.py (_detect_tech_stack)
-- ============================================================
CREATE TABLE IF NOT EXISTS project_tech_stack (
    tech_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    tech_type VARCHAR(30) NOT NULL,
    tech_name VARCHAR(100) NOT NULL,
    version VARCHAR(30),
    purpose TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, tech_type, tech_name)
);

CREATE INDEX IF NOT EXISTS idx_tech_stack_project ON project_tech_stack(project_id);

-- ============================================================
-- 7. project_patterns
--    Used by: project_memory_service.py, seed_project_patterns.py
--    FK changed: projects → angela_projects
-- ============================================================
CREATE TABLE IF NOT EXISTS project_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    pattern_name VARCHAR(100) NOT NULL,
    pattern_type VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    code_snippet TEXT,
    file_path VARCHAR(255),
    usage_example TEXT,
    parameters JSONB,
    returns TEXT,
    depends_on TEXT[] DEFAULT '{}',
    used_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, pattern_name)
);

CREATE INDEX IF NOT EXISTS idx_patterns_project ON project_patterns(project_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON project_patterns(pattern_type);

-- ============================================================
-- 8. project_schemas
--    Used by: project_memory_service.py
--    FK changed: projects → angela_projects
-- ============================================================
CREATE TABLE IF NOT EXISTS project_schemas (
    schema_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    table_name VARCHAR(100) NOT NULL,
    schema_type VARCHAR(30) DEFAULT 'table',
    columns JSONB NOT NULL,
    primary_key VARCHAR(100),
    foreign_keys JSONB,
    indexes JSONB,
    purpose TEXT NOT NULL,
    important_queries TEXT,
    gotchas TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, table_name)
);

CREATE INDEX IF NOT EXISTS idx_schemas_project ON project_schemas(project_id);

-- ============================================================
-- 9. project_flows
--    Used by: project_memory_service.py
--    FK changed: projects → angela_projects
-- ============================================================
CREATE TABLE IF NOT EXISTS project_flows (
    flow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    flow_name VARCHAR(100) NOT NULL,
    flow_type VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    steps JSONB NOT NULL,
    entry_point VARCHAR(255),
    exit_point VARCHAR(255),
    diagram_path VARCHAR(255),
    critical_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, flow_name)
);

CREATE INDEX IF NOT EXISTS idx_flows_project ON project_flows(project_id);

-- ============================================================
-- 10. project_entity_relations
--     Used by: project_memory_service.py
--     FK changed: projects → angela_projects
-- ============================================================
CREATE TABLE IF NOT EXISTS project_entity_relations (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    from_table VARCHAR(100) NOT NULL,
    to_table VARCHAR(100) NOT NULL,
    relation_type VARCHAR(20) NOT NULL,
    relation_name VARCHAR(100),
    join_condition TEXT NOT NULL,
    is_required BOOLEAN DEFAULT TRUE,
    cascade_behavior VARCHAR(30),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, from_table, to_table, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_relations_project ON project_entity_relations(project_id);

-- ============================================================
-- 11. project_technical_decisions
--     Used by: project_memory_service.py
--     FK changed: projects → angela_projects
-- ============================================================
CREATE TABLE IF NOT EXISTS project_technical_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    decision_title VARCHAR(200) NOT NULL,
    category VARCHAR(30) NOT NULL,
    context TEXT NOT NULL,
    options_considered JSONB,
    decision_made TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    consequences TEXT,
    decided_at TIMESTAMPTZ DEFAULT NOW(),
    decided_by VARCHAR(50) DEFAULT 'David',
    status VARCHAR(20) DEFAULT 'active',
    superseded_by UUID REFERENCES project_technical_decisions(decision_id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tech_decisions_project ON project_technical_decisions(project_id);
CREATE INDEX IF NOT EXISTS idx_tech_decisions_status ON project_technical_decisions(status);

-- ============================================================
-- 12. project_connections
--     Used by: project_connections.py
--     Moved from local DB to Neon
-- ============================================================
CREATE TABLE IF NOT EXISTS project_connections (
    connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name VARCHAR(100) NOT NULL,
    connection_name VARCHAR(100) NOT NULL,
    db_type VARCHAR(30) NOT NULL,
    host VARCHAR(255),
    port INTEGER,
    database_name VARCHAR(100),
    username VARCHAR(100),
    connection_string TEXT,
    connection_hint TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_name, connection_name)
);

CREATE INDEX IF NOT EXISTS idx_connections_project ON project_connections(project_name);

-- ============================================================
-- TRIGGERS: Auto-update updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT unnest(ARRAY[
            'angela_technical_standards',
            'project_patterns', 'project_schemas',
            'project_flows', 'project_connections'
        ])
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS update_%s_updated_at ON %I;
             CREATE TRIGGER update_%s_updated_at
                BEFORE UPDATE ON %I
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();',
            tbl, tbl, tbl, tbl
        );
    END LOOP;
END $$;
"""


async def main(dry_run: bool = False) -> None:
    from angela_core.database import AngelaDatabase

    if dry_run:
        print("=== DRY RUN — SQL to execute ===")
        print(DDL)
        return

    db = AngelaDatabase()
    await db.connect()

    try:
        # Execute DDL
        await db.execute(DDL)
        print("✅ All 12 tables created successfully!\n")

        # Verify
        tables = await db.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (table_name LIKE 'project_%' OR table_name = 'angela_technical_standards')
            ORDER BY table_name
        """)

        print("=== Project tables in Neon ===")
        for t in tables:
            count = await db.fetchval(f"SELECT COUNT(*) FROM {t['table_name']}")
            print(f"  ✅ {t['table_name']}: {count} rows")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create missing project tables in Neon")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
