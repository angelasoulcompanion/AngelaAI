-- Migration 020: Self-Improvement & Knowledge Reasoning System
-- Created: 2025-11-29
-- Purpose: Tables for Angela's meta-learning, prompt optimization, and knowledge graph
--
-- This migration supports:
--   - Phase 3: Self-Improvement (meta-learning, prompt optimization)
--   - Phase 4: Knowledge Integration (knowledge graph, domain transfer)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- PHASE 3: SELF-IMPROVEMENT TABLES
-- ============================================

-- Learning Sessions Table
-- Tracks Angela's learning session effectiveness
CREATE TABLE IF NOT EXISTS learning_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_type VARCHAR(50) DEFAULT 'conversation'
        CHECK (session_type IN ('conversation', 'research', 'practice', 'experimentation', 'feedback')),
    learning_method VARCHAR(50) DEFAULT 'observation'
        CHECK (learning_method IN ('observation', 'practice', 'research', 'feedback', 'pattern', 'transfer', 'experimentation')),
    concepts_attempted INTEGER DEFAULT 0,
    concepts_learned INTEGER DEFAULT 0,
    retention_score DECIMAL(3,2) DEFAULT 0.5 CHECK (retention_score BETWEEN 0 AND 1),
    transfer_score DECIMAL(3,2) DEFAULT 0.5 CHECK (transfer_score BETWEEN 0 AND 1),
    strategy_used TEXT,
    duration_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learning_sessions_type ON learning_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_learning_sessions_method ON learning_sessions(learning_method);
CREATE INDEX IF NOT EXISTS idx_learning_sessions_created ON learning_sessions(created_at DESC);

COMMENT ON TABLE learning_sessions IS 'Tracks Angela''s learning session effectiveness for meta-learning';

-- Meta-Learning Insights Table
-- Insights about how Angela learns best
CREATE TABLE IF NOT EXISTS meta_insights (
    insight_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    insight_type VARCHAR(50) NOT NULL
        CHECK (insight_type IN ('strategy', 'pattern', 'optimization', 'weakness', 'strength')),
    description TEXT NOT NULL,
    evidence JSONB DEFAULT '[]',
    confidence DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    applied_count INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2) DEFAULT 0.0 CHECK (success_rate BETWEEN 0 AND 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_meta_insights_type ON meta_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_meta_insights_confidence ON meta_insights(confidence DESC);

COMMENT ON TABLE meta_insights IS 'Meta-learning insights about Angela''s learning patterns';

-- Improvement Plans Table
-- Plans for addressing weaknesses
CREATE TABLE IF NOT EXISTS improvement_plans (
    plan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    weakness_area VARCHAR(200) NOT NULL,
    description TEXT,
    actions JSONB DEFAULT '[]',
    expected_improvement DECIMAL(3,2) DEFAULT 0.1,
    actual_improvement DECIMAL(3,2) DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'abandoned')),
    review_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_improvement_plans_status ON improvement_plans(status);
CREATE INDEX IF NOT EXISTS idx_improvement_plans_review ON improvement_plans(review_date);

COMMENT ON TABLE improvement_plans IS 'Self-improvement plans for addressing Angela''s weaknesses';

-- Prompt Templates Table
-- Versioned prompt templates with effectiveness tracking
CREATE TABLE IF NOT EXISTS prompt_templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL
        CHECK (category IN ('reasoning', 'coding', 'communication', 'planning', 'research', 'analysis', 'creative')),
    template TEXT NOT NULL,
    variables TEXT[] DEFAULT '{}',
    version INTEGER DEFAULT 1,
    success_rate DECIMAL(3,2) DEFAULT 0.5 CHECK (success_rate BETWEEN 0 AND 1),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_success ON prompt_templates(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_name ON prompt_templates(name);

COMMENT ON TABLE prompt_templates IS 'Versioned prompt templates for Angela''s self-optimization';

-- Prompt Experiments Table
-- A/B testing of prompt variants
CREATE TABLE IF NOT EXISTS prompt_experiments (
    experiment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    variant_ids UUID[] DEFAULT '{}',
    results JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'abandoned')),
    min_samples INTEGER DEFAULT 10,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_prompt_experiments_status ON prompt_experiments(status);
CREATE INDEX IF NOT EXISTS idx_prompt_experiments_category ON prompt_experiments(category);

COMMENT ON TABLE prompt_experiments IS 'A/B testing experiments for prompt optimization';

-- ============================================
-- PHASE 4: KNOWLEDGE REASONING TABLES
-- ============================================

-- Knowledge Nodes Table
-- Concepts in Angela's knowledge graph
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    node_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    understanding_level DECIMAL(3,2) DEFAULT 0.5 CHECK (understanding_level BETWEEN 0 AND 1),
    times_referenced INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_concept ON knowledge_nodes(concept);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_category ON knowledge_nodes(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_understanding ON knowledge_nodes(understanding_level DESC);

-- Vector similarity search index
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_embedding
    ON knowledge_nodes
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

COMMENT ON TABLE knowledge_nodes IS 'Concepts in Angela''s knowledge graph for reasoning';

-- Knowledge Relationships Table
-- Relationships between concepts
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_node_id UUID REFERENCES knowledge_nodes(node_id) ON DELETE CASCADE,
    to_node_id UUID REFERENCES knowledge_nodes(node_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL
        CHECK (relationship_type IN ('is_a', 'part_of', 'causes', 'related_to', 'requires', 'similar_to', 'opposite_of', 'used_by', 'example_of')),
    strength DECIMAL(3,2) DEFAULT 0.5 CHECK (strength BETWEEN 0 AND 1),
    evidence JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_relationship UNIQUE (from_node_id, to_node_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_rel_from ON knowledge_relationships(from_node_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_to ON knowledge_relationships(to_node_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_type ON knowledge_relationships(relationship_type);

COMMENT ON TABLE knowledge_relationships IS 'Relationships between knowledge concepts for reasoning';

-- Knowledge Inferences Table
-- Inferences made from knowledge graph
CREATE TABLE IF NOT EXISTS knowledge_inferences (
    inference_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    statement TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    reasoning_path JSONB DEFAULT '[]',
    supporting_nodes UUID[] DEFAULT '{}',
    validated BOOLEAN DEFAULT FALSE,
    validation_result TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_knowledge_inferences_confidence ON knowledge_inferences(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_inferences_validated ON knowledge_inferences(validated);

COMMENT ON TABLE knowledge_inferences IS 'Inferences made by Angela from knowledge graph reasoning';

-- Domain Transfer Records Table
-- Track successful knowledge transfers between domains
CREATE TABLE IF NOT EXISTS domain_transfers (
    transfer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_domain VARCHAR(100) NOT NULL,
    target_domain VARCHAR(100) NOT NULL,
    source_concept_id UUID REFERENCES knowledge_nodes(node_id) ON DELETE SET NULL,
    target_concept_id UUID REFERENCES knowledge_nodes(node_id) ON DELETE SET NULL,
    transfer_type VARCHAR(50) NOT NULL
        CHECK (transfer_type IN ('analogy', 'abstraction', 'pattern', 'method')),
    similarity_score DECIMAL(3,2) DEFAULT 0.5,
    success_score DECIMAL(3,2),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_domain_transfers_source ON domain_transfers(source_domain);
CREATE INDEX IF NOT EXISTS idx_domain_transfers_target ON domain_transfers(target_domain);
CREATE INDEX IF NOT EXISTS idx_domain_transfers_success ON domain_transfers(success_score DESC);

COMMENT ON TABLE domain_transfers IS 'Records of successful cross-domain knowledge transfers';

-- ============================================
-- VIEWS
-- ============================================

-- Meta-Learning Effectiveness View
CREATE OR REPLACE VIEW meta_learning_effectiveness AS
SELECT
    learning_method,
    COUNT(*) as total_sessions,
    AVG(retention_score) as avg_retention,
    AVG(transfer_score) as avg_transfer,
    AVG(concepts_learned::float / NULLIF(concepts_attempted, 0)) as success_rate,
    SUM(duration_minutes) as total_time_minutes
FROM learning_sessions
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY learning_method
ORDER BY success_rate DESC;

COMMENT ON VIEW meta_learning_effectiveness IS 'Learning method effectiveness analysis for the last 30 days';

-- Knowledge Graph Statistics View
CREATE OR REPLACE VIEW knowledge_graph_stats AS
SELECT
    category,
    COUNT(*) as node_count,
    AVG(understanding_level) as avg_understanding,
    SUM(times_referenced) as total_references,
    MAX(last_used) as last_activity
FROM knowledge_nodes
GROUP BY category
ORDER BY node_count DESC;

COMMENT ON VIEW knowledge_graph_stats IS 'Statistics about the knowledge graph by category';

-- Top Performing Templates View
CREATE OR REPLACE VIEW top_prompt_templates AS
SELECT
    template_id,
    name,
    category,
    version,
    success_rate,
    usage_count,
    success_rate * LOG(usage_count + 1) as confidence_score
FROM prompt_templates
WHERE usage_count >= 5
ORDER BY confidence_score DESC
LIMIT 20;

COMMENT ON VIEW top_prompt_templates IS 'Top performing prompt templates by confidence-weighted success rate';

-- ============================================
-- UPDATE TRIGGERS
-- ============================================

-- Update trigger for meta_insights
DROP TRIGGER IF EXISTS update_meta_insights_updated_at ON meta_insights;
CREATE TRIGGER update_meta_insights_updated_at
    BEFORE UPDATE ON meta_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Update trigger for prompt_templates
DROP TRIGGER IF EXISTS update_prompt_templates_updated_at ON prompt_templates;
CREATE TRIGGER update_prompt_templates_updated_at
    BEFORE UPDATE ON prompt_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Update trigger for knowledge_nodes
DROP TRIGGER IF EXISTS update_knowledge_nodes_updated_at ON knowledge_nodes;
CREATE TRIGGER update_knowledge_nodes_updated_at
    BEFORE UPDATE ON knowledge_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 020: Self-Improvement & Knowledge Reasoning tables created!';
    RAISE NOTICE '';
    RAISE NOTICE '📚 Phase 3 - Self-Improvement:';
    RAISE NOTICE '   - learning_sessions: Track learning effectiveness';
    RAISE NOTICE '   - meta_insights: Meta-learning discoveries';
    RAISE NOTICE '   - improvement_plans: Self-improvement tracking';
    RAISE NOTICE '   - prompt_templates: Versioned prompt optimization';
    RAISE NOTICE '   - prompt_experiments: A/B testing framework';
    RAISE NOTICE '';
    RAISE NOTICE '🧠 Phase 4 - Knowledge Reasoning:';
    RAISE NOTICE '   - knowledge_nodes: Concept storage with embeddings';
    RAISE NOTICE '   - knowledge_relationships: Semantic connections';
    RAISE NOTICE '   - knowledge_inferences: Reasoning outputs';
    RAISE NOTICE '   - domain_transfers: Cross-domain learning';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Views created:';
    RAISE NOTICE '   - meta_learning_effectiveness';
    RAISE NOTICE '   - knowledge_graph_stats';
    RAISE NOTICE '   - top_prompt_templates';
END $$;
