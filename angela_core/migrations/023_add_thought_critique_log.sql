-- Migration 023: Thought Critique Log for Self-Critique Loop
-- Phase 2 of 3 Major Improvements
-- Created: 2026-02-15

CREATE TABLE IF NOT EXISTS thought_critique_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thought_id UUID REFERENCES angela_thoughts(thought_id),
    original_message TEXT,
    suggested_message TEXT,
    verification_passed BOOLEAN,
    quality_score FLOAT,
    uncertainty_level FLOAT,
    suppress_reason VARCHAR(100),
    checks_detail JSONB,
    created_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')
);

CREATE INDEX IF NOT EXISTS idx_thought_critique_log_created
    ON thought_critique_log (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_thought_critique_log_passed
    ON thought_critique_log (verification_passed);

CREATE INDEX IF NOT EXISTS idx_thought_critique_log_thought
    ON thought_critique_log (thought_id);
