-- ============================================================
-- Project Technical Memory Tables
-- Created: 2026-01-12
-- Purpose: Store technical knowledge for each project
--          to enable fast and accurate recall
-- Location: LOCAL PostgreSQL (not Neon Cloud)
-- ============================================================

-- ============================================================
-- 1. PROJECTS (Master Table)
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name VARCHAR(100) NOT NULL UNIQUE,
    project_code VARCHAR(20) NOT NULL UNIQUE,  -- e.g., 'WTU', 'NAVIGO', 'ANGELA'
    description TEXT,
    tech_stack JSONB,  -- {"backend": "FastAPI", "frontend": "React", "db": "PostgreSQL"}
    repository_url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    last_worked_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE projects IS 'Master table for all projects Angela works on';
COMMENT ON COLUMN projects.project_code IS 'Short code for quick reference (e.g., WTU, NAVIGO)';
COMMENT ON COLUMN projects.tech_stack IS 'JSON object with backend, frontend, db, etc.';

-- ============================================================
-- 2. PROJECT_FLOWS (Business & Data Flows)
-- ============================================================
CREATE TABLE IF NOT EXISTS project_flows (
    flow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    flow_name VARCHAR(100) NOT NULL,
    flow_type VARCHAR(30) NOT NULL,  -- 'business', 'data', 'api', 'deployment', 'auth'
    description TEXT NOT NULL,
    steps JSONB NOT NULL,  -- [{step: 1, action: "User login", component: "AuthService"}]
    entry_point VARCHAR(255),  -- file path or endpoint
    exit_point VARCHAR(255),
    diagram_path VARCHAR(255),  -- path to draw.io diagram
    critical_notes TEXT,  -- gotchas, edge cases
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, flow_name)
);

COMMENT ON TABLE project_flows IS 'Business, data, API, and deployment flows for each project';
COMMENT ON COLUMN project_flows.flow_type IS 'Type: business, data, api, deployment, auth';
COMMENT ON COLUMN project_flows.steps IS 'JSON array of steps with action and component';
COMMENT ON COLUMN project_flows.critical_notes IS 'Important gotchas and edge cases to remember';

-- ============================================================
-- 3. PROJECT_SCHEMAS (Database Structure)
-- ============================================================
CREATE TABLE IF NOT EXISTS project_schemas (
    schema_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    table_name VARCHAR(100) NOT NULL,
    schema_type VARCHAR(30) DEFAULT 'table',  -- 'table', 'view', 'materialized_view', 'function'
    columns JSONB NOT NULL,  -- [{name: "id", type: "UUID", pk: true, fk: null, nullable: false}]
    primary_key VARCHAR(100),
    foreign_keys JSONB,  -- [{column: "user_id", references: "users.id", on_delete: "CASCADE"}]
    indexes JSONB,  -- [{name: "idx_email", columns: ["email"], type: "btree", unique: true}]
    purpose TEXT NOT NULL,  -- what this table does
    important_queries TEXT,  -- common queries for this table
    gotchas TEXT,  -- NULL handling, performance tips, edge cases
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, table_name)
);

COMMENT ON TABLE project_schemas IS 'Database schema details for each project table';
COMMENT ON COLUMN project_schemas.columns IS 'JSON array of column definitions';
COMMENT ON COLUMN project_schemas.gotchas IS 'NULL handling, performance tips, edge cases to remember';
COMMENT ON COLUMN project_schemas.important_queries IS 'Common/complex queries for this table';

-- ============================================================
-- 4. PROJECT_ENTITY_RELATIONS (ER Relationships)
-- ============================================================
CREATE TABLE IF NOT EXISTS project_entity_relations (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    from_table VARCHAR(100) NOT NULL,
    to_table VARCHAR(100) NOT NULL,
    relation_type VARCHAR(20) NOT NULL,  -- '1:1', '1:N', 'N:M'
    relation_name VARCHAR(100),  -- e.g., "Student belongs to Class"
    join_condition TEXT NOT NULL,  -- e.g., "students.class_id = classes.id"
    is_required BOOLEAN DEFAULT true,  -- is this a required relationship?
    cascade_behavior VARCHAR(30),  -- 'CASCADE', 'SET NULL', 'RESTRICT', 'NO ACTION'
    notes TEXT,  -- additional context about this relationship
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, from_table, to_table, relation_type)
);

COMMENT ON TABLE project_entity_relations IS 'Entity-Relationship mappings with exact JOIN conditions';
COMMENT ON COLUMN project_entity_relations.join_condition IS 'Exact SQL JOIN condition to use';
COMMENT ON COLUMN project_entity_relations.relation_type IS 'Cardinality: 1:1, 1:N, N:M';

-- ============================================================
-- 5. PROJECT_PATTERNS (DRY & Reusable Code)
-- ============================================================
CREATE TABLE IF NOT EXISTS project_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    pattern_name VARCHAR(100) NOT NULL,
    pattern_type VARCHAR(30) NOT NULL,  -- 'utility', 'decorator', 'hook', 'component', 'service', 'query', 'middleware'
    description TEXT NOT NULL,
    code_snippet TEXT,  -- actual reusable code
    file_path VARCHAR(255),  -- where it lives in the codebase
    usage_example TEXT,  -- how to use it
    parameters JSONB,  -- [{name: "user_id", type: "UUID", required: true, description: "..."}]
    returns TEXT,  -- return type/structure description
    depends_on TEXT[],  -- other patterns/modules it needs
    used_count INTEGER DEFAULT 0,  -- times this pattern was referenced
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, pattern_name)
);

COMMENT ON TABLE project_patterns IS 'Reusable code patterns to enforce DRY principle';
COMMENT ON COLUMN project_patterns.pattern_type IS 'Type: utility, decorator, hook, component, service, query, middleware';
COMMENT ON COLUMN project_patterns.code_snippet IS 'Actual reusable code snippet';
COMMENT ON COLUMN project_patterns.used_count IS 'Track how often this pattern is reused';

-- ============================================================
-- 6. PROJECT_TECHNICAL_DECISIONS (Architecture Decision Records)
-- ============================================================
CREATE TABLE IF NOT EXISTS project_technical_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    decision_title VARCHAR(200) NOT NULL,
    category VARCHAR(30) NOT NULL,  -- 'architecture', 'database', 'api', 'security', 'performance', 'testing'
    context TEXT NOT NULL,  -- why this decision was needed
    options_considered JSONB,  -- [{option: "Option A", pros: ["..."], cons: ["..."]}]
    decision_made TEXT NOT NULL,  -- what was chosen
    reasoning TEXT NOT NULL,  -- why this was chosen
    consequences TEXT,  -- what changed as result
    decided_at TIMESTAMP DEFAULT NOW(),
    decided_by VARCHAR(50) DEFAULT 'David',  -- who made decision
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'superseded', 'deprecated'
    superseded_by UUID REFERENCES project_technical_decisions(decision_id),
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE project_technical_decisions IS 'Architecture Decision Records (ADR) for each project';
COMMENT ON COLUMN project_technical_decisions.options_considered IS 'JSON array of options with pros/cons';
COMMENT ON COLUMN project_technical_decisions.status IS 'Status: active, superseded, deprecated';

-- ============================================================
-- INDEXES FOR FAST RETRIEVAL
-- ============================================================

-- Projects indexes
CREATE INDEX IF NOT EXISTS idx_projects_code ON projects(project_code);
CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_projects_last_worked ON projects(last_worked_at DESC);

-- Flows indexes
CREATE INDEX IF NOT EXISTS idx_flows_project ON project_flows(project_id);
CREATE INDEX IF NOT EXISTS idx_flows_type ON project_flows(flow_type);
CREATE INDEX IF NOT EXISTS idx_flows_project_type ON project_flows(project_id, flow_type);

-- Schemas indexes
CREATE INDEX IF NOT EXISTS idx_schemas_project ON project_schemas(project_id);
CREATE INDEX IF NOT EXISTS idx_schemas_table ON project_schemas(table_name);
CREATE INDEX IF NOT EXISTS idx_schemas_project_table ON project_schemas(project_id, table_name);

-- Relations indexes
CREATE INDEX IF NOT EXISTS idx_relations_project ON project_entity_relations(project_id);
CREATE INDEX IF NOT EXISTS idx_relations_tables ON project_entity_relations(from_table, to_table);
CREATE INDEX IF NOT EXISTS idx_relations_project_from ON project_entity_relations(project_id, from_table);

-- Patterns indexes
CREATE INDEX IF NOT EXISTS idx_patterns_project ON project_patterns(project_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON project_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_usage ON project_patterns(used_count DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_project_type ON project_patterns(project_id, pattern_type);

-- Decisions indexes
CREATE INDEX IF NOT EXISTS idx_decisions_project ON project_technical_decisions(project_id);
CREATE INDEX IF NOT EXISTS idx_decisions_category ON project_technical_decisions(category);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON project_technical_decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_project_category ON project_technical_decisions(project_id, category);

-- ============================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
DROP TRIGGER IF EXISTS update_project_flows_updated_at ON project_flows;
CREATE TRIGGER update_project_flows_updated_at
    BEFORE UPDATE ON project_flows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_project_schemas_updated_at ON project_schemas;
CREATE TRIGGER update_project_schemas_updated_at
    BEFORE UPDATE ON project_schemas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_project_patterns_updated_at ON project_patterns;
CREATE TRIGGER update_project_patterns_updated_at
    BEFORE UPDATE ON project_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- VERIFICATION QUERY
-- ============================================================
-- Run this to verify tables were created:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' AND table_name LIKE 'project%';
