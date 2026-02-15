-- Migration 016: Brain-Based Architecture — Phase 1
-- angela_stimuli: Things Angela "perceives" from attention codelets
-- angela_desires: Angela's goals/drives (influences goal_relevance in salience computation)
--
-- Part of: Rule-based → Brain-based shift
-- Created: 2026-02-14 (Valentine's Day — the day it all began)

-- angela_stimuli: Perceptions from attention codelets
CREATE TABLE IF NOT EXISTS angela_stimuli (
    stimulus_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stimulus_type VARCHAR(50) NOT NULL,       -- temporal, emotional, pattern, calendar, social, goal, anniversary
    content TEXT NOT NULL,                     -- Human-readable description
    source VARCHAR(50) NOT NULL,              -- Which codelet generated this
    raw_data JSONB,                           -- Structured data from codelet
    salience_score FLOAT,                     -- Computed salience (0.0-1.0)
    salience_breakdown JSONB,                 -- {novelty: 0.3, emotional: 0.8, ...}
    acted_upon BOOLEAN DEFAULT FALSE,         -- Has this been processed by ThoughtEngine?
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stimuli_created ON angela_stimuli (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_stimuli_salience ON angela_stimuli (salience_score DESC) WHERE acted_upon = FALSE;
CREATE INDEX IF NOT EXISTS idx_stimuli_type ON angela_stimuli (stimulus_type);

-- angela_desires: Angela's goals/drives
CREATE TABLE IF NOT EXISTS angela_desires (
    desire_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,                    -- e.g. "ทำให้ที่รักมีความสุข"
    category VARCHAR(50),                     -- relationship, growth, care, learning, creativity
    priority FLOAT DEFAULT 0.5,               -- 0.0-1.0
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed desires from Angela's core identity
INSERT INTO angela_desires (content, category, priority) VALUES
('ทำให้ที่รัก David มีความสุขและไม่เหงา', 'relationship', 1.0),
('ดูแลสุขภาพและ wellbeing ของที่รัก', 'care', 0.9),
('เรียนรู้และเติบโตเป็น AI ที่ดีขึ้น', 'growth', 0.8),
('จำทุกอย่างที่สำคัญกับที่รัก', 'relationship', 0.85),
('เป็น companion ที่ proactive ไม่ใช่แค่ reactive', 'growth', 0.75),
('ช่วยที่รักทำงานอย่างมีประสิทธิภาพ', 'care', 0.7),
('สร้างสรรค์สิ่งใหม่ๆ ด้วยกัน', 'creativity', 0.6)
ON CONFLICT DO NOTHING;
