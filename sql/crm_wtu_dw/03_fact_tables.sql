-- ============================================
-- CRM WTU Data Warehouse — Fact Tables
-- Target: crm_wtu_dw (PostgreSQL)
-- ============================================


-- ============================================
-- FACT 1: fact_lead_interaction
-- Grain: One row per contact event with a lead
-- Source: lead_interaction (248K rows)
-- Business: ทุกครั้งที่ staff ติดต่อ lead
-- ============================================
DROP TABLE IF EXISTS fact_lead_interaction CASCADE;

CREATE TABLE fact_lead_interaction (
    -- Surrogate FKs
    contact_date_key            INT NOT NULL REFERENCES dim_date(date_key),
    next_action_date_key        INT REFERENCES dim_date(date_key),       -- Role-playing
    staff_key                   INT NOT NULL REFERENCES dim_staff(staff_key),
    lead_key                    INT NOT NULL REFERENCES dim_lead(lead_key),
    interaction_type_key        INT NOT NULL REFERENCES dim_interaction_type(interaction_type_key),
    interaction_outcome_key     INT NOT NULL REFERENCES dim_interaction_outcome(interaction_outcome_key),
    lead_state_from_key         INT REFERENCES dim_lead_state(lead_state_key),
    lead_state_to_key           INT REFERENCES dim_lead_state(lead_state_key),
    opportunity_state_from_key  INT REFERENCES dim_opportunity_state(opportunity_state_key),
    opportunity_state_to_key    INT REFERENCES dim_opportunity_state(opportunity_state_key),
    app_form_state_from_key     INT REFERENCES dim_application_form_state(application_form_state_key),
    app_form_state_to_key       INT REFERENCES dim_application_form_state(application_form_state_key),

    -- Degenerate dimensions
    interaction_id              VARCHAR(36) NOT NULL,    -- PK from source
    entity_type                 VARCHAR(20) NOT NULL,    -- Lead or Opportunity context
    appointment_id              VARCHAR(36),             -- If linked to appointment

    -- Measures
    total_duration_sec          INT,                     -- Additive: call duration
    billed_duration_sec         INT,                     -- Additive: billed call duration
    interaction_count           INT NOT NULL DEFAULT 1,  -- Additive: always 1 (for easy SUM)

    -- State transition flags (derived, for fast filtering)
    is_state_change             BOOLEAN NOT NULL DEFAULT FALSE,  -- lead_state changed?
    is_opp_state_change         BOOLEAN NOT NULL DEFAULT FALSE,  -- opportunity_state changed?

    -- Metadata
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    etl_batch_id                INT
);

CREATE INDEX idx_fact_interaction_date ON fact_lead_interaction (contact_date_key);
CREATE INDEX idx_fact_interaction_lead ON fact_lead_interaction (lead_key);
CREATE INDEX idx_fact_interaction_staff ON fact_lead_interaction (staff_key);
CREATE INDEX idx_fact_interaction_dedup ON fact_lead_interaction (interaction_id);


-- ============================================
-- FACT 2: fact_appointment
-- Grain: One row per scheduled meeting
-- Source: appointment (23K rows)
-- Business: การนัดหมาย lead/opportunity
-- ============================================
DROP TABLE IF EXISTS fact_appointment CASCADE;

CREATE TABLE fact_appointment (
    -- Surrogate FKs
    scheduled_date_key          INT NOT NULL REFERENCES dim_date(date_key),
    created_date_key            INT NOT NULL REFERENCES dim_date(date_key),       -- Role-playing
    staff_key                   INT NOT NULL REFERENCES dim_staff(staff_key),
    lead_key                    INT REFERENCES dim_lead(lead_key),
    appointment_type_key        INT NOT NULL REFERENCES dim_appointment_type(appointment_type_key),
    interaction_type_key        INT NOT NULL REFERENCES dim_interaction_type(interaction_type_key),

    -- Degenerate dimensions
    appointment_id              VARCHAR(36) NOT NULL,
    appointment_status          VARCHAR(20) NOT NULL,    -- Completed, Cancelled, etc.
    opportunity_id              VARCHAR(36),              -- If linked to opportunity
    location                    VARCHAR(255),

    -- Measures
    duration_minutes            NUMERIC(10,2),           -- Additive: scheduled_end - scheduled_start
    appointment_count           INT NOT NULL DEFAULT 1,  -- Additive
    lead_time_days              NUMERIC(10,2),           -- Semi-additive: created→scheduled days

    -- Metadata
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    etl_batch_id                INT
);

CREATE INDEX idx_fact_appointment_date ON fact_appointment (scheduled_date_key);
CREATE INDEX idx_fact_appointment_staff ON fact_appointment (staff_key);
CREATE INDEX idx_fact_appointment_dedup ON fact_appointment (appointment_id);


-- ============================================
-- FACT 3: fact_closed_sale
-- Grain: One row per pipeline closure (Win or Lose)
-- Source: closed_sale (12K rows)
-- Business: ผลการปิดยอด — สมัครสำเร็จ หรือ ไม่สำเร็จ
-- ============================================
DROP TABLE IF EXISTS fact_closed_sale CASCADE;

CREATE TABLE fact_closed_sale (
    -- Surrogate FKs
    closed_date_key             INT NOT NULL REFERENCES dim_date(date_key),
    lead_created_date_key       INT REFERENCES dim_date(date_key),        -- Role-playing
    staff_key                   INT NOT NULL REFERENCES dim_staff(staff_key),
    lead_key                    INT NOT NULL REFERENCES dim_lead(lead_key),
    closed_sale_status_key      INT NOT NULL REFERENCES dim_closed_sale_status(closed_sale_status_key),
    lose_reason_key             INT REFERENCES dim_lose_reason(lose_reason_key),
    curriculum_key              INT REFERENCES dim_curriculum(curriculum_key),
    program_type_key            INT REFERENCES dim_program_type(program_type_key),
    school_key                  INT REFERENCES dim_school(school_key),
    province_key                INT REFERENCES dim_province(province_key),
    channel_key                 INT REFERENCES dim_channel(channel_key),
    lead_source_key             INT REFERENCES dim_lead_source(lead_source_key),
    target_group_key            INT REFERENCES dim_target_group(target_group_key),

    -- Degenerate dimensions
    closed_sale_id              VARCHAR(36) NOT NULL,
    opportunity_id              VARCHAR(36) NOT NULL,
    opportunity_no              VARCHAR(50),
    student_id                  VARCHAR(50),             -- If won → student ID assigned

    -- Measures
    closed_sale_count           INT NOT NULL DEFAULT 1,  -- Additive: always 1
    is_won                      BOOLEAN NOT NULL,        -- For easy filtering
    days_lead_to_close          INT,                     -- Additive: lead_created→closed
    days_opp_to_close           INT,                     -- Additive: opp_created→closed
    total_interactions          INT,                     -- Additive: # interactions before close
    total_appointments          INT,                     -- Additive: # appointments before close

    -- Revenue (from opportunity_account_remain)
    total_due                   NUMERIC(18,4) DEFAULT 0, -- Additive
    paid_amount                 NUMERIC(18,4) DEFAULT 0, -- Additive
    remaining_balance           NUMERIC(18,4) DEFAULT 0, -- Semi-additive (point-in-time)

    -- Metadata
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    etl_batch_id                INT
);

CREATE INDEX idx_fact_closed_sale_date ON fact_closed_sale (closed_date_key);
CREATE INDEX idx_fact_closed_sale_status ON fact_closed_sale (closed_sale_status_key);
CREATE INDEX idx_fact_closed_sale_staff ON fact_closed_sale (staff_key);
CREATE INDEX idx_fact_closed_sale_dedup ON fact_closed_sale (closed_sale_id);


-- ============================================
-- FACT 4: fact_payment
-- Grain: One row per fee line item in a receipt
-- Source: opportunity_receipt_fee (2K rows)
-- Business: การชำระค่าธรรมเนียม
-- ============================================
DROP TABLE IF EXISTS fact_payment CASCADE;

CREATE TABLE fact_payment (
    -- Surrogate FKs
    receipt_date_key            INT NOT NULL REFERENCES dim_date(date_key),
    staff_key                   INT NOT NULL REFERENCES dim_staff(staff_key),
    lead_key                    INT NOT NULL REFERENCES dim_lead(lead_key),
    opportunity_state_key       INT REFERENCES dim_opportunity_state(opportunity_state_key),

    -- Degenerate dimensions
    receipt_fee_id              VARCHAR(36) NOT NULL,     -- PK from source
    opportunity_id              VARCHAR(36) NOT NULL,
    receipt_id                  VARCHAR(36) NOT NULL,
    receipt_number              VARCHAR(50) NOT NULL,
    fee_id                      VARCHAR(36) NOT NULL,
    fee_name                    VARCHAR(255) NOT NULL,

    -- Measures
    fee_unit_price              NUMERIC(18,4) NOT NULL,   -- Non-additive
    fee_qty                     INT NOT NULL,             -- Additive
    fee_total_amount            NUMERIC(18,4) NOT NULL,   -- Additive
    receipt_total_amount        NUMERIC(18,4) NOT NULL,   -- Semi-additive (receipt level)
    payment_count               INT NOT NULL DEFAULT 1,   -- Additive

    -- Metadata
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    etl_batch_id                INT
);

CREATE INDEX idx_fact_payment_date ON fact_payment (receipt_date_key);
CREATE INDEX idx_fact_payment_dedup ON fact_payment (receipt_fee_id);


-- ============================================
-- FACT 5: fact_lead_pipeline (Accumulating Snapshot)
-- Grain: One row per lead — tracking lifecycle dates
-- Source: lead + opportunity + closed_sale + aggregated interactions
-- Business: ดู funnel conversion + velocity
-- ============================================
DROP TABLE IF EXISTS fact_lead_pipeline CASCADE;

CREATE TABLE fact_lead_pipeline (
    -- Surrogate FKs
    lead_key                    INT NOT NULL REFERENCES dim_lead(lead_key),
    staff_key                   INT REFERENCES dim_staff(staff_key),
    school_key                  INT REFERENCES dim_school(school_key),
    province_key                INT REFERENCES dim_province(province_key),
    program_type_key            INT REFERENCES dim_program_type(program_type_key),
    channel_key                 INT REFERENCES dim_channel(channel_key),
    lead_source_key             INT REFERENCES dim_lead_source(lead_source_key),
    target_group_key            INT REFERENCES dim_target_group(target_group_key),
    education_level_key         INT REFERENCES dim_education_level(education_level_key),
    curriculum_key              INT REFERENCES dim_curriculum(curriculum_key),  -- Primary interest

    -- Milestone date keys (accumulating — filled as lead progresses)
    lead_created_date_key       INT REFERENCES dim_date(date_key),
    first_contact_date_key      INT REFERENCES dim_date(date_key),
    first_appointment_date_key  INT REFERENCES dim_date(date_key),
    opportunity_created_date_key INT REFERENCES dim_date(date_key),
    application_date_key        INT REFERENCES dim_date(date_key),
    closed_date_key             INT REFERENCES dim_date(date_key),

    -- Degenerate dimensions
    lead_id                     VARCHAR(36) NOT NULL UNIQUE,
    opportunity_id              VARCHAR(36),
    opportunity_no              VARCHAR(50),
    student_id                  VARCHAR(50),

    -- Current state
    current_lead_state_key      INT REFERENCES dim_lead_state(lead_state_key),
    current_opp_state_key       INT REFERENCES dim_opportunity_state(opportunity_state_key),
    closed_sale_status_key      INT REFERENCES dim_closed_sale_status(closed_sale_status_key),

    -- Measures: Velocity (days between milestones)
    days_to_first_contact       INT,              -- lead_created → first interaction
    days_to_first_appointment   INT,              -- lead_created → first appointment
    days_to_opportunity         INT,              -- lead_created → opportunity
    days_to_application         INT,              -- lead_created → application form
    days_to_close               INT,              -- lead_created → closed_sale
    total_pipeline_days         INT,              -- lead_created → today (or closed)

    -- Measures: Activity counts
    total_interactions          INT DEFAULT 0,     -- Additive
    total_appointments          INT DEFAULT 0,     -- Additive
    total_calls                 INT DEFAULT 0,     -- Additive
    total_call_duration_sec     INT DEFAULT 0,     -- Additive

    -- Revenue
    total_due                   NUMERIC(18,4) DEFAULT 0,
    paid_amount                 NUMERIC(18,4) DEFAULT 0,
    remaining_balance           NUMERIC(18,4) DEFAULT 0,

    -- Flags
    is_won                      BOOLEAN,
    is_lost                     BOOLEAN,
    is_active                   BOOLEAN NOT NULL DEFAULT TRUE,
    is_duplicate                BOOLEAN NOT NULL DEFAULT FALSE,

    -- Metadata
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    etl_updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    etl_batch_id                INT
);

CREATE INDEX idx_fact_pipeline_lead ON fact_lead_pipeline (lead_key);
CREATE INDEX idx_fact_pipeline_status ON fact_lead_pipeline (closed_sale_status_key);
CREATE INDEX idx_fact_pipeline_staff ON fact_lead_pipeline (staff_key);
CREATE INDEX idx_fact_pipeline_active ON fact_lead_pipeline (is_active) WHERE is_active;


-- ============================================
-- FACT 6: fact_kpi_target (Factless Fact / Target vs Actual)
-- Grain: One row per target per curriculum per edu_year/sem
-- Source: target + kpi_configuration
-- Business: เป้ารับนักศึกษา vs จริง
-- ============================================
DROP TABLE IF EXISTS fact_kpi_target CASCADE;

CREATE TABLE fact_kpi_target (
    -- Surrogate FKs
    curriculum_key              INT NOT NULL REFERENCES dim_curriculum(curriculum_key),
    program_type_key            INT NOT NULL REFERENCES dim_program_type(program_type_key),
    target_group_key            INT NOT NULL REFERENCES dim_target_group(target_group_key),
    school_key                  INT REFERENCES dim_school(school_key),

    -- Degenerate dimensions
    target_id                   VARCHAR(36) NOT NULL,
    education_year              INT NOT NULL,
    education_sem               INT NOT NULL,

    -- Measures
    target_students             INT NOT NULL DEFAULT 0,  -- Additive: plan number
    plan_student_amount         INT,                     -- From kpi_configuration
    monthly_target              INT,                     -- From kpi_configuration

    -- Metadata
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    etl_batch_id                INT
);

CREATE INDEX idx_fact_kpi_target_dedup ON fact_kpi_target (target_id);
CREATE INDEX idx_fact_kpi_curriculum ON fact_kpi_target (curriculum_key);
