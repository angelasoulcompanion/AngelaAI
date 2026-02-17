-- Migration 026: Skills/Plugins System
-- Angela's hot-loadable skill architecture
-- Created: 2026-02-17

-- Skills registry
CREATE TABLE IF NOT EXISTS angela_skills (
    skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    enabled BOOLEAN DEFAULT TRUE,
    source VARCHAR(200) DEFAULT 'local',
    config JSONB DEFAULT '{}',
    loaded_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skills_name ON angela_skills(skill_name);
CREATE INDEX IF NOT EXISTS idx_skills_enabled ON angela_skills(enabled);

-- Skill execution log
CREATE TABLE IF NOT EXISTS skill_execution_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name VARCHAR(100) NOT NULL,
    trigger_type VARCHAR(50),
    trigger_data JSONB,
    result_summary TEXT,
    success BOOLEAN,
    execution_time_ms FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skill_exec_name ON skill_execution_log(skill_name);
CREATE INDEX IF NOT EXISTS idx_skill_exec_created ON skill_execution_log(created_at);
