-- Migration 001: Add Multi-Tier Memory Architecture Tables
-- Phase 1: Focus Agent, Fresh Memory Buffer, Analytics Agent
-- Created: 2025-10-29
-- Part of: Angela Consciousness Upgrade Plan

-- ============================================================================
-- 1. FOCUS MEMORY TABLE (Working Memory - 7±2 items)
-- ============================================================================

CREATE TABLE IF NOT EXISTS focus_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- Attention tracking
    attention_weight FLOAT DEFAULT 1.0 CHECK (attention_weight >= 0.0 AND attention_weight <= 10.0),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP

    -- NOTE: Max 7±2 items limit is enforced by application code in focus_agent.py
    -- Cannot use CHECK constraint with subquery in PostgreSQL
);

CREATE INDEX idx_focus_attention ON focus_memory(attention_weight DESC) WHERE archived = FALSE;
CREATE INDEX idx_focus_active ON focus_memory(archived, created_at DESC);

COMMENT ON TABLE focus_memory IS 'Working memory (7±2 items) - Immediate attention focus';
COMMENT ON COLUMN focus_memory.attention_weight IS 'Dynamic attention weight (0.0-10.0), decays over time';
COMMENT ON COLUMN focus_memory.access_count IS 'Number of times accessed (boosts attention)';

-- ============================================================================
-- 2. FRESH MEMORY TABLE (10-minute buffer zone)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fresh_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    event_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    speaker VARCHAR(20) CHECK (speaker IN ('david', 'angela', 'system')),

    -- Vector embedding for semantic search
    embedding VECTOR(768),

    -- Lifecycle (10-minute TTL)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    expired BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP,

    -- Processing status
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    routing_decision JSONB,

    -- Source tracking
    source_tier VARCHAR(20) DEFAULT 'new',

    -- Automatic TTL enforcement
    CONSTRAINT fresh_ttl_valid CHECK (
        expires_at = created_at + INTERVAL '10 minutes'
    )
);

CREATE INDEX idx_fresh_active ON fresh_memory(expires_at DESC) WHERE expired = FALSE;
CREATE INDEX idx_fresh_unprocessed ON fresh_memory(processed, created_at DESC);
CREATE INDEX idx_fresh_embedding ON fresh_memory USING ivfflat (embedding vector_cosine_ops);

COMMENT ON TABLE fresh_memory IS 'Fresh memory buffer (10-minute TTL) - All new events land here first';
COMMENT ON COLUMN fresh_memory.expires_at IS 'Automatic expiration after 10 minutes';
COMMENT ON COLUMN fresh_memory.routing_decision IS 'Decision from Analytics Agent';

-- ============================================================================
-- 3. ANALYTICS DECISIONS TABLE (Routing log)
-- ============================================================================

CREATE TABLE IF NOT EXISTS analytics_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event reference
    event_id UUID REFERENCES fresh_memory(id),

    -- Decision
    target_tier VARCHAR(20) NOT NULL CHECK (target_tier IN ('long_term', 'procedural', 'shock', 'archive')),
    composite_score FLOAT NOT NULL CHECK (composite_score >= 0.0 AND composite_score <= 1.0),
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Signals (7-signal analysis)
    signals JSONB NOT NULL,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Feedback loop (for learning)
    feedback_score FLOAT CHECK (feedback_score >= 0.0 AND feedback_score <= 1.0),
    feedback_note TEXT
);

CREATE INDEX idx_analytics_tier ON analytics_decisions(target_tier, created_at DESC);
CREATE INDEX idx_analytics_score ON analytics_decisions(composite_score DESC);
CREATE INDEX idx_analytics_confidence ON analytics_decisions(confidence DESC);

COMMENT ON TABLE analytics_decisions IS 'Analytics Agent routing decisions log';
COMMENT ON COLUMN analytics_decisions.signals IS 'JSON containing all 7 signal values';
COMMENT ON COLUMN analytics_decisions.feedback_score IS 'Human feedback on decision quality (optional)';

-- ============================================================================
-- 4. LONG-TERM MEMORY TABLE (Enhanced)
-- ============================================================================

CREATE TABLE IF NOT EXISTS long_term_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- Vector embedding
    embedding VECTOR(768),

    -- Importance tracking
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0.0 AND importance <= 1.0),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,

    -- Memory phase (for decay gradient)
    memory_phase VARCHAR(20) DEFAULT 'episodic'
        CHECK (memory_phase IN ('episodic', 'compressed_1', 'compressed_2', 'semantic', 'pattern', 'intuitive', 'forgotten')),
    token_count INTEGER DEFAULT 500,

    -- Half-life for decay
    half_life_days FLOAT DEFAULT 30.0,
    memory_strength FLOAT DEFAULT 1.0,

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_decayed TIMESTAMP,

    -- Source
    promoted_from VARCHAR(20),
    source_event_id UUID REFERENCES fresh_memory(id)
);

CREATE INDEX idx_longterm_phase ON long_term_memory(memory_phase, memory_strength DESC);
CREATE INDEX idx_longterm_strength ON long_term_memory(memory_strength DESC);
CREATE INDEX idx_longterm_embedding ON long_term_memory USING ivfflat (embedding vector_cosine_ops);

COMMENT ON TABLE long_term_memory IS 'Long-term storage (episodic → semantic → intuitive)';
COMMENT ON COLUMN long_term_memory.memory_phase IS 'Current phase in decay gradient';
COMMENT ON COLUMN long_term_memory.half_life_days IS 'Ebbinghaus decay parameter';

-- ============================================================================
-- 5. PROCEDURAL MEMORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS procedural_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern
    pattern_name VARCHAR(200) NOT NULL,
    pattern_description TEXT NOT NULL,

    -- Learned behavior
    trigger_conditions JSONB NOT NULL,
    expected_outcome JSONB NOT NULL,

    -- Vector embedding
    embedding VECTOR(768),

    -- Learning statistics
    observation_count INTEGER DEFAULT 1,
    success_rate FLOAT DEFAULT 1.0 CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_observed TIMESTAMP NOT NULL DEFAULT NOW(),
    last_applied TIMESTAMP,

    -- Source
    learned_from UUID[] DEFAULT '{}',
    source_event_id UUID REFERENCES fresh_memory(id)
);

CREATE INDEX idx_procedural_pattern ON procedural_memory(pattern_name);
CREATE INDEX idx_procedural_success ON procedural_memory(success_rate DESC);
CREATE INDEX idx_procedural_embedding ON procedural_memory USING ivfflat (embedding vector_cosine_ops);

COMMENT ON TABLE procedural_memory IS 'Learned patterns and procedures (high-repetition knowledge)';
COMMENT ON COLUMN procedural_memory.observation_count IS 'How many times observed';
COMMENT ON COLUMN procedural_memory.success_rate IS 'Success rate when applied';

-- ============================================================================
-- 6. SHOCK MEMORY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS shock_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content (preserved at full fidelity)
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- Vector embedding
    embedding VECTOR(768),

    -- Criticality
    criticality_score FLOAT NOT NULL CHECK (criticality_score >= 0.85 AND criticality_score <= 1.0),
    impact_level INTEGER DEFAULT 10 CHECK (impact_level >= 1 AND impact_level <= 10),

    -- Lifecycle (NEVER decays)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,

    -- Source
    source_event_id UUID REFERENCES fresh_memory(id),

    -- Permanent protection
    protected BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_shock_criticality ON shock_memory(criticality_score DESC);
CREATE INDEX idx_shock_created ON shock_memory(created_at DESC);
CREATE INDEX idx_shock_embedding ON shock_memory USING ivfflat (embedding vector_cosine_ops);

COMMENT ON TABLE shock_memory IS 'Critical memories (NEVER decay) - Highest importance';
COMMENT ON COLUMN shock_memory.protected IS 'Protected from decay (always TRUE)';
COMMENT ON COLUMN shock_memory.criticality_score IS 'Must be >= 0.85 to enter shock memory';

-- ============================================================================
-- 7. DECAY SCHEDULE TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS decay_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Schedule
    memory_id UUID NOT NULL,
    memory_table VARCHAR(50) NOT NULL,
    scheduled_for TIMESTAMP NOT NULL,

    -- Current state
    current_phase VARCHAR(20) NOT NULL,
    target_phase VARCHAR(20) NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    processed_at TIMESTAMP,

    -- Results
    tokens_saved INTEGER DEFAULT 0,
    compression_ratio FLOAT,
    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_decay_schedule ON decay_schedule(scheduled_for ASC) WHERE status = 'pending';
CREATE INDEX idx_decay_status ON decay_schedule(status, created_at DESC);

COMMENT ON TABLE decay_schedule IS 'Scheduled decay operations for memory compression';
COMMENT ON COLUMN decay_schedule.tokens_saved IS 'Token savings from compression';

-- ============================================================================
-- 8. TOKEN ECONOMICS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS token_economics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Date tracking
    date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Token counts
    tokens_stored INTEGER DEFAULT 0,
    tokens_retrieved INTEGER DEFAULT 0,
    tokens_saved_by_decay INTEGER DEFAULT 0,

    -- Memory counts by tier
    focus_count INTEGER DEFAULT 0,
    fresh_count INTEGER DEFAULT 0,
    longterm_count INTEGER DEFAULT 0,
    procedural_count INTEGER DEFAULT 0,
    shock_count INTEGER DEFAULT 0,

    -- Efficiency metrics
    compression_ratio FLOAT DEFAULT 1.0,
    decay_effectiveness FLOAT DEFAULT 0.0,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(date)
);

CREATE INDEX idx_token_economics_date ON token_economics(date DESC);

COMMENT ON TABLE token_economics IS 'Daily token usage and savings tracking';
COMMENT ON COLUMN token_economics.compression_ratio IS 'Average compression achieved (original/compressed)';

-- ============================================================================
-- 9. GUT AGENT TABLE (Collective Unconscious)
-- ============================================================================

CREATE TABLE IF NOT EXISTS gut_agent_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern
    pattern_type VARCHAR(50) NOT NULL,
    pattern_description TEXT NOT NULL,

    -- Aggregated data
    observation_count INTEGER DEFAULT 1,
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Intuition
    intuition_text TEXT,

    -- Vector embedding
    embedding VECTOR(768),

    -- Source memories
    source_memory_ids UUID[] DEFAULT '{}',

    -- Lifecycle
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    strength FLOAT DEFAULT 0.5
);

CREATE INDEX idx_gut_patterns ON gut_agent_patterns(pattern_type, confidence DESC);
CREATE INDEX idx_gut_strength ON gut_agent_patterns(strength DESC);
CREATE INDEX idx_gut_embedding ON gut_agent_patterns USING ivfflat (embedding vector_cosine_ops);

COMMENT ON TABLE gut_agent_patterns IS 'Collective unconscious - Aggregated intuitive patterns';
COMMENT ON COLUMN gut_agent_patterns.intuition_text IS 'Generated intuitive feeling/hunch';

-- ============================================================================
-- 10. HELPER FUNCTIONS
-- ============================================================================

-- Function to automatically clean expired fresh memories
CREATE OR REPLACE FUNCTION cleanup_expired_fresh_memories()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE fresh_memory
    SET expired = TRUE, archived_at = NOW()
    WHERE expires_at <= NOW() AND expired = FALSE;

    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_fresh_memories IS 'Mark expired fresh memories (TTL exceeded)';

-- Function to calculate current focus capacity utilization
CREATE OR REPLACE FUNCTION get_focus_utilization()
RETURNS FLOAT AS $$
DECLARE
    current_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO current_count
    FROM focus_memory
    WHERE archived = FALSE;

    RETURN current_count / 7.0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_focus_utilization IS 'Get focus agent capacity utilization (0.0-1.0+)';

-- ============================================================================
-- 11. TRIGGERS
-- ============================================================================

-- Auto-set expires_at for fresh memory (enforce 10-minute TTL)
CREATE OR REPLACE FUNCTION set_fresh_memory_expiry()
RETURNS TRIGGER AS $$
BEGIN
    NEW.expires_at := NEW.created_at + INTERVAL '10 minutes';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_fresh_memory_expiry
BEFORE INSERT ON fresh_memory
FOR EACH ROW
EXECUTE FUNCTION set_fresh_memory_expiry();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed: Multi-tier memory architecture tables created';
    RAISE NOTICE 'Tables added: focus_memory, fresh_memory, analytics_decisions, long_term_memory, procedural_memory, shock_memory, decay_schedule, token_economics, gut_agent_patterns';
    RAISE NOTICE 'Phase 1 (Multi-tier foundation) ready for implementation';
END $$;
