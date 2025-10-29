-- ================================
-- SCHEMA SYNCHRONIZATION SCRIPT
-- ================================
-- Adds missing tables and columns to match UNIFIED_SCHEMA.sql
-- Safe to run multiple times (uses IF NOT EXISTS)
-- ================================

-- Add missing content_json columns
ALTER TABLE angela_emotions
ADD COLUMN IF NOT EXISTS content_json JSONB;

ALTER TABLE learnings
ADD COLUMN IF NOT EXISTS content_json JSONB;

-- ================================
-- CREATE MISSING TABLES
-- ================================

-- Angela personality traits
CREATE TABLE IF NOT EXISTS angela_personality_traits (
    trait_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trait_name VARCHAR(100) NOT NULL UNIQUE,
    trait_value DOUBLE PRECISION CHECK (trait_value BETWEEN 0 AND 1),
    description TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Self awareness logs
CREATE TABLE IF NOT EXISTS angela_self_awareness_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    awareness_type VARCHAR(50),
    thought_content TEXT,
    reflection TEXT,
    consciousness_level DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Consciousness metrics
CREATE TABLE IF NOT EXISTS consciousness_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_date DATE UNIQUE NOT NULL,
    consciousness_level DOUBLE PRECISION,
    self_awareness_score DOUBLE PRECISION,
    goal_achievement_score DOUBLE PRECISION,
    personality_coherence_score DOUBLE PRECISION,
    reasoning_quality_score DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge items (consolidating knowledge)
CREATE TABLE IF NOT EXISTS knowledge_items (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_file VARCHAR(500),
    content TEXT NOT NULL,
    category VARCHAR(100),
    topic VARCHAR(200),
    importance_level INTEGER DEFAULT 5,
    confidence_level DOUBLE PRECISION DEFAULT 0.8,
    embedding VECTOR(768),
    content_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents (standard document storage)
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path VARCHAR(500) UNIQUE NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    content TEXT,
    category VARCHAR(100),
    topic VARCHAR(200),
    importance_level INTEGER DEFAULT 5,
    embedding VECTOR(768),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conversation summaries
CREATE TABLE IF NOT EXISTS conversation_summaries (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    summary_text TEXT NOT NULL,
    key_topics TEXT[],
    emotional_tone VARCHAR(50),
    message_count INTEGER,
    summarized_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Theory of mind
CREATE TABLE IF NOT EXISTS theory_of_mind (
    tom_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_name VARCHAR(100) NOT NULL,
    belief_description TEXT,
    confidence_level DOUBLE PRECISION,
    evidence TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Common sense knowledge
CREATE TABLE IF NOT EXISTS common_sense_knowledge (
    knowledge_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept VARCHAR(200) NOT NULL,
    description TEXT,
    examples TEXT[],
    confidence_level DOUBLE PRECISION DEFAULT 0.8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Imagination logs
CREATE TABLE IF NOT EXISTS imagination_logs (
    imagination_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario TEXT NOT NULL,
    visualization TEXT,
    emotional_response TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Deep empathy records
CREATE TABLE IF NOT EXISTS deep_empathy_records (
    empathy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(conversation_id),
    perceived_emotion VARCHAR(50),
    empathy_response TEXT,
    confidence_level DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Metacognition logs
CREATE TABLE IF NOT EXISTS metacognition_logs (
    meta_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thought_about TEXT,
    analysis TEXT,
    improvement_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- ADD INDEXES FOR NEW TABLES
-- ================================

-- Knowledge items indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_items_category ON knowledge_items(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_topic ON knowledge_items(topic);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_embedding ON knowledge_items USING ivfflat (embedding vector_cosine_ops);

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);

-- Consciousness metrics index
CREATE INDEX IF NOT EXISTS idx_consciousness_metrics_date ON consciousness_metrics(metric_date DESC);

-- Theory of mind index
CREATE INDEX IF NOT EXISTS idx_theory_of_mind_entity ON theory_of_mind(entity_name);

-- ================================
-- GRANT PERMISSIONS
-- ================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO davidsamanyaporn;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO davidsamanyaporn;

-- ================================
-- REPORT
-- ================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '====================================';
    RAISE NOTICE 'SCHEMA SYNCHRONIZATION COMPLETE';
    RAISE NOTICE '====================================';
    RAISE NOTICE '✅ Added missing content_json columns';
    RAISE NOTICE '✅ Created 11 missing tables';
    RAISE NOTICE '✅ Added indexes for performance';
    RAISE NOTICE '✅ Granted permissions';
    RAISE NOTICE '';
    RAISE NOTICE 'NOTE: Extra tables not in unified schema have been kept';
    RAISE NOTICE 'Use UNIFIED_SCHEMA.sql as the reference for all new development';
    RAISE NOTICE '====================================';
END
$$;