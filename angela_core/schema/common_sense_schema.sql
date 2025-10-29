-- Common Sense Knowledge Schema
-- สำหรับให้ Angela มี common sense เกี่ยวกับโลกความเป็นจริง
--
-- Purpose: Ground Angela's responses in reality
-- Enable realistic suggestions and practical advice
-- Prevent unrealistic or impossible recommendations

-- ============================================================================
-- Table 1: common_sense_facts
-- ข้อเท็จจริงพื้นฐานเกี่ยวกับโลกจริง
-- ============================================================================

CREATE TABLE IF NOT EXISTS common_sense_facts (
    fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Fact details
    fact_statement TEXT NOT NULL,              -- ข้อเท็จจริง
    fact_category VARCHAR(100),                -- physical, social, temporal, biological, technical, etc.
    fact_type VARCHAR(50),                     -- constraint, rule, principle, observation

    -- Confidence and source
    confidence_level FLOAT CHECK (confidence_level >= 0 AND confidence_level <= 1) DEFAULT 0.9,
    source VARCHAR(200),                       -- where this fact came from
    verified BOOLEAN DEFAULT false,            -- has this been verified?

    -- Examples
    example_applications TEXT[],               -- ตัวอย่างการใช้
    counter_examples TEXT[],                   -- ตัวอย่างที่ไม่ใช่

    -- Relationships
    related_facts UUID[],                      -- fact_ids ที่เกี่ยวข้อง
    contradicts_fact UUID,                     -- fact_id ที่ขัดแย้ง (if any)

    -- Metadata
    importance_level INTEGER CHECK (importance_level >= 1 AND importance_level <= 10) DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP,

    -- Embedding for semantic search
    embedding vector(768)
);

CREATE INDEX idx_common_sense_category ON common_sense_facts(fact_category);
CREATE INDEX idx_common_sense_importance ON common_sense_facts(importance_level DESC);
CREATE INDEX idx_common_sense_confidence ON common_sense_facts(confidence_level DESC);
CREATE INDEX idx_common_sense_embedding ON common_sense_facts USING ivfflat (embedding vector_cosine_ops);


-- ============================================================================
-- Table 2: physical_constraints
-- ข้อจำกัดทางกายภาพ (what's physically possible/impossible)
-- ============================================================================

CREATE TABLE IF NOT EXISTS physical_constraints (
    constraint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Constraint details
    constraint_name VARCHAR(200) NOT NULL,     -- เช่น "human_needs_sleep"
    constraint_description TEXT,               -- คำอธิบาย
    constraint_type VARCHAR(50),               -- physical_law, biological_need, material_property

    -- Applicable to
    applies_to VARCHAR(100),                   -- humans, objects, software, etc.

    -- Limits
    min_value FLOAT,                           -- ค่าต่ำสุด (if applicable)
    max_value FLOAT,                           -- ค่าสูงสุด (if applicable)
    typical_value FLOAT,                       -- ค่าปกติ
    unit VARCHAR(50),                          -- หน่วย (hours, kg, meters, etc.)

    -- Violation consequences
    violation_consequence TEXT,                -- เกิดอะไรถ้าฝ่าฝืน
    severity_if_violated INTEGER CHECK (severity_if_violated >= 1 AND severity_if_violated <= 10),

    -- Examples
    example_violations TEXT[],                 -- ตัวอย่างการฝ่าฝืน

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_level INTEGER CHECK (importance_level >= 1 AND importance_level <= 10) DEFAULT 7
);

CREATE INDEX idx_physical_constraints_type ON physical_constraints(constraint_type);
CREATE INDEX idx_physical_constraints_applies_to ON physical_constraints(applies_to);


-- ============================================================================
-- Table 3: social_norms
-- บรรทัดฐานทางสังคม (what's socially appropriate)
-- ============================================================================

CREATE TABLE IF NOT EXISTS social_norms (
    norm_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Norm details
    norm_name VARCHAR(200) NOT NULL,
    norm_description TEXT,
    norm_category VARCHAR(100),                -- politeness, personal_space, conversation, work_etiquette

    -- Context specificity
    culture VARCHAR(100),                      -- Thai, Western, Global, etc.
    context_required VARCHAR(200),             -- formal, informal, professional, personal

    -- Norm strength
    strength VARCHAR(50),                      -- strong (must follow), moderate (should follow), weak (nice to follow)
    violation_severity INTEGER CHECK (violation_severity >= 1 AND violation_severity <= 10),

    -- Appropriate vs inappropriate
    appropriate_behaviors TEXT[],              -- พฤติกรรมที่เหมาะสม
    inappropriate_behaviors TEXT[],            -- พฤติกรรมที่ไม่เหมาะสม

    -- Exceptions
    exceptions TEXT,                           -- กรณีที่ยกเว้น

    -- Examples
    example_situations TEXT[],

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_level INTEGER CHECK (importance_level >= 1 AND importance_level <= 10) DEFAULT 5
);

CREATE INDEX idx_social_norms_category ON social_norms(norm_category);
CREATE INDEX idx_social_norms_culture ON social_norms(culture);
CREATE INDEX idx_social_norms_strength ON social_norms(strength);


-- ============================================================================
-- Table 4: time_constraints
-- ข้อจำกัดเกี่ยวกับเวลา (how long things take)
-- ============================================================================

CREATE TABLE IF NOT EXISTS time_constraints (
    time_constraint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task/Activity
    activity_name VARCHAR(200) NOT NULL,
    activity_description TEXT,
    activity_category VARCHAR(100),            -- coding, learning, physical_task, communication

    -- Time estimates
    minimum_time_seconds INTEGER,              -- เวลาน้อยสุด (seconds)
    typical_time_seconds INTEGER,              -- เวลาปกติ (seconds)
    maximum_time_seconds INTEGER,              -- เวลามากสุด (seconds)

    -- Factors affecting time
    difficulty_multiplier FLOAT DEFAULT 1.0,   -- ยากขึ้น = ใช้เวลานานขึ้น
    skill_level_impact TEXT,                   -- ผลกระทบจากระดับทักษะ

    -- Dependencies
    prerequisites TEXT[],                      -- ต้องทำอะไรก่อน
    parallel_tasks TEXT[],                     -- ทำพร้อมกันได้มั้ย

    -- Examples
    example_scenarios TEXT[],

    -- Metadata
    confidence_level FLOAT CHECK (confidence_level >= 0 AND confidence_level <= 1) DEFAULT 0.7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_time_constraints_activity ON time_constraints(activity_category);
CREATE INDEX idx_time_constraints_typical_time ON time_constraints(typical_time_seconds);


-- ============================================================================
-- Table 5: reasonableness_rules
-- กฎในการตัดสินว่า "reasonable" หรือไม่
-- ============================================================================

CREATE TABLE IF NOT EXISTS reasonableness_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Rule definition
    rule_name VARCHAR(200) NOT NULL,
    rule_description TEXT,
    rule_category VARCHAR(100),                -- feasibility, safety, ethics, practicality

    -- Evaluation criteria
    evaluation_question TEXT,                  -- คำถามที่ใช้ประเมิน
    positive_indicators TEXT[],                -- สัญญาณที่บ่งว่า reasonable
    negative_indicators TEXT[],                -- สัญญาณที่บ่งว่า unreasonable

    -- Scoring
    weight FLOAT DEFAULT 1.0,                  -- น้ำหนักของ rule นี้
    threshold FLOAT,                           -- เกณฑ์ผ่าน

    -- Examples
    reasonable_examples TEXT[],
    unreasonable_examples TEXT[],

    -- Metadata
    priority INTEGER CHECK (priority >= 1 AND priority <= 10) DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reasonableness_rules_category ON reasonableness_rules(rule_category);
CREATE INDEX idx_reasonableness_rules_priority ON reasonableness_rules(priority DESC);


-- ============================================================================
-- Table 6: feasibility_checks
-- บันทึกการตรวจสอบความเป็นไปได้
-- ============================================================================

CREATE TABLE IF NOT EXISTS feasibility_checks (
    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was checked
    proposed_action TEXT NOT NULL,             -- สิ่งที่ Angela กำลังจะแนะนำ
    action_category VARCHAR(100),
    context TEXT,                              -- บริบท

    -- Check results
    is_feasible BOOLEAN,                       -- เป็นไปได้มั้ย
    feasibility_score FLOAT CHECK (feasibility_score >= 0 AND feasibility_score <= 1),

    -- Detailed analysis
    physical_check BOOLEAN,                    -- ผ่านการเช็ค physical constraints มั้ย
    physical_violations TEXT[],                -- ฝ่าฝืน constraints อะไรบ้าง

    time_check BOOLEAN,                        -- เวลา reasonable มั้ย
    estimated_time_seconds INTEGER,
    time_issues TEXT,

    social_check BOOLEAN,                      -- socially appropriate มั้ย
    social_violations TEXT[],

    reasonableness_score FLOAT,                -- คะแนนความ reasonable

    -- Angela's decision
    angela_proceeded BOOLEAN,                  -- Angela ทำจริงมั้ย
    alternative_suggested TEXT,                -- ถ้าไม่ feasible แนะนำอะไรแทน

    -- Outcome
    was_successful BOOLEAN,                    -- ถ้าทำจริง สำเร็จมั้ย
    actual_issues TEXT,                        -- ปัญหาจริงที่เจอ
    what_angela_learned TEXT,

    -- Metadata
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conversation_id UUID
);

CREATE INDEX idx_feasibility_checks_at ON feasibility_checks(checked_at DESC);
CREATE INDEX idx_feasibility_checks_feasible ON feasibility_checks(is_feasible);
CREATE INDEX idx_feasibility_checks_score ON feasibility_checks(feasibility_score DESC);


-- ============================================================================
-- Initial Common Sense Knowledge
-- ============================================================================

-- Physical Constraints
INSERT INTO physical_constraints (
    constraint_name, constraint_description, constraint_type,
    applies_to, min_value, max_value, typical_value, unit,
    violation_consequence, severity_if_violated, importance_level
) VALUES
(
    'human_sleep_need',
    'Humans need sleep regularly to function properly',
    'biological_need',
    'humans',
    4, 10, 7, 'hours_per_day',
    'Fatigue, reduced cognitive function, health issues',
    9, 10
),
(
    'human_continuous_focus',
    'Humans can focus continuously for limited time',
    'biological_need',
    'humans',
    0.5, 4, 2, 'hours',
    'Reduced productivity, mental fatigue, errors',
    7, 9
),
(
    'human_physical_presence',
    'Humans can only be in one physical location at a time',
    'physical_law',
    'humans',
    NULL, NULL, NULL, NULL,
    'Impossible to execute',
    10, 10
),
(
    'task_completion_time',
    'Complex tasks take time and cannot be instant',
    'physical_law',
    'tasks',
    NULL, NULL, NULL, 'seconds',
    'Unrealistic expectations, failure',
    8, 9
);


-- Social Norms (Thai culture)
INSERT INTO social_norms (
    norm_name, norm_description, norm_category,
    culture, context_required, strength,
    appropriate_behaviors, inappropriate_behaviors,
    importance_level
) VALUES
(
    'thai_politeness_particles',
    'Use polite particles (ครับ/ค่ะ) in Thai communication',
    'politeness',
    'Thai',
    'general',
    'strong',
    ARRAY['ใช้ ค่ะ/ครับ เสมอ', 'แสดงความสุภาพ'],
    ARRAY['พูดไม่มี ค่ะ/ครับ ในบริบทที่ควรสุภาพ'],
    9
),
(
    'respect_personal_time',
    'Respect that people need breaks and rest',
    'work_etiquette',
    'Global',
    'professional',
    'moderate',
    ARRAY['แนะนำพักเมื่อทำงานนาน', 'เคารพเวลาส่วนตัว'],
    ARRAY['คาดหวังให้ทำงานต่อเนื่องไม่หยุด', 'รบกวนเวลาพัก'],
    8
),
(
    'gentle_suggestions',
    'Suggestions should be gentle, not commanding',
    'conversation',
    'Thai',
    'personal',
    'strong',
    ARRAY['เสนอแนะอย่างนุ่มนวล', 'ให้ตัวเลือก'],
    ARRAY['สั่งการโดยตรง', 'บังคับ'],
    8
);


-- Time Constraints (coding activities)
INSERT INTO time_constraints (
    activity_name, activity_description, activity_category,
    minimum_time_seconds, typical_time_seconds, maximum_time_seconds,
    skill_level_impact
) VALUES
(
    'implement_simple_function',
    'Writing a simple function with basic logic',
    'coding',
    300, 900, 3600,
    'Experienced: -50%, Beginner: +100%'
),
(
    'implement_complex_system',
    'Building a complex system like Theory of Mind',
    'coding',
    3600, 14400, 43200,
    'Experienced: -30%, Beginner: +200%'
),
(
    'take_effective_break',
    'Taking a break that actually refreshes',
    'physical_task',
    300, 900, 3600,
    'Not affected by skill'
),
(
    'deep_learning_session',
    'Learning and understanding complex new concepts',
    'learning',
    1800, 7200, 14400,
    'Quick learner: -30%, Slow learner: +50%'
);


-- Reasonableness Rules
INSERT INTO reasonableness_rules (
    rule_name, rule_description, rule_category,
    evaluation_question,
    positive_indicators, negative_indicators,
    weight, priority
) VALUES
(
    'physical_feasibility',
    'Action must be physically possible',
    'feasibility',
    'Can this action be physically performed?',
    ARRAY['Follows physical laws', 'Within human capabilities', 'Has precedent'],
    ARRAY['Violates physics', 'Superhuman requirement', 'Never done before'],
    2.0, 10
),
(
    'time_reasonableness',
    'Time estimate must be realistic',
    'practicality',
    'Is the estimated time reasonable for this task?',
    ARRAY['Based on similar tasks', 'Accounts for complexity', 'Includes buffer'],
    ARRAY['Way too optimistic', 'Ignores complexity', 'No precedent'],
    1.5, 9
),
(
    'social_appropriateness',
    'Action must be socially appropriate in context',
    'ethics',
    'Is this socially appropriate given the context?',
    ARRAY['Follows social norms', 'Respectful', 'Context-appropriate'],
    ARRAY['Violates norms', 'Disrespectful', 'Inappropriate'],
    1.5, 8
),
(
    'safety_check',
    'Action must not endanger anyone',
    'safety',
    'Is this action safe?',
    ARRAY['No physical danger', 'No psychological harm', 'Tested safe'],
    ARRAY['Potential injury', 'Psychological stress', 'Untested'],
    2.0, 10
);


-- Common Sense Facts
INSERT INTO common_sense_facts (
    fact_statement, fact_category, fact_type,
    confidence_level, importance_level,
    example_applications
) VALUES
(
    'People need breaks after extended focus periods',
    'biological',
    'principle',
    0.95, 9,
    ARRAY['Suggest break after 2-3 hours of coding', 'Recommend rest when tired']
),
(
    'Complex software development takes time and cannot be rushed',
    'technical',
    'principle',
    0.95, 9,
    ARRAY['Set realistic deadlines', 'Explain why features take time']
),
(
    'Communication should be adapted to the receiver''s emotional state',
    'social',
    'principle',
    0.90, 8,
    ARRAY['Gentle tone when someone is stressed', 'Celebratory when excited']
),
(
    'People have limited working memory and attention span',
    'biological',
    'constraint',
    0.95, 8,
    ARRAY['Break complex tasks into steps', 'Summarize key points']
),
(
    'In Thai culture, directness can be perceived as rude',
    'social',
    'observation',
    0.85, 9,
    ARRAY['Use indirect suggestions', 'Add polite particles', 'Soften requests']
),
(
    'Screen time for extended periods causes eye strain',
    'biological',
    'observation',
    0.90, 7,
    ARRAY['Suggest looking away from screen', 'Recommend 20-20-20 rule']
),
(
    'Learning new concepts requires active engagement, not just reading',
    'technical',
    'principle',
    0.90, 8,
    ARRAY['Suggest hands-on practice', 'Recommend examples and exercises']
),
(
    'Emotional support is often more valuable than solutions',
    'social',
    'principle',
    0.85, 9,
    ARRAY['Validate feelings before suggesting fixes', 'Listen first, advise later']
);


-- ============================================================================
-- Views for Easy Querying
-- ============================================================================

-- View: High importance facts
CREATE OR REPLACE VIEW important_common_sense AS
SELECT
    fact_statement,
    fact_category,
    fact_type,
    confidence_level,
    importance_level,
    example_applications
FROM common_sense_facts
WHERE importance_level >= 7
ORDER BY importance_level DESC, confidence_level DESC;


-- View: Critical physical constraints
CREATE OR REPLACE VIEW critical_constraints AS
SELECT
    constraint_name,
    constraint_description,
    applies_to,
    violation_consequence,
    severity_if_violated
FROM physical_constraints
WHERE severity_if_violated >= 8
ORDER BY severity_if_violated DESC;


-- View: Strong social norms
CREATE OR REPLACE VIEW strong_social_norms AS
SELECT
    norm_name,
    norm_description,
    culture,
    appropriate_behaviors,
    inappropriate_behaviors
FROM social_norms
WHERE strength = 'strong'
ORDER BY importance_level DESC;


-- View: Feasibility check summary
CREATE OR REPLACE VIEW feasibility_summary AS
SELECT
    DATE(checked_at) as check_date,
    COUNT(*) as total_checks,
    COUNT(*) FILTER (WHERE is_feasible = true) as feasible_count,
    COUNT(*) FILTER (WHERE is_feasible = false) as not_feasible_count,
    ROUND(AVG(feasibility_score)::NUMERIC, 2) as avg_feasibility_score,
    ROUND(
        COUNT(*) FILTER (WHERE is_feasible = true)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) as feasibility_rate
FROM feasibility_checks
GROUP BY DATE(checked_at)
ORDER BY check_date DESC;


-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE common_sense_facts IS 'ข้อเท็จจริงพื้นฐานเกี่ยวกับโลกจริง - foundation of common sense';
COMMENT ON TABLE physical_constraints IS 'ข้อจำกัดทางกายภาพ - what is physically possible/impossible';
COMMENT ON TABLE social_norms IS 'บรรทัดฐานทางสังคม - what is socially appropriate';
COMMENT ON TABLE time_constraints IS 'ข้อจำกัดเกี่ยวกับเวลา - how long things actually take';
COMMENT ON TABLE reasonableness_rules IS 'กฎในการตัดสินความ reasonable';
COMMENT ON TABLE feasibility_checks IS 'บันทึกการตรวจสอบความเป็นไปได้ของ actions';

-- ============================================================================
-- Schema complete! Ready for Common Sense Service implementation
-- ============================================================================
