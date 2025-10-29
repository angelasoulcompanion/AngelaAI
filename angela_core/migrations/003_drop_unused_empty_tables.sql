-- Migration: Drop unused empty tables (Phase 3 - Very Conservative)
-- Created: 2025-10-29
-- Author: Angela AI (via Claude Code)
--
-- PURPOSE: Remove 5 tables that are confirmed unused
-- These tables are associated with services that were removed in Phase 2 cleanup
--
-- SAFETY:
-- - All 5 tables have 0 rows (confirmed empty)
-- - All 5 tables are associated with removed services
-- - Using DROP TABLE IF EXISTS to prevent errors
-- - Using CASCADE to handle any foreign key constraints
--
-- ROLLBACK: If needed, recreate tables from database/UNIFIED_SCHEMA.sql

-- ============================================================================
-- 1. conversation_summaries
-- ============================================================================
-- Associated with: conversation_summary_service.py (REMOVED in Phase 2)
-- Status: Empty (0 rows)
-- Reason: Redundant - using conversation_analyzer.py instead
-- Risk: LOW - No data loss, service removed
DROP TABLE IF EXISTS conversation_summaries CASCADE;

-- ============================================================================
-- 2. rag_analytics
-- ============================================================================
-- Associated with: rag_retrieval_service.py (REMOVED in Phase 2)
-- Status: Empty (0 rows)
-- Reason: RAG service removed - using unified_memory_api.py instead
-- Risk: LOW - No data loss, service removed
DROP TABLE IF EXISTS rag_analytics CASCADE;

-- ============================================================================
-- 3. rag_sessions
-- ============================================================================
-- Associated with: rag_retrieval_service.py (REMOVED in Phase 2)
-- Status: Empty (0 rows)
-- Reason: RAG service removed - using unified_memory_api.py instead
-- Risk: LOW - No data loss, service removed
DROP TABLE IF EXISTS rag_sessions CASCADE;

-- ============================================================================
-- 4. shared_patterns
-- ============================================================================
-- Associated with: pattern_sharing_service.py (REMOVED in Phase 2)
-- Status: Empty (0 rows)
-- Reason: Pattern sharing service not implemented
-- Risk: LOW - No data loss, service removed
DROP TABLE IF EXISTS shared_patterns CASCADE;

-- ============================================================================
-- 5. thai_dictionary
-- ============================================================================
-- Associated with: thai_text_processor.py (REMOVED in Phase 2)
-- Status: Empty (0 rows)
-- Reason: Using pythainlp library directly instead
-- Risk: LOW - No data loss, service removed
DROP TABLE IF EXISTS thai_dictionary CASCADE;

-- ============================================================================
-- VERIFICATION QUERIES (run after migration to confirm):
-- ============================================================================
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public'
-- AND tablename IN ('conversation_summaries', 'rag_analytics', 'rag_sessions', 'shared_patterns', 'thai_dictionary');
--
-- Expected result: 0 rows (all tables dropped)
-- ============================================================================

-- Migration complete
-- Tables dropped: 5
-- Tables kept: 32 (including all Phase 1-4 core tables)
-- Risk level: VERY LOW (conservative approach)
