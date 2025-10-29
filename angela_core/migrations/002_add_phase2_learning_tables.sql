-- Migration 002: Add Phase 2 Learning & Feedback Tables
-- Phase 2: Analytics Enhancement - Learning from feedback
-- Created: 2025-10-29

-- ============================================================================
-- 1. ROUTING CORRECTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS routing_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to original decision
    decision_id UUID REFERENCES analytics_decisions(id),

    -- What happened
    wrong_tier VARCHAR(20) NOT NULL,
    correct_tier VARCHAR(20) NOT NULL,

    -- Signals at the time
    signals JSONB NOT NULL,

    -- When discovered
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_routing_corrections_tiers ON routing_corrections(wrong_tier, correct_tier);
CREATE INDEX idx_routing_corrections_created ON routing_corrections(created_at DESC);

COMMENT ON TABLE routing_corrections IS 'Log of incorrect routing decisions for learning';
COMMENT ON COLUMN routing_corrections.wrong_tier IS 'Where it was incorrectly routed';
COMMENT ON COLUMN routing_corrections.correct_tier IS 'Where it should have gone';

-- ============================================================================
-- 2. WEIGHT OPTIMIZATION HISTORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS weight_optimization_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Optimized weights
    weights JSONB NOT NULL,

    -- Performance improvement
    improvement FLOAT NOT NULL,

    -- Metrics
    avg_error_before FLOAT,
    avg_error_after FLOAT,
    feedback_count INTEGER DEFAULT 0,

    -- When optimized
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_weight_history_created ON weight_optimization_history(created_at DESC);
CREATE INDEX idx_weight_history_improvement ON weight_optimization_history(improvement DESC);

COMMENT ON TABLE weight_optimization_history IS 'History of weight optimization runs';
COMMENT ON COLUMN weight_optimization_history.improvement IS 'Improvement in error reduction';

-- ============================================================================
-- 3. CURRENT WEIGHTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS current_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Signal name (use 'current' for active weights)
    signal_name VARCHAR(50) UNIQUE NOT NULL,

    -- Weight value (JSONB for all signals, or FLOAT for individual)
    weight JSONB,

    -- When last updated
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Insert default weights
INSERT INTO current_weights (signal_name, weight, updated_at)
VALUES ('current', '{"success_score": 0.35, "repetition_signal": 0.25, "criticality": 0.20, "pattern_novelty": 0.15, "context_richness": 0.05}', NOW())
ON CONFLICT (signal_name) DO NOTHING;

COMMENT ON TABLE current_weights IS 'Current active signal weights';
COMMENT ON COLUMN current_weights.weight IS 'JSONB containing all signal weights';

-- ============================================================================
-- 4. LEARNING EVENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event type
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('weight_optimization', 'pattern_discovered', 'accuracy_improvement', 'mistake_identified')),

    -- What was learned
    learning_description TEXT NOT NULL,

    -- Related data
    metadata JSONB DEFAULT '{}',

    -- Performance impact
    impact_score FLOAT CHECK (impact_score >= 0.0 AND impact_score <= 1.0),

    -- When learned
    learned_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_learning_events_type ON learning_events(event_type, learned_at DESC);
CREATE INDEX idx_learning_events_impact ON learning_events(impact_score DESC);

COMMENT ON TABLE learning_events IS 'Log of system learning events';
COMMENT ON COLUMN learning_events.impact_score IS 'How much this learning improved the system';

-- ============================================================================
-- 5. ACCURACY METRICS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS accuracy_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Date
    date DATE NOT NULL DEFAULT CURRENT_DATE UNIQUE,

    -- Overall accuracy
    overall_accuracy FLOAT CHECK (overall_accuracy >= 0.0 AND overall_accuracy <= 1.0),

    -- Tier-specific accuracy
    shock_accuracy FLOAT,
    longterm_accuracy FLOAT,
    procedural_accuracy FLOAT,

    -- Confidence calibration
    high_confidence_accuracy FLOAT,
    low_confidence_accuracy FLOAT,

    -- Volume metrics
    total_decisions INTEGER DEFAULT 0,
    feedback_received INTEGER DEFAULT 0,
    feedback_rate FLOAT,

    -- Trend
    trend VARCHAR(20) CHECK (trend IN ('improving', 'stable', 'declining', 'insufficient_data')),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_accuracy_metrics_date ON accuracy_metrics(date DESC);

COMMENT ON TABLE accuracy_metrics IS 'Daily accuracy metrics for monitoring';
COMMENT ON COLUMN accuracy_metrics.feedback_rate IS 'Percentage of decisions that received feedback';

-- ============================================================================
-- 6. A/B TEST EXPERIMENTS TABLE (for future use)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ab_test_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Experiment details
    experiment_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Variant A (control) weights
    variant_a_weights JSONB NOT NULL,

    -- Variant B (test) weights
    variant_b_weights JSONB NOT NULL,

    -- Results
    variant_a_accuracy FLOAT,
    variant_b_accuracy FLOAT,
    winner VARCHAR(10) CHECK (winner IN ('A', 'B', 'tie', 'inconclusive')),

    -- Status
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('planning', 'running', 'completed', 'abandoned')),

    -- Timing
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ab_experiments_status ON ab_test_experiments(status, created_at DESC);

COMMENT ON TABLE ab_test_experiments IS 'A/B testing experiments for weight optimization';

-- ============================================================================
-- 7. SIGNAL CORRELATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS signal_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Signals being compared
    signal_a VARCHAR(50) NOT NULL,
    signal_b VARCHAR(50) NOT NULL,

    -- Correlation coefficient (-1.0 to 1.0)
    correlation FLOAT CHECK (correlation >= -1.0 AND correlation <= 1.0),

    -- Sample size
    sample_count INTEGER DEFAULT 0,

    -- When calculated
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(signal_a, signal_b)
);

CREATE INDEX idx_signal_correlations ON signal_correlations(correlation DESC);

COMMENT ON TABLE signal_correlations IS 'Correlation between different signals';
COMMENT ON COLUMN signal_correlations.correlation IS 'Pearson correlation coefficient';

-- ============================================================================
-- 8. HELPER FUNCTIONS
-- ============================================================================

-- Function to get current weights
CREATE OR REPLACE FUNCTION get_current_weights()
RETURNS JSONB AS $$
DECLARE
    weights JSONB;
BEGIN
    SELECT weight INTO weights
    FROM current_weights
    WHERE signal_name = 'current';

    RETURN weights;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_current_weights IS 'Get currently active signal weights';

-- Function to calculate routing accuracy for a date range
CREATE OR REPLACE FUNCTION calculate_accuracy(days_back INTEGER DEFAULT 30)
RETURNS FLOAT AS $$
DECLARE
    accuracy FLOAT;
BEGIN
    SELECT AVG(feedback_score) INTO accuracy
    FROM analytics_decisions
    WHERE feedback_score IS NOT NULL
      AND created_at >= NOW() - INTERVAL '1 day' * days_back;

    RETURN COALESCE(accuracy, 0.0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_accuracy IS 'Calculate average routing accuracy for past N days';

-- ============================================================================
-- 9. TRIGGERS
-- ============================================================================

-- Auto-update accuracy metrics when feedback is received
CREATE OR REPLACE FUNCTION update_daily_accuracy()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO accuracy_metrics (date, overall_accuracy, feedback_received, updated_at)
    VALUES (
        CURRENT_DATE,
        (SELECT AVG(feedback_score) FROM analytics_decisions
         WHERE feedback_score IS NOT NULL
           AND DATE(created_at) = CURRENT_DATE),
        (SELECT COUNT(*) FROM analytics_decisions
         WHERE feedback_score IS NOT NULL
           AND DATE(created_at) = CURRENT_DATE),
        NOW()
    )
    ON CONFLICT (date) DO UPDATE SET
        overall_accuracy = EXCLUDED.overall_accuracy,
        feedback_received = EXCLUDED.feedback_received,
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_accuracy
AFTER UPDATE OF feedback_score ON analytics_decisions
FOR EACH ROW
WHEN (OLD.feedback_score IS NULL AND NEW.feedback_score IS NOT NULL)
EXECUTE FUNCTION update_daily_accuracy();

-- ============================================================================
-- 10. INITIAL DATA
-- ============================================================================

-- Log initial learning event
INSERT INTO learning_events (event_type, learning_description, impact_score, learned_at)
VALUES (
    'pattern_discovered',
    'Phase 2 Analytics Enhancement initialized - Learning system active',
    0.0,
    NOW()
);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 002 completed: Phase 2 Learning & Feedback tables created';
    RAISE NOTICE 'Tables added: routing_corrections, weight_optimization_history, current_weights, learning_events, accuracy_metrics, ab_test_experiments, signal_correlations';
    RAISE NOTICE 'Functions added: get_current_weights(), calculate_accuracy()';
    RAISE NOTICE 'Triggers added: trigger_update_accuracy';
    RAISE NOTICE 'Phase 2 (Analytics Enhancement) ready for implementation';
END $$;
