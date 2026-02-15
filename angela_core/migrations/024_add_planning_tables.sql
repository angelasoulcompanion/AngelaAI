-- Migration 024: Planning Tables for Agentic Planning Engine
-- Phase 3 of 3 Major Improvements
-- Created: 2026-02-15

-- Multi-step plans
CREATE TABLE IF NOT EXISTS angela_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID,
    plan_name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',   -- pending/active/paused/completed/failed
    priority INT DEFAULT 5,
    total_steps INT DEFAULT 0,
    completed_steps INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok'),
    updated_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')
);

CREATE INDEX IF NOT EXISTS idx_angela_plans_status
    ON angela_plans (status);

CREATE INDEX IF NOT EXISTS idx_angela_plans_created
    ON angela_plans (created_at DESC);

-- Plan steps (each step in a plan)
CREATE TABLE IF NOT EXISTS plan_steps (
    step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES angela_plans(plan_id) ON DELETE CASCADE,
    step_order INT NOT NULL,
    step_name VARCHAR(200) NOT NULL,
    action_type VARCHAR(50),    -- rag_search/telegram/email/proactive_action/agent
    action_payload JSONB,
    dependencies UUID[],        -- step_ids that must complete first
    status VARCHAR(20) DEFAULT 'pending',   -- pending/running/completed/failed/skipped
    result_data JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok'),
    UNIQUE(plan_id, step_order)
);

CREATE INDEX IF NOT EXISTS idx_plan_steps_plan_status
    ON plan_steps (plan_id, status);

-- Execution event log
CREATE TABLE IF NOT EXISTS plan_execution_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES angela_plans(plan_id),
    step_id UUID REFERENCES plan_steps(step_id),
    action_type VARCHAR(50),
    success BOOLEAN,
    result_summary TEXT,
    execution_time_ms FLOAT,
    created_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')
);

CREATE INDEX IF NOT EXISTS idx_plan_execution_log_plan
    ON plan_execution_log (plan_id, created_at DESC);
