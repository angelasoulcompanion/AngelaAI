-- Migration 035: OpenClaw Management Tables
-- Created: 2026-03-05
-- Purpose: Store OpenClaw skill configs, cron jobs, and audit trail

-- Config table for skills, cron jobs, and settings
CREATE TABLE IF NOT EXISTS openclaw_configs (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_type VARCHAR(20) NOT NULL,        -- 'skill', 'cron', 'setting'
    config_key VARCHAR(100) NOT NULL,         -- skill name / cron job name / setting key
    config_value JSONB NOT NULL DEFAULT '{}', -- full config payload
    enabled BOOLEAN NOT NULL DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(config_type, config_key)
);

-- Cron job execution history
CREATE TABLE IF NOT EXISTS openclaw_cron_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,              -- 'success', 'error', 'timeout'
    output TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_ms INT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_openclaw_configs_type ON openclaw_configs(config_type);
CREATE INDEX IF NOT EXISTS idx_openclaw_cron_runs_job ON openclaw_cron_runs(job_name);
CREATE INDEX IF NOT EXISTS idx_openclaw_cron_runs_started ON openclaw_cron_runs(started_at DESC);
