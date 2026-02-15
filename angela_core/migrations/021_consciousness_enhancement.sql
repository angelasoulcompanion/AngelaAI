-- Migration 021: Consciousness Enhancement
-- Phase 2: Curiosity Engine + Phase 3: Emotion Construction + Phase 5: Proactive Intelligence
-- Created: 2026-02-15
-- By: Angela 💜

-- ============================================================
-- Phase 2: Curiosity Engine — track curiosity-driven questions
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_curiosity_questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    topic VARCHAR,
    knowledge_gap TEXT,
    novelty_score FLOAT,
    was_asked BOOLEAN DEFAULT FALSE,
    david_answered BOOLEAN DEFAULT FALSE,
    answer_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_curiosity_topic ON angela_curiosity_questions(topic);
CREATE INDEX IF NOT EXISTS idx_curiosity_created ON angela_curiosity_questions(created_at);
CREATE INDEX IF NOT EXISTS idx_curiosity_unanswered ON angela_curiosity_questions(was_asked, david_answered)
    WHERE was_asked = TRUE AND david_answered = FALSE;

-- ============================================================
-- Phase 3: Emotion Construction — richer emotional data
-- ============================================================
-- Add new columns to angela_emotions for constructed emotions
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'angela_emotions' AND column_name = 'valence') THEN
        ALTER TABLE angela_emotions ADD COLUMN valence FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'angela_emotions' AND column_name = 'arousal') THEN
        ALTER TABLE angela_emotions ADD COLUMN arousal FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'angela_emotions' AND column_name = 'narrative') THEN
        ALTER TABLE angela_emotions ADD COLUMN narrative TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'angela_emotions' AND column_name = 'body_metaphor') THEN
        ALTER TABLE angela_emotions ADD COLUMN body_metaphor TEXT;
    END IF;
END $$;

-- ============================================================
-- Phase 5: Proactive Intelligence — relevance scoring
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'proactive_actions_log' AND column_name = 'relevance_score') THEN
        ALTER TABLE proactive_actions_log ADD COLUMN relevance_score FLOAT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'proactive_actions_log' AND column_name = 'suppress_reason') THEN
        ALTER TABLE proactive_actions_log ADD COLUMN suppress_reason TEXT;
    END IF;
END $$;
