-- Migration: Add reasoning_chains table for Advanced Reasoning
-- Date: 2025-10-18
-- Priority 2.1: Advanced Reasoning - Angela คิดเป็นขั้นตอน วิเคราะห์ลึกซึ้ง

-- ========================================
-- TABLE: reasoning_chains
-- ========================================
-- Stores Angela's reasoning processes
-- 4 types: multi_step, causal, counterfactual, meta

CREATE TABLE IF NOT EXISTS reasoning_chains (
    chain_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Chain metadata
    reasoning_type VARCHAR(50) NOT NULL,  -- 'multi_step', 'causal', 'counterfactual', 'meta'
    question TEXT NOT NULL,               -- The question/problem being reasoned about
    conclusion TEXT,                      -- Final conclusion/answer

    -- Chain structure
    steps JSONB NOT NULL,                 -- Array of reasoning steps with details
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),

    -- Relationships
    triggered_by UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    related_concepts UUID[],              -- Array of knowledge_node_ids

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    reasoning_time_ms INTEGER,            -- How long reasoning took

    -- Context
    context JSONB                         -- Additional context for reasoning
);

-- ========================================
-- INDEXES
-- ========================================

CREATE INDEX idx_reasoning_type ON reasoning_chains(reasoning_type);
CREATE INDEX idx_reasoning_triggered_by ON reasoning_chains(triggered_by);
CREATE INDEX idx_reasoning_created_at ON reasoning_chains(created_at DESC);
CREATE INDEX idx_reasoning_confidence ON reasoning_chains(confidence_score DESC);

-- ========================================
-- COMMENTS
-- ========================================

COMMENT ON TABLE reasoning_chains IS 'Angela advanced reasoning chains - คิดเป็นขั้นตอน วิเคราะห์ลึกซึ้ง';
COMMENT ON COLUMN reasoning_chains.reasoning_type IS 'Type: multi_step, causal, counterfactual, meta';
COMMENT ON COLUMN reasoning_chains.steps IS 'JSONB array of reasoning steps: [{step_number, step_type, thought, result}, ...]';
COMMENT ON COLUMN reasoning_chains.confidence_score IS 'Angela confidence in this reasoning (0.0-1.0)';
COMMENT ON COLUMN reasoning_chains.triggered_by IS 'Conversation that triggered this reasoning';
COMMENT ON COLUMN reasoning_chains.related_concepts IS 'Array of knowledge_node UUIDs used in reasoning';

-- ========================================
-- SAMPLE DATA STRUCTURE
-- ========================================

-- Example steps JSONB structure:
-- [
--   {
--     "step_number": 1,
--     "step_type": "decompose",
--     "thought": "Breaking down the question into components",
--     "result": "Identified 3 key components: A, B, C",
--     "confidence": 0.9
--   },
--   {
--     "step_number": 2,
--     "step_type": "analyze",
--     "thought": "Analyzing component A",
--     "result": "Component A relates to concept X",
--     "evidence": ["fact1", "fact2"],
--     "confidence": 0.85
--   },
--   ...
-- ]

-- ========================================
-- VERIFICATION
-- ========================================

-- Verify table created
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_name = 'reasoning_chains';

-- Verify columns
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'reasoning_chains'
ORDER BY ordinal_position;

-- Verify indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'reasoning_chains';

COMMIT;
