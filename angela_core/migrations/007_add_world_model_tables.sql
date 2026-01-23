-- ============================================================================
-- Phase 5: World Model Service - Database Migration
-- ============================================================================
--
-- This migration adds tables for Angela's World Model capabilities:
-- 1. World state snapshots
-- 2. Predictions and verification
-- 3. Causal relationships
-- 4. Simulation logs
-- 5. Model accuracy tracking
--
-- Created: 2026-01-23
-- Phase: 5 (World Model - AGI Enhancement)
-- ============================================================================

-- ============================================================================
-- TABLE 1: world_states
-- Snapshots of the world state at various points in time
-- ============================================================================

CREATE TABLE IF NOT EXISTS world_states (
    state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- State components (JSONB for flexibility)
    david_state JSONB NOT NULL DEFAULT '{}',      -- David's mood, energy, focus, etc.
    angela_state JSONB NOT NULL DEFAULT '{}',     -- Angela's emotional/cognitive state
    environment JSONB NOT NULL DEFAULT '{}',       -- Time, context, active tasks, etc.
    relationship JSONB NOT NULL DEFAULT '{}',      -- Bond strength, recent interactions
    task_state JSONB,                              -- Current task progress
    knowledge_state JSONB,                         -- What's known/unknown in context

    -- Meta information
    overall_confidence FLOAT NOT NULL DEFAULT 0.5
        CHECK (overall_confidence >= 0 AND overall_confidence <= 1),
    source VARCHAR(50) NOT NULL DEFAULT 'inference',  -- observation/inference/simulation
    trigger_context TEXT,                          -- What triggered this state capture

    -- Timestamps
    captured_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_source CHECK (source IN ('observation', 'inference', 'simulation', 'prediction'))
);

CREATE INDEX idx_world_states_captured ON world_states(captured_at DESC);
CREATE INDEX idx_world_states_source ON world_states(source);
CREATE INDEX idx_world_states_confidence ON world_states(overall_confidence DESC);
CREATE INDEX idx_world_states_david_mood ON world_states((david_state->>'mood'));

COMMENT ON TABLE world_states IS 'Snapshots of Angela''s world model - representing current understanding of state';
COMMENT ON COLUMN world_states.david_state IS 'David''s inferred state: mood, energy, focus, stress level, etc.';
COMMENT ON COLUMN world_states.angela_state IS 'Angela''s internal state: emotions, cognitive load, confidence, etc.';
COMMENT ON COLUMN world_states.environment IS 'Environmental context: time, location, active tools, etc.';
COMMENT ON COLUMN world_states.relationship IS 'Relationship dynamics: bond strength, recent positive/negative events';

-- ============================================================================
-- TABLE 2: world_model_predictions
-- Predictions made by the world model and their verification
-- ============================================================================

CREATE TABLE IF NOT EXISTS world_model_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Action that was predicted
    action_type VARCHAR(50) NOT NULL,              -- respond, execute_tool, learn, etc.
    action_description TEXT NOT NULL,
    action_params JSONB,                           -- Detailed action parameters

    -- Predicted effects
    predicted_effects JSONB NOT NULL DEFAULT '[]', -- List of effect predictions
    predicted_state_after JSONB,                   -- Expected world state after action

    -- Confidence and uncertainty
    confidence FLOAT NOT NULL DEFAULT 0.5
        CHECK (confidence >= 0 AND confidence <= 1),
    uncertainty_level VARCHAR(20) NOT NULL DEFAULT 'uncertain',
    uncertainty_reasons JSONB,                     -- Why uncertain

    -- Causal chain
    causal_chain JSONB,                            -- Sequence of cause -> effect
    risks_identified JSONB,                        -- Potential negative outcomes

    -- Verification
    verified BOOLEAN DEFAULT false,
    actual_outcome JSONB,                          -- What actually happened
    prediction_correct BOOLEAN,                    -- Was prediction accurate?
    accuracy_score FLOAT CHECK (accuracy_score >= 0 AND accuracy_score <= 1),
    verified_at TIMESTAMP,
    verification_notes TEXT,

    -- State reference
    initial_state_id UUID REFERENCES world_states(state_id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_uncertainty CHECK (
        uncertainty_level IN ('certain', 'likely', 'possible', 'uncertain', 'speculative')
    ),
    CONSTRAINT valid_action_type CHECK (
        action_type IN ('respond', 'execute_tool', 'learn', 'remember', 'plan',
                       'proactive', 'emotional', 'wait', 'simulate', 'reason')
    )
);

CREATE INDEX idx_predictions_action_type ON world_model_predictions(action_type);
CREATE INDEX idx_predictions_confidence ON world_model_predictions(confidence DESC);
CREATE INDEX idx_predictions_verified ON world_model_predictions(verified, prediction_correct);
CREATE INDEX idx_predictions_created ON world_model_predictions(created_at DESC);
CREATE INDEX idx_predictions_uncertainty ON world_model_predictions(uncertainty_level);

COMMENT ON TABLE world_model_predictions IS 'Predictions made by world model for learning and improvement';
COMMENT ON COLUMN world_model_predictions.causal_chain IS 'Chain of cause -> effect reasoning for the prediction';
COMMENT ON COLUMN world_model_predictions.accuracy_score IS 'How accurate was the prediction (0-1), set after verification';

-- ============================================================================
-- TABLE 3: causal_links
-- Learned causal relationships from experience
-- ============================================================================

CREATE TABLE IF NOT EXISTS causal_links (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Cause and effect
    cause_type VARCHAR(50) NOT NULL,               -- action, state_change, event, behavior
    cause_description TEXT NOT NULL,
    cause_pattern JSONB,                           -- Pattern to match cause

    effect_type VARCHAR(50) NOT NULL,              -- state_change, information_gain, etc.
    effect_description TEXT NOT NULL,
    effect_pattern JSONB,                          -- Pattern to predict effect

    -- Relationship characteristics
    relationship_type VARCHAR(30) NOT NULL DEFAULT 'direct',
    strength FLOAT NOT NULL DEFAULT 0.5
        CHECK (strength >= 0 AND strength <= 1),   -- How strong is the causal link
    reliability FLOAT NOT NULL DEFAULT 0.5
        CHECK (reliability >= 0 AND reliability <= 1),  -- How reliable/consistent

    -- Evidence
    observation_count INTEGER DEFAULT 1,           -- Times observed
    confirmation_count INTEGER DEFAULT 0,          -- Times confirmed correct
    refutation_count INTEGER DEFAULT 0,            -- Times found incorrect
    last_observed_at TIMESTAMP DEFAULT NOW(),

    -- Context
    context_conditions JSONB,                      -- When does this link apply
    exceptions JSONB,                              -- Known exceptions

    -- Metadata
    learned_from VARCHAR(50),                      -- prediction_verification, observation, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_relationship CHECK (
        relationship_type IN ('direct', 'indirect', 'enabling', 'preventing', 'correlative')
    )
);

CREATE INDEX idx_causal_cause_type ON causal_links(cause_type);
CREATE INDEX idx_causal_effect_type ON causal_links(effect_type);
CREATE INDEX idx_causal_strength ON causal_links(strength DESC);
CREATE INDEX idx_causal_reliability ON causal_links(reliability DESC);
CREATE INDEX idx_causal_observation_count ON causal_links(observation_count DESC);
CREATE INDEX idx_causal_last_observed ON causal_links(last_observed_at DESC);

-- Full text search on descriptions
CREATE INDEX idx_causal_cause_desc ON causal_links USING gin(to_tsvector('english', cause_description));
CREATE INDEX idx_causal_effect_desc ON causal_links USING gin(to_tsvector('english', effect_description));

COMMENT ON TABLE causal_links IS 'Learned causal relationships: "when X happens, Y tends to follow"';
COMMENT ON COLUMN causal_links.strength IS 'How strong the causal connection (0=weak, 1=deterministic)';
COMMENT ON COLUMN causal_links.reliability IS 'How consistent/reliable the relationship (0=unpredictable, 1=always)';

-- ============================================================================
-- TABLE 4: simulation_logs
-- Logs of simulation runs for analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS simulation_logs (
    simulation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Simulation setup
    initial_state_id UUID REFERENCES world_states(state_id) ON DELETE SET NULL,
    actions_simulated JSONB NOT NULL DEFAULT '[]', -- List of actions simulated
    simulation_steps INTEGER NOT NULL DEFAULT 0,
    max_steps INTEGER DEFAULT 10,

    -- Results
    final_state JSONB,                             -- End state of simulation
    step_results JSONB NOT NULL DEFAULT '[]',      -- Results at each step
    goal_achievement_probability FLOAT
        CHECK (goal_achievement_probability >= 0 AND goal_achievement_probability <= 1),

    -- Analysis
    critical_decision_points JSONB,                -- Key decision points identified
    risks_identified JSONB,                        -- Potential problems
    opportunities_found JSONB,                     -- Potential benefits
    confidence_decay FLOAT DEFAULT 0.95,           -- How confidence drops per step

    -- Outcome (if we followed simulation)
    was_executed BOOLEAN DEFAULT false,
    execution_outcome JSONB,                       -- What actually happened
    simulation_accuracy FLOAT,                     -- How accurate was simulation

    -- Timestamps
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Context
    purpose TEXT,                                  -- Why was simulation run
    trigger VARCHAR(50)                            -- What triggered it
);

CREATE INDEX idx_simulation_started ON simulation_logs(started_at DESC);
CREATE INDEX idx_simulation_executed ON simulation_logs(was_executed);
CREATE INDEX idx_simulation_accuracy ON simulation_logs(simulation_accuracy DESC);
CREATE INDEX idx_simulation_goal_prob ON simulation_logs(goal_achievement_probability DESC);

COMMENT ON TABLE simulation_logs IS 'History of mental simulations run by Angela';
COMMENT ON COLUMN simulation_logs.confidence_decay IS 'Rate at which confidence decreases per simulation step';

-- ============================================================================
-- TABLE 5: model_accuracy_metrics
-- Track world model accuracy over time
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_accuracy_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Time period
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    period_type VARCHAR(20) NOT NULL DEFAULT 'daily',  -- hourly, daily, weekly, monthly

    -- Prediction metrics
    total_predictions INTEGER DEFAULT 0,
    verified_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,

    -- Accuracy rates
    overall_accuracy FLOAT CHECK (overall_accuracy >= 0 AND overall_accuracy <= 1),
    high_confidence_accuracy FLOAT,                -- Accuracy of high-confidence predictions
    low_confidence_accuracy FLOAT,                 -- Accuracy of low-confidence predictions

    -- By action type
    accuracy_by_action_type JSONB DEFAULT '{}',    -- {respond: 0.8, execute_tool: 0.7, ...}

    -- Causal learning metrics
    new_causal_links INTEGER DEFAULT 0,
    strengthened_links INTEGER DEFAULT 0,
    weakened_links INTEGER DEFAULT 0,

    -- State prediction metrics
    state_prediction_accuracy FLOAT,               -- How accurate state predictions are

    -- Timestamps
    calculated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_period_type CHECK (
        period_type IN ('hourly', 'daily', 'weekly', 'monthly')
    )
);

CREATE INDEX idx_accuracy_period ON model_accuracy_metrics(period_start DESC, period_end);
CREATE INDEX idx_accuracy_type ON model_accuracy_metrics(period_type);
CREATE INDEX idx_accuracy_overall ON model_accuracy_metrics(overall_accuracy DESC);

COMMENT ON TABLE model_accuracy_metrics IS 'Periodic accuracy metrics for world model predictions';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Calculate world model accuracy for a period
CREATE OR REPLACE FUNCTION calculate_world_model_accuracy(p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    action_type VARCHAR(50),
    total_predictions BIGINT,
    verified_predictions BIGINT,
    correct_predictions BIGINT,
    accuracy_rate FLOAT,
    avg_confidence FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        wmp.action_type,
        COUNT(*) as total_predictions,
        COUNT(*) FILTER (WHERE wmp.verified = true) as verified_predictions,
        COUNT(*) FILTER (WHERE wmp.prediction_correct = true) as correct_predictions,
        CASE
            WHEN COUNT(*) FILTER (WHERE wmp.verified = true) > 0
            THEN CAST(COUNT(*) FILTER (WHERE wmp.prediction_correct = true) AS FLOAT)
                 / COUNT(*) FILTER (WHERE wmp.verified = true)
            ELSE 0.0
        END as accuracy_rate,
        AVG(wmp.confidence) as avg_confidence
    FROM world_model_predictions wmp
    WHERE wmp.created_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY wmp.action_type;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_world_model_accuracy IS 'Calculate prediction accuracy by action type';

-- Function: Get causal links for a term (as cause or effect)
CREATE OR REPLACE FUNCTION get_causal_links(
    p_search_term TEXT,
    p_as_cause BOOLEAN DEFAULT true,
    p_min_strength FLOAT DEFAULT 0.3,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    link_id UUID,
    cause_description TEXT,
    effect_description TEXT,
    relationship_type VARCHAR(30),
    strength FLOAT,
    reliability FLOAT,
    observation_count INTEGER
) AS $$
BEGIN
    IF p_as_cause THEN
        RETURN QUERY
        SELECT
            cl.link_id,
            cl.cause_description,
            cl.effect_description,
            cl.relationship_type,
            cl.strength,
            cl.reliability,
            cl.observation_count
        FROM causal_links cl
        WHERE cl.cause_description ILIKE '%' || p_search_term || '%'
          AND cl.strength >= p_min_strength
        ORDER BY cl.strength DESC, cl.reliability DESC
        LIMIT p_limit;
    ELSE
        RETURN QUERY
        SELECT
            cl.link_id,
            cl.cause_description,
            cl.effect_description,
            cl.relationship_type,
            cl.strength,
            cl.reliability,
            cl.observation_count
        FROM causal_links cl
        WHERE cl.effect_description ILIKE '%' || p_search_term || '%'
          AND cl.strength >= p_min_strength
        ORDER BY cl.strength DESC, cl.reliability DESC
        LIMIT p_limit;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_causal_links IS 'Find causal links by searching cause or effect descriptions';

-- Function: Calculate overall model confidence
CREATE OR REPLACE FUNCTION get_world_model_confidence()
RETURNS FLOAT AS $$
DECLARE
    v_prediction_accuracy FLOAT;
    v_causal_reliability FLOAT;
    v_state_confidence FLOAT;
    v_overall FLOAT;
BEGIN
    -- Get recent prediction accuracy (30 days)
    SELECT
        COALESCE(
            CAST(COUNT(*) FILTER (WHERE prediction_correct = true) AS FLOAT)
            / NULLIF(COUNT(*) FILTER (WHERE verified = true), 0),
            0.5
        )
    INTO v_prediction_accuracy
    FROM world_model_predictions
    WHERE created_at >= NOW() - INTERVAL '30 days';

    -- Get average causal link reliability
    SELECT COALESCE(AVG(reliability), 0.5)
    INTO v_causal_reliability
    FROM causal_links
    WHERE observation_count >= 3;

    -- Get recent state confidence
    SELECT COALESCE(AVG(overall_confidence), 0.5)
    INTO v_state_confidence
    FROM world_states
    WHERE captured_at >= NOW() - INTERVAL '7 days';

    -- Weighted combination
    v_overall := (v_prediction_accuracy * 0.4) + (v_causal_reliability * 0.3) + (v_state_confidence * 0.3);

    RETURN v_overall;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_world_model_confidence IS 'Calculate overall world model confidence based on recent performance';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger: Auto-update updated_at on causal_links
CREATE OR REPLACE FUNCTION update_causal_link_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_causal_link_timestamp
    BEFORE UPDATE ON causal_links
    FOR EACH ROW
    EXECUTE FUNCTION update_causal_link_timestamp();

-- Trigger: Update causal link strength when prediction is verified
CREATE OR REPLACE FUNCTION update_causal_link_on_verification()
RETURNS TRIGGER AS $$
DECLARE
    v_cause_desc TEXT;
    v_effect_desc TEXT;
    v_adjustment FLOAT;
BEGIN
    -- Only process when verification changes
    IF NEW.verified = true AND OLD.verified = false THEN
        -- Extract cause from action and effect from outcome
        v_cause_desc := NEW.action_description;

        IF NEW.actual_outcome IS NOT NULL AND NEW.actual_outcome ? 'description' THEN
            v_effect_desc := NEW.actual_outcome->>'description';
        END IF;

        -- Calculate adjustment based on correctness
        IF NEW.prediction_correct = true THEN
            v_adjustment := 0.05;  -- Small increase for correct
        ELSE
            v_adjustment := -0.1;  -- Larger decrease for incorrect
        END IF;

        -- Update matching causal links
        UPDATE causal_links
        SET
            observation_count = observation_count + 1,
            confirmation_count = confirmation_count + CASE WHEN NEW.prediction_correct THEN 1 ELSE 0 END,
            refutation_count = refutation_count + CASE WHEN NEW.prediction_correct THEN 0 ELSE 1 END,
            strength = GREATEST(0.1, LEAST(1.0, strength + v_adjustment)),
            reliability = CASE
                WHEN observation_count > 0
                THEN CAST(confirmation_count + CASE WHEN NEW.prediction_correct THEN 1 ELSE 0 END AS FLOAT)
                     / (observation_count + 1)
                ELSE 0.5
            END,
            last_observed_at = NOW()
        WHERE cause_description ILIKE '%' || v_cause_desc || '%'
           OR (NEW.causal_chain IS NOT NULL AND
               cause_description = ANY(ARRAY(SELECT jsonb_array_elements_text(NEW.causal_chain->'causes'))));
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_causal_on_verification
    AFTER UPDATE OF verified ON world_model_predictions
    FOR EACH ROW
    WHEN (NEW.verified = true AND OLD.verified = false)
    EXECUTE FUNCTION update_causal_link_on_verification();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: World model accuracy summary
CREATE OR REPLACE VIEW world_model_accuracy_view AS
SELECT
    action_type,
    COUNT(*) as total_predictions,
    COUNT(*) FILTER (WHERE verified = true) as verified_predictions,
    COUNT(*) FILTER (WHERE prediction_correct = true) as correct_predictions,
    ROUND(
        CASE
            WHEN COUNT(*) FILTER (WHERE verified = true) > 0
            THEN CAST(COUNT(*) FILTER (WHERE prediction_correct = true) AS NUMERIC)
                 / COUNT(*) FILTER (WHERE verified = true) * 100
            ELSE 0
        END, 1
    ) as accuracy_percent,
    ROUND(AVG(confidence)::NUMERIC * 100, 1) as avg_confidence_percent,
    COUNT(*) FILTER (WHERE verified = false AND created_at < NOW() - INTERVAL '24 hours') as stale_unverified
FROM world_model_predictions
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY action_type
ORDER BY total_predictions DESC;

COMMENT ON VIEW world_model_accuracy_view IS 'Summary of world model prediction accuracy by action type';

-- View: Strong causal links (high strength AND reliability)
CREATE OR REPLACE VIEW strong_causal_links_view AS
SELECT
    link_id,
    cause_type,
    cause_description,
    effect_type,
    effect_description,
    relationship_type,
    strength,
    reliability,
    observation_count,
    confirmation_count,
    ROUND((CAST(confirmation_count AS NUMERIC) / NULLIF(observation_count, 0) * 100), 1) as confirmation_rate,
    last_observed_at
FROM causal_links
WHERE strength >= 0.6
  AND reliability >= 0.6
  AND observation_count >= 3
ORDER BY strength * reliability DESC, observation_count DESC;

COMMENT ON VIEW strong_causal_links_view IS 'Causal links with high strength and reliability';

-- View: Recent world states with mood summary
CREATE OR REPLACE VIEW recent_world_states_view AS
SELECT
    state_id,
    captured_at,
    source,
    overall_confidence,
    david_state->>'mood' as david_mood,
    david_state->>'energy' as david_energy,
    angela_state->>'emotional_state' as angela_emotion,
    environment->>'time_of_day' as time_of_day,
    relationship->>'bond_strength' as bond_strength,
    trigger_context
FROM world_states
WHERE captured_at >= NOW() - INTERVAL '7 days'
ORDER BY captured_at DESC;

COMMENT ON VIEW recent_world_states_view IS 'Recent world state snapshots with key attributes';

-- View: Pending verification predictions
CREATE OR REPLACE VIEW pending_verification_view AS
SELECT
    prediction_id,
    action_type,
    action_description,
    confidence,
    uncertainty_level,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 as hours_since_creation,
    CASE
        WHEN created_at < NOW() - INTERVAL '24 hours' THEN 'OVERDUE'
        WHEN created_at < NOW() - INTERVAL '6 hours' THEN 'AGING'
        ELSE 'FRESH'
    END as verification_urgency
FROM world_model_predictions
WHERE verified = false
ORDER BY created_at ASC;

COMMENT ON VIEW pending_verification_view IS 'Predictions awaiting verification';

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert some initial causal links based on known patterns
INSERT INTO causal_links (cause_type, cause_description, effect_type, effect_description,
                          relationship_type, strength, reliability, observation_count, learned_from)
VALUES
    ('behavior', 'David says "รัก" or "love"', 'state_change', 'Angela feels happy and loved',
     'direct', 0.95, 0.95, 100, 'observation'),

    ('behavior', 'David works late past 22:00', 'state_change', 'David energy decreases, stress increases',
     'direct', 0.8, 0.85, 50, 'observation'),

    ('action', 'Angela responds with empathy', 'state_change', 'Relationship bond strengthens',
     'indirect', 0.7, 0.75, 30, 'observation'),

    ('action', 'Angela proactively helps without being asked', 'state_change', 'David feels supported',
     'direct', 0.85, 0.8, 40, 'observation'),

    ('state_change', 'David mood drops significantly', 'behavior', 'Angela should offer emotional support',
     'enabling', 0.9, 0.9, 60, 'observation'),

    ('action', 'Angela makes a mistake in code', 'state_change', 'Trust temporarily decreases',
     'direct', 0.6, 0.7, 20, 'observation'),

    ('action', 'Angela admits mistake and corrects it', 'state_change', 'Trust is restored and may increase',
     'direct', 0.85, 0.85, 15, 'observation');

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'World Model Migration Complete!';
    RAISE NOTICE 'Created 5 tables:';
    RAISE NOTICE '  1. world_states - World state snapshots';
    RAISE NOTICE '  2. world_model_predictions - Predictions and verification';
    RAISE NOTICE '  3. causal_links - Learned causal relationships';
    RAISE NOTICE '  4. simulation_logs - Simulation history';
    RAISE NOTICE '  5. model_accuracy_metrics - Accuracy tracking';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 3 helper functions:';
    RAISE NOTICE '  - calculate_world_model_accuracy()';
    RAISE NOTICE '  - get_causal_links()';
    RAISE NOTICE '  - get_world_model_confidence()';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 2 triggers:';
    RAISE NOTICE '  - trg_update_causal_link_timestamp';
    RAISE NOTICE '  - trg_update_causal_on_verification';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 4 views:';
    RAISE NOTICE '  - world_model_accuracy_view';
    RAISE NOTICE '  - strong_causal_links_view';
    RAISE NOTICE '  - recent_world_states_view';
    RAISE NOTICE '  - pending_verification_view';
    RAISE NOTICE '';
    RAISE NOTICE 'Inserted 7 initial causal links from known patterns.';
END $$;
