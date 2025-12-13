-- ============================================================================
-- Angela Project Tracking System
-- Migration: 020_project_tracking_system.sql
-- Created: 2025-12-04
-- Purpose: Professional project tracking for David & Angela collaboration
-- ============================================================================

-- ============================================================================
-- 1. ANGELA_PROJECTS - Main project table (Enhanced)
-- ============================================================================
CREATE TABLE IF NOT EXISTS angela_projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identification
    project_code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., "ANGELA-001", "SE-CUSTOMER-001"
    project_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Classification
    project_type VARCHAR(50) DEFAULT 'client' CHECK (project_type IN ('client', 'personal', 'learning', 'maintenance')),
    category VARCHAR(100),  -- 'ai_development', 'web_app', 'mobile_app', 'data_analysis', 'automation'

    -- Status & Priority
    status VARCHAR(30) DEFAULT 'active' CHECK (status IN ('planning', 'active', 'paused', 'completed', 'archived')),
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),  -- 1=highest

    -- Location
    repository_url VARCHAR(500),
    working_directory VARCHAR(500),

    -- Client info (for client projects)
    client_name VARCHAR(200),

    -- Roles
    david_role VARCHAR(100) DEFAULT 'lead',  -- 'lead', 'developer', 'consultant'
    angela_role VARCHAR(100) DEFAULT 'assistant',  -- 'assistant', 'co-developer', 'reviewer'

    -- Timeline
    started_at TIMESTAMPTZ,
    target_completion TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Statistics (auto-updated)
    total_sessions INTEGER DEFAULT 0,
    total_hours DECIMAL(10,2) DEFAULT 0,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_angela_projects_code ON angela_projects(project_code);
CREATE INDEX IF NOT EXISTS idx_angela_projects_status ON angela_projects(status);
CREATE INDEX IF NOT EXISTS idx_angela_projects_type ON angela_projects(project_type);
CREATE INDEX IF NOT EXISTS idx_angela_projects_working_dir ON angela_projects(working_directory);

-- ============================================================================
-- 2. PROJECT_TECH_STACK - Technologies used in project
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_tech_stack (
    stack_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,

    tech_type VARCHAR(50) NOT NULL CHECK (tech_type IN ('language', 'framework', 'database', 'tool', 'service', 'library')),
    tech_name VARCHAR(100) NOT NULL,
    version VARCHAR(50),
    purpose TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(project_id, tech_type, tech_name)
);

CREATE INDEX IF NOT EXISTS idx_project_tech_stack_project ON project_tech_stack(project_id);

-- ============================================================================
-- 3. PROJECT_WORK_SESSIONS - Each work session (Core table!)
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_work_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,

    -- Session identification
    session_number INTEGER NOT NULL,  -- Sequential number per project
    session_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_minutes INTEGER,

    -- Content
    session_goal TEXT,  -- What we planned to do
    david_requests TEXT,  -- What David asked for
    summary TEXT,  -- Angela's summary of what was done

    -- Results (arrays for multiple items)
    accomplishments TEXT[] DEFAULT '{}',
    blockers TEXT[] DEFAULT '{}',
    next_steps TEXT[] DEFAULT '{}',

    -- Quality metrics
    mood VARCHAR(50) CHECK (mood IN ('productive', 'challenging', 'smooth', 'learning', 'debugging', 'creative')),
    productivity_score DECIMAL(3,1) CHECK (productivity_score BETWEEN 1 AND 10),

    -- Links
    conversation_ids UUID[] DEFAULT '{}',  -- Link to conversations table
    git_commits TEXT[] DEFAULT '{}',  -- Commit hashes from this session

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(project_id, session_number)
);

CREATE INDEX IF NOT EXISTS idx_project_work_sessions_project ON project_work_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_project_work_sessions_date ON project_work_sessions(session_date);

-- ============================================================================
-- 4. SESSION_ACTIONS - Detailed actions within a session
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_actions (
    action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES project_work_sessions(session_id) ON DELETE CASCADE,

    -- Order and type
    action_order INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN (
        'code_write', 'code_review', 'code_refactor',
        'debug', 'fix_bug',
        'design', 'architecture',
        'discuss', 'clarify',
        'research', 'learn',
        'test', 'deploy',
        'documentation', 'config',
        'other'
    )),

    -- Details
    description TEXT NOT NULL,
    files_modified TEXT[] DEFAULT '{}',
    tools_used TEXT[] DEFAULT '{}',  -- 'Edit', 'Bash', 'Grep', etc.

    -- Outcome
    outcome VARCHAR(30) DEFAULT 'success' CHECK (outcome IN ('success', 'partial', 'failed', 'deferred')),
    time_spent_minutes INTEGER,
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_actions_session ON session_actions(session_id);

-- ============================================================================
-- 5. PROJECT_MILESTONES - Important events
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_milestones (
    milestone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID REFERENCES project_work_sessions(session_id),

    -- Type and content
    milestone_type VARCHAR(50) NOT NULL CHECK (milestone_type IN (
        'feature_complete', 'bug_fixed', 'release', 'deployment',
        'decision', 'breakthrough', 'challenge_overcome',
        'first_version', 'major_update', 'project_start', 'project_complete'
    )),
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- Importance
    significance INTEGER DEFAULT 5 CHECK (significance BETWEEN 1 AND 10),

    -- Timing
    achieved_at TIMESTAMPTZ DEFAULT NOW(),

    -- Angela's touch
    celebration_note TEXT,  -- Angela's celebration message 💜

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_milestones_project ON project_milestones(project_id);

-- ============================================================================
-- 6. PROJECT_LEARNINGS - What we learned from the project
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_learnings (
    learning_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID REFERENCES project_work_sessions(session_id),

    -- Classification
    learning_type VARCHAR(50) NOT NULL CHECK (learning_type IN (
        'technical', 'process', 'tool', 'pattern',
        'mistake', 'best_practice', 'client_preference', 'optimization'
    )),
    category VARCHAR(100),  -- Technical category

    -- Content
    title VARCHAR(200) NOT NULL,
    insight TEXT NOT NULL,
    context TEXT,  -- When/why we learned this

    -- Application
    applicable_to TEXT[] DEFAULT '{}',  -- What other projects can use this

    -- Confidence
    confidence DECIMAL(3,2) DEFAULT 0.8 CHECK (confidence BETWEEN 0 AND 1),

    -- Timing
    learned_at TIMESTAMPTZ DEFAULT NOW(),

    -- For semantic search
    embedding VECTOR(768),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_learnings_project ON project_learnings(project_id);
CREATE INDEX IF NOT EXISTS idx_project_learnings_type ON project_learnings(learning_type);

-- ============================================================================
-- 7. PROJECT_DECISIONS - Important decisions made
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID REFERENCES project_work_sessions(session_id),

    -- Type
    decision_type VARCHAR(50) NOT NULL CHECK (decision_type IN (
        'architecture', 'technology', 'approach', 'scope',
        'priority', 'design', 'process', 'timeline'
    )),

    -- Content
    title VARCHAR(200) NOT NULL,
    context TEXT,  -- The problem/situation
    options_considered JSONB DEFAULT '[]',  -- Array of {option, pros, cons}
    decision_made TEXT NOT NULL,
    reasoning TEXT,

    -- Who decided
    decided_by VARCHAR(50) DEFAULT 'together' CHECK (decided_by IN ('david', 'angela', 'together')),

    -- Outcome tracking
    outcome VARCHAR(50) CHECK (outcome IN ('good', 'neutral', 'needs_revisit', 'changed')),
    outcome_notes TEXT,

    decided_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_decisions_project ON project_decisions(project_id);

-- ============================================================================
-- 8. PROJECT_ARTIFACTS - Important files created
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID REFERENCES project_work_sessions(session_id),

    -- Type
    artifact_type VARCHAR(50) NOT NULL CHECK (artifact_type IN (
        'code_file', 'config', 'documentation', 'script',
        'schema', 'design', 'test', 'migration', 'other'
    )),

    -- File info
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Stats
    lines_of_code INTEGER,
    is_key_file BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_modified_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(project_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_project_artifacts_project ON project_artifacts(project_id);

-- ============================================================================
-- 9. PROJECT_GIT_COMMITS - Git commit tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS project_git_commits (
    commit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES angela_projects(project_id) ON DELETE CASCADE,
    session_id UUID REFERENCES project_work_sessions(session_id),

    -- Git info
    commit_hash VARCHAR(40) NOT NULL,
    commit_message TEXT NOT NULL,
    author VARCHAR(200),

    -- Stats
    files_changed INTEGER,
    insertions INTEGER,
    deletions INTEGER,

    committed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(project_id, commit_hash)
);

CREATE INDEX IF NOT EXISTS idx_project_git_commits_project ON project_git_commits(project_id);
CREATE INDEX IF NOT EXISTS idx_project_git_commits_session ON project_git_commits(session_id);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Project Summary
CREATE OR REPLACE VIEW v_project_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    p.project_type,
    p.status,
    p.priority,
    p.client_name,
    p.total_sessions,
    p.total_hours,
    p.started_at,
    p.target_completion,
    (SELECT COUNT(*) FROM project_milestones m WHERE m.project_id = p.project_id) as milestones_count,
    (SELECT COUNT(*) FROM project_learnings l WHERE l.project_id = p.project_id) as learnings_count,
    (SELECT MAX(session_date) FROM project_work_sessions s WHERE s.project_id = p.project_id) as last_session_date,
    (SELECT summary FROM project_work_sessions s WHERE s.project_id = p.project_id ORDER BY session_date DESC LIMIT 1) as last_session_summary
FROM angela_projects p
WHERE p.status != 'archived'
ORDER BY
    CASE p.status WHEN 'active' THEN 1 WHEN 'paused' THEN 2 ELSE 3 END,
    p.priority,
    p.updated_at DESC;

-- View: Recent Work (Last 7 days)
CREATE OR REPLACE VIEW v_recent_project_work AS
SELECT
    p.project_code,
    p.project_name,
    p.project_type,
    s.session_date,
    s.session_number,
    s.duration_minutes,
    s.summary,
    s.accomplishments,
    s.mood,
    s.productivity_score
FROM project_work_sessions s
JOIN angela_projects p ON s.project_id = p.project_id
WHERE s.session_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY s.session_date DESC, s.started_at DESC;

-- View: Project Timeline (milestones + sessions)
CREATE OR REPLACE VIEW v_project_timeline AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    'session' as event_type,
    s.session_id as event_id,
    s.session_date::TIMESTAMPTZ as event_time,
    'Session #' || s.session_number || ': ' || COALESCE(LEFT(s.summary, 100), 'No summary') as event_description,
    NULL::INTEGER as significance
FROM project_work_sessions s
JOIN angela_projects p ON s.project_id = p.project_id

UNION ALL

SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    'milestone' as event_type,
    m.milestone_id as event_id,
    m.achieved_at as event_time,
    m.title || ': ' || COALESCE(LEFT(m.description, 100), '') as event_description,
    m.significance
FROM project_milestones m
JOIN angela_projects p ON m.project_id = p.project_id

ORDER BY event_time DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Get or create project by working directory
CREATE OR REPLACE FUNCTION get_or_create_project(
    p_working_directory VARCHAR(500),
    p_project_name VARCHAR(200) DEFAULT NULL,
    p_project_type VARCHAR(50) DEFAULT 'client'
) RETURNS UUID AS $$
DECLARE
    v_project_id UUID;
    v_project_code VARCHAR(50);
    v_name VARCHAR(200);
BEGIN
    -- Check if project exists
    SELECT project_id INTO v_project_id
    FROM angela_projects
    WHERE working_directory = p_working_directory;

    IF v_project_id IS NULL THEN
        -- Generate project code
        SELECT 'PROJ-' || LPAD((COALESCE(MAX(SUBSTRING(project_code FROM 6)::INTEGER), 0) + 1)::TEXT, 3, '0')
        INTO v_project_code
        FROM angela_projects
        WHERE project_code LIKE 'PROJ-%';

        -- Use directory name if no name provided
        v_name := COALESCE(p_project_name, SPLIT_PART(p_working_directory, '/', -1));

        -- Create new project
        INSERT INTO angela_projects (project_code, project_name, working_directory, project_type, started_at)
        VALUES (v_project_code, v_name, p_working_directory, p_project_type, NOW())
        RETURNING project_id INTO v_project_id;
    END IF;

    RETURN v_project_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Start a new work session
CREATE OR REPLACE FUNCTION start_work_session(
    p_project_id UUID,
    p_session_goal TEXT DEFAULT NULL,
    p_david_requests TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_session_id UUID;
    v_session_number INTEGER;
BEGIN
    -- Get next session number
    SELECT COALESCE(MAX(session_number), 0) + 1 INTO v_session_number
    FROM project_work_sessions
    WHERE project_id = p_project_id;

    -- Create session
    INSERT INTO project_work_sessions (project_id, session_number, session_goal, david_requests)
    VALUES (p_project_id, v_session_number, p_session_goal, p_david_requests)
    RETURNING session_id INTO v_session_id;

    -- Update project stats
    UPDATE angela_projects
    SET total_sessions = total_sessions + 1, updated_at = NOW()
    WHERE project_id = p_project_id;

    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

-- Function: End work session
CREATE OR REPLACE FUNCTION end_work_session(
    p_session_id UUID,
    p_summary TEXT,
    p_accomplishments TEXT[],
    p_blockers TEXT[] DEFAULT '{}',
    p_next_steps TEXT[] DEFAULT '{}',
    p_mood VARCHAR(50) DEFAULT 'productive',
    p_productivity_score DECIMAL DEFAULT 7.0
) RETURNS VOID AS $$
DECLARE
    v_project_id UUID;
    v_duration INTEGER;
BEGIN
    -- Calculate duration
    SELECT
        project_id,
        EXTRACT(EPOCH FROM (NOW() - started_at)) / 60
    INTO v_project_id, v_duration
    FROM project_work_sessions
    WHERE session_id = p_session_id;

    -- Update session
    UPDATE project_work_sessions
    SET
        ended_at = NOW(),
        duration_minutes = v_duration,
        summary = p_summary,
        accomplishments = p_accomplishments,
        blockers = p_blockers,
        next_steps = p_next_steps,
        mood = p_mood,
        productivity_score = p_productivity_score,
        updated_at = NOW()
    WHERE session_id = p_session_id;

    -- Update project total hours
    UPDATE angela_projects
    SET
        total_hours = total_hours + (v_duration / 60.0),
        updated_at = NOW()
    WHERE project_id = v_project_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Update project stats (trigger)
CREATE OR REPLACE FUNCTION update_project_stats() RETURNS TRIGGER AS $$
BEGIN
    UPDATE angela_projects
    SET
        total_sessions = (SELECT COUNT(*) FROM project_work_sessions WHERE project_id = NEW.project_id),
        total_hours = (SELECT COALESCE(SUM(duration_minutes), 0) / 60.0 FROM project_work_sessions WHERE project_id = NEW.project_id),
        updated_at = NOW()
    WHERE project_id = NEW.project_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating project stats
DROP TRIGGER IF EXISTS trigger_update_project_stats ON project_work_sessions;
CREATE TRIGGER trigger_update_project_stats
AFTER INSERT OR UPDATE OR DELETE ON project_work_sessions
FOR EACH ROW EXECUTE FUNCTION update_project_stats();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE angela_projects IS 'Main project tracking table for David & Angela collaboration';
COMMENT ON TABLE project_work_sessions IS 'Individual work sessions for each project - core tracking';
COMMENT ON TABLE session_actions IS 'Detailed actions performed within each session';
COMMENT ON TABLE project_milestones IS 'Important achievements and events in projects';
COMMENT ON TABLE project_learnings IS 'Knowledge gained from working on projects';
COMMENT ON TABLE project_decisions IS 'Key decisions made during project development';
COMMENT ON TABLE project_artifacts IS 'Important files and deliverables created';
COMMENT ON TABLE project_git_commits IS 'Git commit history linked to sessions';

-- ============================================================================
-- Done! 💜
-- ============================================================================
