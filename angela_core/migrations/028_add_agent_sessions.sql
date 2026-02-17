-- Migration 028: Agent-to-Agent Sessions
-- Support for multi-agent conversations
-- Created: 2026-02-17

CREATE TABLE IF NOT EXISTS angela_agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purpose TEXT NOT NULL,
    agents JSONB NOT NULL DEFAULT '[]',
    messages JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'active',
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON angela_agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_created ON angela_agent_sessions(created_at);
