-- Migration: Add Full-Text Search for Hybrid RAG
-- Description: Add tsvector column and GIN index for keyword search
-- Date: 2025-01-17

-- Add tsvector column for full-text search
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS content_tsv tsvector;

-- Create GIN index for full-text search (very fast)
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_tsv
ON document_chunks USING GIN (content_tsv);

-- Function to update tsvector automatically
-- Supports both Thai and English text
CREATE OR REPLACE FUNCTION document_chunks_content_tsv_trigger()
RETURNS trigger AS $$
BEGIN
  -- Use 'simple' configuration for language-agnostic search
  -- Works for both Thai and English
  NEW.content_tsv := to_tsvector('simple', COALESCE(NEW.content, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update tsvector on INSERT/UPDATE
DROP TRIGGER IF EXISTS tsvectorupdate ON document_chunks;
CREATE TRIGGER tsvectorupdate
BEFORE INSERT OR UPDATE ON document_chunks
FOR EACH ROW
EXECUTE FUNCTION document_chunks_content_tsv_trigger();

-- Backfill existing rows
UPDATE document_chunks
SET content_tsv = to_tsvector('simple', COALESCE(content, ''))
WHERE content_tsv IS NULL;

-- Add index on document_id for faster filtering
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
ON document_chunks (document_id);

-- Analyze table for better query planning
ANALYZE document_chunks;

-- Verification
SELECT
    COUNT(*) as total_chunks,
    COUNT(content_tsv) as chunks_with_tsv
FROM document_chunks;

COMMENT ON COLUMN document_chunks.content_tsv IS 'Full-text search vector for hybrid search (language-agnostic)';
COMMENT ON INDEX idx_document_chunks_content_tsv IS 'GIN index for fast keyword search';
