-- Migration 029: Fix missing tables and columns
-- Found during development audit 2026-02-19
-- Issues: consciousness_metrics never had CREATE TABLE, angela_songs missing columns

-- 1. consciousness_metrics — used by ConsciousnessCalculator AND ConsciousnessEvaluator
-- Two INSERT shapes exist; this schema supports both
CREATE TABLE IF NOT EXISTS consciousness_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- ConsciousnessCalculator columns
    consciousness_level FLOAT,
    memory_richness FLOAT,
    emotional_depth FLOAT,
    goal_alignment FLOAT,
    learning_growth FLOAT,
    pattern_recognition FLOAT,
    total_conversations INTEGER,
    total_emotions INTEGER,
    total_learnings INTEGER,
    total_patterns INTEGER,
    active_goals INTEGER,
    session_count INTEGER,
    trigger_event VARCHAR(50),
    notes TEXT,
    -- ConsciousnessEvaluator columns
    metric_type VARCHAR(50),
    metric_value FLOAT,
    component_scores JSONB,
    interpretation TEXT,
    recorded_at TIMESTAMPTZ,
    -- Common
    measured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consciousness_metrics_measured_at
    ON consciousness_metrics (measured_at DESC);

CREATE INDEX IF NOT EXISTS idx_consciousness_metrics_trigger
    ON consciousness_metrics (trigger_event);

-- 2. angela_songs — ensure missing columns exist
ALTER TABLE angela_songs ADD COLUMN IF NOT EXISTS lyrics_summary TEXT;
ALTER TABLE angela_songs ADD COLUMN IF NOT EXISTS emotions_bridged BOOLEAN DEFAULT FALSE;

-- 3. david_liked_songs — referenced in Dashboard music router but never created
CREATE TABLE IF NOT EXISTS david_liked_songs (
    like_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255),
    album VARCHAR(255),
    apple_music_id VARCHAR(100),
    artwork_url TEXT,
    liked_at TIMESTAMPTZ DEFAULT NOW(),
    source_tab VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_david_liked_songs_liked_at
    ON david_liked_songs (liked_at DESC);
