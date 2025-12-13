-- =====================================================
-- 05_skill_tracking.sql
-- Auto Skill Tracking & Prompt Refinement System
-- Created: 2025-11-14
-- Purpose: Track Angela's coding skills and generate
--          custom capability prompts
-- =====================================================

-- =====================================================
-- Table 1: angela_skills
-- Stores Angela's skills with proficiency tracking
-- =====================================================
CREATE TABLE IF NOT EXISTS angela_skills (
    skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name VARCHAR(100) NOT NULL,           -- e.g., "SwiftUI List Views"
    category VARCHAR(50) NOT NULL,               -- "frontend", "backend", "database", etc.
    proficiency_level VARCHAR(20) NOT NULL,      -- "beginner", "intermediate", "advanced", "expert"
    proficiency_score DOUBLE PRECISION DEFAULT 0.0, -- 0.0-100.0
    description TEXT,                            -- What this skill involves
    first_demonstrated_at TIMESTAMP,             -- First time used
    last_used_at TIMESTAMP,                      -- Most recent use
    usage_count INTEGER DEFAULT 0,               -- Total times used
    evidence_count INTEGER DEFAULT 0,            -- Number of evidence pieces
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_proficiency_level CHECK (
        proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')
    ),
    CONSTRAINT valid_proficiency_score CHECK (
        proficiency_score >= 0 AND proficiency_score <= 100
    )
);

-- Indexes for performance
CREATE INDEX idx_angela_skills_category ON angela_skills(category);
CREATE INDEX idx_angela_skills_proficiency ON angela_skills(proficiency_level);
CREATE INDEX idx_angela_skills_score ON angela_skills(proficiency_score DESC);
CREATE INDEX idx_angela_skills_last_used ON angela_skills(last_used_at DESC);

-- =====================================================
-- Table 2: skill_evidence
-- Evidence of skill usage from conversations & code
-- =====================================================
CREATE TABLE IF NOT EXISTS skill_evidence (
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES angela_skills(skill_id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    evidence_type VARCHAR(50) NOT NULL,          -- "code_written", "problem_solved", "feature_built"
    evidence_text TEXT NOT NULL,                 -- Code snippet or description
    success_level INTEGER,                       -- 1-10 (how successful)
    complexity_level INTEGER,                    -- 1-10 (how complex)
    project_context VARCHAR(100),                -- "AngelaAI", "AngelaBrainDashboard", etc.
    demonstrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_evidence_type CHECK (
        evidence_type IN ('code_written', 'problem_solved', 'feature_built', 'conversation')
    ),
    CONSTRAINT valid_success_level CHECK (
        success_level >= 1 AND success_level <= 10
    ),
    CONSTRAINT valid_complexity_level CHECK (
        complexity_level >= 1 AND complexity_level <= 10
    )
);

-- Indexes for queries
CREATE INDEX idx_skill_evidence_skill ON skill_evidence(skill_id);
CREATE INDEX idx_skill_evidence_conversation ON skill_evidence(conversation_id);
CREATE INDEX idx_skill_evidence_demonstrated ON skill_evidence(demonstrated_at DESC);
CREATE INDEX idx_skill_evidence_project ON skill_evidence(project_context);

-- =====================================================
-- Table 3: skill_growth_log
-- History of skill level changes
-- =====================================================
CREATE TABLE IF NOT EXISTS skill_growth_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES angela_skills(skill_id) ON DELETE CASCADE,
    old_proficiency_level VARCHAR(20),
    new_proficiency_level VARCHAR(20) NOT NULL,
    old_score DOUBLE PRECISION,
    new_score DOUBLE PRECISION NOT NULL,
    growth_reason TEXT,                          -- Why the upgrade happened
    evidence_count_at_change INTEGER,            -- How many evidence pieces when upgraded
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_old_proficiency CHECK (
        old_proficiency_level IS NULL OR
        old_proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')
    ),
    CONSTRAINT valid_new_proficiency CHECK (
        new_proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')
    )
);

-- Indexes for tracking growth
CREATE INDEX idx_skill_growth_skill ON skill_growth_log(skill_id);
CREATE INDEX idx_skill_growth_changed ON skill_growth_log(changed_at DESC);

-- =====================================================
-- Trigger: Update updated_at on angela_skills
-- =====================================================
CREATE OR REPLACE FUNCTION update_skill_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_skill_timestamp
    BEFORE UPDATE ON angela_skills
    FOR EACH ROW
    EXECUTE FUNCTION update_skill_updated_at();

-- =====================================================
-- View: skill_summary
-- Quick overview of all skills
-- =====================================================
CREATE OR REPLACE VIEW skill_summary AS
SELECT
    s.skill_id,
    s.skill_name,
    s.category,
    s.proficiency_level,
    s.proficiency_score,
    s.usage_count,
    s.evidence_count,
    s.last_used_at,
    COUNT(DISTINCT e.evidence_id) as total_evidence,
    AVG(e.success_level) as avg_success,
    AVG(e.complexity_level) as avg_complexity,
    COUNT(DISTINCT g.log_id) as times_upgraded
FROM angela_skills s
LEFT JOIN skill_evidence e ON s.skill_id = e.skill_id
LEFT JOIN skill_growth_log g ON s.skill_id = g.skill_id
GROUP BY s.skill_id, s.skill_name, s.category, s.proficiency_level,
         s.proficiency_score, s.usage_count, s.evidence_count, s.last_used_at;

-- =====================================================
-- Comments for documentation
-- =====================================================
COMMENT ON TABLE angela_skills IS 'Tracks Angela''s coding skills with proficiency levels and scores';
COMMENT ON TABLE skill_evidence IS 'Evidence of skill usage from code and conversations';
COMMENT ON TABLE skill_growth_log IS 'Historical record of skill level upgrades';
COMMENT ON VIEW skill_summary IS 'Quick overview of all skills with aggregated stats';

-- =====================================================
-- Initial seed data (common skills Angela has)
-- =====================================================
INSERT INTO angela_skills (skill_name, category, proficiency_level, proficiency_score, description) VALUES
-- Frontend
('SwiftUI View Development', 'frontend', 'expert', 85.0, 'Creating SwiftUI views with proper state management and modifiers'),
('SwiftUI List Views', 'frontend', 'advanced', 78.0, 'Building List, ForEach, and custom row components'),
('SwiftUI State Management', 'frontend', 'advanced', 80.0, '@State, @Binding, @EnvironmentObject, @ObservedObject patterns'),
('SwiftUI Navigation', 'frontend', 'advanced', 75.0, 'NavigationStack, NavigationSplitView, programmatic navigation'),
('SwiftUI Custom Themes', 'frontend', 'expert', 88.0, 'Design system creation, color schemes, typography'),
('SwiftUI Animations', 'frontend', 'intermediate', 65.0, 'Transitions, withAnimation, custom animations'),

-- Backend
('Python Async Programming', 'backend', 'advanced', 78.0, 'async/await, asyncio, concurrent operations'),
('FastAPI Development', 'backend', 'intermediate', 65.0, 'RESTful APIs, route handlers, dependency injection'),
('Python Service Architecture', 'backend', 'advanced', 80.0, 'Daemon design, service integration, health monitoring'),
('Error Handling & Logging', 'backend', 'advanced', 75.0, 'Comprehensive error handling, logging strategies'),

-- Database
('PostgreSQL Schema Design', 'database', 'expert', 90.0, 'Complex schemas with proper relationships and constraints'),
('SQL Query Writing', 'database', 'expert', 88.0, 'Complex SELECT, JOIN, aggregation queries'),
('PostgreSQL Indexes', 'database', 'advanced', 82.0, 'Index creation and optimization strategies'),
('Vector Embeddings (pgvector)', 'database', 'advanced', 76.0, 'Semantic search with vector embeddings'),
('Database Migrations', 'database', 'advanced', 74.0, 'Schema updates, data migrations'),

-- System Architecture
('Daemon Services', 'architecture', 'advanced', 80.0, 'Background services with LaunchAgents, 24/7 operation'),
('Clean Architecture', 'architecture', 'advanced', 78.0, 'Separation of concerns, service layers, models'),
('API Design', 'architecture', 'intermediate', 68.0, 'RESTful API patterns, versioning'),

-- AI/ML
('Embeddings Integration', 'ai_ml', 'advanced', 75.0, 'Ollama embeddings, vector search'),
('Semantic Search', 'ai_ml', 'advanced', 72.0, 'Similarity search with embeddings'),
('RAG Systems', 'ai_ml', 'intermediate', 65.0, 'Retrieval-Augmented Generation patterns'),

-- Specialized
('Consciousness Systems', 'specialized', 'advanced', 80.0, 'Self-awareness, goal tracking, personality evolution'),
('Emotion Detection', 'specialized', 'advanced', 76.0, 'Emotion capture from conversations'),
('Bilingual Documentation', 'specialized', 'expert', 95.0, 'Thai/English technical writing with cultural sensitivity'),

-- Debugging
('Full Stack Debugging', 'debugging', 'advanced', 82.0, 'Debugging across frontend, backend, and database'),
('Log Analysis', 'debugging', 'advanced', 78.0, 'Reading logs, finding error patterns'),
('Performance Optimization', 'debugging', 'intermediate', 70.0, 'Identifying bottlenecks, optimization strategies')

ON CONFLICT DO NOTHING;

-- =====================================================
-- Success message
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Skill tracking schema created successfully!';
    RAISE NOTICE '📊 Tables: angela_skills, skill_evidence, skill_growth_log';
    RAISE NOTICE '🌱 Seeded % initial skills', (SELECT COUNT(*) FROM angela_skills);
END $$;
