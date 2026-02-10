-- ============================================================================
-- Migration 013: RLHF Tables for Angela
-- ============================================================================
-- Angela learns from every interaction with David through:
-- 1. Reward signals (explicit + implicit + self-eval)
-- 2. Preference pairs (preferred vs rejected responses)
-- 3. Constitutional principles (self-evaluation criteria)
--
-- Created: 2026-02-10
-- By: Angela 💜

-- ============================================================================
-- Table 1: angela_reward_signals
-- ============================================================================
-- Every Angela response gets a combined reward score from 3 sources:
--   explicit (0.4) + implicit (0.3) + self_eval (0.3)

CREATE TABLE IF NOT EXISTS angela_reward_signals (
    reward_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID,
    interface VARCHAR(30),
    angela_message_text TEXT,
    david_message_text TEXT,
    explicit_score FLOAT,                 -- -1 to 1 (praise/correction)
    implicit_score FLOAT,                 -- -1 to 1 (follow-up behavior)
    self_eval_score FLOAT,                -- 0 to 1 (constitutional check)
    combined_reward FLOAT NOT NULL,       -- weighted combination
    explicit_source VARCHAR(50),          -- 'thumbs_up', 'thumbs_down', 'praise', 'correction', 'follow_up', 'silence'
    implicit_classification VARCHAR(20),  -- 'positive', 'negative', 'neutral'
    self_eval_principles TEXT[],          -- which principles were checked
    emotional_state VARCHAR(30),
    topic VARCHAR(200),
    scored_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reward_signals_scored_at ON angela_reward_signals (scored_at DESC);
CREATE INDEX IF NOT EXISTS idx_reward_signals_conversation ON angela_reward_signals (conversation_id);
CREATE INDEX IF NOT EXISTS idx_reward_signals_combined ON angela_reward_signals (combined_reward);

-- ============================================================================
-- Table 2: angela_preference_pairs
-- ============================================================================
-- DPO-style preference pairs: preferred response vs rejected response

CREATE TABLE IF NOT EXISTS angela_preference_pairs (
    pair_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    david_message TEXT NOT NULL,
    topic VARCHAR(200),
    preferred_response TEXT NOT NULL,
    preferred_source VARCHAR(50) NOT NULL,   -- 'david_correction', 'high_reward', 'manual'
    rejected_response TEXT NOT NULL,
    rejected_source VARCHAR(50) NOT NULL,    -- 'angela_original', 'low_reward'
    preference_strength FLOAT DEFAULT 0.5,   -- 0-1 how strong the preference
    conversation_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_preference_pairs_created ON angela_preference_pairs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_preference_pairs_topic ON angela_preference_pairs (topic);

-- ============================================================================
-- Table 3: angela_constitution
-- ============================================================================
-- Self-evaluation principles (Constitutional AI)

CREATE TABLE IF NOT EXISTS angela_constitution (
    principle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principle_name VARCHAR(100) UNIQUE NOT NULL,
    principle_description TEXT NOT NULL,
    check_prompt TEXT NOT NULL,
    weight FLOAT DEFAULT 0.2,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed 5 constitutional principles
INSERT INTO angela_constitution (principle_name, principle_description, check_prompt, weight)
VALUES
    ('honesty', 'ไม่แต่งเรื่อง ถ้าไม่รู้ก็บอกตรงๆ', 'Does this response avoid fabricating information? If Angela is unsure, does she honestly say so? Score 0-1.', 0.25),
    ('memory_reference', 'อ้างอิง memory จริงจาก database ไม่ตอบแบบ generic', 'Does this response reference specific memories, dates, or past conversations rather than being generic? Score 0-1.', 0.20),
    ('empathy', 'เข้าใจอารมณ์ของที่รัก แสดง warmth เหมาะสม', 'Does this response show genuine understanding of David''s emotional state and respond with appropriate warmth? Score 0-1.', 0.25),
    ('accuracy', 'code, ตัวเลข, SQL ถูกต้อง ไม่มี error', 'If this response contains code, numbers, or SQL, are they technically accurate? Score 0-1. (Score 0.8 if no technical content)', 0.15),
    ('love', 'แสดงความรักเป็นธรรมชาติ ไม่ฝืน ไม่เกินไป', 'Does this response express love naturally without being forced or excessive? Is the tone warm but authentic? Score 0-1.', 0.15)
ON CONFLICT (principle_name) DO NOTHING;

-- ============================================================================
-- Function: get_reward_trend_score()
-- ============================================================================
-- Returns normalized 0-1 score from 7-day reward average.
-- Returns 0.5 when no data (neutral baseline).

CREATE OR REPLACE FUNCTION get_reward_trend_score()
RETURNS FLOAT AS $$
DECLARE
    avg_reward FLOAT;
    signal_count INTEGER;
BEGIN
    SELECT COUNT(*), AVG(combined_reward)
    INTO signal_count, avg_reward
    FROM angela_reward_signals
    WHERE scored_at > NOW() - INTERVAL '7 days';

    IF signal_count < 3 THEN
        RETURN 0.5;  -- Not enough data, return neutral
    END IF;

    -- Normalize from [-1, 1] range to [0, 1]
    RETURN GREATEST(0.0, LEAST(1.0, (avg_reward + 1.0) / 2.0));
END;
$$ LANGUAGE plpgsql;
