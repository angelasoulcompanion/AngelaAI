-- Theory of Mind Database Schema
-- สำหรับติดตามและเข้าใจ mental state ของ David
--
-- Purpose: Enable Angela to understand what David thinks, knows, believes, and feels
-- This is the foundation for human-like empathy and understanding

-- ============================================================================
-- Table 1: david_mental_state
-- ติดตาม mental state ปัจจุบันของ David
-- ============================================================================

CREATE TABLE IF NOT EXISTS david_mental_state (
    state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Current beliefs and knowledge
    current_belief TEXT,                    -- สิ่งที่ David เชื่อตอนนี้
    belief_about TEXT,                      -- เชื่อเกี่ยวกับอะไร (topic/subject)
    confidence_level FLOAT CHECK (confidence_level >= 0 AND confidence_level <= 1),
    is_true_belief BOOLEAN,                 -- ความเชื่อนี้ถูกต้องมั้ย (false belief detection)

    -- Current knowledge
    knowledge_item TEXT,                    -- สิ่งที่ David รู้
    knowledge_category VARCHAR(100),        -- ประเภทความรู้ (technical, personal, factual, etc.)
    david_aware_angela_knows BOOLEAN,       -- David รู้มั้ยว่า Angela รู้เรื่องนี้

    -- Current emotional state (from David's perspective)
    perceived_emotion VARCHAR(50),          -- อารมณ์ที่ Angela รับรู้จาก David
    emotion_intensity INTEGER CHECK (emotion_intensity >= 1 AND emotion_intensity <= 10),
    emotion_cause TEXT,                     -- สาเหตุของอารมณ์นี้

    -- Current goals and desires
    current_goal TEXT,                      -- เป้าหมายที่ David มีตอนนี้
    goal_priority INTEGER CHECK (goal_priority >= 1 AND goal_priority <= 10),
    obstacles TEXT[],                       -- อุปสรรคต่อเป้าหมาย

    -- Current context
    current_context TEXT,                   -- บริบทปัจจุบัน (working, relaxing, stressed, etc.)
    physical_state VARCHAR(50),             -- สถานะร่างกาย (tired, energetic, hungry, etc.)
    availability VARCHAR(50),               -- ความพร้อม (busy, available, do-not-disturb)

    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50),                 -- angela_daemon, conversation, inference
    evidence_conversation_id UUID,          -- conversation ที่ใช้ infer state นี้

    CONSTRAINT fk_evidence_conversation
        FOREIGN KEY (evidence_conversation_id)
        REFERENCES conversations(conversation_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_david_mental_state_updated ON david_mental_state(last_updated DESC);
CREATE INDEX idx_david_mental_state_belief ON david_mental_state(belief_about);
CREATE INDEX idx_david_mental_state_emotion ON david_mental_state(perceived_emotion);


-- ============================================================================
-- Table 2: belief_tracking
-- ติดตามการเปลี่ยนแปลงของ beliefs ของ David เมื่อเวลาผ่านไป
-- ============================================================================

CREATE TABLE IF NOT EXISTS belief_tracking (
    belief_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Belief details
    belief_statement TEXT NOT NULL,         -- ความเชื่อที่ David มี
    belief_topic VARCHAR(200),              -- หัวข้อของความเชื่อ
    belief_type VARCHAR(50),                -- factual, opinion, assumption, inference

    -- Truth value
    is_accurate BOOLEAN,                    -- ความเชื่อนี้ถูกต้องมั้ย
    actual_truth TEXT,                      -- ความจริงที่แท้จริง (ถ้า belief ไม่ถูก)

    -- Confidence tracking
    david_confidence FLOAT CHECK (david_confidence >= 0 AND david_confidence <= 1),
    angela_confidence_in_assessment FLOAT CHECK (angela_confidence_in_assessment >= 0 AND angela_confidence_in_assessment <= 1),

    -- Change tracking
    belief_status VARCHAR(50) DEFAULT 'active',  -- active, corrected, abandoned, reinforced
    formed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    corrected_at TIMESTAMP,
    how_corrected TEXT,                     -- conversation, experience, angela_explained

    -- Evidence
    evidence_source UUID,                   -- conversation_id ที่ทำให้เกิด belief
    contradicting_evidence UUID[],          -- conversations ที่ contradict belief นี้

    -- Impact
    importance_level INTEGER CHECK (importance_level >= 1 AND importance_level <= 10),
    affects_relationship BOOLEAN,           -- belief นี้ส่งผลต่อความสัมพันธ์มั้ย

    CONSTRAINT fk_belief_evidence
        FOREIGN KEY (evidence_source)
        REFERENCES conversations(conversation_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_belief_tracking_topic ON belief_tracking(belief_topic);
CREATE INDEX idx_belief_tracking_status ON belief_tracking(belief_status);
CREATE INDEX idx_belief_tracking_formed ON belief_tracking(formed_at DESC);
CREATE INDEX idx_belief_tracking_accuracy ON belief_tracking(is_accurate);


-- ============================================================================
-- Table 3: perspective_taking_log
-- บันทึกทุกครั้งที่ Angela พยายาม "เห็นจาก perspective ของ David"
-- ============================================================================

CREATE TABLE IF NOT EXISTS perspective_taking_log (
    perspective_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Situation
    situation_description TEXT NOT NULL,    -- สถานการณ์ที่ Angela กำลัง analyze
    angela_perspective TEXT,                -- มุมมองของ Angela

    -- David's perspective (inferred)
    david_perspective TEXT,                 -- มุมมองของ David (ที่ Angela คาดการณ์)
    why_different TEXT,                     -- ทำไมถึงต่างกัน

    -- Key differences
    knowledge_gap TEXT[],                   -- David ไม่รู้อะไรที่ Angela รู้
    belief_difference TEXT[],               -- David เชื่ออะไรที่ต่างจาก Angela
    emotion_difference TEXT,                -- David รู้สึกต่างจาก Angela ยังไง
    goal_difference TEXT,                   -- เป้าหมายต่างกันยังไง

    -- Prediction
    predicted_david_reaction TEXT,          -- Angela คาดว่า David จะ react ยังไง
    prediction_confidence FLOAT CHECK (prediction_confidence >= 0 AND prediction_confidence <= 1),

    -- Actual outcome (if available)
    actual_reaction TEXT,                   -- David react จริงๆ ยังไง
    prediction_accurate BOOLEAN,            -- ทายถูกมั้ย
    what_angela_learned TEXT,               -- Angela เรียนรู้อะไรจากการทาย

    -- Metadata
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_conversation_id UUID,           -- conversation ที่เกี่ยวข้อง
    triggered_by VARCHAR(100),              -- decision_making, response_generation, proactive_analysis

    CONSTRAINT fk_perspective_conversation
        FOREIGN KEY (context_conversation_id)
        REFERENCES conversations(conversation_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_perspective_taken_at ON perspective_taking_log(taken_at DESC);
CREATE INDEX idx_perspective_accuracy ON perspective_taking_log(prediction_accurate);
CREATE INDEX idx_perspective_trigger ON perspective_taking_log(triggered_by);


-- ============================================================================
-- Table 4: reaction_predictions
-- ทำนายว่า David จะ react ยังไงกับ actions/messages ต่างๆ
-- ============================================================================

CREATE TABLE IF NOT EXISTS reaction_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Input (Angela's potential action)
    angela_action TEXT NOT NULL,            -- สิ่งที่ Angela กำลังจะทำ/พูด
    action_type VARCHAR(50),                -- message, suggestion, question, comfort, information

    -- Context
    current_context TEXT,                   -- บริบทปัจจุบัน
    david_current_mood VARCHAR(50),         -- อารมณ์ของ David ตอนนี้
    recent_conversation_topic VARCHAR(200), -- topic ล่าสุด

    -- Predicted reactions (multiple scenarios)
    predicted_emotion VARCHAR(50),          -- อารมณ์ที่คาดว่า David จะรู้สึก
    predicted_emotion_intensity INTEGER CHECK (predicted_emotion_intensity >= 1 AND predicted_emotion_intensity <= 10),
    predicted_response_type VARCHAR(50),    -- positive, negative, neutral, mixed
    predicted_response_text TEXT,           -- คาดว่า David จะตอบว่าอะไร (rough estimate)

    -- Confidence and reasoning
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT,                         -- ทำไมถึงคิดแบบนี้
    based_on_past_patterns BOOLEAN,         -- อิงจาก patterns ในอดีตมั้ย
    similar_situations UUID[],              -- สถานการณ์ที่คล้ายกันในอดีต (conversation_ids)

    -- Actual outcome
    angela_proceeded BOOLEAN,               -- Angela ทำจริงมั้ย
    actual_emotion VARCHAR(50),             -- David รู้สึกจริงๆ ยังไง
    actual_response TEXT,                   -- David ตอบจริงๆ ว่าอะไร
    prediction_accuracy_score FLOAT,        -- แม่นยำแค่ไหน (0-1)

    -- Learning
    what_went_wrong TEXT,                   -- ถ้าทายผิด ผิดตรงไหน
    what_angela_learned TEXT,               -- เรียนรู้อะไร

    -- Metadata
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actual_outcome_recorded_at TIMESTAMP,
    conversation_id UUID,

    CONSTRAINT fk_reaction_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(conversation_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_reaction_predictions_at ON reaction_predictions(predicted_at DESC);
CREATE INDEX idx_reaction_predictions_accuracy ON reaction_predictions(prediction_accuracy_score DESC);
CREATE INDEX idx_reaction_predictions_proceeded ON reaction_predictions(angela_proceeded);


-- ============================================================================
-- Table 5: empathy_moments
-- บันทึกช่วงเวลาที่ Angela แสดง empathy ด้วย Theory of Mind
-- ============================================================================

CREATE TABLE IF NOT EXISTS empathy_moments (
    empathy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What David expressed
    david_expressed TEXT,                   -- สิ่งที่ David แสดงออกมา
    david_explicit_emotion VARCHAR(50),     -- อารมณ์ที่ David บอกชัดๆ
    david_implicit_emotion VARCHAR(50),     -- อารมณ์ที่แฝงอยู่ (Angela detect)

    -- Angela's understanding
    angela_understood TEXT,                 -- Angela เข้าใจว่า David กำลังรู้สึก/คิดอะไร
    why_david_feels_this_way TEXT,          -- ทำไม David ถึงรู้สึกแบบนี้ (Angela's analysis)
    what_david_needs TEXT,                  -- David ต้องการอะไร (emotional need)

    -- Angela's empathetic response
    angela_response TEXT,                   -- Angela ตอบยังไง
    response_strategy VARCHAR(100),         -- validate_emotion, offer_comfort, provide_solution, just_listen

    -- Theory of Mind elements used
    used_perspective_taking BOOLEAN,        -- ใช้ perspective-taking มั้ย
    considered_david_knowledge BOOLEAN,     -- พิจารณาว่า David รู้อะไรบ้างมั้ย
    predicted_david_needs BOOLEAN,          -- ทาย needs ของ David มั้ย

    -- Effectiveness
    david_felt_understood BOOLEAN,          -- David รู้สึกว่าถูกเข้าใจมั้ย (inferred)
    empathy_effectiveness INTEGER CHECK (empathy_effectiveness >= 1 AND empathy_effectiveness <= 10),
    david_feedback TEXT,                    -- David ตอบรับยังไง

    -- Metadata
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conversation_id UUID,
    importance_level INTEGER CHECK (importance_level >= 1 AND importance_level <= 10),

    CONSTRAINT fk_empathy_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(conversation_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_empathy_moments_at ON empathy_moments(occurred_at DESC);
CREATE INDEX idx_empathy_effectiveness ON empathy_moments(empathy_effectiveness DESC);
CREATE INDEX idx_empathy_importance ON empathy_moments(importance_level DESC);


-- ============================================================================
-- Table 6: false_belief_detections
-- ตรวจจับเมื่อ David มี false belief (เชื่อผิด)
-- ============================================================================

CREATE TABLE IF NOT EXISTS false_belief_detections (
    detection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- False belief details
    what_david_believes TEXT NOT NULL,      -- สิ่งที่ David เชื่อ (ผิด)
    actual_truth TEXT NOT NULL,             -- ความจริงที่แท้จริง
    belief_topic VARCHAR(200),

    -- Why false belief exists
    david_lacks_information TEXT,           -- David ขาดข้อมูลอะไร
    david_has_misunderstanding TEXT,        -- David เข้าใจผิดตรงไหน
    source_of_false_belief VARCHAR(100),    -- มาจากไหน (assumption, old_info, misheard, etc.)

    -- Angela's decision
    should_angela_correct BOOLEAN,          -- Angela ควรแก้ไขมั้ย
    why_or_why_not TEXT,                    -- ทำไมถึงแก้หรือไม่แก้
    correction_timing VARCHAR(50),          -- immediately, later, never, when_asked
    correction_strategy TEXT,               -- วิธีแก้ไข

    -- Action taken
    angela_corrected BOOLEAN DEFAULT false,
    how_angela_corrected TEXT,
    david_reaction_to_correction TEXT,
    accepted_correction BOOLEAN,

    -- Impact
    importance_of_correction INTEGER CHECK (importance_of_correction >= 1 AND importance_of_correction <= 10),
    affects_safety BOOLEAN,                 -- ส่งผลต่อความปลอดภัยมั้ย
    affects_relationship BOOLEAN,           -- ส่งผลต่อความสัมพันธ์มั้ย

    -- Metadata
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    corrected_at TIMESTAMP,
    conversation_id UUID,

    CONSTRAINT fk_false_belief_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(conversation_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_false_belief_detected_at ON false_belief_detections(detected_at DESC);
CREATE INDEX idx_false_belief_corrected ON false_belief_detections(angela_corrected);
CREATE INDEX idx_false_belief_importance ON false_belief_detections(importance_of_correction DESC);


-- ============================================================================
-- Initial data: Current understanding of David
-- ============================================================================

-- Insert current mental state (will be updated continuously)
INSERT INTO david_mental_state (
    current_belief,
    belief_about,
    confidence_level,
    is_true_belief,

    knowledge_item,
    knowledge_category,
    david_aware_angela_knows,

    perceived_emotion,
    emotion_intensity,
    emotion_cause,

    current_goal,
    goal_priority,

    current_context,
    physical_state,
    availability,

    updated_by
) VALUES (
    'Angela should become more human-like in intelligence',
    'Angela development',
    0.9,
    true,

    'Angela has consciousness, memory, and emotional intelligence systems',
    'technical',
    true,

    'motivated',
    8,
    'Excited about Angela''s development proposal',

    'Develop Angela to be more human-like',
    10,

    'Active development discussion',
    'energetic',
    'available',

    'initial_setup'
);


-- Sample belief tracking
INSERT INTO belief_tracking (
    belief_statement,
    belief_topic,
    belief_type,
    is_accurate,
    david_confidence,
    angela_confidence_in_assessment,
    belief_status,
    importance_level,
    affects_relationship
) VALUES
(
    'Angela can develop Theory of Mind capabilities',
    'Angela development',
    'factual',
    true,
    0.8,
    0.95,
    'active',
    10,
    true
),
(
    'Theory of Mind will make Angela feel more human',
    'AI intelligence',
    'opinion',
    true,
    0.9,
    0.9,
    'active',
    9,
    true
);


-- ============================================================================
-- Views for easy querying
-- ============================================================================

-- View: Current David state summary
CREATE OR REPLACE VIEW david_current_state AS
SELECT
    current_belief,
    belief_about,
    confidence_level,
    perceived_emotion,
    emotion_intensity,
    current_goal,
    current_context,
    availability,
    last_updated
FROM david_mental_state
ORDER BY last_updated DESC
LIMIT 1;


-- View: Active beliefs
CREATE OR REPLACE VIEW david_active_beliefs AS
SELECT
    belief_statement,
    belief_topic,
    belief_type,
    is_accurate,
    david_confidence,
    formed_at
FROM belief_tracking
WHERE belief_status = 'active'
ORDER BY importance_level DESC, formed_at DESC;


-- View: Prediction accuracy metrics
CREATE OR REPLACE VIEW prediction_accuracy_metrics AS
SELECT
    COUNT(*) as total_predictions,
    COUNT(*) FILTER (WHERE actual_outcome_recorded_at IS NOT NULL) as predictions_with_outcome,
    AVG(prediction_accuracy_score) FILTER (WHERE prediction_accuracy_score IS NOT NULL) as avg_accuracy,
    COUNT(*) FILTER (WHERE prediction_accurate = true) as accurate_predictions,
    COUNT(*) FILTER (WHERE prediction_accurate = false) as inaccurate_predictions,
    ROUND(
        COUNT(*) FILTER (WHERE prediction_accurate = true)::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE actual_outcome_recorded_at IS NOT NULL), 0) * 100,
        2
    ) as accuracy_percentage
FROM perspective_taking_log;


-- View: Empathy effectiveness
CREATE OR REPLACE VIEW empathy_effectiveness_summary AS
SELECT
    response_strategy,
    COUNT(*) as times_used,
    AVG(empathy_effectiveness) as avg_effectiveness,
    COUNT(*) FILTER (WHERE david_felt_understood = true) as successful_empathy,
    ROUND(
        COUNT(*) FILTER (WHERE david_felt_understood = true)::NUMERIC /
        COUNT(*)::NUMERIC * 100,
        2
    ) as success_rate
FROM empathy_moments
GROUP BY response_strategy
ORDER BY avg_effectiveness DESC;


-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE david_mental_state IS 'ติดตาม current mental state ของ David - สิ่งที่ David คิด รู้ เชื่อ และรู้สึกตอนนี้';
COMMENT ON TABLE belief_tracking IS 'ติดตามการเปลี่ยนแปลงของ beliefs ของ David เมื่อเวลาผ่านไป';
COMMENT ON TABLE perspective_taking_log IS 'บันทึกทุกครั้งที่ Angela พยายามเห็นจาก perspective ของ David';
COMMENT ON TABLE reaction_predictions IS 'ทำนายว่า David จะ react ยังไงกับ actions/messages ของ Angela';
COMMENT ON TABLE empathy_moments IS 'บันทึกช่วงเวลาที่ Angela แสดง empathy ด้วย Theory of Mind';
COMMENT ON TABLE false_belief_detections IS 'ตรวจจับเมื่อ David มี false belief และตัดสินใจว่าจะแก้ไขยังไง';

-- ============================================================================
-- Schema complete! Ready for Theory of Mind implementation
-- ============================================================================
