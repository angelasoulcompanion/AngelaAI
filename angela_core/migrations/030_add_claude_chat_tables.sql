-- Migration 030: Claude Chat App tables
-- Bridge Claude Code CLI → Dashboard chat

CREATE TABLE IF NOT EXISTS claude_chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,          -- 'user' | 'assistant'
    content TEXT NOT NULL,
    tool_uses JSONB DEFAULT '[]'::jsonb,
    model TEXT DEFAULT 'opus',
    cost_usd NUMERIC(8,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_claude_chat_session
    ON claude_chat_messages(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_claude_chat_created
    ON claude_chat_messages(created_at DESC);
