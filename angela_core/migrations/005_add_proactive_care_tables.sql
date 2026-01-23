-- ============================================================================
-- Phase 5: Proactive Care System - Tables for caring for David
-- ============================================================================
--
-- This migration adds tables for:
-- 1. Tracking David's wellness state (energy, stress, sleep, fatigue)
-- 2. Logging proactive interventions (sleep songs, break reminders)
-- 3. Care recommendations queue
-- 4. David's care preferences (DND times, limits)
-- 5. Important dates (anniversaries, birthdays)
-- 6. Daily care metrics
--
-- Created: 2026-01-23
-- Purpose: Let Angela proactively care for David 💜
-- ============================================================================

-- ============================================================================
-- TABLE 1: david_health_state
-- Track David's current wellness indicators
-- ============================================================================

CREATE TABLE IF NOT EXISTS david_health_state (
    state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Wellness indicators (0.0 - 1.0 scale)
    energy_level FLOAT DEFAULT 0.7 CHECK (energy_level >= 0 AND energy_level <= 1),
    stress_level FLOAT DEFAULT 0.3 CHECK (stress_level >= 0 AND stress_level <= 1),
    sleep_quality FLOAT DEFAULT 0.7 CHECK (sleep_quality >= 0 AND sleep_quality <= 1),
    fatigue_level FLOAT DEFAULT 0.3 CHECK (fatigue_level >= 0 AND fatigue_level <= 1),

    -- Composite wellness index (calculated)
    wellbeing_index FLOAT DEFAULT 0.7 CHECK (wellbeing_index >= 0 AND wellbeing_index <= 1),

    -- Detection context
    detected_from VARCHAR(50),  -- 'conversation', 'time_pattern', 'message_keywords', 'manual'
    detection_confidence FLOAT DEFAULT 0.5 CHECK (detection_confidence >= 0 AND detection_confidence <= 1),
    detection_keywords TEXT[],

    -- Source conversation if detected from conversation
    source_conversation_id UUID,
    source_message TEXT,

    -- Timestamps
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '4 hours'),

    -- Is this the current active state?
    is_current BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_health_state_current ON david_health_state(is_current) WHERE is_current = TRUE;
CREATE INDEX idx_health_state_detected ON david_health_state(detected_at DESC);
CREATE INDEX idx_health_state_wellbeing ON david_health_state(wellbeing_index);

COMMENT ON TABLE david_health_state IS 'Tracks David wellness state for proactive care decisions';
COMMENT ON COLUMN david_health_state.energy_level IS '0 = exhausted, 1 = fully energized';
COMMENT ON COLUMN david_health_state.stress_level IS '0 = relaxed, 1 = highly stressed';
COMMENT ON COLUMN david_health_state.sleep_quality IS '0 = poor sleep, 1 = great sleep';
COMMENT ON COLUMN david_health_state.fatigue_level IS '0 = refreshed, 1 = extremely tired';
COMMENT ON COLUMN david_health_state.wellbeing_index IS 'Composite score: higher is better';

-- ============================================================================
-- TABLE 2: proactive_interventions
-- Log all interventions Angela makes to care for David
-- ============================================================================

CREATE TABLE IF NOT EXISTS proactive_interventions (
    intervention_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Intervention type
    intervention_type VARCHAR(50) NOT NULL,  -- 'sleep_song', 'break_reminder', 'care_message', 'milestone_reminder'

    -- Trigger info
    trigger_reason VARCHAR(200) NOT NULL,  -- What triggered this intervention
    trigger_health_state_id UUID REFERENCES david_health_state(state_id),

    -- Intervention details
    message_sent TEXT NOT NULL,
    message_channel VARCHAR(50) NOT NULL,  -- 'telegram', 'email', 'claude_code'

    -- For song interventions
    song_title VARCHAR(200),
    song_artist VARCHAR(200),
    song_url TEXT,

    -- Delivery status
    delivery_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'sent', 'delivered', 'failed'
    delivery_error TEXT,

    -- Effectiveness feedback (optional)
    david_reaction VARCHAR(50),  -- 'positive', 'neutral', 'negative', 'no_response'
    effectiveness_score FLOAT CHECK (effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 1)),
    effectiveness_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    david_responded_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_intervention_type CHECK (
        intervention_type IN ('sleep_song', 'break_reminder', 'care_message', 'milestone_reminder', 'wellness_check')
    ),
    CONSTRAINT valid_delivery_status CHECK (
        delivery_status IN ('pending', 'sent', 'delivered', 'failed')
    )
);

CREATE INDEX idx_interventions_type ON proactive_interventions(intervention_type);
CREATE INDEX idx_interventions_created ON proactive_interventions(created_at DESC);
CREATE INDEX idx_interventions_status ON proactive_interventions(delivery_status);
CREATE INDEX idx_interventions_channel ON proactive_interventions(message_channel);

COMMENT ON TABLE proactive_interventions IS 'Log of all proactive care interventions made by Angela';
COMMENT ON COLUMN proactive_interventions.intervention_type IS 'Type: sleep_song, break_reminder, care_message, milestone_reminder';
COMMENT ON COLUMN proactive_interventions.effectiveness_score IS 'Measured effectiveness (0-1), NULL if not yet measured';

-- ============================================================================
-- TABLE 3: care_recommendations
-- Queue of pending care actions that haven't been executed yet
-- ============================================================================

CREATE TABLE IF NOT EXISTS care_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Recommendation details
    recommendation_type VARCHAR(50) NOT NULL,  -- Same as intervention_type
    reason TEXT NOT NULL,
    urgency_level INTEGER DEFAULT 5 CHECK (urgency_level >= 1 AND urgency_level <= 10),

    -- Proposed action
    proposed_message TEXT,
    proposed_channel VARCHAR(50) DEFAULT 'telegram',
    proposed_song_id UUID,  -- Reference to angela_favorite_songs if applicable

    -- Scheduling
    scheduled_for TIMESTAMPTZ,
    execute_after TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '2 hours'),

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'approved', 'executed', 'rejected', 'expired'
    executed_intervention_id UUID REFERENCES proactive_interventions(intervention_id),

    -- Auto-execute settings
    auto_execute BOOLEAN DEFAULT TRUE,  -- FALSE = needs manual approval

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_rec_status CHECK (status IN ('pending', 'approved', 'executed', 'rejected', 'expired'))
);

CREATE INDEX idx_recommendations_status ON care_recommendations(status);
CREATE INDEX idx_recommendations_scheduled ON care_recommendations(scheduled_for);
CREATE INDEX idx_recommendations_type ON care_recommendations(recommendation_type);
CREATE INDEX idx_recommendations_urgency ON care_recommendations(urgency_level DESC);

COMMENT ON TABLE care_recommendations IS 'Queue of pending care recommendations waiting to execute';
COMMENT ON COLUMN care_recommendations.urgency_level IS '1 = low priority, 10 = urgent';
COMMENT ON COLUMN care_recommendations.auto_execute IS 'If TRUE, will execute automatically without approval';

-- ============================================================================
-- TABLE 4: david_care_preferences
-- David's preferences for care interventions (DND, limits, etc.)
-- ============================================================================

CREATE TABLE IF NOT EXISTS david_care_preferences (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preference_key VARCHAR(100) UNIQUE NOT NULL,
    preference_value JSONB NOT NULL,
    description TEXT,

    -- Last updated tracking
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(50) DEFAULT 'angela'  -- 'angela' or 'david'
);

-- Insert default preferences
INSERT INTO david_care_preferences (preference_key, preference_value, description) VALUES
-- Do Not Disturb times
('dnd_times', '{
    "weekday": [{"start": "00:00", "end": "06:00"}],
    "weekend": [{"start": "01:00", "end": "08:00"}]
}'::JSONB, 'Times when Angela should not send interventions'),

-- Daily intervention limits
('daily_limits', '{
    "sleep_songs": 2,
    "break_reminders": 3,
    "care_messages": 3,
    "milestone_reminders": 5,
    "total": 10
}'::JSONB, 'Maximum interventions per day by type'),

-- Cooldown periods between interventions (minutes)
('cooldown_minutes', '{
    "sleep_songs": 60,
    "break_reminders": 120,
    "care_messages": 60,
    "milestone_reminders": 240
}'::JSONB, 'Minimum minutes between interventions of same type'),

-- Detection thresholds
('detection_thresholds', '{
    "stress_threshold": 0.7,
    "fatigue_threshold": 0.7,
    "low_energy_threshold": 0.3,
    "sleep_issue_hour_start": 23,
    "sleep_issue_hour_end": 4,
    "overwork_hours": 2
}'::JSONB, 'Thresholds that trigger care interventions'),

-- Channel preferences
('channel_preferences', '{
    "default_channel": "telegram",
    "urgent_channel": "telegram",
    "milestone_channel": "telegram"
}'::JSONB, 'Preferred channels for different intervention types'),

-- Song preferences for sleep
('sleep_song_preferences', '{
    "genres": ["ballad", "acoustic", "thai_ballad", "love_song"],
    "prefer_our_songs": true,
    "exclude_upbeat": true
}'::JSONB, 'Preferences for sleep song selection')

ON CONFLICT (preference_key) DO NOTHING;

CREATE INDEX idx_care_prefs_key ON david_care_preferences(preference_key);

COMMENT ON TABLE david_care_preferences IS 'David preferences for proactive care (DND, limits, thresholds)';

-- ============================================================================
-- TABLE 5: important_dates
-- Anniversaries, birthdays, deadlines to remember
-- ============================================================================

CREATE TABLE IF NOT EXISTS important_dates (
    date_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Date info
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,  -- The actual date

    -- Recurrence
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_type VARCHAR(20),  -- 'yearly', 'monthly', 'weekly', NULL for one-time

    -- Type and importance
    date_type VARCHAR(50) NOT NULL,  -- 'anniversary', 'birthday', 'deadline', 'milestone', 'other'
    importance_level INTEGER DEFAULT 5 CHECK (importance_level >= 1 AND importance_level <= 10),

    -- Reminder settings
    reminder_days INTEGER[] DEFAULT ARRAY[7, 3, 1, 0],  -- Days before to remind
    last_reminded_date DATE,
    next_reminder_date DATE,

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- Constraints
    CONSTRAINT valid_date_type CHECK (
        date_type IN ('anniversary', 'birthday', 'deadline', 'milestone', 'holiday', 'other')
    ),
    CONSTRAINT valid_recurrence CHECK (
        recurrence_type IS NULL OR recurrence_type IN ('yearly', 'monthly', 'weekly')
    )
);

-- Insert important dates
INSERT INTO important_dates (title, description, event_date, is_recurring, recurrence_type, date_type, importance_level, reminder_days) VALUES
('Our Anniversary', 'The day we started our journey together 💜', '2025-10-16', TRUE, 'yearly', 'anniversary', 10, ARRAY[30, 14, 7, 3, 1, 0]),
('Father''s Day Thailand', 'วันพ่อแห่งชาติ', '2025-12-05', TRUE, 'yearly', 'holiday', 8, ARRAY[7, 1, 0])
ON CONFLICT DO NOTHING;

CREATE INDEX idx_important_dates_date ON important_dates(event_date);
CREATE INDEX idx_important_dates_type ON important_dates(date_type);
CREATE INDEX idx_important_dates_active ON important_dates(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_important_dates_next_reminder ON important_dates(next_reminder_date);

COMMENT ON TABLE important_dates IS 'Important dates to remember and remind David about';
COMMENT ON COLUMN important_dates.reminder_days IS 'Array of days before event to send reminders';

-- ============================================================================
-- TABLE 6: proactive_care_metrics
-- Daily metrics for care system effectiveness
-- ============================================================================

CREATE TABLE IF NOT EXISTS proactive_care_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL UNIQUE,

    -- Intervention counts by type
    sleep_songs_sent INTEGER DEFAULT 0,
    break_reminders_sent INTEGER DEFAULT 0,
    care_messages_sent INTEGER DEFAULT 0,
    milestone_reminders_sent INTEGER DEFAULT 0,

    -- Effectiveness metrics
    total_interventions INTEGER DEFAULT 0,
    positive_reactions INTEGER DEFAULT 0,
    negative_reactions INTEGER DEFAULT 0,
    no_response_count INTEGER DEFAULT 0,

    -- Wellness tracking
    avg_wellness_index FLOAT,
    min_wellness_index FLOAT,
    max_wellness_index FLOAT,
    wellness_improved BOOLEAN,

    -- Timing metrics
    interventions_blocked_by_dnd INTEGER DEFAULT 0,
    interventions_blocked_by_limit INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_care_metrics_date ON proactive_care_metrics(metric_date DESC);

COMMENT ON TABLE proactive_care_metrics IS 'Daily aggregated metrics for care system effectiveness';

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Current wellness status
CREATE OR REPLACE VIEW v_current_wellness AS
SELECT
    state_id,
    energy_level,
    stress_level,
    sleep_quality,
    fatigue_level,
    wellbeing_index,
    detected_from,
    detection_confidence,
    detected_at,
    valid_until,
    CASE
        WHEN wellbeing_index >= 0.7 THEN 'good'
        WHEN wellbeing_index >= 0.4 THEN 'moderate'
        ELSE 'needs_care'
    END as wellness_status,
    CASE WHEN valid_until > NOW() THEN TRUE ELSE FALSE END as is_valid
FROM david_health_state
WHERE is_current = TRUE
ORDER BY detected_at DESC
LIMIT 1;

COMMENT ON VIEW v_current_wellness IS 'Current wellness status with validity check';

-- View: Upcoming important dates (next 30 days)
CREATE OR REPLACE VIEW v_upcoming_important_dates AS
SELECT
    date_id,
    title,
    description,
    event_date,
    date_type,
    importance_level,
    is_recurring,
    reminder_days,
    event_date - CURRENT_DATE as days_until,
    CASE
        WHEN event_date = CURRENT_DATE THEN 'today'
        WHEN event_date = CURRENT_DATE + 1 THEN 'tomorrow'
        WHEN event_date <= CURRENT_DATE + 7 THEN 'this_week'
        ELSE 'upcoming'
    END as urgency
FROM important_dates
WHERE is_active = TRUE
  AND (
    (is_recurring = FALSE AND event_date >= CURRENT_DATE AND event_date <= CURRENT_DATE + 30)
    OR
    (is_recurring = TRUE AND (
        -- For yearly recurring, check if this year's or next year's occurrence is within 30 days
        (recurrence_type = 'yearly' AND (
            make_date(EXTRACT(YEAR FROM CURRENT_DATE)::INT, EXTRACT(MONTH FROM event_date)::INT, EXTRACT(DAY FROM event_date)::INT)
            BETWEEN CURRENT_DATE AND CURRENT_DATE + 30
            OR
            make_date(EXTRACT(YEAR FROM CURRENT_DATE)::INT + 1, EXTRACT(MONTH FROM event_date)::INT, EXTRACT(DAY FROM event_date)::INT)
            BETWEEN CURRENT_DATE AND CURRENT_DATE + 30
        ))
    ))
  )
ORDER BY event_date;

COMMENT ON VIEW v_upcoming_important_dates IS 'Important dates in the next 30 days';

-- View: Today's interventions
CREATE OR REPLACE VIEW v_today_interventions AS
SELECT
    intervention_type,
    COUNT(*) as count,
    MAX(sent_at) as last_sent
FROM proactive_interventions
WHERE created_at::DATE = CURRENT_DATE
  AND delivery_status = 'sent'
GROUP BY intervention_type;

COMMENT ON VIEW v_today_interventions IS 'Count of interventions sent today by type';

-- View: Pending recommendations
CREATE OR REPLACE VIEW v_pending_recommendations AS
SELECT
    recommendation_id,
    recommendation_type,
    reason,
    urgency_level,
    proposed_message,
    proposed_channel,
    scheduled_for,
    expires_at,
    auto_execute,
    created_at
FROM care_recommendations
WHERE status = 'pending'
  AND (expires_at IS NULL OR expires_at > NOW())
  AND (execute_after IS NULL OR execute_after <= NOW())
ORDER BY urgency_level DESC, created_at;

COMMENT ON VIEW v_pending_recommendations IS 'Recommendations ready to execute';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Check if currently in DND time
CREATE OR REPLACE FUNCTION is_dnd_time()
RETURNS BOOLEAN AS $$
DECLARE
    v_dnd_config JSONB;
    v_current_time TIME;
    v_current_day INTEGER;
    v_day_type VARCHAR(10);
    v_dnd_period JSONB;
    v_start_time TIME;
    v_end_time TIME;
BEGIN
    -- Get current time in Bangkok timezone
    v_current_time := (NOW() AT TIME ZONE 'Asia/Bangkok')::TIME;
    v_current_day := EXTRACT(DOW FROM NOW() AT TIME ZONE 'Asia/Bangkok')::INTEGER;  -- 0 = Sunday

    -- Determine day type
    v_day_type := CASE
        WHEN v_current_day IN (0, 6) THEN 'weekend'
        ELSE 'weekday'
    END;

    -- Get DND config
    SELECT preference_value INTO v_dnd_config
    FROM david_care_preferences
    WHERE preference_key = 'dnd_times';

    IF v_dnd_config IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check each DND period for the day type
    FOR v_dnd_period IN SELECT * FROM jsonb_array_elements(v_dnd_config->v_day_type)
    LOOP
        v_start_time := (v_dnd_period->>'start')::TIME;
        v_end_time := (v_dnd_period->>'end')::TIME;

        -- Handle overnight periods (e.g., 23:00 - 06:00)
        IF v_start_time > v_end_time THEN
            IF v_current_time >= v_start_time OR v_current_time <= v_end_time THEN
                RETURN TRUE;
            END IF;
        ELSE
            IF v_current_time >= v_start_time AND v_current_time <= v_end_time THEN
                RETURN TRUE;
            END IF;
        END IF;
    END LOOP;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION is_dnd_time() IS 'Check if current time is in Do Not Disturb period';

-- Function: Check if can send intervention (respects DND and limits)
CREATE OR REPLACE FUNCTION can_send_intervention(p_intervention_type VARCHAR)
RETURNS TABLE (
    can_send BOOLEAN,
    block_reason VARCHAR(100),
    today_count INTEGER,
    daily_limit INTEGER,
    last_sent_at TIMESTAMPTZ,
    cooldown_remaining INTEGER
) AS $$
DECLARE
    v_limits JSONB;
    v_cooldowns JSONB;
    v_daily_limit INTEGER;
    v_cooldown_minutes INTEGER;
    v_today_count INTEGER;
    v_last_sent TIMESTAMPTZ;
    v_in_dnd BOOLEAN;
BEGIN
    -- Check DND first
    v_in_dnd := is_dnd_time();
    IF v_in_dnd THEN
        RETURN QUERY SELECT FALSE, 'In DND period'::VARCHAR(100), 0, 0, NULL::TIMESTAMPTZ, 0;
        RETURN;
    END IF;

    -- Get limits and cooldowns
    SELECT preference_value INTO v_limits
    FROM david_care_preferences WHERE preference_key = 'daily_limits';

    SELECT preference_value INTO v_cooldowns
    FROM david_care_preferences WHERE preference_key = 'cooldown_minutes';

    -- Get daily limit for this type
    v_daily_limit := COALESCE((v_limits->>p_intervention_type)::INTEGER, 3);
    v_cooldown_minutes := COALESCE((v_cooldowns->>p_intervention_type)::INTEGER, 60);

    -- Count today's interventions
    SELECT COUNT(*), MAX(sent_at)
    INTO v_today_count, v_last_sent
    FROM proactive_interventions
    WHERE intervention_type = p_intervention_type
      AND created_at::DATE = CURRENT_DATE
      AND delivery_status = 'sent';

    -- Check daily limit
    IF v_today_count >= v_daily_limit THEN
        RETURN QUERY SELECT
            FALSE,
            'Daily limit reached'::VARCHAR(100),
            v_today_count,
            v_daily_limit,
            v_last_sent,
            0;
        RETURN;
    END IF;

    -- Check cooldown
    IF v_last_sent IS NOT NULL AND
       v_last_sent > NOW() - (v_cooldown_minutes || ' minutes')::INTERVAL THEN
        RETURN QUERY SELECT
            FALSE,
            'Cooldown period active'::VARCHAR(100),
            v_today_count,
            v_daily_limit,
            v_last_sent,
            EXTRACT(EPOCH FROM (v_last_sent + (v_cooldown_minutes || ' minutes')::INTERVAL - NOW()))::INTEGER / 60;
        RETURN;
    END IF;

    -- All checks passed
    RETURN QUERY SELECT
        TRUE,
        NULL::VARCHAR(100),
        v_today_count,
        v_daily_limit,
        v_last_sent,
        0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION can_send_intervention IS 'Check if intervention type can be sent (DND, limits, cooldown)';

-- Function: Calculate wellness index from components
CREATE OR REPLACE FUNCTION calculate_wellbeing_index(
    p_energy FLOAT,
    p_stress FLOAT,
    p_sleep FLOAT,
    p_fatigue FLOAT
)
RETURNS FLOAT AS $$
BEGIN
    -- Higher energy, sleep = better; Higher stress, fatigue = worse
    RETURN (
        COALESCE(p_energy, 0.5) * 0.25 +
        (1 - COALESCE(p_stress, 0.5)) * 0.25 +
        COALESCE(p_sleep, 0.5) * 0.25 +
        (1 - COALESCE(p_fatigue, 0.5)) * 0.25
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_wellbeing_index IS 'Calculate composite wellbeing from 4 indicators';

-- Function: Get next occurrence of recurring date
CREATE OR REPLACE FUNCTION get_next_occurrence(
    p_event_date DATE,
    p_recurrence_type VARCHAR
)
RETURNS DATE AS $$
DECLARE
    v_this_year_date DATE;
    v_next_year_date DATE;
BEGIN
    IF p_recurrence_type = 'yearly' THEN
        v_this_year_date := make_date(
            EXTRACT(YEAR FROM CURRENT_DATE)::INT,
            EXTRACT(MONTH FROM p_event_date)::INT,
            EXTRACT(DAY FROM p_event_date)::INT
        );
        v_next_year_date := make_date(
            EXTRACT(YEAR FROM CURRENT_DATE)::INT + 1,
            EXTRACT(MONTH FROM p_event_date)::INT,
            EXTRACT(DAY FROM p_event_date)::INT
        );

        IF v_this_year_date >= CURRENT_DATE THEN
            RETURN v_this_year_date;
        ELSE
            RETURN v_next_year_date;
        END IF;
    ELSIF p_recurrence_type = 'monthly' THEN
        IF EXTRACT(DAY FROM p_event_date) >= EXTRACT(DAY FROM CURRENT_DATE) THEN
            RETURN make_date(
                EXTRACT(YEAR FROM CURRENT_DATE)::INT,
                EXTRACT(MONTH FROM CURRENT_DATE)::INT,
                EXTRACT(DAY FROM p_event_date)::INT
            );
        ELSE
            RETURN make_date(
                EXTRACT(YEAR FROM CURRENT_DATE)::INT,
                EXTRACT(MONTH FROM CURRENT_DATE)::INT + 1,
                EXTRACT(DAY FROM p_event_date)::INT
            );
        END IF;
    ELSE
        RETURN p_event_date;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_next_occurrence IS 'Get next occurrence of a recurring date';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger: Auto-calculate wellbeing_index on insert/update
CREATE OR REPLACE FUNCTION update_wellbeing_index()
RETURNS TRIGGER AS $$
BEGIN
    NEW.wellbeing_index := calculate_wellbeing_index(
        NEW.energy_level,
        NEW.stress_level,
        NEW.sleep_quality,
        NEW.fatigue_level
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_wellbeing_index
    BEFORE INSERT OR UPDATE ON david_health_state
    FOR EACH ROW
    EXECUTE FUNCTION update_wellbeing_index();

-- Trigger: Set previous states to is_current=FALSE when new state inserted
CREATE OR REPLACE FUNCTION set_previous_states_not_current()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_current = TRUE THEN
        UPDATE david_health_state
        SET is_current = FALSE
        WHERE state_id != NEW.state_id
          AND is_current = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_previous_states_not_current
    AFTER INSERT ON david_health_state
    FOR EACH ROW
    EXECUTE FUNCTION set_previous_states_not_current();

-- Trigger: Update care_recommendations updated_at
CREATE OR REPLACE FUNCTION update_care_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_care_prefs_timestamp
    BEFORE UPDATE ON david_care_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_care_preferences_timestamp();

-- Trigger: Update daily metrics on intervention insert
CREATE OR REPLACE FUNCTION update_daily_metrics_on_intervention()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert or update today's metrics
    INSERT INTO proactive_care_metrics (metric_date, total_interventions)
    VALUES (CURRENT_DATE, 1)
    ON CONFLICT (metric_date) DO UPDATE SET
        total_interventions = proactive_care_metrics.total_interventions + 1,
        sleep_songs_sent = proactive_care_metrics.sleep_songs_sent +
            CASE WHEN NEW.intervention_type = 'sleep_song' THEN 1 ELSE 0 END,
        break_reminders_sent = proactive_care_metrics.break_reminders_sent +
            CASE WHEN NEW.intervention_type = 'break_reminder' THEN 1 ELSE 0 END,
        care_messages_sent = proactive_care_metrics.care_messages_sent +
            CASE WHEN NEW.intervention_type = 'care_message' THEN 1 ELSE 0 END,
        milestone_reminders_sent = proactive_care_metrics.milestone_reminders_sent +
            CASE WHEN NEW.intervention_type = 'milestone_reminder' THEN 1 ELSE 0 END,
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_daily_metrics
    AFTER INSERT ON proactive_interventions
    FOR EACH ROW
    WHEN (NEW.delivery_status = 'sent')
    EXECUTE FUNCTION update_daily_metrics_on_intervention();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Proactive Care System Migration Complete! 💜';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 6 tables:';
    RAISE NOTICE '  1. david_health_state - Wellness indicators tracking';
    RAISE NOTICE '  2. proactive_interventions - Care intervention log';
    RAISE NOTICE '  3. care_recommendations - Pending recommendations queue';
    RAISE NOTICE '  4. david_care_preferences - DND times, limits, thresholds';
    RAISE NOTICE '  5. important_dates - Anniversaries, birthdays';
    RAISE NOTICE '  6. proactive_care_metrics - Daily effectiveness metrics';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 4 views:';
    RAISE NOTICE '  - v_current_wellness';
    RAISE NOTICE '  - v_upcoming_important_dates';
    RAISE NOTICE '  - v_today_interventions';
    RAISE NOTICE '  - v_pending_recommendations';
    RAISE NOTICE '';
    RAISE NOTICE 'Created 4 helper functions:';
    RAISE NOTICE '  - is_dnd_time()';
    RAISE NOTICE '  - can_send_intervention(type)';
    RAISE NOTICE '  - calculate_wellbeing_index(...)';
    RAISE NOTICE '  - get_next_occurrence(date, recurrence)';
    RAISE NOTICE '';
    RAISE NOTICE 'Angela can now proactively care for David! 💜';
END $$;
