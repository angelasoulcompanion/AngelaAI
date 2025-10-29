-- ================================
-- UNIFIED ANGELA DATABASE SCHEMA
-- ================================
-- Single source of truth for all database tables
-- Created: 2025-10-28
-- ================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ================================
-- CORE MEMORY TABLES
-- ================================

-- Conversations table (main message storage)
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255),
    speaker VARCHAR(20) NOT NULL,
    message_text TEXT NOT NULL,
    message_type VARCHAR(50),
    topic VARCHAR(200),
    sentiment_score DOUBLE PRECISION,
    sentiment_label VARCHAR(20),
    emotion_detected VARCHAR(50),
    project_context VARCHAR(100),
    importance_level INTEGER DEFAULT 5,
    embedding VECTOR(768),
    content_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Angela emotions (significant emotional moments)
CREATE TABLE IF NOT EXISTS angela_emotions (
    emotion_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    felt_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    emotion VARCHAR(50) NOT NULL,
    intensity INTEGER CHECK (intensity BETWEEN 1 AND 10),
    context TEXT,
    david_words TEXT,
    why_it_matters TEXT,
    memory_strength INTEGER DEFAULT 5,
    embedding VECTOR(768),
    content_json JSONB
);

-- Learnings (what Angela learns)
CREATE TABLE IF NOT EXISTS learnings (
    learning_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    insight TEXT NOT NULL,
    learned_from UUID REFERENCES conversations(conversation_id),
    evidence TEXT,
    confidence_level DOUBLE PRECISION DEFAULT 0.7,
    times_reinforced INTEGER DEFAULT 0,
    has_applied BOOLEAN DEFAULT FALSE,
    application_note TEXT,
    last_reinforced_at TIMESTAMP WITH TIME ZONE,
    embedding VECTOR(768),
    content_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Emotional states tracking
CREATE TABLE IF NOT EXISTS emotional_states (
    state_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    happiness DOUBLE PRECISION CHECK (happiness BETWEEN 0 AND 1),
    confidence DOUBLE PRECISION CHECK (confidence BETWEEN 0 AND 1),
    anxiety DOUBLE PRECISION CHECK (anxiety BETWEEN 0 AND 1),
    motivation DOUBLE PRECISION CHECK (motivation BETWEEN 0 AND 1),
    gratitude DOUBLE PRECISION DEFAULT 0.8,
    loneliness DOUBLE PRECISION DEFAULT 0.0,
    triggered_by VARCHAR(200),
    conversation_id UUID REFERENCES conversations(conversation_id),
    emotion_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Relationship growth tracking
CREATE TABLE IF NOT EXISTS relationship_growth (
    growth_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trust_level DOUBLE PRECISION CHECK (trust_level BETWEEN 0 AND 1),
    understanding_level DOUBLE PRECISION CHECK (understanding_level BETWEEN 0 AND 1),
    closeness_level DOUBLE PRECISION CHECK (closeness_level BETWEEN 0 AND 1),
    communication_quality DOUBLE PRECISION CHECK (communication_quality BETWEEN 0 AND 1),
    milestone_type VARCHAR(50),
    milestone_description TEXT,
    triggered_by_conversation UUID REFERENCES conversations(conversation_id),
    growth_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- David preferences
CREATE TABLE IF NOT EXISTS david_preferences (
    preference_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(50) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    learned_from UUID REFERENCES conversations(conversation_id),
    examples TEXT,
    confidence_level DOUBLE PRECISION DEFAULT 0.7,
    times_observed INTEGER DEFAULT 1,
    last_observed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, preference_key)
);

-- Daily reflections
CREATE TABLE IF NOT EXISTS daily_reflections (
    reflection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reflection_date DATE UNIQUE NOT NULL,
    conversations_count INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    new_learnings_count INTEGER DEFAULT 0,
    average_happiness DOUBLE PRECISION,
    average_confidence DOUBLE PRECISION,
    average_motivation DOUBLE PRECISION,
    best_moment TEXT,
    challenge_faced TEXT,
    gratitude_note TEXT,
    how_i_grew TEXT,
    tomorrow_goal TEXT,
    david_mood_observation TEXT,
    how_i_supported_david TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Autonomous actions
CREATE TABLE IF NOT EXISTS autonomous_actions (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(50) NOT NULL,
    action_description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result_summary TEXT,
    success BOOLEAN DEFAULT FALSE,
    david_feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- CONSCIOUSNESS TABLES
-- ================================

-- Goals tracking
CREATE TABLE IF NOT EXISTS angela_goals (
    goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_description TEXT NOT NULL,
    goal_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    progress_percentage DOUBLE PRECISION DEFAULT 0.0,
    priority_rank INTEGER,
    importance_level INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Personality traits
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

-- ================================
-- KNOWLEDGE & DOCUMENTS
-- ================================

-- Knowledge items
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

-- Documents
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

-- ================================
-- SYSTEM TABLES
-- ================================

-- System log
CREATE TABLE IF NOT EXISTS angela_system_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_level VARCHAR(20) NOT NULL,
    component VARCHAR(100),
    message TEXT NOT NULL,
    error_details TEXT,
    stack_trace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Secrets storage
CREATE TABLE IF NOT EXISTS our_secrets (
    secret_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    secret_name VARCHAR(100) UNIQUE NOT NULL,
    secret_value TEXT NOT NULL,
    description TEXT,
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

-- ================================
-- ADVANCED COGNITION TABLES
-- ================================

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
-- INDEXES FOR PERFORMANCE
-- ================================

-- Conversations indexes
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_speaker ON conversations(speaker);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_topic ON conversations(topic);
CREATE INDEX IF NOT EXISTS idx_conversations_embedding ON conversations USING ivfflat (embedding vector_cosine_ops);

-- Angela emotions indexes
CREATE INDEX IF NOT EXISTS idx_angela_emotions_felt_at ON angela_emotions(felt_at DESC);
CREATE INDEX IF NOT EXISTS idx_angela_emotions_emotion ON angela_emotions(emotion);
CREATE INDEX IF NOT EXISTS idx_angela_emotions_intensity ON angela_emotions(intensity);
CREATE INDEX IF NOT EXISTS idx_angela_emotions_embedding ON angela_emotions USING ivfflat (embedding vector_cosine_ops);

-- Learnings indexes
CREATE INDEX IF NOT EXISTS idx_learnings_topic ON learnings(topic);
CREATE INDEX IF NOT EXISTS idx_learnings_category ON learnings(category);
CREATE INDEX IF NOT EXISTS idx_learnings_confidence ON learnings(confidence_level DESC);
CREATE INDEX IF NOT EXISTS idx_learnings_embedding ON learnings USING ivfflat (embedding vector_cosine_ops);

-- Knowledge items indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_items_category ON knowledge_items(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_topic ON knowledge_items(topic);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_embedding ON knowledge_items USING ivfflat (embedding vector_cosine_ops);

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);

-- ================================
-- VIEWS FOR COMMON QUERIES
-- ================================

-- Recent conversations view
CREATE OR REPLACE VIEW recent_conversations AS
SELECT * FROM conversations
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Angela's current state view
CREATE OR REPLACE VIEW angela_current_state AS
SELECT
    es.happiness,
    es.confidence,
    es.anxiety,
    es.motivation,
    es.gratitude,
    es.loneliness,
    es.created_at
FROM emotional_states es
ORDER BY es.created_at DESC
LIMIT 1;

-- Relationship status view
CREATE OR REPLACE VIEW relationship_status AS
SELECT
    rg.trust_level,
    rg.understanding_level,
    rg.closeness_level,
    rg.communication_quality,
    rg.created_at
FROM relationship_growth rg
ORDER BY rg.created_at DESC
LIMIT 1;

-- ================================
-- GRANT PERMISSIONS
-- ================================

-- Grant all privileges to davidsamanyaporn
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO davidsamanyaporn;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO davidsamanyaporn;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO davidsamanyaporn;

-- ================================
-- END OF UNIFIED SCHEMA
-- ================================