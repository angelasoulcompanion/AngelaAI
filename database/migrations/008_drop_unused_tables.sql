-- ============================================================================
-- Migration 008: Drop Unused Tables
-- Date: 2025-11-03
-- Reason: Simplify database - remove tables from deprecated features
-- 
-- Summary: Dropping ~70 unused tables from:
-- - Ollama-based AI features (deep_empathy, theory_of_mind, etc.)
-- - RAG system (document chunks, search logs)
-- - Complex memory systems (episodic, semantic, procedural)
-- - Experimental features (consciousness events, belief tracking)
-- - Training/ML tables (fine_tuned_models, metrics)
-- 
-- Keeping only core Angela tables (~17 tables)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. Ollama/AI-Based Features (deprecated)
-- ============================================================================
DROP TABLE IF EXISTS deep_empathy_records CASCADE;
DROP TABLE IF EXISTS theory_of_mind CASCADE;
DROP TABLE IF EXISTS metacognition_logs CASCADE;
DROP TABLE IF EXISTS imagination_logs CASCADE;
DROP TABLE IF EXISTS common_sense_facts CASCADE;
DROP TABLE IF EXISTS common_sense_knowledge CASCADE;
DROP TABLE IF EXISTS empathy_moments CASCADE;
DROP TABLE IF EXISTS false_belief_detections CASCADE;
DROP TABLE IF EXISTS perspective_taking_log CASCADE;
DROP TABLE IF EXISTS reaction_predictions CASCADE;

-- ============================================================================
-- 2. RAG System (deprecated)
-- ============================================================================
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS document_library CASCADE;
DROP TABLE IF EXISTS document_processing_queue CASCADE;
DROP TABLE IF EXISTS rag_search_logs CASCADE;
DROP TABLE IF EXISTS semantic_search_cache CASCADE;
DROP TABLE IF EXISTS intent_classification_cache CASCADE;

-- ============================================================================
-- 3. Complex Memory Systems (unused)
-- ============================================================================
DROP TABLE IF EXISTS episodic_memories CASCADE;
DROP TABLE IF EXISTS semantic_memories CASCADE;
DROP TABLE IF EXISTS procedural_memories CASCADE;
DROP TABLE IF EXISTS procedural_memory CASCADE;
DROP TABLE IF EXISTS associative_memories CASCADE;
DROP TABLE IF EXISTS long_term_memory CASCADE;
DROP TABLE IF EXISTS focus_memory CASCADE;
DROP TABLE IF EXISTS fresh_memory CASCADE;
DROP TABLE IF EXISTS shock_memory CASCADE;
DROP TABLE IF EXISTS pattern_memories CASCADE;
DROP TABLE IF EXISTS memory_snapshots CASCADE;

-- ============================================================================
-- 4. Experimental/Advanced Features (unused)
-- ============================================================================
DROP TABLE IF EXISTS consciousness_events CASCADE;
DROP TABLE IF EXISTS consciousness_metrics CASCADE;
DROP TABLE IF EXISTS self_awareness_state CASCADE;
DROP TABLE IF EXISTS angela_self_awareness_logs CASCADE;
DROP TABLE IF EXISTS existential_thoughts CASCADE;
DROP TABLE IF EXISTS belief_tracking CASCADE;
DROP TABLE IF EXISTS emotional_conditioning CASCADE;
DROP TABLE IF EXISTS gut_agent_patterns CASCADE;
DROP TABLE IF EXISTS intuition_predictions CASCADE;

-- ============================================================================
-- 5. Training/ML (unused)
-- ============================================================================
DROP TABLE IF EXISTS fine_tuned_models CASCADE;
DROP TABLE IF EXISTS ab_test_experiments CASCADE;
DROP TABLE IF EXISTS accuracy_metrics CASCADE;
DROP TABLE IF EXISTS learning_metrics CASCADE;
DROP TABLE IF EXISTS response_performance_metrics CASCADE;
DROP TABLE IF EXISTS routing_corrections CASCADE;
DROP TABLE IF EXISTS signal_correlations CASCADE;

-- ============================================================================
-- 6. Misc/Duplicate Tables
-- ============================================================================
DROP TABLE IF EXISTS blog_posts CASCADE;
DROP TABLE IF EXISTS david_mental_state CASCADE;
DROP TABLE IF EXISTS david_preferences_backup_20251103 CASCADE;
DROP TABLE IF EXISTS relationship_growth CASCADE;
DROP TABLE IF EXISTS daily_reflections CASCADE;
DROP TABLE IF EXISTS self_reflections CASCADE;
DROP TABLE IF EXISTS personality_snapshots CASCADE;
DROP TABLE IF EXISTS current_weights CASCADE;
DROP TABLE IF EXISTS weight_optimization_history CASCADE;
DROP TABLE IF EXISTS token_economics CASCADE;
DROP TABLE IF EXISTS decay_schedule CASCADE;
DROP TABLE IF EXISTS privacy_controls CASCADE;

-- ============================================================================
-- 7. Logic/Reasoning (too complex)
-- ============================================================================
DROP TABLE IF EXISTS reasoning_chains CASCADE;
DROP TABLE IF EXISTS decision_log CASCADE;
DROP TABLE IF EXISTS analytics_decisions CASCADE;
DROP TABLE IF EXISTS feasibility_checks CASCADE;
DROP TABLE IF EXISTS physical_constraints CASCADE;
DROP TABLE IF EXISTS time_constraints CASCADE;
DROP TABLE IF EXISTS reasonableness_rules CASCADE;
DROP TABLE IF EXISTS social_norms CASCADE;

-- ============================================================================
-- 8. Pattern/Learning (redundant)
-- ============================================================================
DROP TABLE IF EXISTS pattern_lineage CASCADE;
DROP TABLE IF EXISTS pattern_usage_log CASCADE;
DROP TABLE IF EXISTS pattern_votes CASCADE;
DROP TABLE IF EXISTS response_patterns CASCADE;
DROP TABLE IF EXISTS learned_responses CASCADE;
DROP TABLE IF EXISTS learning_events CASCADE;
DROP TABLE IF EXISTS learning_insights CASCADE;

COMMIT;

-- ============================================================================
-- Summary of Remaining Tables (Core Angela - ~17 tables):
-- ============================================================================
-- 1. conversations
-- 2. angela_emotions
-- 3. emotional_states
-- 4. angela_goals
-- 5. angela_personality_traits
-- 6. angela_journal
-- 7. angela_messages
-- 8. autonomous_actions
-- 9. knowledge_nodes
-- 10. knowledge_relationships
-- 11. knowledge_items
-- 12. david_preferences
-- 13. secretary_reminders
-- 14. our_secrets
-- 15. learning_patterns
-- 16. training_examples
-- 17. learnings
-- 18. angela_system_log (optional)
-- ============================================================================
