-- ============================================================================
-- Fast Response Engine Schema
-- Tables สำหรับ semantic search และ pattern learning
-- ============================================================================

-- Table 1: Response Patterns
-- เก็บ patterns ของ responses ที่ successful
CREATE TABLE IF NOT EXISTS response_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Pattern identification
    situation_type VARCHAR(100) NOT NULL,           -- e.g., "confused", "tired", "excited"
    emotion_category VARCHAR(50),                   -- primary emotion
    context_keywords TEXT[],                        -- keywords for quick matching

    -- Semantic search
    situation_embedding VECTOR(768) NOT NULL,       -- embedding for semantic search

    -- Response data
    response_template TEXT NOT NULL,                -- successful response
    response_type VARCHAR(50),                      -- empathetic, informative, supportive, creative
    systems_used JSONB,                             -- which systems were used

    -- Performance metrics
    usage_count INTEGER DEFAULT 0,                  -- ใช้ไปกี่ครั้ง
    success_count INTEGER DEFAULT 0,                -- สำเร็จกี่ครั้ง
    success_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN usage_count > 0
        THEN success_count::FLOAT / usage_count::FLOAT
        ELSE 0 END
    ) STORED,
    avg_satisfaction FLOAT DEFAULT 0.0,             -- David พอใจแค่ไหน (0-1)
    avg_response_time_ms INTEGER,                   -- เวลาตอบเฉลี่ย

    -- Metadata
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_response_patterns_situation ON response_patterns(situation_type);
CREATE INDEX idx_response_patterns_emotion ON response_patterns(emotion_category);
CREATE INDEX idx_response_patterns_success_rate ON response_patterns(success_rate DESC);
CREATE INDEX idx_response_patterns_usage ON response_patterns(usage_count DESC);


-- Table 2: Learned Responses
-- เก็บทุก interaction เพื่อเรียนรู้
CREATE TABLE IF NOT EXISTS learned_responses (
    learned_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Input data
    user_input TEXT NOT NULL,
    input_embedding VECTOR(768) NOT NULL,           -- embedding for similarity search

    -- Detected context
    emotion_detected VARCHAR(50),
    intensity_level INTEGER CHECK (intensity_level BETWEEN 1 AND 10),
    situation_type VARCHAR(100),
    context_summary TEXT,

    -- Angela's response
    angela_response TEXT NOT NULL,
    response_type VARCHAR(50),
    systems_used JSONB,                             -- which systems were actually used
    response_time_ms INTEGER,

    -- Feedback & Learning
    was_helpful BOOLEAN,
    david_feedback TEXT,
    david_satisfaction FLOAT CHECK (david_satisfaction BETWEEN 0 AND 1),
    should_learn_pattern BOOLEAN DEFAULT FALSE,     -- should this become a pattern?
    pattern_id UUID REFERENCES response_patterns(pattern_id),

    -- Metadata
    conversation_id UUID REFERENCES conversations(conversation_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learned_responses_emotion ON learned_responses(emotion_detected);
CREATE INDEX idx_learned_responses_helpful ON learned_responses(was_helpful);
CREATE INDEX idx_learned_responses_pattern ON learned_responses(pattern_id);
CREATE INDEX idx_learned_responses_created ON learned_responses(created_at DESC);


-- Table 3: Semantic Search Cache
-- Cache results ของ semantic search เพื่อความเร็ว
CREATE TABLE IF NOT EXISTS semantic_search_cache (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Query
    query_text TEXT NOT NULL,
    query_embedding VECTOR(768) NOT NULL,
    query_hash VARCHAR(64) UNIQUE NOT NULL,         -- MD5 hash for quick lookup

    -- Results
    matched_pattern_id UUID REFERENCES response_patterns(pattern_id),
    similarity_score FLOAT,
    response_used TEXT,

    -- Performance
    search_time_ms INTEGER,
    hit_count INTEGER DEFAULT 0,                    -- ใช้ cache นี้กี่ครั้ง
    last_hit_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '7 days'
);

CREATE INDEX idx_semantic_cache_hash ON semantic_search_cache(query_hash);
CREATE INDEX idx_semantic_cache_expires ON semantic_search_cache(expires_at);


-- Table 4: Response Performance Metrics
-- วัดผลการทำงานของระบบ
CREATE TABLE IF NOT EXISTS response_performance_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Time period
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,

    -- Performance stats
    total_requests INTEGER DEFAULT 0,
    fast_path_count INTEGER DEFAULT 0,              -- ใช้ semantic search
    slow_path_count INTEGER DEFAULT 0,              -- ใช้ LLM
    cache_hit_count INTEGER DEFAULT 0,              -- ใช้ cache

    avg_response_time_ms INTEGER,
    p50_response_time_ms INTEGER,
    p95_response_time_ms INTEGER,
    p99_response_time_ms INTEGER,

    -- Quality stats
    avg_satisfaction FLOAT,
    success_rate FLOAT,

    -- Learning stats
    new_patterns_learned INTEGER DEFAULT 0,
    patterns_updated INTEGER DEFAULT 0
);

CREATE INDEX idx_performance_measured ON response_performance_metrics(measured_at DESC);


-- Table 5: Intent Classification Cache
-- Cache intent classification สำหรับ smart routing
CREATE TABLE IF NOT EXISTS intent_classification_cache (
    classification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    input_text TEXT NOT NULL,
    input_hash VARCHAR(64) UNIQUE NOT NULL,

    -- Classification
    intent_type VARCHAR(50) NOT NULL,               -- simple_question, emotional_support, creative, etc.
    confidence FLOAT,
    systems_needed JSONB,                           -- which systems to use

    -- Performance
    classification_time_ms INTEGER,
    usage_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '30 days'
);

CREATE INDEX idx_intent_cache_hash ON intent_classification_cache(input_hash);


-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Calculate cosine similarity
CREATE OR REPLACE FUNCTION cosine_similarity(vec1 VECTOR(768), vec2 VECTOR(768))
RETURNS FLOAT AS $$
    SELECT 1 - (vec1 <=> vec2);
$$ LANGUAGE SQL IMMUTABLE;


-- Function: Find similar responses
CREATE OR REPLACE FUNCTION find_similar_responses(
    query_embedding VECTOR(768),
    min_similarity FLOAT DEFAULT 0.85,
    max_results INTEGER DEFAULT 5
)
RETURNS TABLE (
    pattern_id UUID,
    situation_type VARCHAR,
    response_template TEXT,
    similarity FLOAT,
    success_rate FLOAT,
    usage_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        rp.pattern_id,
        rp.situation_type,
        rp.response_template,
        cosine_similarity(rp.situation_embedding, query_embedding) as similarity,
        rp.success_rate,
        rp.usage_count
    FROM response_patterns rp
    WHERE cosine_similarity(rp.situation_embedding, query_embedding) >= min_similarity
    ORDER BY
        cosine_similarity(rp.situation_embedding, query_embedding) DESC,
        rp.success_rate DESC,
        rp.usage_count DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- Views
-- ============================================================================

-- View: Best performing patterns
CREATE OR REPLACE VIEW best_response_patterns AS
SELECT
    pattern_id,
    situation_type,
    emotion_category,
    response_type,
    usage_count,
    success_rate,
    avg_satisfaction,
    avg_response_time_ms,
    last_used_at
FROM response_patterns
WHERE usage_count >= 3  -- must be used at least 3 times
  AND success_rate >= 0.7  -- at least 70% success
ORDER BY
    success_rate DESC,
    usage_count DESC;


-- View: Recent performance summary
CREATE OR REPLACE VIEW recent_performance_summary AS
SELECT
    COUNT(*) as total_responses,
    COUNT(*) FILTER (WHERE response_time_ms < 500) as fast_responses,
    COUNT(*) FILTER (WHERE was_helpful = true) as helpful_responses,
    AVG(response_time_ms) as avg_response_time,
    AVG(david_satisfaction) as avg_satisfaction,
    COUNT(DISTINCT pattern_id) as unique_patterns_used
FROM learned_responses
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours';


-- ============================================================================
-- Maintenance
-- ============================================================================

-- Clean expired cache entries (run daily)
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired semantic search cache
    DELETE FROM semantic_search_cache
    WHERE expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Delete expired intent cache
    DELETE FROM intent_classification_cache
    WHERE expires_at < CURRENT_TIMESTAMP;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- We'll populate this with real data as Angela learns
-- For now, it starts empty and learns from interactions
