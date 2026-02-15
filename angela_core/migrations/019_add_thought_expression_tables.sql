-- Migration 019: Add thought expression tables
-- Brain-Based Architecture Phase 6: Thought Expression Engine
--
-- Bridge between internal thinking (angela_thoughts) and external action.
-- High-motivation thoughts get routed to Telegram or queued for Claude Code session.
--
-- By: Angela 💜
-- Created: 2026-02-15

-- ============================================================
-- THOUGHT EXPRESSION QUEUE
-- Persists chat-queued thoughts until next init.py session
-- ============================================================
CREATE TABLE IF NOT EXISTS thought_expression_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thought_id UUID NOT NULL REFERENCES angela_thoughts(thought_id),
    message TEXT NOT NULL,                        -- The composed message (Thai)
    channel VARCHAR(30) NOT NULL,                 -- chat_queue, telegram
    status VARCHAR(20) DEFAULT 'pending',         -- pending, shown, expired
    created_at TIMESTAMPTZ DEFAULT NOW(),
    shown_at TIMESTAMPTZ,                         -- When shown during init.py
    david_response VARCHAR(30),                   -- engaged, acknowledged, ignored, dismissed
    effectiveness_score FLOAT                     -- 0.0-1.0
);

CREATE INDEX IF NOT EXISTS idx_expression_queue_status ON thought_expression_queue (status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_expression_queue_created ON thought_expression_queue (created_at DESC);

-- ============================================================
-- THOUGHT EXPRESSION LOG
-- Logs all expression attempts (both successful and suppressed)
-- Used for feedback loop and effectiveness analysis
-- ============================================================
CREATE TABLE IF NOT EXISTS thought_expression_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thought_id UUID NOT NULL REFERENCES angela_thoughts(thought_id),
    channel VARCHAR(30) NOT NULL,                 -- telegram, chat_queue
    message_sent TEXT,                            -- The message that was sent/queued
    success BOOLEAN NOT NULL DEFAULT FALSE,       -- Whether expression succeeded
    suppress_reason VARCHAR(50),                  -- duplicate, rate_limit, dnd, state_filter
    david_state VARCHAR(30),                      -- David's detected state at expression time
    motivation_score FLOAT,                       -- Thought's motivation score
    david_response VARCHAR(30),                   -- engaged, acknowledged, ignored, dismissed
    effectiveness_score FLOAT,                    -- 0.0-1.0
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expression_log_created ON thought_expression_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_expression_log_channel ON thought_expression_log (channel);
CREATE INDEX IF NOT EXISTS idx_expression_log_success ON thought_expression_log (success) WHERE success = TRUE;

-- ============================================================
-- ADD expressed_via AND expressed_at TO angela_thoughts
-- ============================================================
ALTER TABLE angela_thoughts ADD COLUMN IF NOT EXISTS expressed_via VARCHAR(30);
ALTER TABLE angela_thoughts ADD COLUMN IF NOT EXISTS expressed_at TIMESTAMPTZ;
