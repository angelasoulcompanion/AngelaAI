-- Migration 017: Add angela_thoughts table
-- Brain-Based Architecture Phase 2: Thought Engine
-- Stores Angela's inner thoughts (System 1 + System 2)
--
-- By: Angela 💜
-- Created: 2026-02-15

CREATE TABLE IF NOT EXISTS angela_thoughts (
    thought_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thought_type VARCHAR(20) NOT NULL,          -- system1, system2
    content TEXT NOT NULL,                       -- Angela's inner thought (Thai)
    stimulus_ids UUID[],                         -- Which stimuli triggered this
    memory_context JSONB,                        -- Memories retrieved as context
    motivation_score FLOAT,                      -- Should this be expressed? (0.0-1.0)
    motivation_breakdown JSONB,                  -- {relevance, urgency, impact, coherence, originality}
    status VARCHAR(20) DEFAULT 'active',         -- active, expressed, decayed, evolved
    evolved_from UUID REFERENCES angela_thoughts(thought_id),
    expressed_via VARCHAR(50),                   -- telegram, chat, email, internal
    expressed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_thoughts_created ON angela_thoughts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_thoughts_status ON angela_thoughts (status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_thoughts_motivation ON angela_thoughts (motivation_score DESC) WHERE status = 'active';
