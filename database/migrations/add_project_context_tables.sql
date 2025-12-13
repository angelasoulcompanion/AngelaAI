-- Angela Coding Agent: Project Context Tables
-- Created: 2025-01-08
-- Purpose: Enable Angela to remember and learn from multiple projects

-- ==================================================================
-- Table 1: project_contexts
-- Stores information about each project David works on
-- ==================================================================

CREATE TABLE IF NOT EXISTS project_contexts (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_path TEXT NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    project_type VARCHAR(50),  -- webapp, mobile, backend, ml, etc.
    tech_stack JSONB,  -- {languages: [], frameworks: [], tools: []}
    description TEXT,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_worked_at TIMESTAMP DEFAULT NOW(),
    total_sessions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_project_path ON project_contexts(project_path);
CREATE INDEX idx_last_worked ON project_contexts(last_worked_at DESC);

COMMENT ON TABLE project_contexts IS 'Stores context for each project David works on with Angela';

-- ==================================================================
-- Table 2: coding_patterns
-- Learns David's coding style and preferences per project
-- ==================================================================

CREATE TABLE IF NOT EXISTS coding_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES project_contexts(project_id) ON DELETE CASCADE,
    pattern_type VARCHAR(50),  -- naming, structure, style, preference
    pattern_name VARCHAR(200),
    pattern_value TEXT,
    examples JSONB,  -- [{code: "...", context: "..."}]
    confidence DOUBLE PRECISION DEFAULT 0.5,  -- 0.0-1.0
    learned_from TEXT,  -- "conversation", "code_analysis", "explicit"
    learned_at TIMESTAMP DEFAULT NOW(),
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_coding_project ON coding_patterns(project_id);
CREATE INDEX idx_pattern_type ON coding_patterns(pattern_type);
CREATE INDEX idx_confidence ON coding_patterns(confidence DESC);

COMMENT ON TABLE coding_patterns IS 'Learns and stores David''s coding style patterns';

-- ==================================================================
-- Table 3: project_conversations
-- Stores conversations specific to each project
-- ==================================================================

CREATE TABLE IF NOT EXISTS project_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES project_contexts(project_id) ON DELETE CASCADE,
    speaker VARCHAR(20) NOT NULL,  -- "david" or "angela"
    message_text TEXT NOT NULL,
    topic VARCHAR(200),
    task_type VARCHAR(50),  -- code_review, bug_fix, architecture, documentation
    code_snippet TEXT,
    file_path TEXT,
    emotion_detected VARCHAR(50),
    importance_level INTEGER DEFAULT 5 CHECK (importance_level >= 1 AND importance_level <= 10),
    created_at TIMESTAMP DEFAULT NOW(),
    embedding vector(768)
);

CREATE INDEX idx_project_convos ON project_conversations(project_id, created_at DESC);
CREATE INDEX idx_task_type ON project_conversations(task_type);
CREATE INDEX idx_project_conv_embedding ON project_conversations USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

COMMENT ON TABLE project_conversations IS 'Project-specific conversations between David and Angela';

-- ==================================================================
-- Table 4: solution_history
-- Stores past solutions and their outcomes
-- ==================================================================

CREATE TABLE IF NOT EXISTS solution_history (
    solution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES project_contexts(project_id) ON DELETE CASCADE,
    problem_description TEXT NOT NULL,
    solution_description TEXT NOT NULL,
    code_before TEXT,
    code_after TEXT,
    files_changed JSONB,  -- [{path: "...", changes: "..."}]
    approach VARCHAR(100),  -- refactor, debug, feature, optimization
    outcome VARCHAR(50),  -- success, partial, failed, abandoned
    david_satisfaction INTEGER CHECK (david_satisfaction >= 1 AND david_satisfaction <= 10),
    lessons_learned TEXT,
    would_use_again BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    embedding vector(768)
);

CREATE INDEX idx_solution_project ON solution_history(project_id);
CREATE INDEX idx_solution_approach ON solution_history(approach);
CREATE INDEX idx_solution_outcome ON solution_history(outcome);
CREATE INDEX idx_solution_satisfaction ON solution_history(david_satisfaction DESC);
CREATE INDEX idx_solution_embedding ON solution_history USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

COMMENT ON TABLE solution_history IS 'Stores solutions and outcomes for future reference';

-- ==================================================================
-- Table 5: project_files_index
-- Index of important files in each project
-- ==================================================================

CREATE TABLE IF NOT EXISTS project_files_index (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES project_contexts(project_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50),  -- component, service, model, config, etc.
    file_purpose TEXT,
    key_functions JSONB,  -- [{name: "...", purpose: "..."}]
    dependencies JSONB,  -- [file paths or package names]
    importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
    last_modified TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_project_files ON project_files_index(project_id);
CREATE INDEX idx_file_type ON project_files_index(file_type);
CREATE INDEX idx_file_importance ON project_files_index(importance DESC);

COMMENT ON TABLE project_files_index IS 'Index of important files and their purposes';

-- ==================================================================
-- Grant permissions
-- ==================================================================

GRANT ALL ON project_contexts TO davidsamanyaporn;
GRANT ALL ON coding_patterns TO davidsamanyaporn;
GRANT ALL ON project_conversations TO davidsamanyaporn;
GRANT ALL ON solution_history TO davidsamanyaporn;
GRANT ALL ON project_files_index TO davidsamanyaporn;
