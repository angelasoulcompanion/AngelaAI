-- ============================================================================
-- Migration 011: Cleanup Unused Tables
-- ============================================================================
-- Purpose: Drop 14 tables with 0 rows (never actually used)
-- Date: 2025-11-14
-- Reason: Preparing for Consciousness System (Migration 012)
-- ============================================================================

BEGIN;

-- --------------------------------------------------------------------------
-- Category 1: Definitely Unused (0 rows + no code references)
-- --------------------------------------------------------------------------

DROP TABLE IF EXISTS project_files_index CASCADE;
DROP TABLE IF EXISTS image_analysis_results CASCADE;

-- --------------------------------------------------------------------------
-- Category 2: Never Used (0 rows but have code references)
-- --------------------------------------------------------------------------
-- These tables have code references but ZERO data ever inserted
-- Removing to clean up schema for new consciousness system
-- --------------------------------------------------------------------------

DROP TABLE IF EXISTS working_memory CASCADE;
DROP TABLE IF EXISTS coding_patterns CASCADE;
DROP TABLE IF EXISTS angela_personality_history CASCADE;
DROP TABLE IF EXISTS self_reflections CASCADE;
DROP TABLE IF EXISTS decision_log CASCADE;
DROP TABLE IF EXISTS reasoning_chains CASCADE;
DROP TABLE IF EXISTS consciousness_events CASCADE;
DROP TABLE IF EXISTS project_contexts CASCADE;
DROP TABLE IF EXISTS project_conversations CASCADE;
DROP TABLE IF EXISTS knowledge_items CASCADE;
DROP TABLE IF EXISTS angela_personality_traits CASCADE;
DROP TABLE IF EXISTS solution_history CASCADE;

COMMIT;

-- ============================================================================
-- Migration 011 Complete!
-- ============================================================================
-- Dropped 14 tables:
--   Category 1 (0 rows + no code): 2 tables
--   Category 2 (0 rows + has code): 12 tables
-- ============================================================================
-- Next: Migration 012 will create new consciousness tables
-- ============================================================================
