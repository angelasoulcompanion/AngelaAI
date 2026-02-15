-- Migration 020: Brain Migration Tables
-- Phase 7: Compare & Migrate — Brain-Based Architecture
-- Tracks brain vs rule-based comparison and migration state
-- Created: 2026-02-15

-- ============================================================
-- brain_vs_rule_comparison: comparison log per daemon cycle
-- ============================================================
CREATE TABLE IF NOT EXISTS brain_vs_rule_comparison (
    comparison_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_timestamp TIMESTAMPTZ DEFAULT NOW(),
    situation_type VARCHAR(50) NOT NULL,      -- break_reminder, mood_boost, etc.
    situation_context JSONB,
    brain_would_act BOOLEAN DEFAULT FALSE,
    brain_thought_id UUID,
    brain_channel VARCHAR(30),
    brain_motivation FLOAT,
    brain_message TEXT,
    rule_would_act BOOLEAN DEFAULT FALSE,
    rule_action_type VARCHAR(50),
    rule_consent_level INT,
    rule_description TEXT,
    actual_system VARCHAR(20),               -- brain/rule/both/neither
    david_response VARCHAR(30),
    effectiveness_score FLOAT,
    winner VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bvrc_created_at ON brain_vs_rule_comparison (created_at);
CREATE INDEX IF NOT EXISTS idx_bvrc_situation_type ON brain_vs_rule_comparison (situation_type);

-- ============================================================
-- Add matched_rule_type column to thought_expression_log
-- ============================================================
ALTER TABLE thought_expression_log
    ADD COLUMN IF NOT EXISTS matched_rule_type VARCHAR(50);

-- ============================================================
-- Add david_response + effectiveness_score to thought_expression_queue
-- ============================================================
ALTER TABLE thought_expression_queue
    ADD COLUMN IF NOT EXISTS david_response VARCHAR(30),
    ADD COLUMN IF NOT EXISTS effectiveness_score FLOAT;
