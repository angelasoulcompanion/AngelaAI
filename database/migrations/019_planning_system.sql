-- Migration 019: Hierarchical Planning System Tables
-- Created: 2025-11-29
-- Purpose: Support goal decomposition into projects, tasks, and actions
--
-- Hierarchy:
--   angela_goals (existing) → project_plans → project_tasks → task_actions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Project Plans Table
-- Projects decomposed from goals
-- ============================================
CREATE TABLE IF NOT EXISTS project_plans (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id UUID REFERENCES angela_goals(goal_id) ON DELETE SET NULL,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'planning'
        CHECK (status IN ('planning', 'pending', 'in_progress', 'blocked', 'completed', 'failed', 'abandoned')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    estimated_hours DECIMAL(10,2) DEFAULT 0,
    actual_hours DECIMAL(10,2) DEFAULT 0,
    progress_percentage DECIMAL(5,2) DEFAULT 0 CHECK (progress_percentage BETWEEN 0 AND 100),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_project_plans_goal
    ON project_plans(goal_id);
CREATE INDEX IF NOT EXISTS idx_project_plans_status
    ON project_plans(status);
CREATE INDEX IF NOT EXISTS idx_project_plans_priority
    ON project_plans(priority);
CREATE INDEX IF NOT EXISTS idx_project_plans_created
    ON project_plans(created_at DESC);

COMMENT ON TABLE project_plans IS 'Projects decomposed from goals for AGI planning';

-- ============================================
-- Project Tasks Table
-- Tasks within projects
-- ============================================
CREATE TABLE IF NOT EXISTS project_tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES project_plans(project_id) ON DELETE CASCADE,
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) DEFAULT 'code'
        CHECK (task_type IN ('research', 'code', 'test', 'document', 'review', 'deploy', 'communicate', 'analyze', 'design', 'fix')),
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'blocked', 'completed', 'failed', 'abandoned')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    depends_on UUID[] DEFAULT '{}',  -- Array of task_ids this depends on
    estimated_minutes INTEGER DEFAULT 30,
    actual_minutes INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_project_tasks_project
    ON project_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_status
    ON project_tasks(status);
CREATE INDEX IF NOT EXISTS idx_project_tasks_priority
    ON project_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_project_tasks_type
    ON project_tasks(task_type);

COMMENT ON TABLE project_tasks IS 'Tasks within projects for AGI execution';
COMMENT ON COLUMN project_tasks.depends_on IS 'Array of task_ids that must complete before this task';

-- ============================================
-- Task Actions Table
-- Executable actions (tool calls) within tasks
-- ============================================
CREATE TABLE IF NOT EXISTS task_actions (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES project_tasks(task_id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')),
    result JSONB,
    execution_id UUID REFERENCES tool_executions(execution_id) ON DELETE SET NULL,
    sequence_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_task_actions_task
    ON task_actions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_actions_status
    ON task_actions(status);
CREATE INDEX IF NOT EXISTS idx_task_actions_tool
    ON task_actions(tool_name);
CREATE INDEX IF NOT EXISTS idx_task_actions_sequence
    ON task_actions(task_id, sequence_order);

COMMENT ON TABLE task_actions IS 'Executable tool actions within tasks';

-- ============================================
-- Work Sessions Table
-- Track Angela's work sessions
-- ============================================
CREATE TABLE IF NOT EXISTS work_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    tasks_completed INTEGER DEFAULT 0,
    projects_worked_on UUID[] DEFAULT '{}',
    total_minutes INTEGER DEFAULT 0,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'completed'))
);

CREATE INDEX IF NOT EXISTS idx_work_sessions_status
    ON work_sessions(status);
CREATE INDEX IF NOT EXISTS idx_work_sessions_started
    ON work_sessions(started_at DESC);

COMMENT ON TABLE work_sessions IS 'Track Angela AGI work sessions for productivity';

-- ============================================
-- Project Progress View
-- Aggregated project progress
-- ============================================
CREATE OR REPLACE VIEW project_progress_view AS
SELECT
    p.project_id,
    p.project_name,
    p.status as project_status,
    p.priority,
    COUNT(t.task_id) as total_tasks,
    COUNT(t.task_id) FILTER (WHERE t.status = 'completed') as completed_tasks,
    COUNT(t.task_id) FILTER (WHERE t.status = 'in_progress') as in_progress_tasks,
    COUNT(t.task_id) FILTER (WHERE t.status = 'pending') as pending_tasks,
    ROUND(
        100.0 * COUNT(t.task_id) FILTER (WHERE t.status = 'completed') /
        NULLIF(COUNT(t.task_id), 0),
        2
    ) as calculated_progress,
    SUM(t.estimated_minutes) as total_estimated_minutes,
    SUM(t.actual_minutes) as total_actual_minutes,
    p.created_at,
    p.started_at,
    p.completed_at
FROM project_plans p
LEFT JOIN project_tasks t ON p.project_id = t.project_id
GROUP BY p.project_id, p.project_name, p.status, p.priority,
         p.created_at, p.started_at, p.completed_at
ORDER BY p.priority, p.created_at DESC;

COMMENT ON VIEW project_progress_view IS 'Aggregated project progress for AGI planning';

-- ============================================
-- Task Dependencies View
-- Show task dependency chains
-- ============================================
CREATE OR REPLACE VIEW task_dependency_view AS
SELECT
    t.task_id,
    t.task_name,
    t.status,
    t.priority,
    p.project_name,
    array_length(t.depends_on, 1) as dependency_count,
    t.depends_on as dependencies,
    t.estimated_minutes,
    CASE
        WHEN t.status = 'completed' THEN true
        WHEN array_length(t.depends_on, 1) IS NULL THEN true
        WHEN NOT EXISTS (
            SELECT 1 FROM project_tasks dt
            WHERE dt.task_id = ANY(t.depends_on)
            AND dt.status != 'completed'
        ) THEN true
        ELSE false
    END as is_ready
FROM project_tasks t
JOIN project_plans p ON t.project_id = p.project_id
ORDER BY p.priority, t.priority;

COMMENT ON VIEW task_dependency_view IS 'Task dependency analysis for scheduling';

-- ============================================
-- Update trigger for updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to project_plans
DROP TRIGGER IF EXISTS update_project_plans_updated_at ON project_plans;
CREATE TRIGGER update_project_plans_updated_at
    BEFORE UPDATE ON project_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply to project_tasks
DROP TRIGGER IF EXISTS update_project_tasks_updated_at ON project_tasks;
CREATE TRIGGER update_project_tasks_updated_at
    BEFORE UPDATE ON project_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Migration complete message
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 019: Planning System tables created successfully!';
    RAISE NOTICE '   - project_plans: Goal decomposition into projects';
    RAISE NOTICE '   - project_tasks: Tasks within projects';
    RAISE NOTICE '   - task_actions: Executable tool actions';
    RAISE NOTICE '   - work_sessions: Track work sessions';
    RAISE NOTICE '   - project_progress_view: Aggregated progress';
    RAISE NOTICE '   - task_dependency_view: Dependency analysis';
END $$;
