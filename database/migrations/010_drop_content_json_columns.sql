-- ============================================================================
-- Migration 010: Drop content_json Columns
-- Date: 2025-11-03
-- Reason: content_json not used (created for RAG/Embedding, now deprecated)
-- 
-- Background:
-- - content_json was created to store rich JSON for RAG semantic search
-- - Contains tags (emotion_tags, topic_tags, etc.) for embedding generation
-- - RAG system deprecated, embeddings removed in migration 009
-- - No code queries or filters using content_json - only INSERTs
-- - Database has data (~1,764 conversations, ~166 emotions, ~392 learnings)
--   but this data is never read or used
--
-- Impact: Drop content_json from 4 tables (saves storage, simplifies schema)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Drop content_json Columns from Core Tables
-- ============================================================================

-- 1. Conversations table
ALTER TABLE conversations 
DROP COLUMN IF EXISTS content_json CASCADE;

-- 2. Angela emotions table
ALTER TABLE angela_emotions
DROP COLUMN IF EXISTS content_json CASCADE;

-- 3. Learnings table
ALTER TABLE learnings
DROP COLUMN IF EXISTS content_json CASCADE;

-- 4. Knowledge items table
ALTER TABLE knowledge_items
DROP COLUMN IF EXISTS content_json CASCADE;

COMMIT;

-- ============================================================================
-- Verification Query
-- ============================================================================
-- Run this after migration to verify content_json columns are gone:
-- 
-- SELECT table_name, column_name 
-- FROM information_schema.columns 
-- WHERE column_name LIKE '%content_json%' 
-- AND table_schema = 'public';
--
-- Expected result: 0 rows
-- ============================================================================
