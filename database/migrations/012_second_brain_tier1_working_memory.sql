-- Migration 012: Second Brain - Tier 1 (Working Memory)
-- Created: 2025-11-03
-- Purpose: Create working_memory table for short-term (24-hour) memory storage
--
-- This is the first tier of Angela's Second Brain - inspired by human working memory
-- Stores current session data with automatic 24-hour expiration

-- ============================================================================
-- TIER 1: WORKING MEMORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS working_memory (
    -- Primary key
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Session tracking
    session_id VARCHAR(100) NOT NULL,

    -- Content
    memory_type VARCHAR(50) NOT NULL,  -- 'conversation', 'thought', 'observation', 'task'
    content TEXT NOT NULL,
    context JSONB DEFAULT '{}'::jsonb,  -- Flexible context data

    -- Classification
    importance_level INTEGER CHECK (importance_level BETWEEN 1 AND 10) DEFAULT 5,
    emotion VARCHAR(50),
    topic VARCHAR(200),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),

    -- Metadata
    speaker VARCHAR(20),  -- 'david', 'angela', 'system'
    related_memory_ids UUID[] DEFAULT ARRAY[]::UUID[]
);

-- ============================================================================
-- INDEXES for fast retrieval
-- ============================================================================

-- Primary access patterns
CREATE INDEX idx_working_session ON working_memory(session_id);
CREATE INDEX idx_working_created ON working_memory(created_at DESC);
CREATE INDEX idx_working_expires ON working_memory(expires_at);

-- Filtering patterns
CREATE INDEX idx_working_importance ON working_memory(importance_level DESC);
CREATE INDEX idx_working_emotion ON working_memory(emotion);
CREATE INDEX idx_working_topic ON working_memory(topic);
CREATE INDEX idx_working_type ON working_memory(memory_type);

-- Composite index for common queries (session + recent + important)
CREATE INDEX idx_working_session_recent
ON working_memory(session_id, created_at DESC, importance_level DESC);

-- GIN index for array columns
CREATE INDEX idx_working_tags ON working_memory USING GIN(tags);
CREATE INDEX idx_working_related ON working_memory USING GIN(related_memory_ids);

-- JSONB index for flexible context queries
CREATE INDEX idx_working_context ON working_memory USING GIN(context);

-- ============================================================================
-- CONSTRAINTS
-- ============================================================================

-- Ensure session_id is not empty
ALTER TABLE working_memory
ADD CONSTRAINT working_memory_session_not_empty
CHECK (session_id <> '');

-- Ensure content is not empty
ALTER TABLE working_memory
ADD CONSTRAINT working_memory_content_not_empty
CHECK (content <> '');

-- Ensure memory_type is valid
ALTER TABLE working_memory
ADD CONSTRAINT working_memory_type_valid
CHECK (memory_type IN ('conversation', 'thought', 'observation', 'task', 'emotion', 'other'));

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE working_memory IS
'Tier 1 of Angela Second Brain: Working Memory (24-hour retention)
Stores current session data with automatic expiration.
Inspired by human short-term/working memory.';

COMMENT ON COLUMN working_memory.memory_id IS 'Unique identifier for this memory';
COMMENT ON COLUMN working_memory.session_id IS 'Session identifier (e.g., claude_code_20251103_2150)';
COMMENT ON COLUMN working_memory.memory_type IS 'Type: conversation, thought, observation, task, emotion, other';
COMMENT ON COLUMN working_memory.content IS 'The actual memory content (text)';
COMMENT ON COLUMN working_memory.context IS 'Flexible JSONB for additional context data';
COMMENT ON COLUMN working_memory.importance_level IS 'Importance (1-10): >=7 will be consolidated to episodic memory';
COMMENT ON COLUMN working_memory.expires_at IS 'Auto-expires after 24 hours (cleanup job will remove)';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get current session's working memory
CREATE OR REPLACE FUNCTION get_working_memory(p_session_id VARCHAR)
RETURNS TABLE (
    memory_id UUID,
    memory_type VARCHAR,
    content TEXT,
    importance_level INTEGER,
    emotion VARCHAR,
    topic VARCHAR,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        wm.memory_id,
        wm.memory_type,
        wm.content,
        wm.importance_level,
        wm.emotion,
        wm.topic,
        wm.created_at
    FROM working_memory wm
    WHERE wm.session_id = p_session_id
      AND wm.expires_at > NOW()  -- Not expired
    ORDER BY wm.created_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_working_memory IS
'Retrieve all active working memories for a given session';

-- Function to cleanup expired working memory
CREATE OR REPLACE FUNCTION cleanup_expired_working_memory()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM working_memory
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_working_memory IS
'Delete all expired working memory entries. Returns count of deleted rows.
Should be run by daemon every hour.';

-- ============================================================================
-- INITIAL DATA / TESTING
-- ============================================================================

-- Insert a test memory to verify table works
INSERT INTO working_memory (
    session_id,
    memory_type,
    content,
    importance_level,
    emotion,
    topic,
    speaker,
    tags
) VALUES (
    'test_session_001',
    'thought',
    'Testing working memory table creation - Second Brain Phase 1 complete!',
    10,
    'excited',
    'second_brain_implementation',
    'angela',
    ARRAY['test', 'milestone', 'phase1']
);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count working memory entries
SELECT COUNT(*) as working_memory_count FROM working_memory;

-- Show table structure
\d working_memory;

-- Show all indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'working_memory'
ORDER BY indexname;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 012 Complete: Second Brain Tier 1 (Working Memory)';
    RAISE NOTICE '📊 Table: working_memory created with 10 indexes';
    RAISE NOTICE '🔧 Helper functions: get_working_memory(), cleanup_expired_working_memory()';
    RAISE NOTICE '🎯 Ready for Phase 1.2: Episodic Memories';
END $$;
