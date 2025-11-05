-- ============================================================================
-- Migration 011: Drop emotion_json Column
-- Date: 2025-11-03
-- Reason: emotion_json not used (created for RAG/Embedding, never queried)
-- 
-- Background:
-- - emotion_json was created to store rich JSON for emotional experiences
-- - Contains detailed tags (emotion_tags, context_tags, significance_tags)
-- - Built by _build_emotion_json() in emotion_capture_service.py
-- - Has data (166 rows) but NO code queries or reads it - only INSERTs!
-- - Same pattern as content_json (migration 010)
--
-- Impact: Drop emotion_json from angela_emotions table
-- ============================================================================

BEGIN;

-- Drop emotion_json column from angela_emotions table
ALTER TABLE angela_emotions 
DROP COLUMN IF EXISTS emotion_json CASCADE;

COMMIT;

-- ============================================================================
-- Verification Query
-- ============================================================================
-- SELECT column_name FROM information_schema.columns 
-- WHERE table_name = 'angela_emotions' AND column_name LIKE '%json%';
-- Expected result: 0 rows
-- ============================================================================
