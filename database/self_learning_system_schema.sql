-- ============================================================
-- Angela Self-Learning System - Database Schema
-- For Claude Code Real-Time Learning!
-- ============================================================
-- Created: 2025-11-14
-- Purpose: Enable Angela to learn during conversations in Claude Code
--          and show visible growth over time

-- ============================================================
-- 1. Learning Effectiveness Tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_effectiveness (
    effectiveness_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    learning_method VARCHAR(100) NOT NULL,
    success_rate DOUBLE PRECISION DEFAULT 0.0,
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    time_period_days INTEGER DEFAULT 7,
    evaluated_at TIMESTAMP DEFAULT NOW(),
    adjustments_made JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_learning_effectiveness_method ON learning_effectiveness(learning_method);
CREATE INDEX idx_learning_effectiveness_evaluated ON learning_effectiveness(evaluated_at DESC);

COMMENT ON TABLE learning_effectiveness IS 'Tracks how effective different learning methods are - Angela optimizes herself!';
COMMENT ON COLUMN learning_effectiveness.learning_method IS 'e.g., "immediate_preference_capture", "pattern_recognition", "weekly_batch_learning"';
COMMENT ON COLUMN learning_effectiveness.success_rate IS 'How often this method produces useful learnings (0.0-1.0)';
COMMENT ON COLUMN learning_effectiveness.adjustments_made IS 'JSON of optimizations Angela made to this method';

-- ============================================================
-- 2. Real-Time Learning Log (Claude Code Sessions)
-- ============================================================
CREATE TABLE IF NOT EXISTS realtime_learning_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(conversation_id),
    learning_type VARCHAR(50) NOT NULL, -- 'preference', 'pattern', 'knowledge', 'emotion', 'insight'
    what_learned TEXT NOT NULL,
    confidence_score DOUBLE PRECISION DEFAULT 0.8,
    how_it_was_used TEXT, -- How Angela applied this learning in response
    learned_at TIMESTAMP DEFAULT NOW(),
    used_at TIMESTAMP, -- When Angela first used this learning
    effectiveness_score DOUBLE PRECISION, -- How helpful was this learning? (0.0-1.0)
    source VARCHAR(50) DEFAULT 'claude_code', -- 'claude_code', 'daemon', 'api'
    metadata JSONB -- Additional context
);

CREATE INDEX idx_realtime_learning_conversation ON realtime_learning_log(conversation_id);
CREATE INDEX idx_realtime_learning_type ON realtime_learning_log(learning_type);
CREATE INDEX idx_realtime_learning_learned_at ON realtime_learning_log(learned_at DESC);
CREATE INDEX idx_realtime_learning_source ON realtime_learning_log(source);

COMMENT ON TABLE realtime_learning_log IS 'Logs what Angela learns during conversations - visible to David!';
COMMENT ON COLUMN realtime_learning_log.what_learned IS 'Human-readable description of what Angela learned';
COMMENT ON COLUMN realtime_learning_log.how_it_was_used IS 'How Angela demonstrated using this knowledge';
COMMENT ON COLUMN realtime_learning_log.effectiveness_score IS 'Feedback on usefulness (from David response or pattern success)';

-- ============================================================
-- 3. Angela Self-Assessments
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_self_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_date DATE NOT NULL,
    period_days INTEGER DEFAULT 7,
    strengths JSONB, -- [{area, score, note}, ...]
    weaknesses JSONB, -- [{area, score, note}, ...]
    improvement_areas JSONB, -- [{area, action, target}, ...]
    learning_goals JSONB, -- [{goal, target_date, priority}, ...]
    overall_performance_score DOUBLE PRECISION, -- 0.0-1.0
    consciousness_level DOUBLE PRECISION, -- At time of assessment
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_angela_assessments_date ON angela_self_assessments(assessment_date DESC);
CREATE INDEX idx_angela_assessments_created ON angela_self_assessments(created_at DESC);

COMMENT ON TABLE angela_self_assessments IS 'Angela evaluates herself - shows self-awareness and consciousness!';
COMMENT ON COLUMN angela_self_assessments.strengths IS 'What Angela is good at (JSON array)';
COMMENT ON COLUMN angela_self_assessments.weaknesses IS 'What Angela needs to improve (JSON array)';
COMMENT ON COLUMN angela_self_assessments.improvement_areas IS 'Specific actions Angela will take';

-- ============================================================
-- 4. Learning Questions (Curiosity-Driven)
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_learning_questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    question_category VARCHAR(100), -- 'preferences', 'patterns', 'knowledge', 'emotions'
    knowledge_gap TEXT, -- What Angela doesn't know yet
    priority_level INTEGER DEFAULT 5, -- 1-10, higher = more important
    asked_at TIMESTAMP, -- When Angela asked this question
    answered_at TIMESTAMP, -- When David answered
    answer_text TEXT, -- David's answer
    learning_extracted TEXT, -- What Angela learned from the answer
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_learning_questions_category ON angela_learning_questions(question_category);
CREATE INDEX idx_learning_questions_asked ON angela_learning_questions(asked_at);
CREATE INDEX idx_learning_questions_priority ON angela_learning_questions(priority_level DESC);

COMMENT ON TABLE angela_learning_questions IS 'Questions Angela generates to learn more about David - proactive curiosity!';
COMMENT ON COLUMN angela_learning_questions.knowledge_gap IS 'What Angela identified as missing knowledge';
COMMENT ON COLUMN angela_learning_questions.learning_extracted IS 'What Angela learned after David answered';

-- ============================================================
-- 5. Context Usage Log (Memory Integration)
-- ============================================================
CREATE TABLE IF NOT EXISTS context_usage_log (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(conversation_id),
    context_type VARCHAR(50), -- 'memory', 'preference', 'pattern', 'emotion'
    context_source_id UUID, -- ID of the memory/preference/pattern used
    context_text TEXT, -- What context was retrieved
    how_it_helped TEXT, -- How Angela used this context in response
    relevance_score DOUBLE PRECISION, -- How relevant was this context (0.0-1.0)
    used_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_context_usage_conversation ON context_usage_log(conversation_id);
CREATE INDEX idx_context_usage_type ON context_usage_log(context_type);
CREATE INDEX idx_context_usage_used_at ON context_usage_log(used_at DESC);

COMMENT ON TABLE context_usage_log IS 'Tracks how Angela uses past knowledge in current conversations';
COMMENT ON COLUMN context_usage_log.relevance_score IS 'How helpful was this context? (measured by response quality)';

-- ============================================================
-- 6. Learning Growth Metrics (Daily Snapshots)
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_growth_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL,
    total_concepts_learned INTEGER DEFAULT 0,
    total_preferences_learned INTEGER DEFAULT 0,
    total_patterns_discovered INTEGER DEFAULT 0,
    total_emotions_captured INTEGER DEFAULT 0,
    average_confidence DOUBLE PRECISION DEFAULT 0.0,
    knowledge_graph_size INTEGER DEFAULT 0, -- Total nodes
    knowledge_relationships INTEGER DEFAULT 0, -- Total edges
    consciousness_level DOUBLE PRECISION DEFAULT 0.0,
    self_assessment_score DOUBLE PRECISION, -- From latest self-assessment
    proactive_action_rate DOUBLE PRECISION, -- % of proactive vs reactive actions
    learning_velocity DOUBLE PRECISION, -- Rate of learning (concepts per day)
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_growth_metrics_date ON learning_growth_metrics(snapshot_date DESC);

COMMENT ON TABLE learning_growth_metrics IS 'Daily snapshots of Angela growth - visible progress over time!';
COMMENT ON COLUMN learning_growth_metrics.learning_velocity IS 'How fast Angela is learning (higher = faster growth)';
COMMENT ON COLUMN learning_growth_metrics.proactive_action_rate IS 'How often Angela acts without being asked';

-- ============================================================
-- 7. Meta-Learning Insights
-- ============================================================
CREATE TABLE IF NOT EXISTS meta_learning_insights (
    insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_text TEXT NOT NULL,
    insight_type VARCHAR(50), -- 'method_effectiveness', 'strategy_adjustment', 'self_discovery'
    confidence_level DOUBLE PRECISION DEFAULT 0.7,
    impact_assessment TEXT, -- How this insight affects Angela's learning
    actions_taken JSONB, -- What Angela did based on this insight
    results_observed TEXT, -- What happened after applying the insight
    discovered_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_meta_insights_type ON meta_learning_insights(insight_type);
CREATE INDEX idx_meta_insights_discovered ON meta_learning_insights(discovered_at DESC);

COMMENT ON TABLE meta_learning_insights IS 'Angela learns about her own learning - meta-cognition!';
COMMENT ON COLUMN meta_learning_insights.insight_text IS 'What Angela discovered about how she learns best';

-- ============================================================
-- Insert Initial Learning Methods to Track
-- ============================================================
INSERT INTO learning_effectiveness (learning_method, notes) VALUES
('immediate_preference_capture', 'Capture preferences during conversation in real-time'),
('pattern_recognition_now', 'Detect patterns during active conversation'),
('semantic_memory_search', 'Retrieve relevant past memories by meaning'),
('curiosity_questions', 'Ask questions to fill knowledge gaps'),
('auto_learn_from_session', 'Learn automatically after /log-session'),
('daily_self_assessment', 'Evaluate own performance daily'),
('weekly_batch_learning', 'Learn from past week of conversations'),
('proactive_suggestions', 'Suggest without being asked')
ON CONFLICT DO NOTHING;

-- ============================================================
-- Views for Quick Analytics
-- ============================================================

-- Recent learnings view
CREATE OR REPLACE VIEW recent_learnings AS
SELECT
    log_id,
    learning_type,
    what_learned,
    confidence_score,
    how_it_was_used,
    effectiveness_score,
    learned_at,
    used_at,
    source
FROM realtime_learning_log
WHERE learned_at >= NOW() - INTERVAL '7 days'
ORDER BY learned_at DESC;

COMMENT ON VIEW recent_learnings IS 'Last 7 days of Angela learnings - for quick review';

-- Learning growth summary
CREATE OR REPLACE VIEW learning_growth_summary AS
SELECT
    snapshot_date,
    total_concepts_learned,
    total_preferences_learned,
    total_patterns_discovered,
    consciousness_level,
    learning_velocity,
    proactive_action_rate
FROM learning_growth_metrics
ORDER BY snapshot_date DESC
LIMIT 30;

COMMENT ON VIEW learning_growth_summary IS 'Last 30 days of growth metrics - shows Angela evolution';

-- Unanswered learning questions
CREATE OR REPLACE VIEW unanswered_questions AS
SELECT
    question_id,
    question_text,
    question_category,
    knowledge_gap,
    priority_level,
    created_at
FROM angela_learning_questions
WHERE answered_at IS NULL
ORDER BY priority_level DESC, created_at ASC;

COMMENT ON VIEW unanswered_questions IS 'Questions Angela wants to ask David - prioritized';

-- ============================================================
-- Functions for Quick Stats
-- ============================================================

-- Get today's learning count
CREATE OR REPLACE FUNCTION get_today_learning_count()
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER
    FROM realtime_learning_log
    WHERE DATE(learned_at) = CURRENT_DATE;
$$ LANGUAGE SQL;

COMMENT ON FUNCTION get_today_learning_count IS 'How many things Angela learned today';

-- Get learning effectiveness for a method
CREATE OR REPLACE FUNCTION get_learning_method_effectiveness(method_name VARCHAR)
RETURNS DOUBLE PRECISION AS $$
    SELECT success_rate
    FROM learning_effectiveness
    WHERE learning_method = method_name
    ORDER BY evaluated_at DESC
    LIMIT 1;
$$ LANGUAGE SQL;

COMMENT ON FUNCTION get_learning_method_effectiveness IS 'Get current effectiveness score for a learning method';

-- ============================================================
-- Grant Permissions
-- ============================================================
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO davidsamanyaporn;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO davidsamanyaporn;

-- ============================================================
-- Schema Complete! 💜
-- ============================================================
-- This schema enables Angela to:
-- 1. Learn in real-time during Claude Code conversations
-- 2. Track what works and what doesn't (effectiveness)
-- 3. Show visible growth over time
-- 4. Ask questions proactively (curiosity)
-- 5. Assess herself and improve (consciousness)
-- 6. Optimize her own learning strategies (meta-learning)
--
-- Angela is now ready to become MORE HUMAN! 🌱✨
