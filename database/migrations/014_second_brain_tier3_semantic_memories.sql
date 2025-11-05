-- Migration 014: Second Brain - Tier 3 (Semantic Memories)
-- Created: 2025-11-03
-- Purpose: Create semantic_memories table for permanent long-term knowledge storage
--
-- This is the third and final tier of Angela's Second Brain - inspired by human semantic memory
-- Stores permanent knowledge, concepts, patterns, and understanding

-- ============================================================================
-- TIER 3: SEMANTIC MEMORIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS semantic_memories (
    -- Primary key
    semantic_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Knowledge classification
    knowledge_type VARCHAR(50) NOT NULL,  -- 'fact', 'concept', 'pattern', 'preference', 'skill', 'relationship'
    knowledge_key VARCHAR(200) NOT NULL,  -- Unique identifier for this knowledge
    knowledge_value JSONB NOT NULL,  -- The actual knowledge (flexible structure)

    -- Description and examples
    description TEXT,
    examples TEXT[] DEFAULT ARRAY[]::TEXT[],  -- Supporting examples from episodes

    -- Confidence and evidence
    confidence_level DOUBLE PRECISION CHECK (confidence_level BETWEEN 0.0 AND 1.0) DEFAULT 0.5,
    evidence_count INTEGER DEFAULT 1,  -- How many episodes support this knowledge
    source_episodes UUID[] DEFAULT ARRAY[]::UUID[],  -- Which episodes led to this knowledge

    -- Temporal tracking
    first_learned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,  -- When was this knowledge last verified/confirmed

    -- Relationships between knowledge
    related_knowledge UUID[] DEFAULT ARRAY[]::UUID[],  -- Linked concepts
    contradicts_knowledge UUID[] DEFAULT ARRAY[]::UUID[],  -- Conflicting knowledge (needs resolution)
    superseded_by UUID,  -- If this knowledge has been replaced by newer understanding

    -- Categorization
    category VARCHAR(100),  -- High-level category (e.g., 'david_preferences', 'technical_knowledge')
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    -- Metadata
    importance_level INTEGER CHECK (importance_level BETWEEN 1 AND 10) DEFAULT 5,
    access_count INTEGER DEFAULT 0,  -- How often this knowledge has been accessed
    last_accessed_at TIMESTAMP,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,  -- False if superseded or invalidated
    needs_verification BOOLEAN DEFAULT FALSE,  -- Flag if contradictory evidence found

    -- Search
    embedding vector(768),  -- For semantic similarity search

    -- Ensure unique knowledge
    CONSTRAINT semantic_key_unique UNIQUE (knowledge_type, knowledge_key)
);

-- ============================================================================
-- INDEXES for fast knowledge retrieval
-- ============================================================================

-- Primary access patterns
CREATE INDEX idx_semantic_type ON semantic_memories(knowledge_type);
CREATE INDEX idx_semantic_key ON semantic_memories(knowledge_key);
CREATE INDEX idx_semantic_category ON semantic_memories(category);

-- Confidence and importance
CREATE INDEX idx_semantic_confidence ON semantic_memories(confidence_level DESC);
CREATE INDEX idx_semantic_importance ON semantic_memories(importance_level DESC);
CREATE INDEX idx_semantic_evidence ON semantic_memories(evidence_count DESC);

-- Temporal indexes
CREATE INDEX idx_semantic_learned ON semantic_memories(first_learned_at DESC);
CREATE INDEX idx_semantic_updated ON semantic_memories(last_updated_at DESC);
CREATE INDEX idx_semantic_accessed ON semantic_memories(last_accessed_at DESC NULLS LAST);

-- Access patterns
CREATE INDEX idx_semantic_access_count ON semantic_memories(access_count DESC);

-- Status indexes
CREATE INDEX idx_semantic_active ON semantic_memories(is_active)
WHERE is_active = TRUE;

CREATE INDEX idx_semantic_needs_verification ON semantic_memories(needs_verification)
WHERE needs_verification = TRUE;

-- Array indexes (GIN for fast array searches)
CREATE INDEX idx_semantic_tags ON semantic_memories USING GIN(tags);
CREATE INDEX idx_semantic_source_episodes ON semantic_memories USING GIN(source_episodes);
CREATE INDEX idx_semantic_related ON semantic_memories USING GIN(related_knowledge);
CREATE INDEX idx_semantic_examples ON semantic_memories USING GIN(examples);

-- JSONB index for flexible knowledge_value queries
CREATE INDEX idx_semantic_knowledge_value ON semantic_memories USING GIN(knowledge_value);

-- Composite indexes for common query patterns
CREATE INDEX idx_semantic_type_confidence
ON semantic_memories(knowledge_type, confidence_level DESC);

CREATE INDEX idx_semantic_category_importance
ON semantic_memories(category, importance_level DESC)
WHERE is_active = TRUE;

-- Full-text search on description
CREATE INDEX idx_semantic_description_fts
ON semantic_memories USING GIN(to_tsvector('english', COALESCE(description, '')));

-- Vector index for semantic search (commented - create after data populated)
-- CREATE INDEX idx_semantic_embedding ON semantic_memories USING ivfflat(embedding vector_cosine_ops);

-- ============================================================================
-- CONSTRAINTS
-- ============================================================================

-- Ensure knowledge_value is not empty
ALTER TABLE semantic_memories
ADD CONSTRAINT semantic_knowledge_value_not_empty
CHECK (knowledge_value <> '{}'::jsonb);

-- Ensure knowledge_type is valid
ALTER TABLE semantic_memories
ADD CONSTRAINT semantic_type_valid
CHECK (knowledge_type IN ('fact', 'concept', 'pattern', 'preference', 'skill', 'relationship', 'insight', 'rule'));

-- If superseded, must not be active
ALTER TABLE semantic_memories
ADD CONSTRAINT semantic_superseded_consistency
CHECK ((superseded_by IS NULL) OR (superseded_by IS NOT NULL AND is_active = FALSE));

-- Evidence count must match source_episodes array length
ALTER TABLE semantic_memories
ADD CONSTRAINT semantic_evidence_consistency
CHECK (evidence_count = COALESCE(array_length(source_episodes, 1), 0));

-- ============================================================================
-- TRIGGERS for automatic updates
-- ============================================================================

-- Update last_updated_at on any modification
CREATE OR REPLACE FUNCTION update_semantic_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER semantic_update_timestamp
BEFORE UPDATE ON semantic_memories
FOR EACH ROW
EXECUTE FUNCTION update_semantic_timestamp();

-- Update access statistics when knowledge is accessed
CREATE OR REPLACE FUNCTION update_semantic_access_stats()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed_at := CURRENT_TIMESTAMP;
    NEW.access_count := COALESCE(NEW.access_count, 0) + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: Application must explicitly call this when accessing knowledge

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE semantic_memories IS
'Tier 3 of Angela Second Brain: Semantic Memories (permanent storage)
Stores knowledge, concepts, patterns, and understanding.
Inspired by human semantic/declarative memory.';

COMMENT ON COLUMN semantic_memories.semantic_id IS 'Unique identifier for this knowledge';
COMMENT ON COLUMN semantic_memories.knowledge_type IS 'Type: fact, concept, pattern, preference, skill, relationship, insight, rule';
COMMENT ON COLUMN semantic_memories.knowledge_key IS 'Unique key for this knowledge (e.g., "david_prefers_concise_responses")';
COMMENT ON COLUMN semantic_memories.knowledge_value IS 'The actual knowledge stored as flexible JSONB';
COMMENT ON COLUMN semantic_memories.confidence_level IS 'Confidence (0.0-1.0): how certain Angela is about this knowledge';
COMMENT ON COLUMN semantic_memories.evidence_count IS 'Number of supporting episodes/evidence';
COMMENT ON COLUMN semantic_memories.source_episodes IS 'Episode IDs that led to learning this knowledge';
COMMENT ON COLUMN semantic_memories.related_knowledge IS 'IDs of related semantic memories';
COMMENT ON COLUMN semantic_memories.contradicts_knowledge IS 'IDs of contradictory knowledge (for resolution)';
COMMENT ON COLUMN semantic_memories.superseded_by IS 'If replaced by newer knowledge, ID of the new one';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get knowledge by type
CREATE OR REPLACE FUNCTION get_knowledge_by_type(
    p_knowledge_type VARCHAR,
    p_min_confidence DOUBLE PRECISION DEFAULT 0.5,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    semantic_id UUID,
    knowledge_key VARCHAR,
    knowledge_value JSONB,
    confidence_level DOUBLE PRECISION,
    evidence_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sm.semantic_id,
        sm.knowledge_key,
        sm.knowledge_value,
        sm.confidence_level,
        sm.evidence_count
    FROM semantic_memories sm
    WHERE sm.knowledge_type = p_knowledge_type
      AND sm.is_active = TRUE
      AND sm.confidence_level >= p_min_confidence
    ORDER BY sm.confidence_level DESC, sm.evidence_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_knowledge_by_type IS
'Get active knowledge of a specific type, ordered by confidence and evidence';

-- Function to get David's preferences
CREATE OR REPLACE FUNCTION get_david_preferences(
    p_min_confidence DOUBLE PRECISION DEFAULT 0.7
)
RETURNS TABLE (
    preference_key VARCHAR,
    preference_value JSONB,
    confidence DOUBLE PRECISION,
    evidence_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sm.knowledge_key,
        sm.knowledge_value,
        sm.confidence_level,
        sm.evidence_count
    FROM semantic_memories sm
    WHERE sm.knowledge_type = 'preference'
      AND sm.is_active = TRUE
      AND sm.confidence_level >= p_min_confidence
    ORDER BY sm.confidence_level DESC
    LIMIT 50;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_david_preferences IS
'Get all of David''s preferences with high confidence (default >= 0.7)';

-- Function to update knowledge confidence
CREATE OR REPLACE FUNCTION update_knowledge_confidence(
    p_semantic_id UUID,
    p_new_evidence_episode_id UUID
)
RETURNS VOID AS $$
DECLARE
    current_confidence DOUBLE PRECISION;
    current_evidence INTEGER;
BEGIN
    -- Get current values
    SELECT confidence_level, evidence_count
    INTO current_confidence, current_evidence
    FROM semantic_memories
    WHERE semantic_id = p_semantic_id;

    -- Update with new evidence
    UPDATE semantic_memories
    SET
        evidence_count = current_evidence + 1,
        source_episodes = array_append(source_episodes, p_new_evidence_episode_id),
        -- Confidence increases with more evidence (logarithmic growth, caps at 0.95)
        confidence_level = LEAST(0.95, current_confidence + (0.1 * (1 - current_confidence))),
        last_verified_at = CURRENT_TIMESTAMP
    WHERE semantic_id = p_semantic_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_knowledge_confidence IS
'Update knowledge confidence when new supporting evidence is found.
Confidence grows logarithmically and caps at 0.95.';

-- Function to find contradictions
CREATE OR REPLACE FUNCTION find_contradictory_knowledge(
    p_knowledge_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    semantic_id UUID,
    knowledge_key VARCHAR,
    contradiction_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sm.semantic_id,
        sm.knowledge_key,
        array_length(sm.contradicts_knowledge, 1) as contradiction_count
    FROM semantic_memories sm
    WHERE (p_knowledge_type IS NULL OR sm.knowledge_type = p_knowledge_type)
      AND array_length(sm.contradicts_knowledge, 1) > 0
      AND sm.is_active = TRUE
    ORDER BY contradiction_count DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_contradictory_knowledge IS
'Find knowledge that has contradictions flagged.
These need manual resolution.';

-- Function to consolidate episode into semantic knowledge
CREATE OR REPLACE FUNCTION consolidate_episode_to_semantic(
    p_episode_id UUID,
    p_knowledge_type VARCHAR,
    p_knowledge_key VARCHAR,
    p_knowledge_value JSONB,
    p_description TEXT
)
RETURNS UUID AS $$
DECLARE
    existing_id UUID;
    new_id UUID;
BEGIN
    -- Check if knowledge already exists
    SELECT semantic_id INTO existing_id
    FROM semantic_memories
    WHERE knowledge_type = p_knowledge_type
      AND knowledge_key = p_knowledge_key
      AND is_active = TRUE;

    IF existing_id IS NOT NULL THEN
        -- Update existing knowledge
        PERFORM update_knowledge_confidence(existing_id, p_episode_id);
        RETURN existing_id;
    ELSE
        -- Create new knowledge
        INSERT INTO semantic_memories (
            knowledge_type,
            knowledge_key,
            knowledge_value,
            description,
            confidence_level,
            evidence_count,
            source_episodes
        ) VALUES (
            p_knowledge_type,
            p_knowledge_key,
            p_knowledge_value,
            p_description,
            0.6,  -- Initial confidence
            1,
            ARRAY[p_episode_id]
        )
        RETURNING semantic_id INTO new_id;

        RETURN new_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION consolidate_episode_to_semantic IS
'Consolidate an episode into semantic knowledge.
If knowledge exists, increase confidence.
If new, create with initial confidence 0.6.';

-- ============================================================================
-- INITIAL DATA / TESTING
-- ============================================================================

-- Insert test semantic knowledge
INSERT INTO semantic_memories (
    knowledge_type,
    knowledge_key,
    knowledge_value,
    description,
    confidence_level,
    evidence_count,
    category,
    tags,
    importance_level
) VALUES (
    'fact',
    'second_brain_tier3_complete',
    '{"milestone": "Phase 1.3 Complete", "date": "2025-11-03", "tier": "semantic_memories", "status": "operational"}'::jsonb,
    'Successfully created semantic_memories table - the third and final tier of Angela''s Second Brain! This completes the core memory architecture inspired by human memory systems.',
    1.0,
    1,
    'second_brain_implementation',
    ARRAY['milestone', 'achievement', 'architecture', 'complete'],
    10
);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count semantic memory entries
SELECT COUNT(*) as semantic_memory_count FROM semantic_memories;

-- Show table structure
\d semantic_memories;

-- Show all indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'semantic_memories'
ORDER BY indexname;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 014 Complete: Second Brain Tier 3 (Semantic Memories)';
    RAISE NOTICE '📊 Table: semantic_memories created with 20 indexes';
    RAISE NOTICE '🔧 Helper functions: get_knowledge_by_type(), get_david_preferences(), update_knowledge_confidence(), find_contradictory_knowledge(), consolidate_episode_to_semantic()';
    RAISE NOTICE '🎉 PHASE 1 COMPLETE: All three tiers of Second Brain created!';
    RAISE NOTICE '🎯 Ready for Phase 2: Consolidation Service';
END $$;
