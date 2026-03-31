-- ============================================
-- CRM WTU Data Warehouse — All Dimensions
-- Target: crm_wtu_dw (PostgreSQL)
-- ============================================

-- ============================================
-- dim_staff — Recruitment Officers
-- SCD Type 2 (track position/program changes)
-- Source: staff
-- ============================================
DROP TABLE IF EXISTS dim_staff CASCADE;

CREATE TABLE dim_staff (
    staff_key           SERIAL PRIMARY KEY,
    staff_id            VARCHAR(36) NOT NULL,          -- Natural key
    staff_code          VARCHAR(20),
    staff_name          VARCHAR(160) NOT NULL,
    staff_surname       VARCHAR(160) NOT NULL,
    staff_full_name     VARCHAR(320) NOT NULL,         -- Derived: name || ' ' || surname
    email               VARCHAR(255),
    phone_number        VARCHAR(60),
    position_id         VARCHAR(36),
    program_type_id     VARCHAR(36),
    program_type_name   VARCHAR(160),
    -- SCD Type 2
    effective_date      DATE NOT NULL DEFAULT '1900-01-01',
    expiration_date     DATE NOT NULL DEFAULT '9999-12-31',
    is_current          BOOLEAN NOT NULL DEFAULT TRUE,
    etl_loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dim_staff_natural ON dim_staff (staff_id, is_current);

-- Unknown member
INSERT INTO dim_staff (staff_key, staff_id, staff_code, staff_name, staff_surname, staff_full_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'UNK', 'ไม่ทราบ', '', 'ไม่ทราบ');


-- ============================================
-- dim_school — Feeder Schools
-- SCD Type 1 (overwrite)
-- Source: school
-- ============================================
DROP TABLE IF EXISTS dim_school CASCADE;

CREATE TABLE dim_school (
    school_key          SERIAL PRIMARY KEY,
    school_id           VARCHAR(36) NOT NULL UNIQUE,
    school_name         VARCHAR(255) NOT NULL,
    -- Add more attributes if school table has them
    effective_date      DATE NOT NULL DEFAULT '1900-01-01',
    expiration_date     DATE NOT NULL DEFAULT '9999-12-31',
    is_current          BOOLEAN NOT NULL DEFAULT TRUE,
    etl_loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dim_school_natural ON dim_school (school_id, is_current);

INSERT INTO dim_school (school_key, school_id, school_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_curriculum — Academic Hierarchy (Conformed)
-- Grain: unique combination of hierarchy levels
-- Source: lead_interest, application_form_curriculum, kpi_configuration, target
-- ============================================
DROP TABLE IF EXISTS dim_curriculum CASCADE;

CREATE TABLE dim_curriculum (
    curriculum_key          SERIAL PRIMARY KEY,
    -- Natural composite key
    study_level_id          VARCHAR(2) NOT NULL,
    campus_id               VARCHAR(2) NOT NULL,
    fac_type_id             VARCHAR(2) NOT NULL,
    division_id             VARCHAR(2) NOT NULL,
    department_id           VARCHAR(2) NOT NULL,
    concentrate_id          VARCHAR(2) NOT NULL,
    curriculum_id           VARCHAR(20) NOT NULL,
    -- Descriptive attributes (hierarchy labels)
    study_level_name        VARCHAR(255) NOT NULL,        -- ปริญญาตรี, ปริญญาโท...
    campus_name             VARCHAR(255) NOT NULL,
    fac_type_name           VARCHAR(255) NOT NULL,        -- Faculty type
    division_name           VARCHAR(255) NOT NULL,
    department_name         VARCHAR(255) NOT NULL,
    concentrate_name        VARCHAR(255) NOT NULL,        -- สาขาวิชาเอก
    curriculum_name         VARCHAR(255) NOT NULL,
    curriculum_year         INT,
    -- Zone hierarchy
    zone_id                 VARCHAR(2),
    zone_name               VARCHAR(255),
    zone_group_id           VARCHAR(2),
    zone_group_name         VARCHAR(255),
    -- Enrollment faculty mapping
    enroll_faculty_id       INT,
    enroll_faculty_code     VARCHAR(4),
    enroll_faculty_name     VARCHAR(255),
    --
    etl_loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (study_level_id, campus_id, fac_type_id, division_id, department_id, concentrate_id, curriculum_id)
);

CREATE INDEX idx_dim_curriculum_study_level ON dim_curriculum (study_level_id);
CREATE INDEX idx_dim_curriculum_campus ON dim_curriculum (campus_id);
CREATE INDEX idx_dim_curriculum_department ON dim_curriculum (department_id);

INSERT INTO dim_curriculum (curriculum_key, study_level_id, campus_id, fac_type_id,
    division_id, department_id, concentrate_id, curriculum_id,
    study_level_name, campus_name, fac_type_name, division_name,
    department_name, concentrate_name, curriculum_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, '-1', '-1', '-1', '-1', '-1', '-1', '-1',
    'ไม่ทราบ', 'ไม่ทราบ', 'ไม่ทราบ', 'ไม่ทราบ',
    'ไม่ทราบ', 'ไม่ทราบ', 'ไม่ทราบ');


-- ============================================
-- dim_province — Geographic Dimension
-- Source: lead.province_code/name, application addresses
-- ============================================
DROP TABLE IF EXISTS dim_province CASCADE;

CREATE TABLE dim_province (
    province_key        SERIAL PRIMARY KEY,
    province_code       INT NOT NULL UNIQUE,
    province_name       VARCHAR(160) NOT NULL,
    region_name         VARCHAR(60),                -- ภาคเหนือ, ภาคกลาง, etc.
    etl_loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_province (province_key, province_code, province_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, -1, 'ไม่ทราบ');


-- ============================================
-- dim_program_type — Program Classification
-- Source: program_type (4 rows)
-- ============================================
DROP TABLE IF EXISTS dim_program_type CASCADE;

CREATE TABLE dim_program_type (
    program_type_key    SERIAL PRIMARY KEY,
    program_type_id     VARCHAR(36) NOT NULL UNIQUE,
    program_type_name   VARCHAR(160) NOT NULL,
    program_type_name_en VARCHAR(160),
    zone_group_id       VARCHAR(36),
    etl_loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_program_type (program_type_key, program_type_id, program_type_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_channel — Marketing Channel
-- Source: channel (9 rows)
-- ============================================
DROP TABLE IF EXISTS dim_channel CASCADE;

CREATE TABLE dim_channel (
    channel_key         SERIAL PRIMARY KEY,
    channel_id          VARCHAR(36) NOT NULL UNIQUE,
    channel_name        VARCHAR(160) NOT NULL,
    channel_name_en     VARCHAR(160),
    etl_loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_channel (channel_key, channel_id, channel_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_interaction_type — Contact Method
-- Source: interaction_type (5 rows)
-- ============================================
DROP TABLE IF EXISTS dim_interaction_type CASCADE;

CREATE TABLE dim_interaction_type (
    interaction_type_key    SERIAL PRIMARY KEY,
    interaction_type_id     VARCHAR(36) NOT NULL UNIQUE,
    interaction_type_name   VARCHAR(160) NOT NULL,
    interaction_type_name_en VARCHAR(160),
    etl_loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_interaction_type (interaction_type_key, interaction_type_id, interaction_type_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_interaction_outcome — Contact Result
-- Source: interaction_outcome (33 rows)
-- ============================================
DROP TABLE IF EXISTS dim_interaction_outcome CASCADE;

CREATE TABLE dim_interaction_outcome (
    interaction_outcome_key     SERIAL PRIMARY KEY,
    interaction_outcome_id      VARCHAR(36) NOT NULL UNIQUE,
    interaction_outcome_name    VARCHAR(160) NOT NULL,
    interaction_outcome_name_en VARCHAR(160),
    program_type_id             VARCHAR(36),
    sequence                    INT,
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_interaction_outcome (interaction_outcome_key, interaction_outcome_id, interaction_outcome_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_lead_state — Lead Pipeline Stage
-- Source: lead_state (12 rows)
-- ============================================
DROP TABLE IF EXISTS dim_lead_state CASCADE;

CREATE TABLE dim_lead_state (
    lead_state_key      SERIAL PRIMARY KEY,
    lead_state_id       VARCHAR(36) NOT NULL UNIQUE,
    lead_state_name     VARCHAR(160) NOT NULL,
    lead_state_name_en  VARCHAR(160),
    state_locked        BOOLEAN NOT NULL DEFAULT FALSE,
    sequence            INT NOT NULL DEFAULT 0,
    program_type_id     VARCHAR(36),
    etl_loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_lead_state (lead_state_key, lead_state_id, lead_state_name, sequence)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ', 0);


-- ============================================
-- dim_opportunity_state — Opportunity Pipeline Stage
-- Source: opportunity_state (14 rows)
-- ============================================
DROP TABLE IF EXISTS dim_opportunity_state CASCADE;

CREATE TABLE dim_opportunity_state (
    opportunity_state_key       SERIAL PRIMARY KEY,
    opportunity_state_id        VARCHAR(36) NOT NULL UNIQUE,
    opportunity_state_name      VARCHAR(160) NOT NULL,
    opportunity_state_name_en   VARCHAR(160),
    state_locked                BOOLEAN NOT NULL DEFAULT FALSE,
    closed_sale_status_id       VARCHAR(36),           -- Links to Win/Lose
    sequence                    INT NOT NULL DEFAULT 0,
    program_type_id             VARCHAR(36),
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_opportunity_state (opportunity_state_key, opportunity_state_id, opportunity_state_name, sequence)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ', 0);


-- ============================================
-- dim_application_form_state — Application Status
-- Source: application_form_state (9 rows)
-- ============================================
DROP TABLE IF EXISTS dim_application_form_state CASCADE;

CREATE TABLE dim_application_form_state (
    application_form_state_key  SERIAL PRIMARY KEY,
    application_form_state_id   VARCHAR(36) NOT NULL UNIQUE,
    application_form_state_name VARCHAR(160) NOT NULL,
    application_form_state_name_en VARCHAR(160),
    sequence                    INT NOT NULL DEFAULT 0,
    etl_loaded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_application_form_state (application_form_state_key, application_form_state_id, application_form_state_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_appointment_type — Meeting Type
-- Source: appointment_type (3 rows)
-- ============================================
DROP TABLE IF EXISTS dim_appointment_type CASCADE;

CREATE TABLE dim_appointment_type (
    appointment_type_key    SERIAL PRIMARY KEY,
    appointment_type_id     VARCHAR(36) NOT NULL UNIQUE,
    appointment_type_name   VARCHAR(160) NOT NULL,
    appointment_type_name_en VARCHAR(160),
    etl_loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_appointment_type (appointment_type_key, appointment_type_id, appointment_type_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_lose_reason — Why Deal Was Lost
-- Source: lose_reason_type (11 rows)
-- ============================================
DROP TABLE IF EXISTS dim_lose_reason CASCADE;

CREATE TABLE dim_lose_reason (
    lose_reason_key     SERIAL PRIMARY KEY,
    lose_reason_id      VARCHAR(36) NOT NULL UNIQUE,
    lose_reason_name    VARCHAR(160) NOT NULL,
    lose_reason_name_en VARCHAR(160),
    etl_loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_lose_reason (lose_reason_key, lose_reason_id, lose_reason_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ / ไม่ระบุ');


-- ============================================
-- dim_closed_sale_status — Win / Lose
-- Source: closed_sale_status (2 rows)
-- ============================================
DROP TABLE IF EXISTS dim_closed_sale_status CASCADE;

CREATE TABLE dim_closed_sale_status (
    closed_sale_status_key  SERIAL PRIMARY KEY,
    closed_sale_status_id   VARCHAR(36) NOT NULL UNIQUE,
    closed_sale_status_name VARCHAR(160) NOT NULL,
    closed_sale_status_name_en VARCHAR(160),
    etl_loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_closed_sale_status (closed_sale_status_key, closed_sale_status_id, closed_sale_status_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_lead_source — Lead Origin
-- Source: lead_from_type (3 rows) + lead.source, lead.ads_campaign
-- ============================================
DROP TABLE IF EXISTS dim_lead_source CASCADE;

CREATE TABLE dim_lead_source (
    lead_source_key     SERIAL PRIMARY KEY,
    lead_from_type_id   VARCHAR(36),
    lead_from_type_name VARCHAR(160),
    source              VARCHAR(255),                 -- lead.source field
    ads_campaign        VARCHAR(255),                 -- lead.ads_campaign
    social_media        VARCHAR(255),                 -- lead.social_media
    etl_loaded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (lead_from_type_id, source, ads_campaign, social_media)
);

INSERT INTO dim_lead_source (lead_source_key, lead_from_type_name, source)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'ไม่ทราบ', 'ไม่ทราบ');


-- ============================================
-- dim_target_group — Recruitment Target Grouping
-- Source: target_group, target_type, target_sub_type
-- ============================================
DROP TABLE IF EXISTS dim_target_group CASCADE;

CREATE TABLE dim_target_group (
    target_group_key        SERIAL PRIMARY KEY,
    target_group_id         VARCHAR(36) NOT NULL UNIQUE,
    target_group_name       VARCHAR(255) NOT NULL,
    target_type_id          VARCHAR(36),
    target_type_name        VARCHAR(160),
    target_type_is_school   BOOLEAN DEFAULT FALSE,
    target_sub_type_id      VARCHAR(36),
    target_sub_type_name    VARCHAR(160),
    education_year          INT,
    education_sem           INT,
    program_type_id         VARCHAR(36),
    etl_loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dim_target_group_natural ON dim_target_group (target_group_id);

INSERT INTO dim_target_group (target_group_key, target_group_id, target_group_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_education_level — Lead's Prior Education
-- Source: education_level (20 rows)
-- ============================================
DROP TABLE IF EXISTS dim_education_level CASCADE;

CREATE TABLE dim_education_level (
    education_level_key     SERIAL PRIMARY KEY,
    education_level_id      VARCHAR(36) NOT NULL UNIQUE,
    education_level_name    VARCHAR(255) NOT NULL,
    education_level_name_en VARCHAR(255),
    use_for_bachelor        BOOLEAN DEFAULT FALSE,
    use_for_master          BOOLEAN DEFAULT FALSE,
    use_for_doctor          BOOLEAN DEFAULT FALSE,
    use_for_certificate     BOOLEAN DEFAULT FALSE,
    program_type_id         VARCHAR(36),
    etl_loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO dim_education_level (education_level_key, education_level_id, education_level_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ');


-- ============================================
-- dim_lead — Lead (Prospective Student) Mini-Dimension
-- SCD Type 2 (track state changes)
-- Source: lead
-- ============================================
DROP TABLE IF EXISTS dim_lead CASCADE;

CREATE TABLE dim_lead (
    lead_key                SERIAL PRIMARY KEY,
    lead_id                 VARCHAR(36) NOT NULL,        -- Natural key
    lead_name               VARCHAR(160) NOT NULL,
    lead_surname            VARCHAR(160) NOT NULL,
    lead_full_name          VARCHAR(320) NOT NULL,       -- Derived
    lead_full_name_en       VARCHAR(320),
    prename                 VARCHAR(40),
    phone                   VARCHAR(60),
    email                   VARCHAR(60),
    line_id                 VARCHAR(100),
    citizen_id              VARCHAR(20),
    -- Current state
    lead_state_id           VARCHAR(36),
    -- Demographics
    province_code           INT,
    province_name           VARCHAR(160),
    education_level_id      VARCHAR(36),
    -- Source/Origin
    program_type_id         VARCHAR(36),
    lead_from_type_id       VARCHAR(36),
    source                  VARCHAR(255),
    ads_campaign            VARCHAR(255),
    social_media            VARCHAR(255),
    -- Target reference
    target_id               VARCHAR(36),
    target_group_id         VARCHAR(36),
    target_type_id          VARCHAR(36),
    target_sub_type_id      VARCHAR(36),
    school_id               VARCHAR(36),
    staff_id                VARCHAR(36),
    -- Duplicate tracking
    is_potential_duplicate   BOOLEAN DEFAULT FALSE,
    merged_to_lead_id       VARCHAR(36),
    -- SCD Type 2
    effective_date          DATE NOT NULL DEFAULT '1900-01-01',
    expiration_date         DATE NOT NULL DEFAULT '9999-12-31',
    is_current              BOOLEAN NOT NULL DEFAULT TRUE,
    etl_loaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dim_lead_natural ON dim_lead (lead_id, is_current);
CREATE INDEX idx_dim_lead_state ON dim_lead (lead_state_id) WHERE is_current;
CREATE INDEX idx_dim_lead_province ON dim_lead (province_code) WHERE is_current;

INSERT INTO dim_lead (lead_key, lead_id, lead_name, lead_surname, lead_full_name)
OVERRIDING SYSTEM VALUE
VALUES (-1, 'UNKNOWN', 'ไม่ทราบ', '', 'ไม่ทราบ');
