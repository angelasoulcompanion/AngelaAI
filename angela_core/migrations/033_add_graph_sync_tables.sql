-- Migration 033: Graph Sync + Graph-RAG Tables
-- Knowledge Graph sync watermarks + Graph-RAG query logging
-- Created: 2026-02-27

-- Graph sync watermark: tracks per-entity-type last synced timestamp
CREATE TABLE IF NOT EXISTS graph_sync_watermarks (
    entity_type TEXT PRIMARY KEY,
    last_synced_at TIMESTAMPTZ NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    rows_synced BIGINT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Graph sync log: audit trail for each sync batch
CREATE TABLE IF NOT EXISTS graph_sync_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_type TEXT NOT NULL,           -- full, incremental
    entity_type TEXT NOT NULL,         -- knowledge_node, conversation, emotion, etc.
    nodes_upserted INT DEFAULT 0,
    edges_upserted INT DEFAULT 0,
    duration_ms FLOAT DEFAULT 0,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Graph-RAG query log: track query performance and quality
CREATE TABLE IF NOT EXISTS graph_rag_query_log (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    query_type TEXT NOT NULL,           -- simple, relational, exploratory
    vector_results INT DEFAULT 0,
    graph_results INT DEFAULT 0,
    final_results INT DEFAULT 0,
    graph_context_nodes INT DEFAULT 0,
    graph_context_edges INT DEFAULT 0,
    retrieval_time_ms FLOAT DEFAULT 0,
    graph_time_ms FLOAT DEFAULT 0,
    total_time_ms FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed watermarks for all entity types
INSERT INTO graph_sync_watermarks (entity_type) VALUES
    ('knowledge_node'),
    ('conversation'),
    ('emotion'),
    ('core_memory'),
    ('learning'),
    ('knowledge_relationship'),
    ('memory_context_binding')
ON CONFLICT (entity_type) DO NOTHING;

-- Index for query log analysis
CREATE INDEX IF NOT EXISTS idx_graph_rag_query_log_type ON graph_rag_query_log(query_type);
CREATE INDEX IF NOT EXISTS idx_graph_sync_log_created ON graph_sync_log(created_at);
