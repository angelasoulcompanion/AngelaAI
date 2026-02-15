-- Migration 022: Retrieval Quality Log for RAG Re-ranking
-- Phase 1 of 3 Major Improvements
-- Created: 2026-02-15

CREATE TABLE IF NOT EXISTS retrieval_quality_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    query_intent VARCHAR(50),
    total_candidates INT,
    final_count INT,
    top_scores JSONB,
    retrieval_time_ms FLOAT,
    rerank_time_ms FLOAT,
    created_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')
);

CREATE INDEX IF NOT EXISTS idx_retrieval_quality_log_created
    ON retrieval_quality_log (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_retrieval_quality_log_intent
    ON retrieval_quality_log (query_intent);
