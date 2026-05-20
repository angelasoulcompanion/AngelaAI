-- ============================================
-- CRM WTU Data Warehouse — ETL: Dimension Loading
-- Source: crm_wtu.public (via FDW schema "src")
-- Target: crm_wtu_dw.public
-- Strategy: INSERT ... ON CONFLICT (upsert) — no TRUNCATE to avoid FK errors
-- ============================================


-- ============================================
-- ETL: dim_program_type (Upsert — 4 rows)
-- ============================================
INSERT INTO dim_program_type (program_type_id, program_type_name, program_type_name_en, zone_group_id)
SELECT id, name, name_en, zone_group_id
FROM src.program_type
WHERE status = 'Active'
ON CONFLICT (program_type_id) DO UPDATE SET
    program_type_name = EXCLUDED.program_type_name,
    program_type_name_en = EXCLUDED.program_type_name_en,
    zone_group_id = EXCLUDED.zone_group_id;


-- ============================================
-- ETL: dim_channel (Upsert — 9 rows)
-- ============================================
INSERT INTO dim_channel (channel_id, channel_name, channel_name_en)
SELECT id, name, name_en
FROM src.channel
WHERE status = 'Active'
ON CONFLICT (channel_id) DO UPDATE SET
    channel_name = EXCLUDED.channel_name,
    channel_name_en = EXCLUDED.channel_name_en;


-- ============================================
-- ETL: dim_interaction_type (Upsert — 5 rows)
-- ============================================
INSERT INTO dim_interaction_type (interaction_type_id, interaction_type_name, interaction_type_name_en)
SELECT id, name, name_en
FROM src.interaction_type
WHERE status = 'Active'
ON CONFLICT (interaction_type_id) DO UPDATE SET
    interaction_type_name = EXCLUDED.interaction_type_name,
    interaction_type_name_en = EXCLUDED.interaction_type_name_en;


-- ============================================
-- ETL: dim_interaction_outcome (Upsert — 33 rows)
-- ============================================
INSERT INTO dim_interaction_outcome (interaction_outcome_id, interaction_outcome_name,
    interaction_outcome_name_en, program_type_id, sequence)
SELECT id, name, name_en, program_type_id, sequence
FROM src.interaction_outcome
WHERE status = 'Active'
ON CONFLICT (interaction_outcome_id) DO UPDATE SET
    interaction_outcome_name = EXCLUDED.interaction_outcome_name,
    interaction_outcome_name_en = EXCLUDED.interaction_outcome_name_en,
    program_type_id = EXCLUDED.program_type_id,
    sequence = EXCLUDED.sequence;


-- ============================================
-- ETL: dim_lead_state (Upsert — 12 rows)
-- ============================================
INSERT INTO dim_lead_state (lead_state_id, lead_state_name, lead_state_name_en,
    state_locked, sequence, program_type_id)
SELECT id, name, name_en, state_locked, sequence, program_type_id
FROM src.lead_state
WHERE status = 'Active'
ON CONFLICT (lead_state_id) DO UPDATE SET
    lead_state_name = EXCLUDED.lead_state_name,
    lead_state_name_en = EXCLUDED.lead_state_name_en,
    state_locked = EXCLUDED.state_locked,
    sequence = EXCLUDED.sequence,
    program_type_id = EXCLUDED.program_type_id;


-- ============================================
-- ETL: dim_opportunity_state (Upsert — 14 rows)
-- ============================================
INSERT INTO dim_opportunity_state (opportunity_state_id, opportunity_state_name,
    opportunity_state_name_en, state_locked, closed_sale_status_id, sequence, program_type_id)
SELECT id, name, name_en, state_locked, closed_sale_status_id, sequence, program_type_id
FROM src.opportunity_state
WHERE status = 'Active'
ON CONFLICT (opportunity_state_id) DO UPDATE SET
    opportunity_state_name = EXCLUDED.opportunity_state_name,
    opportunity_state_name_en = EXCLUDED.opportunity_state_name_en,
    state_locked = EXCLUDED.state_locked,
    closed_sale_status_id = EXCLUDED.closed_sale_status_id,
    sequence = EXCLUDED.sequence,
    program_type_id = EXCLUDED.program_type_id;


-- ============================================
-- ETL: dim_application_form_state (Upsert — 9 rows)
-- ============================================
INSERT INTO dim_application_form_state (application_form_state_id,
    application_form_state_name, application_form_state_name_en, sequence)
SELECT id, name, name_en, sequence
FROM src.application_form_state
WHERE status = 'Active'
ON CONFLICT (application_form_state_id) DO UPDATE SET
    application_form_state_name = EXCLUDED.application_form_state_name,
    application_form_state_name_en = EXCLUDED.application_form_state_name_en,
    sequence = EXCLUDED.sequence;


-- ============================================
-- ETL: dim_appointment_type (Upsert — 3 rows)
-- ============================================
INSERT INTO dim_appointment_type (appointment_type_id, appointment_type_name, appointment_type_name_en)
SELECT id, name, name_en
FROM src.appointment_type
WHERE status = 'Active'
ON CONFLICT (appointment_type_id) DO UPDATE SET
    appointment_type_name = EXCLUDED.appointment_type_name,
    appointment_type_name_en = EXCLUDED.appointment_type_name_en;


-- ============================================
-- ETL: dim_lose_reason (Upsert — 11 rows)
-- ============================================
INSERT INTO dim_lose_reason (lose_reason_id, lose_reason_name, lose_reason_name_en)
SELECT id, name, name_en
FROM src.lose_reason_type
WHERE status = 'Active'
ON CONFLICT (lose_reason_id) DO UPDATE SET
    lose_reason_name = EXCLUDED.lose_reason_name,
    lose_reason_name_en = EXCLUDED.lose_reason_name_en;


-- ============================================
-- ETL: dim_closed_sale_status (Upsert — 2 rows)
-- ============================================
INSERT INTO dim_closed_sale_status (closed_sale_status_id, closed_sale_status_name, closed_sale_status_name_en)
SELECT id, name, name_en
FROM src.closed_sale_status
WHERE status = 'Active'
ON CONFLICT (closed_sale_status_id) DO UPDATE SET
    closed_sale_status_name = EXCLUDED.closed_sale_status_name,
    closed_sale_status_name_en = EXCLUDED.closed_sale_status_name_en;


-- ============================================
-- ETL: dim_education_level (Upsert — 20 rows)
-- ============================================
INSERT INTO dim_education_level (education_level_id, education_level_name, education_level_name_en,
    use_for_bachelor, use_for_master, use_for_doctor, use_for_certificate, program_type_id)
SELECT id, name, name_en,
    use_for_bachelor, use_for_master, use_for_doctor, use_for_certificate, program_type_id
FROM src.education_level
WHERE status = 'Active'
ON CONFLICT (education_level_id) DO UPDATE SET
    education_level_name = EXCLUDED.education_level_name,
    education_level_name_en = EXCLUDED.education_level_name_en,
    use_for_bachelor = EXCLUDED.use_for_bachelor,
    use_for_master = EXCLUDED.use_for_master,
    use_for_doctor = EXCLUDED.use_for_doctor,
    use_for_certificate = EXCLUDED.use_for_certificate,
    program_type_id = EXCLUDED.program_type_id;


-- ============================================
-- ETL: dim_school (Upsert — 269 rows)
-- ============================================
INSERT INTO dim_school (school_id, school_name)
SELECT id, name
FROM src.school
WHERE status = 'Active'
ON CONFLICT (school_id) DO UPDATE SET
    school_name = EXCLUDED.school_name;


-- ============================================
-- ETL: dim_staff (SCD Type 2 — 50 rows)
-- ============================================
-- Step 1: Expire changed records
UPDATE dim_staff SET
    is_current = FALSE,
    expiration_date = CURRENT_DATE
WHERE is_current = TRUE
  AND staff_id IN (
    SELECT s.id FROM src.staff s
    INNER JOIN dim_staff d ON d.staff_id = s.id AND d.is_current = TRUE
    WHERE s.status = 'Active'
      AND (d.staff_code IS DISTINCT FROM s.code
           OR d.position_id IS DISTINCT FROM s.position_id
           OR d.program_type_id IS DISTINCT FROM s.program_type_id)
  );

-- Step 2: Insert new/changed records
INSERT INTO dim_staff (staff_id, staff_code, staff_name, staff_surname, staff_full_name,
    email, phone_number, position_id, program_type_id, program_type_name,
    effective_date, expiration_date, is_current)
SELECT
    s.id, s.code, s.name, s.surname, s.name || ' ' || s.surname,
    s.email, s.phone_number, s.position_id, s.program_type_id,
    pt.name,
    CURRENT_DATE, '9999-12-31'::DATE, TRUE
FROM src.staff s
LEFT JOIN src.program_type pt ON pt.id = s.program_type_id
WHERE s.status = 'Active'
  AND NOT EXISTS (
    SELECT 1 FROM dim_staff d
    WHERE d.staff_id = s.id AND d.is_current = TRUE
  );


-- ============================================
-- ETL: dim_province (Upsert — derived from lead data)
-- ============================================
-- Dedupe: one name per province_code (src has code 0 mapped to both
-- 'กรุงเทพมหานคร' and 'ต่างประเทศ'); pick the most frequent name to avoid
-- "ON CONFLICT cannot affect row a second time".
INSERT INTO dim_province (province_code, province_name)
SELECT province_code, province_name
FROM (
    SELECT province_code, province_name,
           ROW_NUMBER() OVER (PARTITION BY province_code ORDER BY COUNT(*) DESC) AS rn
    FROM src.lead
    WHERE province_code IS NOT NULL AND province_name IS NOT NULL
    GROUP BY province_code, province_name
) t
WHERE rn = 1
ON CONFLICT (province_code) DO UPDATE SET
    province_name = EXCLUDED.province_name;


-- ============================================
-- ETL: dim_curriculum (Upsert — derived from lead_interest)
-- ============================================
INSERT INTO dim_curriculum (
    study_level_id, campus_id, fac_type_id, division_id, department_id,
    concentrate_id, curriculum_id, study_level_name, campus_name, fac_type_name,
    division_name, department_name, concentrate_name, curriculum_name, curriculum_year,
    zone_id, zone_name, zone_group_id, zone_group_name,
    enroll_faculty_id, enroll_faculty_code, enroll_faculty_name
)
SELECT DISTINCT ON (study_level_id, campus_id, fac_type_id, division_id, department_id, concentrate_id, curriculum_id)
    study_level_id, campus_id, fac_type_id, division_id, department_id,
    concentrate_id, curriculum_id, study_level_name, campus_name, fac_type_name,
    division_name, department_name, concentrate_name, curriculum_name, curriculum_year,
    zone_id, zone_name, zone_group_id, zone_group_name,
    enroll_faculty_id, enroll_faculty_code, enroll_faculty_name
FROM (
    SELECT study_level_id, campus_id, fac_type_id, division_id, department_id,
           concentrate_id, curriculum_id, study_level_name, campus_name, fac_type_name,
           division_name, department_name, concentrate_name, curriculum_name, curriculum_year,
           zone_id, zone_name, zone_group_id, zone_group_name,
           enroll_faculty_id, enroll_faculty_code, enroll_faculty_name
    FROM src.lead_interest WHERE status = 'Active'
    UNION ALL
    SELECT study_level_id, campus_id, fac_type_id, division_id, department_id,
           concentrate_id, curriculum_id, study_level_name, campus_name, fac_type_name,
           division_name, department_name, concentrate_name, curriculum_name, curriculum_year,
           zone_id, zone_name, zone_group_id, zone_group_name,
           enroll_faculty_id, enroll_faculty_code, enroll_faculty_name
    FROM src.application_form_curriculum WHERE status = 'Active'
) combined
ORDER BY study_level_id, campus_id, fac_type_id, division_id, department_id, concentrate_id, curriculum_id,
    curriculum_year DESC NULLS LAST
ON CONFLICT (study_level_id, campus_id, fac_type_id, division_id, department_id, concentrate_id, curriculum_id)
DO UPDATE SET
    curriculum_name = EXCLUDED.curriculum_name,
    curriculum_year = EXCLUDED.curriculum_year;


-- ============================================
-- ETL: dim_lead_source (Upsert — derived from lead)
-- ============================================
INSERT INTO dim_lead_source (lead_from_type_id, lead_from_type_name, source, ads_campaign, social_media)
SELECT DISTINCT
    l.lead_from_type_id,
    lft.name,
    COALESCE(l.source, 'N/A'),
    COALESCE(l.ads_campaign, 'N/A'),
    COALESCE(l.social_media, 'N/A')
FROM src.lead l
LEFT JOIN src.lead_from_type lft ON lft.id = l.lead_from_type_id
ON CONFLICT (lead_from_type_id, source, ads_campaign, social_media) DO UPDATE SET
    lead_from_type_name = EXCLUDED.lead_from_type_name;


-- ============================================
-- ETL: dim_target_group (Upsert)
-- ============================================
INSERT INTO dim_target_group (target_group_id, target_group_name,
    target_type_id, target_type_name, target_type_is_school,
    target_sub_type_id, target_sub_type_name,
    education_year, education_sem, program_type_id)
SELECT DISTINCT ON (tg.id)
    tg.id, tg.name,
    tt.id, tt.name, tt.is_school,
    tst.id, tst.name,
    tg.education_year, tg.education_sem, tg.program_type_id
FROM src.target_group tg
LEFT JOIN src.target t ON t.target_group_id = tg.id AND t.status = 'Active'
LEFT JOIN src.target_type tt ON tt.id = t.target_type_id
LEFT JOIN src.target_sub_type tst ON tst.id = t.target_sub_type_id
WHERE tg.status = 'Active'
ORDER BY tg.id
ON CONFLICT (target_group_id) DO UPDATE SET
    target_group_name = EXCLUDED.target_group_name,
    target_type_id = EXCLUDED.target_type_id,
    target_type_name = EXCLUDED.target_type_name,
    education_year = EXCLUDED.education_year,
    education_sem = EXCLUDED.education_sem,
    program_type_id = EXCLUDED.program_type_id;


-- ============================================
-- ETL: dim_lead (SCD Type 2 — 61K rows)
-- ============================================
-- Step 1: Expire changed records
UPDATE dim_lead SET
    is_current = FALSE,
    expiration_date = CURRENT_DATE
WHERE is_current = TRUE
  AND lead_id IN (
    SELECT l.id FROM src.lead l
    INNER JOIN dim_lead d ON d.lead_id = l.id AND d.is_current = TRUE
    WHERE l.status = 'Active'
      AND (d.lead_state_id IS DISTINCT FROM l.lead_state_id
           OR d.staff_id IS DISTINCT FROM l.staff_id
           OR d.is_potential_duplicate IS DISTINCT FROM l.is_potential_duplicate)
  );

-- Step 2: Insert new/changed
INSERT INTO dim_lead (
    lead_id, lead_name, lead_surname, lead_full_name, lead_full_name_en,
    prename, phone, email, line_id, citizen_id,
    lead_state_id, province_code, province_name, education_level_id,
    program_type_id, lead_from_type_id, source, ads_campaign, social_media,
    target_id, target_group_id, target_type_id, target_sub_type_id,
    school_id, staff_id, is_potential_duplicate, merged_to_lead_id,
    effective_date, expiration_date, is_current
)
SELECT
    l.id, l.name, l.surname,
    COALESCE(l.prename, '') || l.name || ' ' || l.surname,
    NULLIF(COALESCE(l.prename_en, '') || COALESCE(l.name_en, '') || ' ' || COALESCE(l.surname_en, ''), ' '),
    l.prename, l.phone, l.email, l.line_id, l.citizen_id,
    l.lead_state_id, l.province_code, l.province_name, l.education_level_id,
    l.program_type_id, l.lead_from_type_id, l.source, l.ads_campaign, l.social_media,
    l.target_id, l.target_group_id, l.target_type_id, l.target_sub_type_id,
    l.school_id, l.staff_id, l.is_potential_duplicate, l.merged_to_lead_id,
    CURRENT_DATE, '9999-12-31'::DATE, TRUE
FROM src.lead l
WHERE l.status = 'Active'
  AND NOT EXISTS (
    SELECT 1 FROM dim_lead d
    WHERE d.lead_id = l.id AND d.is_current = TRUE
  );
