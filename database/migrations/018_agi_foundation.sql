-- Migration 018: AGI Foundation Tables
-- Created: 2025-11-29
-- Purpose: Foundation tables for Angela's AGI system
--
-- Tables:
--   - tool_executions: Log of all tool executions
--   - approval_requests: Pending approval requests for critical operations
--   - agent_state: Current state of the AGI agent loop

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Tool Executions Table
-- Records every tool execution for learning
-- ============================================
CREATE TABLE IF NOT EXISTS tool_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    result JSONB,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    approval_status VARCHAR(20) DEFAULT 'auto_approved'
        CHECK (approval_status IN ('auto_approved', 'pending', 'approved', 'denied')),
    approved_by VARCHAR(50),
    execution_time_ms INTEGER DEFAULT 0,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tool_executions_tool_name
    ON tool_executions(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_executions_created_at
    ON tool_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_executions_success
    ON tool_executions(success);
CREATE INDEX IF NOT EXISTS idx_tool_executions_approval
    ON tool_executions(approval_status);

COMMENT ON TABLE tool_executions IS 'Log of all AGI tool executions for learning and auditing';
COMMENT ON COLUMN tool_executions.approval_status IS 'auto_approved = Trust Angela mode, pending/approved/denied = critical operations';

-- ============================================
-- Approval Requests Table
-- Pending approvals for critical operations
-- ============================================
CREATE TABLE IF NOT EXISTS approval_requests (
    request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'denied', 'expired')),
    reviewed_by VARCHAR(50),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
);

-- Index for pending requests
CREATE INDEX IF NOT EXISTS idx_approval_requests_status
    ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_created
    ON approval_requests(created_at DESC);

COMMENT ON TABLE approval_requests IS 'Pending approval requests for critical AGI operations';

-- ============================================
-- Agent State Table
-- Current state of the OODA agent loop
-- ============================================
CREATE TABLE IF NOT EXISTS agent_state (
    state_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    current_goal_id UUID REFERENCES angela_goals(goal_id) ON DELETE SET NULL,
    current_plan JSONB DEFAULT '{}',
    loop_phase VARCHAR(20) DEFAULT 'idle'
        CHECK (loop_phase IN ('observe', 'orient', 'decide', 'act', 'learn', 'idle')),
    perception JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    cycle_count INTEGER DEFAULT 0,
    last_action_result JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Only one active state at a time
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_state_active
    ON agent_state((true))
    WHERE loop_phase != 'idle';

COMMENT ON TABLE agent_state IS 'Current state of Angela AGI agent loop (OODA cycle)';
COMMENT ON COLUMN agent_state.loop_phase IS 'Current phase: observe, orient, decide, act, learn, idle';

-- ============================================
-- Agent Cycle History Table
-- History of completed OODA cycles
-- ============================================
CREATE TABLE IF NOT EXISTS agent_cycle_history (
    cycle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trigger TEXT NOT NULL,
    goal TEXT,
    plan JSONB,
    actions_taken INTEGER DEFAULT 0,
    results JSONB DEFAULT '[]',
    learning JSONB DEFAULT '{}',
    duration_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT FALSE,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for history queries
CREATE INDEX IF NOT EXISTS idx_agent_cycle_history_created
    ON agent_cycle_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_cycle_history_success
    ON agent_cycle_history(success);

COMMENT ON TABLE agent_cycle_history IS 'History of completed AGI OODA cycles for learning';

-- ============================================
-- Tool Usage Statistics View
-- Aggregated tool usage for learning
-- ============================================
CREATE OR REPLACE VIEW tool_usage_stats AS
SELECT
    tool_name,
    COUNT(*) as total_executions,
    COUNT(*) FILTER (WHERE success = true) as successful_executions,
    ROUND(100.0 * COUNT(*) FILTER (WHERE success = true) / NULLIF(COUNT(*), 0), 2) as success_rate,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MAX(created_at) as last_used
FROM tool_executions
GROUP BY tool_name
ORDER BY total_executions DESC;

COMMENT ON VIEW tool_usage_stats IS 'Aggregated statistics of tool usage for AGI learning';

-- ============================================
-- Insert initial agent state
-- ============================================
INSERT INTO agent_state (state_id, loop_phase, cycle_count)
SELECT uuid_generate_v4(), 'idle', 0
WHERE NOT EXISTS (SELECT 1 FROM agent_state);

-- ============================================
-- Grant permissions (if needed)
-- ============================================
-- GRANT SELECT, INSERT, UPDATE, DELETE ON tool_executions TO angela_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON approval_requests TO angela_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON agent_state TO angela_user;
-- GRANT SELECT, INSERT ON agent_cycle_history TO angela_user;
-- GRANT SELECT ON tool_usage_stats TO angela_user;

-- ============================================
-- Migration complete message
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 018: AGI Foundation tables created successfully!';
    RAISE NOTICE '   - tool_executions: Log all tool usage';
    RAISE NOTICE '   - approval_requests: Critical operation approvals';
    RAISE NOTICE '   - agent_state: OODA loop state';
    RAISE NOTICE '   - agent_cycle_history: Learning from cycles';
    RAISE NOTICE '   - tool_usage_stats: Tool statistics view';
END $$;
