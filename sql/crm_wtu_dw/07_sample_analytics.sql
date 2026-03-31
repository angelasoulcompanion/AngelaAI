-- ============================================
-- CRM WTU Data Warehouse — Sample Analytical Queries
-- ============================================


-- ============================================
-- A. FUNNEL ANALYSIS
-- ============================================

-- A1. Funnel conversion rates by program type
SELECT
    dpt.program_type_name,
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (WHERE fp.first_contact_date_key IS NOT NULL) AS contacted,
    COUNT(*) FILTER (WHERE fp.opportunity_created_date_key IS NOT NULL) AS opportunities,
    COUNT(*) FILTER (WHERE fp.is_won) AS enrolled,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fp.first_contact_date_key IS NOT NULL) / NULLIF(COUNT(*), 0), 1) AS pct_contacted,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fp.opportunity_created_date_key IS NOT NULL) / NULLIF(COUNT(*), 0), 1) AS pct_opportunity,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fp.is_won) / NULLIF(COUNT(*), 0), 1) AS pct_enrolled
FROM fact_lead_pipeline fp
JOIN dim_program_type dpt ON dpt.program_type_key = fp.program_type_key
GROUP BY dpt.program_type_name
ORDER BY total_leads DESC;


-- A2. Monthly funnel trend (leads created per month, how many converted)
SELECT
    dd.year_month,
    COUNT(*) AS new_leads,
    COUNT(*) FILTER (WHERE fp.opportunity_created_date_key IS NOT NULL) AS became_opp,
    COUNT(*) FILTER (WHERE fp.is_won) AS enrolled,
    ROUND(AVG(fp.days_to_close) FILTER (WHERE fp.is_won), 1) AS avg_days_to_enroll
FROM fact_lead_pipeline fp
JOIN dim_date dd ON dd.date_key = fp.lead_created_date_key
WHERE dd.year >= 2024
GROUP BY dd.year_month
ORDER BY dd.year_month;


-- ============================================
-- B. STAFF PERFORMANCE
-- ============================================

-- B1. Staff leaderboard — win rate & activity
SELECT
    ds.staff_full_name,
    dpt.program_type_name,
    COUNT(*) AS total_closed,
    SUM(CASE WHEN fcs.is_won THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN NOT fcs.is_won THEN 1 ELSE 0 END) AS losses,
    ROUND(100.0 * SUM(CASE WHEN fcs.is_won THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS win_rate_pct,
    ROUND(AVG(fcs.days_lead_to_close), 1) AS avg_days_to_close,
    ROUND(AVG(fcs.total_interactions), 1) AS avg_interactions_per_deal
FROM fact_closed_sale fcs
JOIN dim_staff ds ON ds.staff_key = fcs.staff_key
JOIN dim_program_type dpt ON dpt.program_type_key = fcs.program_type_key
GROUP BY ds.staff_full_name, dpt.program_type_name
ORDER BY wins DESC;


-- B2. Staff interaction volume per month
SELECT
    dd.year_month,
    ds.staff_full_name,
    COUNT(*) AS interactions,
    SUM(fi.total_duration_sec) / 3600.0 AS total_hours_calling,
    COUNT(*) FILTER (WHERE fi.is_state_change) AS state_changes
FROM fact_lead_interaction fi
JOIN dim_date dd ON dd.date_key = fi.contact_date_key
JOIN dim_staff ds ON ds.staff_key = fi.staff_key
WHERE dd.year >= 2025
GROUP BY dd.year_month, ds.staff_full_name
ORDER BY dd.year_month DESC, interactions DESC;


-- ============================================
-- C. CURRICULUM / PROGRAM ANALYSIS
-- ============================================

-- C1. Most popular programs (by enrollment)
SELECT
    dc.study_level_name,
    dc.campus_name,
    dc.department_name,
    dc.concentrate_name,
    dc.curriculum_name,
    COUNT(*) FILTER (WHERE fcs.is_won) AS enrollments,
    COUNT(*) AS total_closed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fcs.is_won) / NULLIF(COUNT(*), 0), 1) AS win_rate,
    ROUND(AVG(fcs.days_lead_to_close) FILTER (WHERE fcs.is_won), 1) AS avg_days_to_enroll
FROM fact_closed_sale fcs
JOIN dim_curriculum dc ON dc.curriculum_key = fcs.curriculum_key
WHERE dc.curriculum_key != -1
GROUP BY dc.study_level_name, dc.campus_name, dc.department_name,
         dc.concentrate_name, dc.curriculum_name
ORDER BY enrollments DESC
LIMIT 20;


-- C2. Target vs Actual per curriculum
SELECT
    dc.study_level_name,
    dc.campus_name,
    dc.department_name,
    dc.curriculum_name,
    kt.education_year,
    kt.education_sem,
    SUM(kt.target_students) AS target,
    COUNT(DISTINCT fcs.closed_sale_id) FILTER (WHERE fcs.is_won) AS actual_enrolled,
    SUM(kt.target_students) - COUNT(DISTINCT fcs.closed_sale_id) FILTER (WHERE fcs.is_won) AS gap
FROM fact_kpi_target kt
JOIN dim_curriculum dc ON dc.curriculum_key = kt.curriculum_key
LEFT JOIN fact_closed_sale fcs ON fcs.curriculum_key = kt.curriculum_key
    AND fcs.is_won = TRUE
    -- Match education year from closed date
    AND EXISTS (
        SELECT 1 FROM dim_date dd
        WHERE dd.date_key = fcs.closed_date_key
          AND dd.education_year = kt.education_year + 543  -- Convert to BE
          AND dd.education_sem = kt.education_sem
    )
WHERE dc.curriculum_key != -1
GROUP BY dc.study_level_name, dc.campus_name, dc.department_name,
         dc.curriculum_name, kt.education_year, kt.education_sem
ORDER BY gap DESC;


-- ============================================
-- D. GEOGRAPHIC ANALYSIS
-- ============================================

-- D1. Leads by province — conversion rate
SELECT
    dp.province_name,
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (WHERE fp.is_won) AS enrolled,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fp.is_won) / NULLIF(COUNT(*), 0), 1) AS conversion_pct,
    ROUND(AVG(fp.total_interactions), 1) AS avg_interactions
FROM fact_lead_pipeline fp
JOIN dim_province dp ON dp.province_key = fp.province_key
WHERE dp.province_key != -1
GROUP BY dp.province_name
ORDER BY total_leads DESC
LIMIT 20;


-- ============================================
-- E. LEAD SOURCE / CHANNEL ROI
-- ============================================

-- E1. Source effectiveness
SELECT
    dls.lead_from_type_name,
    dls.source,
    dls.ads_campaign,
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (WHERE fp.is_won) AS enrolled,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fp.is_won) / NULLIF(COUNT(*), 0), 1) AS conversion_pct,
    SUM(fp.paid_amount) FILTER (WHERE fp.is_won) AS total_revenue
FROM fact_lead_pipeline fp
JOIN dim_lead_source dls ON dls.lead_source_key = fp.lead_source_key
WHERE dls.lead_source_key != -1
GROUP BY dls.lead_from_type_name, dls.source, dls.ads_campaign
ORDER BY enrolled DESC
LIMIT 20;


-- ============================================
-- F. SCHOOL FEEDER ANALYSIS
-- ============================================

-- F1. Top feeder schools
SELECT
    dsch.school_name,
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (WHERE fp.is_won) AS enrolled,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fp.is_won) / NULLIF(COUNT(*), 0), 1) AS conversion_pct,
    ROUND(AVG(fp.days_to_close) FILTER (WHERE fp.is_won), 1) AS avg_days_to_enroll
FROM fact_lead_pipeline fp
JOIN dim_school dsch ON dsch.school_key = fp.school_key
WHERE dsch.school_key != -1
GROUP BY dsch.school_name
HAVING COUNT(*) >= 5
ORDER BY enrolled DESC
LIMIT 20;


-- ============================================
-- G. LOSS ANALYSIS
-- ============================================

-- G1. Why are we losing deals?
SELECT
    dlr.lose_reason_name,
    dpt.program_type_name,
    COUNT(*) AS lost_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY dpt.program_type_name), 1) AS pct_of_losses
FROM fact_closed_sale fcs
JOIN dim_lose_reason dlr ON dlr.lose_reason_key = fcs.lose_reason_key
JOIN dim_program_type dpt ON dpt.program_type_key = fcs.program_type_key
WHERE fcs.is_won = FALSE
  AND dlr.lose_reason_key != -1
GROUP BY dlr.lose_reason_name, dpt.program_type_name
ORDER BY dpt.program_type_name, lost_count DESC;


-- ============================================
-- H. INTERACTION EFFECTIVENESS
-- ============================================

-- H1. Which interaction types lead to conversions?
SELECT
    dit.interaction_type_name,
    dio.interaction_outcome_name,
    COUNT(*) AS interaction_count,
    COUNT(DISTINCT fi.lead_key) AS unique_leads,
    COUNT(*) FILTER (WHERE fi.is_state_change) AS led_to_state_change,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fi.is_state_change) / NULLIF(COUNT(*), 0), 1) AS state_change_pct
FROM fact_lead_interaction fi
JOIN dim_interaction_type dit ON dit.interaction_type_key = fi.interaction_type_key
JOIN dim_interaction_outcome dio ON dio.interaction_outcome_key = fi.interaction_outcome_key
GROUP BY dit.interaction_type_name, dio.interaction_outcome_name
ORDER BY interaction_count DESC;


-- ============================================
-- I. REVENUE ANALYSIS
-- ============================================

-- I1. Monthly revenue collection
SELECT
    dd.year_month,
    SUM(fp.fee_total_amount) AS total_collected,
    COUNT(DISTINCT fp.opportunity_id) AS paying_opportunities,
    COUNT(*) AS payment_line_items
FROM fact_payment fp
JOIN dim_date dd ON dd.date_key = fp.receipt_date_key
GROUP BY dd.year_month
ORDER BY dd.year_month DESC;

-- I2. Revenue by fee type
SELECT
    fp.fee_name,
    COUNT(*) AS payment_count,
    SUM(fp.fee_total_amount) AS total_amount,
    ROUND(AVG(fp.fee_unit_price), 2) AS avg_unit_price,
    SUM(fp.fee_qty) AS total_qty
FROM fact_payment fp
GROUP BY fp.fee_name
ORDER BY total_amount DESC;


-- ============================================
-- J. PIPELINE VELOCITY
-- ============================================

-- J1. Average pipeline velocity by program type
SELECT
    dpt.program_type_name,
    ROUND(AVG(fp.days_to_first_contact), 1) AS avg_days_to_contact,
    ROUND(AVG(fp.days_to_opportunity), 1) AS avg_days_to_opp,
    ROUND(AVG(fp.days_to_application), 1) AS avg_days_to_app,
    ROUND(AVG(fp.days_to_close) FILTER (WHERE fp.is_won), 1) AS avg_days_to_enroll,
    ROUND(AVG(fp.total_interactions), 1) AS avg_touches
FROM fact_lead_pipeline fp
JOIN dim_program_type dpt ON dpt.program_type_key = fp.program_type_key
WHERE fp.closed_date_key IS NOT NULL
GROUP BY dpt.program_type_name
ORDER BY dpt.program_type_name;
