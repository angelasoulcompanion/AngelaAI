-- Migration 031: Add GWT Competition Arena + Ignition Gate
-- Phase 2 of Neuroscience-Inspired Brain Architecture
--
-- Implements Baars' Global Workspace Theory:
-- - Thoughts compete for access to consciousness (competition_arena)
-- - Winners "ignite" and broadcast to all brain modules (ignition)
-- - Losers are inhibited (lateral inhibition via softmax)
--
-- By: Angela 💜
-- Created: 2026-02-26

-- 1. Add competition columns to angela_thoughts
ALTER TABLE angela_thoughts
    ADD COLUMN IF NOT EXISTS competition_score FLOAT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS ignition_status TEXT DEFAULT NULL
        CHECK (ignition_status IN ('ignited', 'simmering', 'extinguished', NULL)),
    ADD COLUMN IF NOT EXISTS competition_rank INTEGER DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS inhibited_by UUID DEFAULT NULL;

-- 2. Competition log — tracks each competition cycle
CREATE TABLE IF NOT EXISTS competition_log (
    competition_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    candidates_count INTEGER NOT NULL,
    winner_thought_id UUID REFERENCES angela_thoughts(thought_id),
    winner_score FLOAT,
    runner_up_score FLOAT,
    margin FLOAT,                   -- winner - runner_up (separation quality)
    inhibition_count INTEGER,       -- how many were laterally inhibited
    ignition_triggered BOOLEAN,     -- did the winner pass ignition gate?
    ignition_factors JSONB,         -- {sustained_activation, coherence, emotional_sig, context_match}
    david_state TEXT,               -- David's state at competition time
    metacognitive_snapshot JSONB,   -- Metacognitive state at competition time
    cycle_duration_ms FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_thoughts_ignition_status
    ON angela_thoughts(ignition_status) WHERE ignition_status IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_competition_log_created
    ON competition_log(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_competition_log_winner
    ON competition_log(winner_thought_id) WHERE winner_thought_id IS NOT NULL;

-- 4. Verify
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 031: Competition Arena + Ignition Gate tables ready';
END $$;
