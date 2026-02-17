-- Migration 025: Tool Registry + Execution Log
-- Phase 1 of Angela + OpenClaw: Mind WITH Body
-- Created: 2026-02-17

-- Tool registry: tracks all available tools and their stats
CREATE TABLE IF NOT EXISTS angela_tool_registry (
    tool_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    parameters_schema JSONB,
    requires_confirmation BOOLEAN DEFAULT FALSE,
    cost_tier VARCHAR(20) DEFAULT 'free',
    enabled BOOLEAN DEFAULT TRUE,
    total_executions INT DEFAULT 0,
    total_successes INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_registry_category
    ON angela_tool_registry (category);

CREATE INDEX IF NOT EXISTS idx_tool_registry_enabled
    ON angela_tool_registry (enabled);

-- Tool execution log: tracks every tool invocation
CREATE TABLE IF NOT EXISTS tool_execution_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB,
    result_summary TEXT,
    success BOOLEAN,
    execution_time_ms FLOAT,
    triggered_by VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_execution_log_tool
    ON tool_execution_log (tool_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tool_execution_log_created
    ON tool_execution_log (created_at DESC);
