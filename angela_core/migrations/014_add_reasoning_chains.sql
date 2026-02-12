-- Migration 014: Add angela_reasoning_chains table
-- Purpose: Capture reasoning chains from 5 consciousness loop services
--          for training data export (Angela's "DNA")
--
-- Services: SENSE (emotional_coding_adapter), UNDERSTAND (theory_of_mind),
--           PREDICT (predictive_companion), ACT (proactive_action_engine),
--           LEARN (evolution_engine)
--
-- Created: 2026-02-12
-- By: Angela 💜

CREATE TABLE IF NOT EXISTS angela_reasoning_chains (
    chain_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name    VARCHAR(50) NOT NULL,       -- sense/understand/predict/act/learn
    decision_type   VARCHAR(100) NOT NULL,      -- e.g. 'state_detection', 'emotion_inference'
    input_signals   JSONB NOT NULL DEFAULT '{}', -- what signals were available
    reasoning_steps JSONB NOT NULL DEFAULT '[]', -- array of {step, action, observation, conclusion}
    output_decision JSONB NOT NULL DEFAULT '{}', -- the final decision/result
    confidence      FLOAT DEFAULT 0.0,
    conversation_id UUID,                       -- link to conversations table (nullable)
    related_reward_id UUID,                     -- link to reward_scores (nullable, linked later)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_reasoning_chains_service
    ON angela_reasoning_chains (service_name);

CREATE INDEX IF NOT EXISTS idx_reasoning_chains_conversation
    ON angela_reasoning_chains (conversation_id)
    WHERE conversation_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reasoning_chains_created
    ON angela_reasoning_chains (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reasoning_chains_reward
    ON angela_reasoning_chains (related_reward_id)
    WHERE related_reward_id IS NOT NULL;

COMMENT ON TABLE angela_reasoning_chains IS
    'Reasoning chains from consciousness loop services — Angela''s training DNA';
