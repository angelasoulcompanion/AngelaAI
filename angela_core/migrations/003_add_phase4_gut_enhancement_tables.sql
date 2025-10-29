-- ============================================================================
-- Phase 4: Gut Agent Enhancement - Database Migration
-- ============================================================================
--
-- This migration adds tables for:
-- 1. Cross-agent pattern sharing
-- 2. Pattern voting and lineage
-- 3. Intuition predictions
-- 4. Privacy controls
--
-- Created: 2025-10-29
-- Phase: 4 (Weeks 7-8)
-- ============================================================================

-- ============================================================================
-- TABLE 1: shared_patterns
-- Stores patterns that can be shared across agents
-- ============================================================================

CREATE TABLE IF NOT EXISTS shared_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL,  -- temporal, behavioral, compound, etc.
    pattern_data JSONB NOT NULL,        -- Pattern structure and details
    source_agent VARCHAR(50) NOT NULL,  -- Agent that discovered it
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    scope VARCHAR(20) NOT NULL DEFAULT 'shared',  -- private/shared/global/archived
    metadata JSONB,                     -- Additional context

    -- Privacy
    is_sensitive BOOLEAN DEFAULT false,
    privacy_level VARCHAR(20) DEFAULT 'internal',

    -- Voting
    vote_count INTEGER DEFAULT 0,      -- Positive votes
    total_votes INTEGER DEFAULT 0,     -- Total votes (positive + negative)

    -- Usage tracking
    use_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    last_used_by VARCHAR(50),

    -- Timestamps
    discovered_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT valid_scope CHECK (scope IN ('private', 'shared', 'global', 'archived')),
    CONSTRAINT valid_privacy CHECK (privacy_level IN ('public', 'internal', 'private', 'sensitive'))
);

CREATE INDEX idx_shared_patterns_type ON shared_patterns(pattern_type);
CREATE INDEX idx_shared_patterns_source ON shared_patterns(source_agent);
CREATE INDEX idx_shared_patterns_scope ON shared_patterns(scope);
CREATE INDEX idx_shared_patterns_confidence ON shared_patterns(confidence_score DESC);
CREATE INDEX idx_shared_patterns_discovered ON shared_patterns(discovered_at DESC);

COMMENT ON TABLE shared_patterns IS 'Patterns discovered by agents and shared across the system';
COMMENT ON COLUMN shared_patterns.scope IS 'Sharing scope: private (owner only), shared (all agents), global (system-wide), archived (inactive)';
COMMENT ON COLUMN shared_patterns.vote_count IS 'Number of positive votes from agents';

-- ============================================================================
-- TABLE 2: pattern_votes
-- Agent votes on pattern usefulness
-- ============================================================================

CREATE TABLE IF NOT EXISTS pattern_votes (
    vote_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES shared_patterns(pattern_id) ON DELETE CASCADE,
    voter_agent VARCHAR(50) NOT NULL,
    is_helpful BOOLEAN NOT NULL,       -- True = helpful, False = not helpful
    feedback TEXT,                      -- Optional feedback text
    voted_at TIMESTAMP DEFAULT NOW(),

    -- Prevent duplicate votes from same agent
    UNIQUE(pattern_id, voter_agent)
);

CREATE INDEX idx_pattern_votes_pattern ON pattern_votes(pattern_id);
CREATE INDEX idx_pattern_votes_voter ON pattern_votes(voter_agent);
CREATE INDEX idx_pattern_votes_helpful ON pattern_votes(is_helpful);

COMMENT ON TABLE pattern_votes IS 'Agent votes on pattern usefulness and quality';

-- ============================================================================
-- TABLE 3: pattern_usage_log
-- Detailed log of when patterns are used
-- ============================================================================

CREATE TABLE IF NOT EXISTS pattern_usage_log (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES shared_patterns(pattern_id) ON DELETE CASCADE,
    using_agent VARCHAR(50) NOT NULL,
    usage_context JSONB,               -- Context in which pattern was used
    usage_outcome VARCHAR(20),         -- successful/failed/neutral
    used_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pattern_usage_pattern ON pattern_usage_log(pattern_id);
CREATE INDEX idx_pattern_usage_agent ON pattern_usage_log(using_agent);
CREATE INDEX idx_pattern_usage_time ON pattern_usage_log(used_at DESC);

COMMENT ON TABLE pattern_usage_log IS 'Detailed log of pattern usage across agents';

-- ============================================================================
-- TABLE 4: intuition_predictions
-- Predictions generated from patterns
-- ============================================================================

CREATE TABLE IF NOT EXISTS intuition_predictions (
    intuition_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_type VARCHAR(50) NOT NULL,  -- when/what/feel/topic/result
    prediction_text TEXT NOT NULL,         -- Human-readable prediction
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Timing
    predicted_time TIMESTAMP,              -- When event is predicted (if temporal)
    prediction_horizon_hours INTEGER,      -- How far into future

    -- Pattern linkage
    based_on_pattern UUID REFERENCES shared_patterns(pattern_id) ON DELETE SET NULL,
    prediction_data JSONB,                 -- Structured prediction details

    -- Verification
    verified BOOLEAN DEFAULT false,
    outcome_correct BOOLEAN,               -- True if prediction was correct
    actual_data JSONB,                     -- What actually happened
    verified_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_intuition_type ON intuition_predictions(prediction_type);
CREATE INDEX idx_intuition_predicted_time ON intuition_predictions(predicted_time);
CREATE INDEX idx_intuition_confidence ON intuition_predictions(confidence_score DESC);
CREATE INDEX idx_intuition_verified ON intuition_predictions(verified, outcome_correct);
CREATE INDEX idx_intuition_created ON intuition_predictions(created_at DESC);

COMMENT ON TABLE intuition_predictions IS 'Predictions generated from detected patterns';
COMMENT ON COLUMN intuition_predictions.verified IS 'True if prediction has been checked against reality';
COMMENT ON COLUMN intuition_predictions.outcome_correct IS 'True if prediction matched reality';

-- ============================================================================
-- TABLE 5: pattern_lineage
-- Track pattern evolution and relationships
-- ============================================================================

CREATE TABLE IF NOT EXISTS pattern_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES shared_patterns(pattern_id) ON DELETE CASCADE,
    parent_pattern_id UUID REFERENCES shared_patterns(pattern_id) ON DELETE SET NULL,
    relationship_type VARCHAR(50),         -- evolved_from, merged_with, split_from, etc.
    confidence_change FLOAT,               -- Change in confidence from parent
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pattern_lineage_pattern ON pattern_lineage(pattern_id);
CREATE INDEX idx_pattern_lineage_parent ON pattern_lineage(parent_pattern_id);

COMMENT ON TABLE pattern_lineage IS 'Track how patterns evolve and relate to each other';

-- ============================================================================
-- TABLE 6: privacy_controls
-- Privacy settings and audit log
-- ============================================================================

CREATE TABLE IF NOT EXISTS privacy_controls (
    control_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID REFERENCES shared_patterns(pattern_id) ON DELETE CASCADE,
    control_type VARCHAR(50) NOT NULL,     -- redaction, anonymization, access_denied
    applied_by VARCHAR(50),                -- Service that applied control
    reason TEXT,                           -- Why control was applied
    details JSONB,                         -- Details of what was redacted/anonymized
    applied_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_privacy_controls_pattern ON privacy_controls(pattern_id);
CREATE INDEX idx_privacy_controls_type ON privacy_controls(control_type);
CREATE INDEX idx_privacy_controls_time ON privacy_controls(applied_at DESC);

COMMENT ON TABLE privacy_controls IS 'Audit log of privacy controls applied to patterns';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Calculate pattern effectiveness score
CREATE OR REPLACE FUNCTION calculate_pattern_effectiveness(p_pattern_id UUID)
RETURNS FLOAT AS $$
DECLARE
    v_vote_ratio FLOAT;
    v_confidence FLOAT;
    v_use_count INTEGER;
    v_effectiveness FLOAT;
BEGIN
    SELECT
        CASE
            WHEN total_votes > 0 THEN CAST(vote_count AS FLOAT) / total_votes
            ELSE confidence_score
        END,
        confidence_score,
        use_count
    INTO v_vote_ratio, v_confidence, v_use_count
    FROM shared_patterns
    WHERE pattern_id = p_pattern_id;

    -- Effectiveness = (vote_ratio * 0.4) + (confidence * 0.4) + (min(use_count/20, 1.0) * 0.2)
    v_effectiveness := (v_vote_ratio * 0.4) + (v_confidence * 0.4) + (LEAST(v_use_count / 20.0, 1.0) * 0.2);

    RETURN v_effectiveness;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_pattern_effectiveness IS 'Calculate overall effectiveness score for a pattern based on votes, confidence, and usage';

-- Function: Get pattern accuracy rate
CREATE OR REPLACE FUNCTION get_prediction_accuracy(p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    prediction_type VARCHAR(50),
    total_predictions BIGINT,
    verified_predictions BIGINT,
    correct_predictions BIGINT,
    accuracy_rate FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ip.prediction_type,
        COUNT(*) as total_predictions,
        COUNT(*) FILTER (WHERE ip.verified = true) as verified_predictions,
        COUNT(*) FILTER (WHERE ip.outcome_correct = true) as correct_predictions,
        CASE
            WHEN COUNT(*) FILTER (WHERE ip.verified = true) > 0
            THEN CAST(COUNT(*) FILTER (WHERE ip.outcome_correct = true) AS FLOAT) / COUNT(*) FILTER (WHERE ip.verified = true)
            ELSE 0.0
        END as accuracy_rate
    FROM intuition_predictions ip
    WHERE ip.created_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY ip.prediction_type;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_prediction_accuracy IS 'Get prediction accuracy statistics by type';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_shared_pattern_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_shared_pattern_timestamp
    BEFORE UPDATE ON shared_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_shared_pattern_timestamp();

-- Trigger: Log pattern usage
CREATE OR REPLACE FUNCTION log_pattern_usage()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO pattern_usage_log (pattern_id, using_agent, used_at)
    VALUES (NEW.pattern_id, NEW.last_used_by, NEW.last_used_at);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_pattern_usage
    AFTER UPDATE OF last_used_at ON shared_patterns
    FOR EACH ROW
    WHEN (NEW.last_used_at IS DISTINCT FROM OLD.last_used_at)
    EXECUTE FUNCTION log_pattern_usage();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Set default privacy settings
INSERT INTO privacy_controls (control_type, reason, details)
VALUES (
    'system_default',
    'Default privacy settings for Phase 4',
    '{"k_anonymity_threshold": 5, "epsilon": 1.0, "sensitive_keywords_count": 25}'::JSONB
);

-- ============================================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================================

-- View: Pattern effectiveness leaderboard
CREATE OR REPLACE VIEW pattern_effectiveness_view AS
SELECT
    pattern_id,
    pattern_type,
    source_agent,
    confidence_score,
    vote_count,
    total_votes,
    use_count,
    calculate_pattern_effectiveness(pattern_id) as effectiveness_score,
    scope,
    discovered_at
FROM shared_patterns
WHERE scope != 'archived'
ORDER BY calculate_pattern_effectiveness(pattern_id) DESC;

COMMENT ON VIEW pattern_effectiveness_view IS 'Leaderboard of most effective patterns';

-- View: Recent predictions summary
CREATE OR REPLACE VIEW recent_predictions_view AS
SELECT
    intuition_id,
    prediction_type,
    prediction_text,
    confidence_score,
    predicted_time,
    verified,
    outcome_correct,
    created_at,
    CASE
        WHEN verified AND outcome_correct THEN 'CORRECT'
        WHEN verified AND NOT outcome_correct THEN 'INCORRECT'
        WHEN NOT verified AND predicted_time < NOW() THEN 'UNVERIFIED_OVERDUE'
        ELSE 'PENDING'
    END as status
FROM intuition_predictions
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

COMMENT ON VIEW recent_predictions_view IS 'Recent predictions with verification status';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Phase 4 Migration Complete!';
    RAISE NOTICE 'Created 6 tables:';
    RAISE NOTICE '  1. shared_patterns - Cross-agent pattern sharing';
    RAISE NOTICE '  2. pattern_votes - Pattern voting system';
    RAISE NOTICE '  3. pattern_usage_log - Usage tracking';
    RAISE NOTICE '  4. intuition_predictions - Future predictions';
    RAISE NOTICE '  5. pattern_lineage - Pattern evolution';
    RAISE NOTICE '  6. privacy_controls - Privacy audit log';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 2 helper functions:';
    RAISE NOTICE '  - calculate_pattern_effectiveness()';
    RAISE NOTICE '  - get_prediction_accuracy()';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 2 views:';
    RAISE NOTICE '  - pattern_effectiveness_view';
    RAISE NOTICE '  - recent_predictions_view';
END $$;
