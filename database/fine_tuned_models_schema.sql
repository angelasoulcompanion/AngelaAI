-- 💜 Fine-tuned Models Management Schema
-- Stores information about Angela's fine-tuned models

CREATE TABLE IF NOT EXISTS fine_tuned_models (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Model identification
    model_name VARCHAR(100) NOT NULL UNIQUE,  -- e.g., "angela_qwen_20251026"
    display_name VARCHAR(200) NOT NULL,        -- e.g., "Angela Qwen (October 2025)"
    description TEXT,                          -- Description of what makes this model special

    -- Model details
    base_model VARCHAR(100) NOT NULL,          -- e.g., "Qwen/Qwen2.5-1.5B-Instruct"
    model_type VARCHAR(50) NOT NULL,           -- "qwen", "llama", "mistral"
    model_size VARCHAR(20),                    -- "1.5B", "3B", "7B"

    -- Training information
    training_date TIMESTAMP NOT NULL,
    training_examples INTEGER,                 -- Number of training examples used
    training_epochs INTEGER,                   -- Number of epochs trained
    final_loss DOUBLE PRECISION,               -- Final training loss
    evaluation_score DOUBLE PRECISION,         -- Evaluation metric

    -- File information
    file_path TEXT NOT NULL,                   -- Path to model files on disk
    file_size_mb DOUBLE PRECISION,             -- Model size in MB
    file_hash VARCHAR(64),                     -- SHA-256 hash for integrity

    -- Ollama integration
    ollama_model_name VARCHAR(100),            -- Name in Ollama (e.g., "angela:latest")
    is_imported_to_ollama BOOLEAN DEFAULT FALSE,
    ollama_import_date TIMESTAMP,

    -- Status and management
    status VARCHAR(20) DEFAULT 'uploaded',     -- 'uploaded', 'importing', 'ready', 'active', 'archived', 'failed'
    is_active BOOLEAN DEFAULT FALSE,           -- Only one model can be active
    version VARCHAR(20),                       -- e.g., "v1.0", "v1.1"

    -- Performance metrics
    avg_response_time_ms DOUBLE PRECISION,     -- Average response time
    quality_rating DOUBLE PRECISION,           -- User quality rating (1-10)
    total_uses INTEGER DEFAULT 0,              -- How many times this model was used

    -- Metadata
    tags TEXT[],                               -- ['emotional', 'technical', 'conversational']
    notes TEXT,                                -- Admin notes
    created_by VARCHAR(50) DEFAULT 'David',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_finetuned_models_status ON fine_tuned_models(status);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_active ON fine_tuned_models(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_finetuned_models_ollama ON fine_tuned_models(ollama_model_name);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_created ON fine_tuned_models(created_at DESC);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_finetuned_model_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_finetuned_model_timestamp
BEFORE UPDATE ON fine_tuned_models
FOR EACH ROW
EXECUTE FUNCTION update_finetuned_model_timestamp();

-- Trigger to ensure only one active model
CREATE OR REPLACE FUNCTION ensure_single_active_model()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = TRUE THEN
        -- Deactivate all other models
        UPDATE fine_tuned_models
        SET is_active = FALSE
        WHERE model_id != NEW.model_id AND is_active = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ensure_single_active_model
BEFORE UPDATE OF is_active ON fine_tuned_models
FOR EACH ROW
WHEN (NEW.is_active = TRUE)
EXECUTE FUNCTION ensure_single_active_model();

-- Comments
COMMENT ON TABLE fine_tuned_models IS 'Stores information about Angela''s fine-tuned models';
COMMENT ON COLUMN fine_tuned_models.model_name IS 'Unique identifier for the model';
COMMENT ON COLUMN fine_tuned_models.is_active IS 'Only one model can be active at a time';
COMMENT ON COLUMN fine_tuned_models.ollama_model_name IS 'Name used in Ollama (e.g., angela:latest)';
COMMENT ON COLUMN fine_tuned_models.status IS 'Model lifecycle: uploaded -> importing -> ready -> active/archived';
