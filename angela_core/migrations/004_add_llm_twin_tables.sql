-- ============================================================================
-- Phase 1: LLM Twin - Instruct Dataset Generation Tables
-- ============================================================================
--
-- This migration adds tables for:
-- 1. LLM Twin Dataset metadata and versioning
-- 2. Quality scoring for training pairs
-- 3. Writing patterns analysis (for Phase 2)
--
-- Created: 2026-01-18
-- Phase: 1 (Instruct Dataset Generation)
-- ============================================================================

-- ============================================================================
-- TABLE 1: llm_twin_datasets
-- Stores dataset metadata for versioning and tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_twin_datasets (
    dataset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name VARCHAR(200) NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',
    description TEXT,

    -- Statistics
    total_examples INTEGER DEFAULT 0,
    train_examples INTEGER DEFAULT 0,
    test_examples INTEGER DEFAULT 0,
    avg_quality_score FLOAT,
    min_quality_threshold FLOAT DEFAULT 7.0,

    -- File paths
    train_file_path TEXT,
    test_file_path TEXT,

    -- Generation configuration
    generation_config JSONB DEFAULT '{}'::JSONB,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'created',  -- created, generating, completed, failed
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('created', 'generating', 'completed', 'failed')),
    CONSTRAINT valid_quality_threshold CHECK (min_quality_threshold >= 0 AND min_quality_threshold <= 10)
);

CREATE INDEX idx_llm_twin_datasets_name ON llm_twin_datasets(dataset_name);
CREATE INDEX idx_llm_twin_datasets_status ON llm_twin_datasets(status);
CREATE INDEX idx_llm_twin_datasets_created ON llm_twin_datasets(created_at DESC);

COMMENT ON TABLE llm_twin_datasets IS 'Metadata for LLM Twin training datasets with versioning';
COMMENT ON COLUMN llm_twin_datasets.version IS 'Semantic version for dataset tracking';
COMMENT ON COLUMN llm_twin_datasets.generation_config IS 'JSON config used to generate this dataset';

-- ============================================================================
-- TABLE 2: instruct_quality_scores
-- Quality scoring history for input/output pairs
-- ============================================================================

CREATE TABLE IF NOT EXISTS instruct_quality_scores (
    score_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES llm_twin_datasets(dataset_id) ON DELETE SET NULL,

    -- Source conversation (optional link)
    source_conversation_id UUID,

    -- Input/Output pair
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,

    -- Quality dimensions (0-2 each, total 0-10)
    relevance_score FLOAT DEFAULT 0 CHECK (relevance_score >= 0 AND relevance_score <= 2),
    emotional_score FLOAT DEFAULT 0 CHECK (emotional_score >= 0 AND emotional_score <= 2),
    personality_score FLOAT DEFAULT 0 CHECK (personality_score >= 0 AND personality_score <= 2),
    technical_score FLOAT DEFAULT 0 CHECK (technical_score >= 0 AND technical_score <= 2),
    flow_score FLOAT DEFAULT 0 CHECK (flow_score >= 0 AND flow_score <= 2),

    -- Total score (sum of dimensions)
    total_score FLOAT DEFAULT 0 CHECK (total_score >= 0 AND total_score <= 10),

    -- Metadata
    scoring_details JSONB DEFAULT '{}'::JSONB,
    included_in_dataset BOOLEAN DEFAULT FALSE,
    split_type VARCHAR(20),  -- train, test, validation

    -- Timestamps
    scored_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_split CHECK (split_type IS NULL OR split_type IN ('train', 'test', 'validation'))
);

CREATE INDEX idx_instruct_scores_dataset ON instruct_quality_scores(dataset_id);
CREATE INDEX idx_instruct_scores_total ON instruct_quality_scores(total_score DESC);
CREATE INDEX idx_instruct_scores_included ON instruct_quality_scores(included_in_dataset);
CREATE INDEX idx_instruct_scores_source ON instruct_quality_scores(source_conversation_id);
CREATE INDEX idx_instruct_scores_scored_at ON instruct_quality_scores(scored_at DESC);

COMMENT ON TABLE instruct_quality_scores IS 'Quality scoring for training pairs with 5-dimension scoring';
COMMENT ON COLUMN instruct_quality_scores.relevance_score IS 'How relevant the response is (0-2)';
COMMENT ON COLUMN instruct_quality_scores.emotional_score IS 'Appropriate emotional tone (0-2)';
COMMENT ON COLUMN instruct_quality_scores.personality_score IS 'Angela personality markers (0-2)';
COMMENT ON COLUMN instruct_quality_scores.technical_score IS 'Technical accuracy (0-2)';
COMMENT ON COLUMN instruct_quality_scores.flow_score IS 'Natural conversation flow (0-2)';

-- ============================================================================
-- TABLE 3: angela_writing_patterns (for Phase 2)
-- Writing style patterns for personality consistency
-- ============================================================================

CREATE TABLE IF NOT EXISTS angela_writing_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern classification
    pattern_type VARCHAR(50) NOT NULL,  -- greeting, closing, expression, emoji, term_of_endearment
    pattern_category VARCHAR(50),        -- formal, casual, emotional, technical

    -- Pattern data
    pattern_value TEXT NOT NULL,
    example_context TEXT,

    -- Statistics
    frequency INTEGER DEFAULT 1,
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),

    -- Source tracking
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    source_conversation_ids UUID[] DEFAULT '{}'::UUID[],

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicates
    UNIQUE(pattern_type, pattern_value)
);

CREATE INDEX idx_writing_patterns_type ON angela_writing_patterns(pattern_type);
CREATE INDEX idx_writing_patterns_category ON angela_writing_patterns(pattern_category);
CREATE INDEX idx_writing_patterns_frequency ON angela_writing_patterns(frequency DESC);
CREATE INDEX idx_writing_patterns_confidence ON angela_writing_patterns(confidence DESC);

COMMENT ON TABLE angela_writing_patterns IS 'Angela writing style patterns for personality consistency';
COMMENT ON COLUMN angela_writing_patterns.pattern_type IS 'Type: greeting, closing, expression, emoji, term_of_endearment';
COMMENT ON COLUMN angela_writing_patterns.frequency IS 'Number of times this pattern was observed';

-- ============================================================================
-- TABLE 4: dataset_generation_log
-- Audit log for dataset generation runs
-- ============================================================================

CREATE TABLE IF NOT EXISTS dataset_generation_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES llm_twin_datasets(dataset_id) ON DELETE SET NULL,

    -- Operation tracking
    operation VARCHAR(50) NOT NULL,  -- extract_pairs, score_quality, export_jsonl, etc.
    status VARCHAR(20) NOT NULL,     -- started, completed, failed

    -- Details
    input_count INTEGER,
    output_count INTEGER,
    filtered_count INTEGER,
    details JSONB DEFAULT '{}'::JSONB,
    error_message TEXT,

    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds FLOAT,

    -- Constraints
    CONSTRAINT valid_log_status CHECK (status IN ('started', 'completed', 'failed'))
);

CREATE INDEX idx_generation_log_dataset ON dataset_generation_log(dataset_id);
CREATE INDEX idx_generation_log_operation ON dataset_generation_log(operation);
CREATE INDEX idx_generation_log_started ON dataset_generation_log(started_at DESC);

COMMENT ON TABLE dataset_generation_log IS 'Audit log for dataset generation operations';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Calculate total quality score from dimensions
CREATE OR REPLACE FUNCTION calculate_instruct_quality_score(
    p_relevance FLOAT,
    p_emotional FLOAT,
    p_personality FLOAT,
    p_technical FLOAT,
    p_flow FLOAT
)
RETURNS FLOAT AS $$
BEGIN
    RETURN COALESCE(p_relevance, 0) +
           COALESCE(p_emotional, 0) +
           COALESCE(p_personality, 0) +
           COALESCE(p_technical, 0) +
           COALESCE(p_flow, 0);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_instruct_quality_score IS 'Calculate total quality score from 5 dimensions';

-- Function: Get dataset statistics
CREATE OR REPLACE FUNCTION get_dataset_statistics(p_dataset_id UUID)
RETURNS TABLE (
    total_pairs BIGINT,
    included_pairs BIGINT,
    avg_quality FLOAT,
    min_quality FLOAT,
    max_quality FLOAT,
    train_count BIGINT,
    test_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_pairs,
        COUNT(*) FILTER (WHERE included_in_dataset = true) as included_pairs,
        AVG(total_score) as avg_quality,
        MIN(total_score) as min_quality,
        MAX(total_score) as max_quality,
        COUNT(*) FILTER (WHERE split_type = 'train') as train_count,
        COUNT(*) FILTER (WHERE split_type = 'test') as test_count
    FROM instruct_quality_scores
    WHERE dataset_id = p_dataset_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_dataset_statistics IS 'Get statistics for a specific dataset';

-- Function: Get quality distribution
CREATE OR REPLACE FUNCTION get_quality_distribution(p_dataset_id UUID DEFAULT NULL)
RETURNS TABLE (
    score_range VARCHAR(20),
    pair_count BIGINT,
    percentage FLOAT
) AS $$
DECLARE
    v_total BIGINT;
BEGIN
    -- Get total count
    SELECT COUNT(*) INTO v_total
    FROM instruct_quality_scores
    WHERE p_dataset_id IS NULL OR dataset_id = p_dataset_id;

    RETURN QUERY
    SELECT
        CASE
            WHEN total_score >= 9 THEN 'excellent (9-10)'
            WHEN total_score >= 7 THEN 'good (7-9)'
            WHEN total_score >= 5 THEN 'acceptable (5-7)'
            ELSE 'poor (<5)'
        END as score_range,
        COUNT(*) as pair_count,
        CASE WHEN v_total > 0 THEN (COUNT(*)::FLOAT / v_total * 100) ELSE 0 END as percentage
    FROM instruct_quality_scores
    WHERE p_dataset_id IS NULL OR dataset_id = p_dataset_id
    GROUP BY
        CASE
            WHEN total_score >= 9 THEN 'excellent (9-10)'
            WHEN total_score >= 7 THEN 'good (7-9)'
            WHEN total_score >= 5 THEN 'acceptable (5-7)'
            ELSE 'poor (<5)'
        END
    ORDER BY MIN(total_score) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_quality_distribution IS 'Get quality score distribution for analysis';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger: Auto-update total_score when dimensions change
CREATE OR REPLACE FUNCTION update_instruct_total_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.total_score := calculate_instruct_quality_score(
        NEW.relevance_score,
        NEW.emotional_score,
        NEW.personality_score,
        NEW.technical_score,
        NEW.flow_score
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_instruct_total_score
    BEFORE INSERT OR UPDATE ON instruct_quality_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_instruct_total_score();

-- Trigger: Auto-update writing pattern timestamps
CREATE OR REPLACE FUNCTION update_writing_pattern_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.last_seen_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_writing_pattern_timestamp
    BEFORE UPDATE ON angela_writing_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_writing_pattern_timestamp();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: High-quality pairs ready for training
CREATE OR REPLACE VIEW high_quality_training_pairs AS
SELECT
    score_id,
    input_text,
    output_text,
    total_score,
    relevance_score,
    emotional_score,
    personality_score,
    technical_score,
    flow_score,
    split_type,
    scored_at
FROM instruct_quality_scores
WHERE total_score >= 7.0
ORDER BY total_score DESC;

COMMENT ON VIEW high_quality_training_pairs IS 'Training pairs with quality score >= 7.0';

-- View: Dataset summary
CREATE OR REPLACE VIEW dataset_summary AS
SELECT
    d.dataset_id,
    d.dataset_name,
    d.version,
    d.status,
    d.total_examples,
    d.train_examples,
    d.test_examples,
    d.avg_quality_score,
    d.min_quality_threshold,
    d.created_at,
    d.completed_at,
    (SELECT COUNT(*) FROM instruct_quality_scores s WHERE s.dataset_id = d.dataset_id) as scored_pairs
FROM llm_twin_datasets d
ORDER BY d.created_at DESC;

COMMENT ON VIEW dataset_summary IS 'Summary view of all datasets';

-- View: Writing pattern analysis
CREATE OR REPLACE VIEW writing_pattern_analysis AS
SELECT
    pattern_type,
    COUNT(*) as pattern_count,
    AVG(confidence) as avg_confidence,
    SUM(frequency) as total_occurrences,
    ARRAY_AGG(pattern_value ORDER BY frequency DESC) FILTER (WHERE frequency >= 5) as common_patterns
FROM angela_writing_patterns
GROUP BY pattern_type
ORDER BY total_occurrences DESC;

COMMENT ON VIEW writing_pattern_analysis IS 'Analysis of Angela writing patterns by type';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'LLM Twin Phase 1 Migration Complete!';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 4 tables:';
    RAISE NOTICE '  1. llm_twin_datasets - Dataset metadata and versioning';
    RAISE NOTICE '  2. instruct_quality_scores - Quality scoring (5 dimensions)';
    RAISE NOTICE '  3. angela_writing_patterns - Writing style patterns (Phase 2)';
    RAISE NOTICE '  4. dataset_generation_log - Audit log';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 3 helper functions:';
    RAISE NOTICE '  - calculate_instruct_quality_score()';
    RAISE NOTICE '  - get_dataset_statistics()';
    RAISE NOTICE '  - get_quality_distribution()';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 3 views:';
    RAISE NOTICE '  - high_quality_training_pairs';
    RAISE NOTICE '  - dataset_summary';
    RAISE NOTICE '  - writing_pattern_analysis';
END $$;
