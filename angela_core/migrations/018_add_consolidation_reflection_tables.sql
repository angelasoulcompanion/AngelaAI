-- Migration 018: Add memory consolidation + reflection tables
-- Brain-Based Architecture Phase 4+5
--
-- Phase 4: Memory Consolidation — episodic → semantic (like brain during sleep)
-- Phase 5: Reflection Engine — high-level abstractions from recent experiences
--
-- By: Angela 💜
-- Created: 2026-02-15

-- ============================================================
-- MEMORY CONSOLIDATION LOG
-- Tracks what episodic memories were consolidated into what semantic knowledge
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_consolidation_log (
    consolidation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(30) NOT NULL,        -- conversations, emotions, thoughts
    source_count INT NOT NULL,               -- How many episodes were consolidated
    topic_cluster VARCHAR(200),              -- Topic/theme of the cluster
    abstraction TEXT NOT NULL,               -- LLM-generated insight/pattern
    target_type VARCHAR(30),                 -- knowledge_node, learning, preference
    target_id UUID,                          -- ID of the created/updated target
    confidence FLOAT DEFAULT 0.5,            -- How confident is this abstraction
    source_ids UUID[],                       -- Original episode IDs
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consolidation_created ON memory_consolidation_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_consolidation_topic ON memory_consolidation_log (topic_cluster);

-- ============================================================
-- ANGELA REFLECTIONS
-- High-level reflections that emerge from accumulated experiences
-- Stanford Generative Agents style: experiences → salient questions → insights
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_reflections (
    reflection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reflection_type VARCHAR(30) NOT NULL,    -- insight, question, realization, growth
    content TEXT NOT NULL,                   -- The reflection itself (Thai)
    trigger_summary TEXT,                    -- What triggered this reflection
    importance_sum FLOAT,                    -- Sum of importance that triggered it
    source_thought_ids UUID[],               -- Thoughts that contributed
    source_emotion_ids UUID[],               -- Emotions that contributed
    depth_level INT DEFAULT 1,               -- 1=first-order, 2=reflection-on-reflection
    parent_reflection_id UUID REFERENCES angela_reflections(reflection_id),
    status VARCHAR(20) DEFAULT 'active',     -- active, integrated, superseded
    integrated_into UUID,                    -- knowledge_node_id if integrated
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reflections_created ON angela_reflections (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reflections_status ON angela_reflections (status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_reflections_depth ON angela_reflections (depth_level);
