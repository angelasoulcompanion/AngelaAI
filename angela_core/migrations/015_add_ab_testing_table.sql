-- Phase 4: A/B Response Quality Testing
-- Created: 2026-02-13

CREATE TABLE IF NOT EXISTS angela_ab_tests (
    test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID,
    david_message_text TEXT NOT NULL,
    original_response TEXT NOT NULL,
    alternative_response TEXT NOT NULL,
    original_score FLOAT,
    alternative_score FLOAT,
    winner VARCHAR(20) NOT NULL,      -- 'original' or 'alternative'
    preference_strength FLOAT,
    judge_reasoning TEXT,
    preference_pair_id UUID REFERENCES angela_preference_pairs(pair_id),
    topic VARCHAR(200),
    tested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ab_tests_tested_at ON angela_ab_tests (tested_at DESC);
