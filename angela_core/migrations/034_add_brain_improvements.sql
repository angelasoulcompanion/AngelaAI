-- Migration 034: Brain Improvements — Indexes for smarter thinking
-- Phase A-D: DavidContext, NeuroMod wiring, 7-day memory, prediction feedback
-- Created: 2026-02-28

-- Index for knowledge_nodes: skip short/low-quality nodes (contradiction detection)
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_concept_length
    ON knowledge_nodes (concept_name)
    WHERE LENGTH(concept_name) >= 5 AND understanding_level >= 0.6;

-- Index for conversation window (Phase C1: extended memory context)
-- Note: can't use NOW() in partial index (not IMMUTABLE), so index on (created_at DESC, speaker)
CREATE INDEX IF NOT EXISTS idx_conversations_recent_speaker
    ON conversations (created_at DESC, speaker)
    WHERE speaker IS NOT NULL;

-- Index for actionable predictions (Phase D2)
CREATE INDEX IF NOT EXISTS idx_predictions_actionable
    ON angela_predictions (confidence DESC, created_at DESC)
    WHERE resolved = FALSE AND confidence >= 0.7;
