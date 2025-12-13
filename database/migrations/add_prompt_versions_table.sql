--
-- add_prompt_versions_table.sql
-- Migration: Add table for storing optimized prompt versions
-- Created: 2025-11-06
--

-- Create prompt_versions table
CREATE TABLE IF NOT EXISTS prompt_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(20) NOT NULL,
    prompt_text TEXT NOT NULL,
    components JSONB,  -- List of included components (e.g., ["core_identity", "goals", "preferences"])
    metadata JSONB,    -- Additional metadata (e.g., {"goals_count": 5, "length": 1234})
    notes TEXT,        -- Optional notes about this version
    model_target VARCHAR(100) DEFAULT 'Apple Foundation Models (3B)',
    is_active BOOLEAN DEFAULT false,  -- Is this the currently active prompt?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50) DEFAULT 'angela_system'
);

-- Create index on version
CREATE INDEX idx_prompt_versions_version ON prompt_versions(version);

-- Create index on created_at (for sorting by date)
CREATE INDEX idx_prompt_versions_created_at ON prompt_versions(created_at DESC);

-- Create index on is_active (to quickly find active prompt)
CREATE INDEX idx_prompt_versions_is_active ON prompt_versions(is_active) WHERE is_active = true;

-- Comments
COMMENT ON TABLE prompt_versions IS 'Stores optimized system prompt versions for Angela AI - tracks changes and enables A/B testing';
COMMENT ON COLUMN prompt_versions.version_id IS 'Unique identifier for this prompt version';
COMMENT ON COLUMN prompt_versions.version IS 'Version string (e.g., "1.0.0", "1.1.0")';
COMMENT ON COLUMN prompt_versions.prompt_text IS 'Full optimized system prompt text';
COMMENT ON COLUMN prompt_versions.components IS 'JSON array of included components';
COMMENT ON COLUMN prompt_versions.metadata IS 'JSON object with metadata (goals_count, preferences_count, length, etc.)';
COMMENT ON COLUMN prompt_versions.notes IS 'Optional notes about what changed in this version';
COMMENT ON COLUMN prompt_versions.model_target IS 'Target model for this prompt (e.g., "Apple Foundation Models (3B)")';
COMMENT ON COLUMN prompt_versions.is_active IS 'Whether this is the currently active prompt used in production';
COMMENT ON COLUMN prompt_versions.created_at IS 'When this version was created';
COMMENT ON COLUMN prompt_versions.created_by IS 'Who/what created this version (e.g., "angela_system", "david")';
