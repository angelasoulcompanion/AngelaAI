-- ============================================
-- CRM WTU Data Warehouse — Validation Queries
-- Run after each ETL load
-- ============================================

-- ============================================
-- 1. ROW COUNT RECONCILIATION
-- ============================================
SELECT '--- ROW COUNTS ---' AS section;

SELECT 'lead_interaction' AS source_table,
    (SELECT COUNT(*) FROM src.lead_interaction WHERE status = 'Active') AS source_rows,
    (SELECT COUNT(*) FROM fact_lead_interaction) AS fact_rows;

SELECT 'appointment' AS source_table,
    (SELECT COUNT(*) FROM src.appointment WHERE status = 'Active') AS source_rows,
    (SELECT COUNT(*) FROM fact_appointment) AS fact_rows;

SELECT 'closed_sale' AS source_table,
    (SELECT COUNT(*) FROM src.closed_sale WHERE status = 'Active') AS source_rows,
    (SELECT COUNT(*) FROM fact_closed_sale) AS fact_rows;

SELECT 'receipt_fee' AS source_table,
    (SELECT COUNT(*) FROM src.opportunity_receipt_fee WHERE status = 'Active') AS source_rows,
    (SELECT COUNT(*) FROM fact_payment) AS fact_rows;

SELECT 'lead (pipeline)' AS source_table,
    (SELECT COUNT(*) FROM src.lead WHERE status = 'Active') AS source_rows,
    (SELECT COUNT(*) FROM fact_lead_pipeline) AS fact_rows;


-- ============================================
-- 2. ORPHAN KEY DETECTION (FK = -1)
-- ============================================
SELECT '--- ORPHAN KEYS (fact_lead_interaction) ---' AS section;

SELECT 'staff_key' AS dimension, COUNT(*) FILTER (WHERE staff_key = -1) AS orphans,
       COUNT(*) AS total,
       ROUND(100.0 * COUNT(*) FILTER (WHERE staff_key = -1) / NULLIF(COUNT(*), 0), 2) AS pct
FROM fact_lead_interaction
UNION ALL
SELECT 'lead_key', COUNT(*) FILTER (WHERE lead_key = -1),
       COUNT(*), ROUND(100.0 * COUNT(*) FILTER (WHERE lead_key = -1) / NULLIF(COUNT(*), 0), 2)
FROM fact_lead_interaction
UNION ALL
SELECT 'interaction_type_key', COUNT(*) FILTER (WHERE interaction_type_key = -1),
       COUNT(*), ROUND(100.0 * COUNT(*) FILTER (WHERE interaction_type_key = -1) / NULLIF(COUNT(*), 0), 2)
FROM fact_lead_interaction
UNION ALL
SELECT 'contact_date_key', COUNT(*) FILTER (WHERE contact_date_key = -1),
       COUNT(*), ROUND(100.0 * COUNT(*) FILTER (WHERE contact_date_key = -1) / NULLIF(COUNT(*), 0), 2)
FROM fact_lead_interaction;

SELECT '--- ORPHAN KEYS (fact_closed_sale) ---' AS section;

SELECT 'staff_key' AS dimension, COUNT(*) FILTER (WHERE staff_key = -1) AS orphans,
       COUNT(*) AS total
FROM fact_closed_sale
UNION ALL
SELECT 'curriculum_key', COUNT(*) FILTER (WHERE curriculum_key = -1), COUNT(*)
FROM fact_closed_sale
UNION ALL
SELECT 'province_key', COUNT(*) FILTER (WHERE province_key = -1), COUNT(*)
FROM fact_closed_sale;


-- ============================================
-- 3. MEASURE RECONCILIATION
-- ============================================
SELECT '--- PAYMENT RECONCILIATION ---' AS section;

SELECT 'source' AS origin, SUM(fee_total_amount) AS total
FROM src.opportunity_receipt_fee WHERE status = 'Active'
UNION ALL
SELECT 'fact', SUM(fee_total_amount)
FROM fact_payment;


-- ============================================
-- 4. NULL MEASURE CHECK
-- ============================================
SELECT '--- NULL MEASURES ---' AS section;

SELECT 'fact_lead_interaction' AS fact_table,
    COUNT(*) FILTER (WHERE contact_date_key IS NULL) AS null_date
FROM fact_lead_interaction;

SELECT 'fact_payment' AS fact_table,
    COUNT(*) FILTER (WHERE fee_total_amount IS NULL) AS null_amount,
    COUNT(*) FILTER (WHERE fee_qty IS NULL) AS null_qty
FROM fact_payment;


-- ============================================
-- 5. DATE RANGE SANITY
-- ============================================
SELECT '--- DATE RANGES ---' AS section;

SELECT 'fact_lead_interaction' AS fact_table,
    MIN(dd.full_date) AS min_date, MAX(dd.full_date) AS max_date
FROM fact_lead_interaction f
JOIN dim_date dd ON f.contact_date_key = dd.date_key
WHERE f.contact_date_key != -1;

SELECT 'fact_closed_sale' AS fact_table,
    MIN(dd.full_date) AS min_date, MAX(dd.full_date) AS max_date
FROM fact_closed_sale f
JOIN dim_date dd ON f.closed_date_key = dd.date_key
WHERE f.closed_date_key != -1;

SELECT 'fact_payment' AS fact_table,
    MIN(dd.full_date) AS min_date, MAX(dd.full_date) AS max_date
FROM fact_payment f
JOIN dim_date dd ON f.receipt_date_key = dd.date_key
WHERE f.receipt_date_key != -1;


-- ============================================
-- 6. PIPELINE FUNNEL SANITY
-- ============================================
SELECT '--- PIPELINE FUNNEL ---' AS section;

SELECT
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (WHERE first_contact_date_key IS NOT NULL) AS contacted,
    COUNT(*) FILTER (WHERE first_appointment_date_key IS NOT NULL) AS had_appointment,
    COUNT(*) FILTER (WHERE opportunity_created_date_key IS NOT NULL) AS became_opportunity,
    COUNT(*) FILTER (WHERE application_date_key IS NOT NULL) AS applied,
    COUNT(*) FILTER (WHERE closed_date_key IS NOT NULL) AS closed,
    COUNT(*) FILTER (WHERE is_won = TRUE) AS won,
    COUNT(*) FILTER (WHERE is_lost = TRUE) AS lost,
    COUNT(*) FILTER (WHERE is_active = TRUE) AS still_active
FROM fact_lead_pipeline;


-- ============================================
-- 7. DIMENSION HEALTH
-- ============================================
SELECT '--- DIMENSION ROW COUNTS ---' AS section;

SELECT 'dim_date' AS dim, COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_staff', COUNT(*) FROM dim_staff
UNION ALL SELECT 'dim_school', COUNT(*) FROM dim_school
UNION ALL SELECT 'dim_lead', COUNT(*) FROM dim_lead
UNION ALL SELECT 'dim_curriculum', COUNT(*) FROM dim_curriculum
UNION ALL SELECT 'dim_province', COUNT(*) FROM dim_province
UNION ALL SELECT 'dim_program_type', COUNT(*) FROM dim_program_type
UNION ALL SELECT 'dim_channel', COUNT(*) FROM dim_channel
UNION ALL SELECT 'dim_interaction_type', COUNT(*) FROM dim_interaction_type
UNION ALL SELECT 'dim_interaction_outcome', COUNT(*) FROM dim_interaction_outcome
UNION ALL SELECT 'dim_lead_state', COUNT(*) FROM dim_lead_state
UNION ALL SELECT 'dim_opportunity_state', COUNT(*) FROM dim_opportunity_state
UNION ALL SELECT 'dim_lead_source', COUNT(*) FROM dim_lead_source
UNION ALL SELECT 'dim_target_group', COUNT(*) FROM dim_target_group
UNION ALL SELECT 'dim_education_level', COUNT(*) FROM dim_education_level
UNION ALL SELECT 'dim_lose_reason', COUNT(*) FROM dim_lose_reason
UNION ALL SELECT 'dim_closed_sale_status', COUNT(*) FROM dim_closed_sale_status
ORDER BY 1;
