-- Self-Learning System Tables
-- Created: 2025-11-03
-- Purpose: Store learning patterns, preferences, training examples, and metrics for Angela's continuous self-learning
-- Part of: Self-Learning System (Phase 5+)
-- Author: Angela 💜

-- ===============================================
-- 1. Learning Patterns Table
-- ===============================================
-- Stores behavioral patterns Angela learns from observing David
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern classification
    pattern_type VARCHAR(50) NOT NULL,  -- conversation_flow, emotional_response, preference, communication_style, technical_approach, problem_solving
    description TEXT NOT NULL,          -- Human-readable description of the pattern

    -- Examples and evidence
    examples JSONB DEFAULT '[]'::jsonb, -- List of example strings demonstrating this pattern
    context JSONB DEFAULT '{}'::jsonb,  -- Additional contextual information
    tags JSONB DEFAULT '[]'::jsonb,     -- List of tag strings for categorization

    -- Confidence and observation metrics
    confidence_score DOUBLE PRECISION DEFAULT 0.5 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    occurrence_count INTEGER DEFAULT 0 CHECK (occurrence_count >= 0),
    first_observed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_observed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Vector embedding for similarity search
    embedding vector(768),              -- 768-dim embedding from Ollama nomic-embed-text

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_learning_patterns_type ON learning_patterns(pattern_type);
CREATE INDEX idx_learning_patterns_confidence ON learning_patterns(confidence_score DESC);
CREATE INDEX idx_learning_patterns_occurrences ON learning_patterns(occurrence_count DESC);
CREATE INDEX idx_learning_patterns_last_observed ON learning_patterns(last_observed DESC);
CREATE INDEX idx_learning_patterns_tags ON learning_patterns USING gin(tags);

-- Vector similarity search index
CREATE INDEX idx_learning_patterns_embedding ON learning_patterns
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);


-- ===============================================
-- 2. David's Preferences Table
-- ===============================================
-- Stores specific preferences David has shown through interactions
CREATE TABLE david_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Preference classification
    category VARCHAR(50) NOT NULL,      -- communication, technical, emotional, work, learning, format
    preference_key VARCHAR(100) NOT NULL UNIQUE, -- Unique key identifying the preference
    preference_value JSONB NOT NULL,    -- The actual preference value (can be any type)

    -- Confidence and evidence
    confidence DOUBLE PRECISION DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    evidence_count INTEGER DEFAULT 0,
    evidence_conversation_ids JSONB DEFAULT '[]'::jsonb, -- List of conversation UUIDs supporting this preference

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_david_preferences_category ON david_preferences(category);
CREATE INDEX idx_david_preferences_confidence ON david_preferences(confidence DESC);
CREATE INDEX idx_david_preferences_key ON david_preferences(preference_key);

-- Constraint to ensure unique preference_key per category
CREATE UNIQUE INDEX idx_david_preferences_category_key ON david_preferences(category, preference_key);


-- ===============================================
-- 3. Training Examples Table
-- ===============================================
-- Stores training examples for fine-tuning Angela's model
CREATE TABLE training_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Training data
    input_text TEXT NOT NULL,           -- User input (David's message)
    expected_output TEXT NOT NULL,      -- Expected response (Angela's ideal response)

    -- Quality assessment
    quality_score DOUBLE PRECISION DEFAULT 0.5 CHECK (quality_score >= 0.0 AND quality_score <= 10.0),

    -- Source tracking
    source_type VARCHAR(50) NOT NULL,   -- real_conversation, synthetic, paraphrased, augmented
    source_conversation_id UUID,        -- FK to conversations table if from real conversation
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional metadata about the example

    -- Vector embedding for similarity search and deduplication
    embedding vector(768),              -- 768-dim embedding from Ollama nomic-embed-text

    -- Training tracking
    used_in_training BOOLEAN DEFAULT false,
    training_date TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_training_examples_quality ON training_examples(quality_score DESC);
CREATE INDEX idx_training_examples_source_type ON training_examples(source_type);
CREATE INDEX idx_training_examples_used ON training_examples(used_in_training);
CREATE INDEX idx_training_examples_created ON training_examples(created_at DESC);

-- Vector similarity search index
CREATE INDEX idx_training_examples_embedding ON training_examples
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Optional FK constraint (commented out in case conversations table doesn't exist yet)
-- ALTER TABLE training_examples ADD CONSTRAINT fk_training_source_conversation
--     FOREIGN KEY (source_conversation_id) REFERENCES conversations(conversation_id) ON DELETE SET NULL;


-- ===============================================
-- 4. Learning Metrics Table
-- ===============================================
-- Tracks metrics and progress of the self-learning system
CREATE TABLE learning_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Metric identification
    metric_type VARCHAR(100) NOT NULL,  -- pattern_discovery, preference_confidence, training_quality, model_improvement, etc.
    metric_name VARCHAR(200) NOT NULL,  -- Specific metric name

    -- Metric value and context
    metric_value DOUBLE PRECISION NOT NULL,
    metric_unit VARCHAR(50),            -- Unit of measurement (score, count, percentage, etc.)

    -- Context and metadata
    context JSONB DEFAULT '{}'::jsonb,  -- Additional context about this metric
    related_entity_id UUID,             -- Optional reference to related entity (pattern, preference, etc.)
    related_entity_type VARCHAR(50),    -- Type of related entity (pattern, preference, training_example)

    -- Time period
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_start TIMESTAMP,             -- For aggregate metrics over a period
    period_end TIMESTAMP,               -- For aggregate metrics over a period

    -- Notes
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_learning_metrics_type ON learning_metrics(metric_type);
CREATE INDEX idx_learning_metrics_name ON learning_metrics(metric_name);
CREATE INDEX idx_learning_metrics_measured ON learning_metrics(measured_at DESC);
CREATE INDEX idx_learning_metrics_value ON learning_metrics(metric_value DESC);


-- ===============================================
-- COMMENTS FOR DOCUMENTATION
-- ===============================================

COMMENT ON TABLE learning_patterns IS 'Stores behavioral patterns Angela learns from observing David. Part of Self-Learning System (Phase 5+).';
COMMENT ON COLUMN learning_patterns.pattern_type IS 'Type of pattern: conversation_flow, emotional_response, preference, communication_style, technical_approach, problem_solving';
COMMENT ON COLUMN learning_patterns.confidence_score IS 'Confidence level (0.0-1.0) - increases with each observation using diminishing returns';
COMMENT ON COLUMN learning_patterns.occurrence_count IS 'Number of times this pattern has been observed';

COMMENT ON TABLE david_preferences IS 'Stores David''s learned preferences - specific likes, dislikes, and style choices. Part of Self-Learning System (Phase 5+).';
COMMENT ON COLUMN david_preferences.category IS 'Preference category: communication, technical, emotional, work, learning, format';
COMMENT ON COLUMN david_preferences.preference_key IS 'Unique identifier for the preference (e.g., "response_length", "code_style")';
COMMENT ON COLUMN david_preferences.confidence IS 'Confidence level (0.0-1.0) - increases with more supporting evidence';

COMMENT ON TABLE training_examples IS 'Training examples for fine-tuning Angela''s model. Part of Self-Learning System (Phase 5+).';
COMMENT ON COLUMN training_examples.quality_score IS 'Quality score (0.0-10.0) assessed by quality service';
COMMENT ON COLUMN training_examples.source_type IS 'Source: real_conversation, synthetic, paraphrased, augmented';
COMMENT ON COLUMN training_examples.used_in_training IS 'Whether this example has been used in a training run';

COMMENT ON TABLE learning_metrics IS 'Tracks metrics and progress of the self-learning system. Part of Self-Learning System (Phase 5+).';
COMMENT ON COLUMN learning_metrics.metric_type IS 'High-level category of metric (pattern_discovery, preference_confidence, etc.)';
COMMENT ON COLUMN learning_metrics.metric_value IS 'Numeric value of the metric';


-- ===============================================
-- SAMPLE DATA (for testing)
-- ===============================================

-- Sample learning pattern
INSERT INTO learning_patterns (
    pattern_type, description, examples, confidence_score, occurrence_count,
    first_observed, last_observed, tags
) VALUES (
    'communication_style',
    'David prefers concise, direct responses with code examples over lengthy explanations',
    '["Short answer with code snippet", "Direct solution without theory", "Inline comments in code"]'::jsonb,
    0.85,
    12,
    CURRENT_TIMESTAMP - INTERVAL '30 days',
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    '["communication", "code_style", "brevity"]'::jsonb
);

-- Sample preference
INSERT INTO david_preferences (
    category, preference_key, preference_value, confidence, evidence_count
) VALUES (
    'technical',
    'code_style',
    '"pythonic_with_inline_comments"'::jsonb,
    0.90,
    15
);

-- Sample training example
INSERT INTO training_examples (
    input_text, expected_output, quality_score, source_type
) VALUES (
    'How do I read a file in Python?',
    'Here''s how to read a file in Python:\n\n```python\n# Open and read entire file\nwith open("file.txt", "r") as f:\n    content = f.read()\n\n# Or read line by line\nwith open("file.txt", "r") as f:\n    for line in f:\n        print(line.strip())\n```\n\nThe `with` statement ensures the file is properly closed.',
    9.2,
    'real_conversation'
);

-- Sample metric
INSERT INTO learning_metrics (
    metric_type, metric_name, metric_value, metric_unit, context
) VALUES (
    'pattern_discovery',
    'new_patterns_this_week',
    5,
    'count',
    '{"week": "2025-W44", "category": "communication_style"}'::jsonb
);


-- ===============================================
-- GRANTS (if using specific roles)
-- ===============================================

-- Grant permissions to David's user (adjust username as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON learning_patterns TO davidsamanyaporn;
GRANT SELECT, INSERT, UPDATE, DELETE ON david_preferences TO davidsamanyaporn;
GRANT SELECT, INSERT, UPDATE, DELETE ON training_examples TO davidsamanyaporn;
GRANT SELECT, INSERT, UPDATE, DELETE ON learning_metrics TO davidsamanyaporn;


-- ===============================================
-- COMPLETION MESSAGE
-- ===============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Self-Learning System tables created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Created tables:';
    RAISE NOTICE '  - learning_patterns (behavioral patterns)';
    RAISE NOTICE '  - david_preferences (user preferences)';
    RAISE NOTICE '  - training_examples (fine-tuning data)';
    RAISE NOTICE '  - learning_metrics (system metrics)';
    RAISE NOTICE '';
    RAISE NOTICE 'Author: Angela 💜';
    RAISE NOTICE 'Part of: Self-Learning System (Phase 5+)';
END $$;
