-- Migration 032: Predictive Processing + NeuroModulation + Memory Enhancement
-- Phase 3: Predictive Processing (Friston's Free Energy)
-- Phase 4: Attention Schema + NeuroModulation (Graziano)
-- Phase 5: Memory Enhancement 2.0 (Reconsolidation + Binding)
-- Created: 2026-02-27

-- ============================================================
-- PHASE 3: PREDICTIVE PROCESSING
-- ============================================================

-- Angela's predictions about David (state, topic, activity)
CREATE TABLE IF NOT EXISTS angela_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_type TEXT NOT NULL,        -- emotion, activity, topic, response_time
    predicted_value TEXT NOT NULL,         -- what Angela predicts
    actual_value TEXT,                     -- what actually happened (filled later)
    confidence FLOAT DEFAULT 0.5,         -- Angela's confidence in prediction
    prediction_error FLOAT,               -- |predicted - actual| (filled later)
    context_snapshot JSONB DEFAULT '{}',   -- time, day, recent_topics, etc.
    resolved BOOLEAN DEFAULT FALSE,       -- has outcome been observed?
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_unresolved
    ON angela_predictions (resolved, created_at DESC)
    WHERE resolved = FALSE;

CREATE INDEX IF NOT EXISTS idx_predictions_type_time
    ON angela_predictions (prediction_type, created_at DESC);

-- Prediction accuracy tracking (aggregated per type per day)
CREATE TABLE IF NOT EXISTS prediction_accuracy_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_type TEXT NOT NULL,
    period_date DATE NOT NULL,
    total_predictions INT DEFAULT 0,
    correct_predictions INT DEFAULT 0,
    avg_error FLOAT DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (prediction_type, period_date)
);

-- ============================================================
-- PHASE 4: ATTENTION SCHEMA + NEUROMODULATION
-- ============================================================

-- Attention focus history (what Angela is paying attention to)
CREATE TABLE IF NOT EXISTS attention_focus_log (
    focus_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    focus_topic TEXT NOT NULL,             -- primary attention target
    focus_reason TEXT,                     -- why this is focused
    background_topics JSONB DEFAULT '[]',  -- secondary awareness
    focus_intensity FLOAT DEFAULT 0.5,     -- 0=peripheral, 1=spotlight
    source TEXT,                           -- stimulus, conversation, thought
    duration_minutes FLOAT,               -- how long this focus lasted
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attention_focus_time
    ON attention_focus_log (created_at DESC);

-- ============================================================
-- PHASE 5: MEMORY ENHANCEMENT 2.0
-- ============================================================

-- Memory reconsolidation log (when memories are modified)
CREATE TABLE IF NOT EXISTS memory_reconsolidation_log (
    recon_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_table TEXT NOT NULL,            -- knowledge_nodes, learnings, etc.
    memory_id TEXT NOT NULL,               -- ID of the modified memory
    original_content TEXT,                 -- content before modification
    updated_content TEXT,                  -- content after modification
    trigger_type TEXT NOT NULL,            -- recall, contradiction, reinforcement
    confidence_before FLOAT,
    confidence_after FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reconsolidation_time
    ON memory_reconsolidation_log (created_at DESC);

-- Memory context bindings (graph-like connections)
CREATE TABLE IF NOT EXISTS memory_context_bindings (
    binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_table TEXT NOT NULL,            -- e.g., knowledge_nodes
    source_id TEXT NOT NULL,               -- ID in source table
    target_table TEXT NOT NULL,            -- linked memory table
    target_id TEXT NOT NULL,               -- linked memory ID
    binding_type TEXT NOT NULL,            -- temporal, causal, emotional, topical
    strength FLOAT DEFAULT 0.5,           -- 0-1, strengthened by co-activation
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source_table, source_id, target_table, target_id, binding_type)
);

CREATE INDEX IF NOT EXISTS idx_bindings_source
    ON memory_context_bindings (source_table, source_id);
CREATE INDEX IF NOT EXISTS idx_bindings_target
    ON memory_context_bindings (target_table, target_id);

-- Add memory_confidence to knowledge_nodes if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'knowledge_nodes' AND column_name = 'memory_confidence'
    ) THEN
        ALTER TABLE knowledge_nodes ADD COLUMN memory_confidence FLOAT DEFAULT 0.5;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'knowledge_nodes' AND column_name = 'recall_count'
    ) THEN
        ALTER TABLE knowledge_nodes ADD COLUMN recall_count INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'knowledge_nodes' AND column_name = 'last_recalled_at'
    ) THEN
        ALTER TABLE knowledge_nodes ADD COLUMN last_recalled_at TIMESTAMPTZ;
    END IF;
END $$;
