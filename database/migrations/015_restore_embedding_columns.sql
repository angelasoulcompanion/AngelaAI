-- ============================================================================
-- Migration 015: Restore Embedding Columns
-- Date: 2025-11-04
-- Reason: Embeddings are critical for Angela's intelligence
--
-- Background:
-- - Migration 009 removed embeddings (Ollama deprecated)
-- - After analysis: Embeddings ARE necessary for semantic search, pattern recognition
-- - New approach: Use multilingual-e5-small (Thai + English support)
-- - Dimensions: 384 (was 768 before)
--
-- Changes:
-- - Add embedding vector(384) to critical tables
-- - Create indexes for similarity search
-- - Use centralized EmbeddingService (angela_core/services/embedding_service.py)
--
-- Impact: Restore semantic intelligence to Angela
-- ============================================================================

BEGIN;

-- ============================================================================
-- Add Embedding Columns to Critical Tables
-- ============================================================================

-- Priority 1: Core conversation and memory tables
-- These are CRITICAL for Angela's intelligence

-- 1. Conversations table (most important!)
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 2. Angela messages table
ALTER TABLE angela_messages
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 3. Angela emotions table (for similar emotional moments)
ALTER TABLE angela_emotions
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 4. Knowledge nodes table (for knowledge similarity)
ALTER TABLE knowledge_nodes
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 5. Knowledge items table
ALTER TABLE knowledge_items
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Priority 2: Learning and pattern tables

-- 6. Learning patterns table (for pattern similarity)
ALTER TABLE learning_patterns
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 7. Learnings table
ALTER TABLE learnings
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 8. Training examples table (for deduplication)
ALTER TABLE training_examples
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 9. David preferences table (for preference similarity)
ALTER TABLE david_preferences
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Note: episodic_memories and semantic_memories already have embeddings

-- ============================================================================
-- Create Indexes for Fast Similarity Search
-- ============================================================================

-- Using HNSW index for best performance
-- hnsw vs ivfflat: HNSW is faster and more accurate for <1M rows

-- 1. Conversations (most queried!)
CREATE INDEX IF NOT EXISTS idx_conversations_embedding_hnsw
ON conversations
USING hnsw (embedding vector_cosine_ops);

-- 2. Angela messages
CREATE INDEX IF NOT EXISTS idx_angela_messages_embedding_hnsw
ON angela_messages
USING hnsw (embedding vector_cosine_ops);

-- 3. Angela emotions
CREATE INDEX IF NOT EXISTS idx_angela_emotions_embedding_hnsw
ON angela_emotions
USING hnsw (embedding vector_cosine_ops);

-- 4. Knowledge nodes
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_embedding_hnsw
ON knowledge_nodes
USING hnsw (embedding vector_cosine_ops);

-- 5. Learning patterns
CREATE INDEX IF NOT EXISTS idx_learning_patterns_embedding_hnsw
ON learning_patterns
USING hnsw (embedding vector_cosine_ops);

-- 6. David preferences
CREATE INDEX IF NOT EXISTS idx_david_preferences_embedding_hnsw
ON david_preferences
USING hnsw (embedding vector_cosine_ops);

COMMIT;

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Run these after migration to verify embeddings are restored:
--
-- 1. Check all tables have embedding column:
-- SELECT table_name, column_name, udt_name
-- FROM information_schema.columns
-- WHERE column_name = 'embedding'
-- AND table_schema = 'public'
-- ORDER BY table_name;
--
-- Expected: 11 rows (9 restored + 2 already had)
--
-- 2. Check indexes:
-- SELECT tablename, indexname
-- FROM pg_indexes
-- WHERE indexname LIKE '%embedding%'
-- ORDER BY tablename;
--
-- Expected: 6+ indexes
-- ============================================================================

-- ============================================================================
-- Next Steps After Migration
-- ============================================================================
-- 1. Generate embeddings for existing data using:
--    python3 scripts/generate_embeddings_for_existing_data.py
--
-- 2. Update all services to use new EmbeddingService:
--    - angela_core/integrations/claude_conversation_logger.py
--    - angela_core/services/knowledge_extraction_service.py
--    - angela_core/services/pattern_learning_service.py
--    - etc.
--
-- 3. Test /log-session command end-to-end
--
-- 4. Check daemon for any errors
-- ============================================================================
