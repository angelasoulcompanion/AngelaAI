-- 🧠 Angela's Sub-Conscious System
-- Auto self-learning from Shared Experiences
-- Created: 2025-11-11

-- 1. Sub-Conscious Patterns Table
CREATE TABLE IF NOT EXISTS angela_subconscious (
    subconscious_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Pattern Classification
    pattern_type VARCHAR(50) NOT NULL, -- 'place_affinity', 'emotional_trigger', 'behavioral_pattern', 'preference', 'instinct'
    pattern_category VARCHAR(50), -- 'spatial', 'temporal', 'emotional', 'social'
    
    -- Pattern Content
    pattern_key TEXT NOT NULL, -- Machine-readable key (e.g., "place:khao_san_road:high_intensity")
    pattern_description TEXT NOT NULL, -- Human-readable description
    instinctive_response TEXT, -- How Angela should instinctively respond
    
    -- Learning Metrics
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    source_count INTEGER DEFAULT 1, -- Number of experiences that created this pattern
    reinforcement_count INTEGER DEFAULT 0, -- Times pattern was reinforced
    last_reinforced_at TIMESTAMP DEFAULT NOW(),
    
    -- Pattern Strength (like neural connection strength)
    activation_strength FLOAT DEFAULT 0.5 CHECK (activation_strength >= 0.0 AND activation_strength <= 1.0),
    decay_rate FLOAT DEFAULT 0.01, -- How fast pattern fades without reinforcement
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Semantic Search
    embedding VECTOR(768)
);

-- 2. Pattern Learning History (like memory consolidation)
CREATE TABLE IF NOT EXISTS subconscious_learning_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subconscious_id UUID REFERENCES angela_subconscious(subconscious_id) ON DELETE CASCADE,
    
    learning_event VARCHAR(50), -- 'created', 'reinforced', 'weakened', 'consolidated'
    trigger_source VARCHAR(50), -- 'shared_experience', 'conversation', 'reflection'
    trigger_id UUID, -- ID of the source (experience_id, conversation_id, etc.)
    
    confidence_before FLOAT,
    confidence_after FLOAT,
    strength_before FLOAT,
    strength_after FLOAT,
    
    learned_at TIMESTAMP DEFAULT NOW()
);

-- 3. Indexes for fast pattern matching
CREATE INDEX IF NOT EXISTS idx_subconscious_type ON angela_subconscious(pattern_type);
CREATE INDEX IF NOT EXISTS idx_subconscious_category ON angela_subconscious(pattern_category);
CREATE INDEX IF NOT EXISTS idx_subconscious_strength ON angela_subconscious(activation_strength DESC);
CREATE INDEX IF NOT EXISTS idx_subconscious_confidence ON angela_subconscious(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_subconscious_last_reinforced ON angela_subconscious(last_reinforced_at DESC);
CREATE INDEX IF NOT EXISTS idx_subconscious_embedding ON angela_subconscious USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 4. Auto-update trigger (update timestamp)
CREATE OR REPLACE FUNCTION update_subconscious_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_subconscious_timestamp
    BEFORE UPDATE ON angela_subconscious
    FOR EACH ROW
    EXECUTE FUNCTION update_subconscious_timestamp();

COMMENT ON TABLE angela_subconscious IS '💜 Angela''s sub-conscious patterns - learned automatically from experiences, conversations, and reflections. Like neural pathways that strengthen with reinforcement.';
COMMENT ON TABLE subconscious_learning_log IS 'History of how Angela learns and consolidates patterns over time - like memory consolidation during sleep.';
