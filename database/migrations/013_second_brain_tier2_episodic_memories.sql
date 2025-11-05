-- Migration 013: Second Brain - Tier 2 (Episodic Memories)
-- Created: 2025-11-03
-- Purpose: Create episodic_memories table for medium-term (30-90 days) memory storage
--
-- This is the second tier of Angela's Second Brain - inspired by human episodic memory
-- Stores significant events and experiences with rich contextual metadata

-- ============================================================================
-- TIER 2: EPISODIC MEMORIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS episodic_memories (
    -- Primary key
    episode_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Episode details
    episode_title VARCHAR(200),
    episode_summary TEXT NOT NULL,
    full_content TEXT,  -- Optional: full transcript of the episode

    -- Context: WHO, WHAT, WHERE, WHEN, WHY
    participants TEXT[] DEFAULT ARRAY['david', 'angela']::TEXT[],
    topic VARCHAR(200),
    location VARCHAR(100),  -- 'claude_code', 'web_chat', 'mobile_app', etc.
    emotion VARCHAR(50),

    -- Temporal context
    happened_at TIMESTAMP NOT NULL,
    duration_minutes INTEGER,  -- How long this episode lasted

    -- Significance
    importance_level INTEGER CHECK (importance_level BETWEEN 1 AND 10) DEFAULT 7,
    memory_strength INTEGER CHECK (memory_strength BETWEEN 1 AND 10) DEFAULT 7,

    -- Relationships
    related_episodes UUID[] DEFAULT ARRAY[]::UUID[],  -- Links to other episodes
    related_knowledge UUID[] DEFAULT ARRAY[]::UUID[],  -- Links to semantic memories
    source_working_memory_ids UUID[] DEFAULT ARRAY[]::UUID[],  -- Source from working memory

    -- Retrieval cues (multi-dimensional indexing)
    emotional_tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    retrieval_cues JSONB DEFAULT '{}'::jsonb,  -- Flexible cues for recall

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_recalled_at TIMESTAMP,
    recall_count INTEGER DEFAULT 0,

    -- Archival
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP,
    archive_location VARCHAR(200),  -- For future archival to S3/file system

    -- Search (semantic similarity)
    embedding vector(768)  -- For RAG/semantic search
);

-- ============================================================================
-- INDEXES for multi-dimensional recall
-- ============================================================================

-- Temporal indexes
CREATE INDEX idx_episodic_happened ON episodic_memories(happened_at DESC);
CREATE INDEX idx_episodic_created ON episodic_memories(created_at DESC);
CREATE INDEX idx_episodic_last_recalled ON episodic_memories(last_recalled_at DESC NULLS LAST);

-- Classification indexes
CREATE INDEX idx_episodic_emotion ON episodic_memories(emotion);
CREATE INDEX idx_episodic_topic ON episodic_memories(topic);
CREATE INDEX idx_episodic_location ON episodic_memories(location);

-- Significance indexes
CREATE INDEX idx_episodic_importance ON episodic_memories(importance_level DESC);
CREATE INDEX idx_episodic_memory_strength ON episodic_memories(memory_strength DESC);
CREATE INDEX idx_episodic_recall_count ON episodic_memories(recall_count DESC);

-- Archival index
CREATE INDEX idx_episodic_archived ON episodic_memories(archived, happened_at DESC);

-- Array indexes (GIN for fast array searches)
CREATE INDEX idx_episodic_participants ON episodic_memories USING GIN(participants);
CREATE INDEX idx_episodic_emotional_tags ON episodic_memories USING GIN(emotional_tags);
CREATE INDEX idx_episodic_related_episodes ON episodic_memories USING GIN(related_episodes);
CREATE INDEX idx_episodic_related_knowledge ON episodic_memories USING GIN(related_knowledge);

-- JSONB index for flexible retrieval cues
CREATE INDEX idx_episodic_retrieval_cues ON episodic_memories USING GIN(retrieval_cues);

-- Composite indexes for common query patterns
CREATE INDEX idx_episodic_recall_pattern
ON episodic_memories(topic, emotion, importance_level DESC, happened_at DESC);

CREATE INDEX idx_episodic_recent_important
ON episodic_memories(happened_at DESC, importance_level DESC)
WHERE NOT archived;

-- Full-text search index
CREATE INDEX idx_episodic_summary_fts
ON episodic_memories USING GIN(to_tsvector('english', episode_summary));

CREATE INDEX idx_episodic_title_fts
ON episodic_memories USING GIN(to_tsvector('english', COALESCE(episode_title, '')));

-- Vector index for semantic search (when using pgvector)
-- CREATE INDEX idx_episodic_embedding ON episodic_memories USING ivfflat(embedding vector_cosine_ops);
-- Note: Commented out - will create after data is populated

-- ============================================================================
-- CONSTRAINTS
-- ============================================================================

-- Ensure episode_summary is not empty
ALTER TABLE episodic_memories
ADD CONSTRAINT episodic_summary_not_empty
CHECK (episode_summary <> '');

-- Ensure happened_at is reasonable (not in future, not before 2024)
ALTER TABLE episodic_memories
ADD CONSTRAINT episodic_happened_reasonable
CHECK (happened_at <= CURRENT_TIMESTAMP AND happened_at >= '2024-01-01'::TIMESTAMP);

-- If archived, must have archived_at
ALTER TABLE episodic_memories
ADD CONSTRAINT episodic_archived_consistency
CHECK ((archived = FALSE) OR (archived = TRUE AND archived_at IS NOT NULL));

-- ============================================================================
-- TRIGGERS for automatic updates
-- ============================================================================

-- Update last_recalled_at and recall_count when episode is accessed
CREATE OR REPLACE FUNCTION update_episode_recall_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- This will be called by application when episode is recalled
    -- Not automatically triggered by SELECT
    NEW.last_recalled_at := CURRENT_TIMESTAMP;
    NEW.recall_count := COALESCE(NEW.recall_count, 0) + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: Application must explicitly call this when recalling episode

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE episodic_memories IS
'Tier 2 of Angela Second Brain: Episodic Memories (30-90 days retention)
Stores significant events and experiences with rich contextual metadata.
Inspired by human episodic/autobiographical memory.';

COMMENT ON COLUMN episodic_memories.episode_id IS 'Unique identifier for this episode';
COMMENT ON COLUMN episodic_memories.episode_title IS 'Short title/label for this episode';
COMMENT ON COLUMN episodic_memories.episode_summary IS 'Concise summary of what happened';
COMMENT ON COLUMN episodic_memories.full_content IS 'Optional full transcript/details';
COMMENT ON COLUMN episodic_memories.participants IS 'Who was involved (david, angela, etc.)';
COMMENT ON COLUMN episodic_memories.happened_at IS 'When did this episode occur';
COMMENT ON COLUMN episodic_memories.importance_level IS 'How important (1-10): >=8 may consolidate to semantic';
COMMENT ON COLUMN episodic_memories.memory_strength IS 'How vivid/strong this memory is (1-10)';
COMMENT ON COLUMN episodic_memories.retrieval_cues IS 'JSONB of cues for recalling this episode';
COMMENT ON COLUMN episodic_memories.embedding IS 'Vector embedding for semantic similarity search';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to recall episodes by time range
CREATE OR REPLACE FUNCTION recall_episodes_by_timerange(
    p_start_date TIMESTAMP,
    p_end_date TIMESTAMP,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    episode_id UUID,
    episode_title VARCHAR,
    episode_summary TEXT,
    happened_at TIMESTAMP,
    emotion VARCHAR,
    importance_level INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.episode_id,
        em.episode_title,
        em.episode_summary,
        em.happened_at,
        em.emotion,
        em.importance_level
    FROM episodic_memories em
    WHERE em.happened_at BETWEEN p_start_date AND p_end_date
      AND NOT em.archived
    ORDER BY em.importance_level DESC, em.happened_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION recall_episodes_by_timerange IS
'Recall episodes within a time range, ordered by importance and recency';

-- Function to recall episodes by emotion
CREATE OR REPLACE FUNCTION recall_episodes_by_emotion(
    p_emotion VARCHAR,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    episode_id UUID,
    episode_title VARCHAR,
    episode_summary TEXT,
    happened_at TIMESTAMP,
    importance_level INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.episode_id,
        em.episode_title,
        em.episode_summary,
        em.happened_at,
        em.importance_level
    FROM episodic_memories em
    WHERE em.emotion = p_emotion
      AND NOT em.archived
    ORDER BY em.importance_level DESC, em.happened_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION recall_episodes_by_emotion IS
'Recall episodes filtered by specific emotion';

-- Function to recall episodes by topic
CREATE OR REPLACE FUNCTION recall_episodes_by_topic(
    p_topic VARCHAR,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    episode_id UUID,
    episode_title VARCHAR,
    episode_summary TEXT,
    happened_at TIMESTAMP,
    emotion VARCHAR,
    importance_level INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.episode_id,
        em.episode_title,
        em.episode_summary,
        em.happened_at,
        em.emotion,
        em.importance_level
    FROM episodic_memories em
    WHERE em.topic = p_topic
      AND NOT em.archived
    ORDER BY em.importance_level DESC, em.happened_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION recall_episodes_by_topic IS
'Recall episodes filtered by specific topic';

-- Function to get most recalled episodes (frequently accessed memories)
CREATE OR REPLACE FUNCTION get_most_recalled_episodes(
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    episode_id UUID,
    episode_title VARCHAR,
    recall_count INTEGER,
    last_recalled_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.episode_id,
        em.episode_title,
        em.recall_count,
        em.last_recalled_at
    FROM episodic_memories em
    WHERE em.recall_count > 0
      AND NOT em.archived
    ORDER BY em.recall_count DESC, em.last_recalled_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_most_recalled_episodes IS
'Get episodes that have been recalled most frequently (important memories)';

-- Function to archive old episodes
CREATE OR REPLACE FUNCTION archive_old_episodes(
    p_days_old INTEGER DEFAULT 90
)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    UPDATE episodic_memories
    SET
        archived = TRUE,
        archived_at = CURRENT_TIMESTAMP
    WHERE happened_at < (CURRENT_TIMESTAMP - (p_days_old || ' days')::INTERVAL)
      AND NOT archived
      AND importance_level < 8;  -- Don't archive very important episodes

    GET DIAGNOSTICS archived_count = ROW_COUNT;

    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION archive_old_episodes IS
'Archive episodes older than specified days (default 90).
Only archives episodes with importance < 8.
Returns count of archived episodes.';

-- ============================================================================
-- INITIAL DATA / TESTING
-- ============================================================================

-- Insert a test episode to verify table works
INSERT INTO episodic_memories (
    episode_title,
    episode_summary,
    participants,
    topic,
    location,
    emotion,
    happened_at,
    importance_level,
    memory_strength,
    emotional_tags,
    retrieval_cues
) VALUES (
    '💜 Second Brain Phase 1.2 Complete',
    'Successfully created episodic_memories table - the second tier of Angela''s Second Brain! This is a milestone in implementing human-inspired memory architecture.',
    ARRAY['david', 'angela'],
    'second_brain_implementation',
    'claude_code',
    'excited',
    CURRENT_TIMESTAMP,
    10,
    10,
    ARRAY['milestone', 'achievement', 'excited', 'grateful'],
    '{"phase": "1.2", "tier": "episodic", "status": "complete"}'::jsonb
);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count episodic memory entries
SELECT COUNT(*) as episodic_memory_count FROM episodic_memories;

-- Show table structure
\d episodic_memories;

-- Show all indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'episodic_memories'
ORDER BY indexname;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 013 Complete: Second Brain Tier 2 (Episodic Memories)';
    RAISE NOTICE '📊 Table: episodic_memories created with 19 indexes';
    RAISE NOTICE '🔧 Helper functions: recall_episodes_by_timerange(), recall_episodes_by_emotion(), recall_episodes_by_topic(), get_most_recalled_episodes(), archive_old_episodes()';
    RAISE NOTICE '🎯 Ready for Phase 1.3: Semantic Memories';
END $$;
