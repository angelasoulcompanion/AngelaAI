-- ============================================================================
-- Migration 009: Drop Embedding Columns
-- Date: 2025-11-03
-- Reason: Embeddings not used (Ollama-based, deprecated)
-- 
-- Background:
-- - Embeddings were created using Ollama nomic-embed-text (768 dimensions)
-- - Ollama models deprecated in architecture simplification
-- - knowledge_insight_service.py already uses keyword search instead
-- - Comment in code: "Simple keyword search (actual schema doesn't have embeddings)"
--
-- Impact: Drop embedding columns from 9 tables (saves storage space)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Drop Embedding Columns from Core Tables
-- ============================================================================

-- 1. Conversations table
ALTER TABLE conversations 
DROP COLUMN IF EXISTS embedding CASCADE;

-- 2. Angela messages table  
ALTER TABLE angela_messages
DROP COLUMN IF EXISTS embedding CASCADE;

-- 3. Angela emotions table
ALTER TABLE angela_emotions
DROP COLUMN IF EXISTS embedding CASCADE;

-- 4. Knowledge nodes table
ALTER TABLE knowledge_nodes
DROP COLUMN IF EXISTS embedding CASCADE;

-- 5. Knowledge items table
ALTER TABLE knowledge_items
DROP COLUMN IF EXISTS embedding CASCADE;

-- 6. Learning patterns table
ALTER TABLE learning_patterns
DROP COLUMN IF EXISTS embedding CASCADE;

-- 7. Learnings table
ALTER TABLE learnings
DROP COLUMN IF EXISTS embedding CASCADE;

-- 8. Training examples table
ALTER TABLE training_examples
DROP COLUMN IF EXISTS embedding CASCADE;

-- Note: recent_conversations is a VIEW, not a table
-- It will be CASCADE dropped when we drop embedding from conversations table
-- No need to explicitly drop it here

COMMIT;

-- ============================================================================
-- Verification Query
-- ============================================================================
-- Run this after migration to verify embeddings are gone:
-- 
-- SELECT table_name, column_name 
-- FROM information_schema.columns 
-- WHERE column_name LIKE '%embedding%' 
-- AND table_schema = 'public';
--
-- Expected result: 0 rows
-- ============================================================================
