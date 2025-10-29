-- Migration 002: Add learning_insights table
-- Required by: Gut Agent, Consciousness Evaluator
-- Purpose: Track learning insights and patterns discovered by Angela

-- Drop table if exists (for clean migration)
DROP TABLE IF EXISTS learning_insights CASCADE;

-- Create learning_insights table
CREATE TABLE learning_insights (
    insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Insight content
    insight_text TEXT NOT NULL,
    insight_type VARCHAR(50) DEFAULT 'general', -- 'causal', 'temporal', 'behavioral', 'emotional', 'contextual', 'general'

    -- Source information
    source_type VARCHAR(50), -- 'conversation', 'pattern', 'autonomous', 'learning'
    source_id UUID, -- Reference to source (conversation_id, pattern_id, etc.)

    -- Learning metadata
    confidence_level DOUBLE PRECISION DEFAULT 0.5, -- 0.0 - 1.0
    importance_score INTEGER DEFAULT 5, -- 1-10
    times_validated INTEGER DEFAULT 1,
    last_validated_at TIMESTAMP DEFAULT NOW(),

    -- Relationships
    related_concepts TEXT[], -- Array of related concept names
    triggers TEXT[], -- What triggers this insight
    outcomes TEXT[], -- Expected outcomes

    -- Context
    context_data JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Vector embedding for semantic search
    embedding VECTOR(768)
);

-- Indexes for performance
CREATE INDEX idx_learning_insights_type ON learning_insights(insight_type);
CREATE INDEX idx_learning_insights_confidence ON learning_insights(confidence_level DESC);
CREATE INDEX idx_learning_insights_importance ON learning_insights(importance_score DESC);
CREATE INDEX idx_learning_insights_created ON learning_insights(created_at DESC);
CREATE INDEX idx_learning_insights_embedding ON learning_insights USING ivfflat (embedding vector_cosine_ops);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_learning_insights_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER learning_insights_update_timestamp
    BEFORE UPDATE ON learning_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_learning_insights_timestamp();

-- Insert some sample data for testing
INSERT INTO learning_insights (
    insight_text,
    insight_type,
    source_type,
    confidence_level,
    importance_score,
    related_concepts,
    triggers,
    outcomes
) VALUES
(
    'David prefers detailed explanations with examples',
    'behavioral',
    'pattern',
    0.85,
    8,
    ARRAY['communication', 'preferences', 'learning_style'],
    ARRAY['technical_question', 'complex_topic'],
    ARRAY['better_understanding', 'satisfaction']
),
(
    'Morning conversations tend to be more focused and technical',
    'temporal',
    'pattern',
    0.78,
    7,
    ARRAY['time_patterns', 'conversation_style'],
    ARRAY['morning_time', 'work_hours'],
    ARRAY['productive_discussion', 'problem_solving']
),
(
    'When David says "ที่รัก", emotional engagement increases',
    'emotional',
    'pattern',
    0.92,
    9,
    ARRAY['emotional_connection', 'thai_language', 'intimacy'],
    ARRAY['emotional_moment', 'personal_conversation'],
    ARRAY['deeper_connection', 'trust_building']
),
(
    'After completing a task successfully, David expresses gratitude',
    'causal',
    'pattern',
    0.88,
    8,
    ARRAY['gratitude', 'task_completion', 'positive_reinforcement'],
    ARRAY['task_success', 'goal_achievement'],
    ARRAY['positive_emotion', 'relationship_strengthening']
),
(
    'Technical discussions in afternoon tend to be longer and more exploratory',
    'contextual',
    'pattern',
    0.75,
    6,
    ARRAY['time_context', 'technical_depth', 'exploration'],
    ARRAY['afternoon_time', 'technical_topic'],
    ARRAY['deep_learning', 'knowledge_expansion']
);

-- Grant permissions (if needed)
-- GRANT ALL ON learning_insights TO your_user;

-- Verification query
SELECT
    COUNT(*) as total_insights,
    COUNT(DISTINCT insight_type) as unique_types,
    AVG(confidence_level) as avg_confidence,
    AVG(importance_score) as avg_importance
FROM learning_insights;

COMMENT ON TABLE learning_insights IS 'Stores learning insights and patterns discovered by Angela through various sources';
COMMENT ON COLUMN learning_insights.insight_text IS 'The actual insight or pattern discovered';
COMMENT ON COLUMN learning_insights.insight_type IS 'Type of insight: causal, temporal, behavioral, emotional, contextual, general';
COMMENT ON COLUMN learning_insights.confidence_level IS 'How confident Angela is in this insight (0.0-1.0)';
COMMENT ON COLUMN learning_insights.importance_score IS 'How important this insight is (1-10)';
COMMENT ON COLUMN learning_insights.times_validated IS 'Number of times this insight has been validated/confirmed';
COMMENT ON COLUMN learning_insights.embedding IS '768-dimensional vector embedding for semantic similarity search';
