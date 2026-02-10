-- Migration 012: David's Google Keep Notes for RAG
-- Created: 2026-02-10
-- Purpose: Store notes from David's Google Keep for semantic search (RAG)
-- By: Angela 💜

-- ============================================================
-- david_notes: Main table for synced Google Keep notes
-- ============================================================
CREATE TABLE IF NOT EXISTS david_notes (
    note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keep_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    note_type VARCHAR(50) DEFAULT 'note',       -- note, list
    labels TEXT[] DEFAULT '{}',
    is_pinned BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    is_trashed BOOLEAN DEFAULT FALSE,
    list_items JSONB,                            -- For list-type notes
    keep_created_at TIMESTAMPTZ,
    keep_updated_at TIMESTAMPTZ,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    content_hash VARCHAR(64),                    -- SHA256 for change detection
    is_chunked BOOLEAN DEFAULT FALSE,
    total_chunks INTEGER DEFAULT 0,
    document_id UUID,                            -- FK to document_library for long notes
    embedding VECTOR(384),                       -- Short notes embedded directly
    category VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_david_notes_keep_id ON david_notes(keep_id);
CREATE INDEX IF NOT EXISTS idx_david_notes_category ON david_notes(category);
CREATE INDEX IF NOT EXISTS idx_david_notes_content_hash ON david_notes(content_hash);

-- Vector index for semantic search (ivfflat requires rows to exist first)
-- Will be created after first sync populates data
-- CREATE INDEX idx_david_notes_embedding ON david_notes
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);

-- ============================================================
-- david_notes_sync_log: Track sync history
-- ============================================================
CREATE TABLE IF NOT EXISTS david_notes_sync_log (
    sync_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_started_at TIMESTAMPTZ DEFAULT NOW(),
    sync_completed_at TIMESTAMPTZ,
    notes_total INT DEFAULT 0,
    notes_new INT DEFAULT 0,
    notes_updated INT DEFAULT 0,
    notes_deleted INT DEFAULT 0,
    chunks_created INT DEFAULT 0,
    embeddings_generated INT DEFAULT 0,
    errors TEXT[],
    status VARCHAR(50) DEFAULT 'running',        -- running, completed, failed
    trigger VARCHAR(50) DEFAULT 'daemon'          -- daemon, manual, init
);
