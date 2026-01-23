-- ============================================================================
-- Model Registry Tables for Angela LLM Twin
-- ============================================================================
--
-- This migration adds tables for:
-- 1. Model versions and metadata
-- 2. Training runs and experiments
-- 3. Evaluation metrics
-- 4. Deployment tracking
--
-- Created: 2026-01-23
-- Purpose: Track Angela's fine-tuned models and training history
-- ============================================================================

-- ============================================================================
-- TABLE 1: model_registry
-- Main registry of all trained models
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_registry (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Model identification
    model_name VARCHAR(200) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    base_model VARCHAR(200) NOT NULL,  -- e.g., 'meta-llama/Llama-3.2-3B', 'Qwen/Qwen2.5-7B'

    -- Model type and purpose
    model_type VARCHAR(50) NOT NULL DEFAULT 'chat',  -- 'chat', 'instruct', 'completion'
    purpose VARCHAR(200),  -- e.g., 'Angela personality', 'Technical assistant'

    -- Training info
    training_run_id UUID,
    dataset_id UUID,
    training_method VARCHAR(50),  -- 'lora', 'qlora', 'full_finetune', 'dpo'

    -- Model files
    model_path TEXT,  -- Local path or HuggingFace repo
    adapter_path TEXT,  -- LoRA adapter path if applicable
    config_path TEXT,

    -- Size and performance
    parameter_count BIGINT,
    adapter_size_mb FLOAT,
    inference_speed_tps FLOAT,  -- Tokens per second

    -- Quality metrics (summary)
    overall_quality_score FLOAT CHECK (overall_quality_score IS NULL OR (overall_quality_score >= 0 AND overall_quality_score <= 1)),
    personality_score FLOAT CHECK (personality_score IS NULL OR (personality_score >= 0 AND personality_score <= 1)),
    technical_score FLOAT CHECK (technical_score IS NULL OR (technical_score >= 0 AND technical_score <= 1)),

    -- Status
    status VARCHAR(50) DEFAULT 'created',  -- 'created', 'training', 'trained', 'evaluating', 'deployed', 'archived'
    is_production BOOLEAN DEFAULT FALSE,
    deployed_at TIMESTAMPTZ,

    -- Notes
    description TEXT,
    release_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(model_name, model_version),
    CONSTRAINT valid_model_status CHECK (status IN ('created', 'training', 'trained', 'evaluating', 'deployed', 'archived'))
);

CREATE INDEX idx_model_registry_name ON model_registry(model_name);
CREATE INDEX idx_model_registry_version ON model_registry(model_version);
CREATE INDEX idx_model_registry_status ON model_registry(status);
CREATE INDEX idx_model_registry_production ON model_registry(is_production) WHERE is_production = TRUE;
CREATE INDEX idx_model_registry_created ON model_registry(created_at DESC);

COMMENT ON TABLE model_registry IS 'Registry of all Angela fine-tuned models';
COMMENT ON COLUMN model_registry.base_model IS 'HuggingFace model ID of the base model';
COMMENT ON COLUMN model_registry.training_method IS 'LoRA, QLoRA, full fine-tune, DPO, etc.';

-- ============================================================================
-- TABLE 2: training_runs
-- Individual training runs/experiments
-- ============================================================================

CREATE TABLE IF NOT EXISTS training_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Run identification
    run_name VARCHAR(200) NOT NULL,
    experiment_name VARCHAR(200),

    -- Model being trained
    model_id UUID REFERENCES model_registry(model_id),
    base_model VARCHAR(200) NOT NULL,

    -- Dataset
    dataset_id UUID,
    dataset_name VARCHAR(200),
    train_examples INTEGER,
    eval_examples INTEGER,

    -- Training configuration
    training_config JSONB DEFAULT '{}'::JSONB,
    -- Expected keys: learning_rate, batch_size, epochs, warmup_steps,
    -- lora_rank, lora_alpha, lora_dropout, max_seq_length, etc.

    -- Hardware info
    hardware_type VARCHAR(100),  -- 'A100-40GB', 'T4', 'M3-Pro', 'Colab-T4'
    training_device VARCHAR(50),  -- 'cuda', 'mps', 'cpu'

    -- Progress tracking
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    current_epoch INTEGER DEFAULT 0,
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER,
    progress_percent FLOAT DEFAULT 0,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    training_duration_minutes FLOAT,

    -- Results
    final_loss FLOAT,
    final_eval_loss FLOAT,
    best_checkpoint_step INTEGER,

    -- Error handling
    error_message TEXT,
    error_traceback TEXT,

    -- External tracking
    comet_experiment_key VARCHAR(200),
    wandb_run_id VARCHAR(200),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_run_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_training_runs_model ON training_runs(model_id);
CREATE INDEX idx_training_runs_status ON training_runs(status);
CREATE INDEX idx_training_runs_created ON training_runs(created_at DESC);
CREATE INDEX idx_training_runs_experiment ON training_runs(experiment_name);

COMMENT ON TABLE training_runs IS 'Individual training runs with full configuration and metrics';

-- ============================================================================
-- TABLE 3: training_metrics
-- Detailed metrics logged during training
-- ============================================================================

CREATE TABLE IF NOT EXISTS training_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES training_runs(run_id) ON DELETE CASCADE,

    -- When
    step INTEGER NOT NULL,
    epoch FLOAT NOT NULL,

    -- Core metrics
    loss FLOAT,
    learning_rate FLOAT,
    grad_norm FLOAT,

    -- Evaluation metrics (if eval step)
    eval_loss FLOAT,
    eval_accuracy FLOAT,
    eval_perplexity FLOAT,

    -- Custom metrics
    custom_metrics JSONB DEFAULT '{}'::JSONB,

    -- Timestamp
    logged_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_training_metrics_run ON training_metrics(run_id);
CREATE INDEX idx_training_metrics_step ON training_metrics(run_id, step);

COMMENT ON TABLE training_metrics IS 'Detailed training metrics per step for visualization';

-- ============================================================================
-- TABLE 4: model_evaluations
-- Evaluation results for models
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_evaluations (
    evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES model_registry(model_id) ON DELETE CASCADE,

    -- Evaluation info
    evaluation_name VARCHAR(200) NOT NULL,
    evaluation_type VARCHAR(50) NOT NULL,  -- 'automatic', 'human', 'benchmark'
    evaluator VARCHAR(100),  -- 'gpt-4', 'claude', 'human:david', 'benchmark:mmlu'

    -- Dataset used for evaluation
    eval_dataset_name VARCHAR(200),
    eval_examples_count INTEGER,

    -- Scores (0-1 normalized)
    overall_score FLOAT CHECK (overall_score >= 0 AND overall_score <= 1),

    -- Detailed scores
    scores JSONB DEFAULT '{}'::JSONB,
    -- Expected keys: personality_consistency, response_quality, emotional_tone,
    -- technical_accuracy, thai_language_quality, english_quality, etc.

    -- Benchmark-specific
    benchmark_results JSONB DEFAULT '{}'::JSONB,

    -- Human evaluation
    human_feedback TEXT,
    human_rating INTEGER CHECK (human_rating IS NULL OR (human_rating >= 1 AND human_rating <= 5)),

    -- Timestamps
    evaluated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_eval_type CHECK (evaluation_type IN ('automatic', 'human', 'benchmark', 'ablation'))
);

CREATE INDEX idx_model_evaluations_model ON model_evaluations(model_id);
CREATE INDEX idx_model_evaluations_type ON model_evaluations(evaluation_type);
CREATE INDEX idx_model_evaluations_score ON model_evaluations(overall_score DESC);

COMMENT ON TABLE model_evaluations IS 'Evaluation results for model quality assessment';

-- ============================================================================
-- TABLE 5: model_deployments
-- Track model deployments
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_deployments (
    deployment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES model_registry(model_id),

    -- Deployment info
    deployment_name VARCHAR(200) NOT NULL,
    environment VARCHAR(50) NOT NULL,  -- 'production', 'staging', 'development', 'testing'

    -- Endpoint info
    endpoint_type VARCHAR(50),  -- 'ollama', 'vllm', 'huggingface', 'api'
    endpoint_url TEXT,
    endpoint_config JSONB DEFAULT '{}'::JSONB,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'deploying', 'active', 'inactive', 'failed'
    health_status VARCHAR(50) DEFAULT 'unknown',  -- 'healthy', 'degraded', 'unhealthy', 'unknown'

    -- Performance
    avg_latency_ms FLOAT,
    requests_per_day INTEGER,
    error_rate FLOAT,

    -- Timing
    deployed_at TIMESTAMPTZ,
    last_health_check TIMESTAMPTZ,

    -- Notes
    deployment_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_deployment_status CHECK (status IN ('pending', 'deploying', 'active', 'inactive', 'failed')),
    CONSTRAINT valid_environment CHECK (environment IN ('production', 'staging', 'development', 'testing'))
);

CREATE INDEX idx_deployments_model ON model_deployments(model_id);
CREATE INDEX idx_deployments_env ON model_deployments(environment);
CREATE INDEX idx_deployments_status ON model_deployments(status);
CREATE INDEX idx_deployments_active ON model_deployments(status) WHERE status = 'active';

COMMENT ON TABLE model_deployments IS 'Track model deployments across environments';

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Current production models
CREATE OR REPLACE VIEW v_production_models AS
SELECT
    m.model_id,
    m.model_name,
    m.model_version,
    m.base_model,
    m.overall_quality_score,
    m.personality_score,
    m.deployed_at,
    d.endpoint_url,
    d.health_status
FROM model_registry m
LEFT JOIN model_deployments d ON m.model_id = d.model_id AND d.status = 'active'
WHERE m.is_production = TRUE
ORDER BY m.deployed_at DESC;

COMMENT ON VIEW v_production_models IS 'Currently deployed production models';

-- View: Latest model per name
CREATE OR REPLACE VIEW v_latest_models AS
SELECT DISTINCT ON (model_name)
    model_id,
    model_name,
    model_version,
    base_model,
    status,
    overall_quality_score,
    created_at
FROM model_registry
ORDER BY model_name, created_at DESC;

COMMENT ON VIEW v_latest_models IS 'Latest version of each model';

-- View: Training run summary
CREATE OR REPLACE VIEW v_training_summary AS
SELECT
    r.run_id,
    r.run_name,
    r.base_model,
    r.status,
    r.train_examples,
    r.final_loss,
    r.training_duration_minutes,
    r.created_at,
    m.model_name,
    m.model_version
FROM training_runs r
LEFT JOIN model_registry m ON r.model_id = m.model_id
ORDER BY r.created_at DESC;

COMMENT ON VIEW v_training_summary IS 'Summary of all training runs';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Get latest model version number
CREATE OR REPLACE FUNCTION get_next_model_version(p_model_name VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_latest VARCHAR;
    v_parts TEXT[];
    v_major INT;
    v_minor INT;
    v_patch INT;
BEGIN
    SELECT model_version INTO v_latest
    FROM model_registry
    WHERE model_name = p_model_name
    ORDER BY created_at DESC
    LIMIT 1;

    IF v_latest IS NULL THEN
        RETURN '1.0.0';
    END IF;

    -- Parse version (assumes semver format)
    v_parts := string_to_array(v_latest, '.');

    IF array_length(v_parts, 1) >= 3 THEN
        v_major := v_parts[1]::INT;
        v_minor := v_parts[2]::INT;
        v_patch := v_parts[3]::INT;

        -- Increment patch version
        RETURN format('%s.%s.%s', v_major, v_minor, v_patch + 1);
    END IF;

    RETURN '1.0.0';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_next_model_version IS 'Get next version number for a model';

-- Function: Set model as production
CREATE OR REPLACE FUNCTION set_production_model(p_model_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Remove production flag from other models with same name
    UPDATE model_registry
    SET is_production = FALSE,
        updated_at = NOW()
    WHERE model_name = (SELECT model_name FROM model_registry WHERE model_id = p_model_id)
      AND model_id != p_model_id
      AND is_production = TRUE;

    -- Set this model as production
    UPDATE model_registry
    SET is_production = TRUE,
        status = 'deployed',
        deployed_at = NOW(),
        updated_at = NOW()
    WHERE model_id = p_model_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION set_production_model IS 'Set a model as the production model';

-- Function: Get model quality trend
CREATE OR REPLACE FUNCTION get_model_quality_trend(p_model_name VARCHAR, p_limit INT DEFAULT 10)
RETURNS TABLE (
    model_version VARCHAR,
    overall_score FLOAT,
    personality_score FLOAT,
    technical_score FLOAT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.model_version,
        m.overall_quality_score,
        m.personality_score,
        m.technical_score,
        m.created_at
    FROM model_registry m
    WHERE m.model_name = p_model_name
    ORDER BY m.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_model_quality_trend IS 'Get quality score trend for a model';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger: Update timestamp on model_registry
CREATE OR REPLACE FUNCTION update_model_registry_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_model_registry_timestamp
    BEFORE UPDATE ON model_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_model_registry_timestamp();

-- Trigger: Update timestamp on training_runs
CREATE TRIGGER trg_update_training_runs_timestamp
    BEFORE UPDATE ON training_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_model_registry_timestamp();

-- Trigger: Update timestamp on model_deployments
CREATE TRIGGER trg_update_deployments_timestamp
    BEFORE UPDATE ON model_deployments
    FOR EACH ROW
    EXECUTE FUNCTION update_model_registry_timestamp();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Model Registry Migration Complete!';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 5 tables:';
    RAISE NOTICE '  1. model_registry - Main model registry';
    RAISE NOTICE '  2. training_runs - Training experiments';
    RAISE NOTICE '  3. training_metrics - Step-by-step metrics';
    RAISE NOTICE '  4. model_evaluations - Evaluation results';
    RAISE NOTICE '  5. model_deployments - Deployment tracking';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 3 views:';
    RAISE NOTICE '  - v_production_models';
    RAISE NOTICE '  - v_latest_models';
    RAISE NOTICE '  - v_training_summary';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 3 helper functions:';
    RAISE NOTICE '  - get_next_model_version()';
    RAISE NOTICE '  - set_production_model()';
    RAISE NOTICE '  - get_model_quality_trend()';
END $$;
