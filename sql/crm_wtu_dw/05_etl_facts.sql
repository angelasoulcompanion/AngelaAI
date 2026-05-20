-- ============================================
-- CRM WTU Data Warehouse — ETL: Fact Loading
-- Source: crm_wtu.public (via FDW schema "src")
-- Target: crm_wtu_dw.public
-- ============================================


-- ============================================
-- FACT 1: fact_lead_interaction
-- Source: lead_interaction → 248K rows
-- Incremental: by created_at > last load
-- ============================================

-- Cleanup: remove rows whose source record is no longer Active
DELETE FROM fact_lead_interaction fi
WHERE NOT EXISTS (
    SELECT 1 FROM src.lead_interaction li
    WHERE li.id = fi.interaction_id AND li.status = 'Active'
);

INSERT INTO fact_lead_interaction (
    contact_date_key, next_action_date_key,
    staff_key, lead_key,
    interaction_type_key, interaction_outcome_key,
    lead_state_from_key, lead_state_to_key,
    opportunity_state_from_key, opportunity_state_to_key,
    app_form_state_from_key, app_form_state_to_key,
    interaction_id, entity_type, appointment_id,
    total_duration_sec, billed_duration_sec, interaction_count,
    is_state_change, is_opp_state_change
)
SELECT
    -- Date keys
    COALESCE(dd_contact.date_key, -1),
    dd_next.date_key,
    -- Dimension keys
    COALESCE(ds.staff_key, -1),
    COALESCE(dl.lead_key, -1),
    COALESCE(dit.interaction_type_key, -1),
    COALESCE(dio.interaction_outcome_key, -1),
    dls_from.lead_state_key,
    dls_to.lead_state_key,
    dos_from.opportunity_state_key,
    dos_to.opportunity_state_key,
    dafs_from.application_form_state_key,
    dafs_to.application_form_state_key,
    -- Degenerate
    li.id,
    li.entity_type,
    li.appointment_id,
    -- Measures
    li.total_duration_sec,
    li.billed_duration_sec,
    1,
    -- Flags
    li.lead_state_from_id IS DISTINCT FROM li.lead_state_to_id
        AND li.lead_state_to_id IS NOT NULL,
    li.opportunity_state_from_id IS DISTINCT FROM li.opportunity_state_to_id
        AND li.opportunity_state_to_id IS NOT NULL

FROM src.lead_interaction li

-- Date lookups
LEFT JOIN dim_date dd_contact
    ON dd_contact.full_date = li.contact_date::DATE
LEFT JOIN dim_date dd_next
    ON dd_next.full_date = li.next_action_date::DATE

-- Staff (from created_by — the person who logged the interaction)
LEFT JOIN dim_staff ds
    ON ds.staff_id = li.created_by_id AND ds.is_current = TRUE

-- Lead
LEFT JOIN dim_lead dl
    ON dl.lead_id = li.lead_id AND dl.is_current = TRUE

-- Interaction type & outcome
LEFT JOIN dim_interaction_type dit
    ON dit.interaction_type_id = li.interaction_type_id
LEFT JOIN dim_interaction_outcome dio
    ON dio.interaction_outcome_id = li.interaction_outcome_id

-- State transitions
LEFT JOIN dim_lead_state dls_from
    ON dls_from.lead_state_id = li.lead_state_from_id
LEFT JOIN dim_lead_state dls_to
    ON dls_to.lead_state_id = li.lead_state_to_id
LEFT JOIN dim_opportunity_state dos_from
    ON dos_from.opportunity_state_id = li.opportunity_state_from_id
LEFT JOIN dim_opportunity_state dos_to
    ON dos_to.opportunity_state_id = li.opportunity_state_to_id
LEFT JOIN dim_application_form_state dafs_from
    ON dafs_from.application_form_state_id = li.application_form_state_from_id
LEFT JOIN dim_application_form_state dafs_to
    ON dafs_to.application_form_state_id = li.application_form_state_to_id

WHERE li.status = 'Active'
  AND NOT EXISTS (
    SELECT 1 FROM fact_lead_interaction f WHERE f.interaction_id = li.id
  );


-- ============================================
-- FACT 2: fact_appointment
-- Source: appointment → 23K rows
-- ============================================

-- Cleanup: remove rows whose source record is no longer Active
DELETE FROM fact_appointment fa
WHERE NOT EXISTS (
    SELECT 1 FROM src.appointment a
    WHERE a.id = fa.appointment_id AND a.status = 'Active'
);

INSERT INTO fact_appointment (
    scheduled_date_key, created_date_key,
    staff_key, lead_key,
    appointment_type_key, interaction_type_key,
    appointment_id, appointment_status, opportunity_id, location,
    duration_minutes, appointment_count, lead_time_days
)
SELECT
    COALESCE(dd_sched.date_key, -1),
    COALESCE(dd_created.date_key, -1),
    COALESCE(ds.staff_key, -1),
    COALESCE(dl.lead_key, -1),
    COALESCE(dat.appointment_type_key, -1),
    COALESCE(dit.interaction_type_key, -1),
    a.id,
    a.appointment_status,
    a.opportunity_id,
    a.location,
    -- Duration in minutes
    CASE WHEN a.scheduled_end IS NOT NULL
        THEN EXTRACT(EPOCH FROM (a.scheduled_end - a.scheduled_start)) / 60.0
    END,
    1,
    -- Lead time: days between creation and scheduled date
    EXTRACT(DAY FROM (a.scheduled_start - a.created_at))

FROM src.appointment a

LEFT JOIN dim_date dd_sched
    ON dd_sched.full_date = a.scheduled_start::DATE
LEFT JOIN dim_date dd_created
    ON dd_created.full_date = a.created_at::DATE
LEFT JOIN dim_staff ds
    ON ds.staff_id = a.staff_id AND ds.is_current = TRUE
LEFT JOIN dim_lead dl
    ON dl.lead_id = a.lead_id AND dl.is_current = TRUE
LEFT JOIN dim_appointment_type dat
    ON dat.appointment_type_id = a.appointment_type_id
LEFT JOIN dim_interaction_type dit
    ON dit.interaction_type_id = a.interaction_type_id

WHERE a.status = 'Active'
  AND NOT EXISTS (
    SELECT 1 FROM fact_appointment f WHERE f.appointment_id = a.id
  );


-- ============================================
-- FACT 3: fact_closed_sale
-- Source: closed_sale + opportunity + lead + aggregations
-- ============================================

-- Cleanup: remove rows whose source record is no longer Active
DELETE FROM fact_closed_sale fc
WHERE NOT EXISTS (
    SELECT 1 FROM src.closed_sale cs
    WHERE cs.id = fc.closed_sale_id AND cs.status = 'Active'
);

INSERT INTO fact_closed_sale (
    closed_date_key, lead_created_date_key,
    staff_key, lead_key,
    closed_sale_status_key, lose_reason_key,
    curriculum_key, program_type_key,
    school_key, province_key, target_group_key,
    closed_sale_id, opportunity_id, opportunity_no, student_id,
    closed_sale_count, is_won,
    days_lead_to_close, days_opp_to_close,
    total_interactions, total_appointments,
    total_due, paid_amount, remaining_balance
)
SELECT
    COALESCE(dd_closed.date_key, -1),
    dd_lead_created.date_key,
    COALESCE(ds.staff_key, -1),
    COALESCE(dl.lead_key, -1),
    COALESCE(dcss.closed_sale_status_key, -1),
    COALESCE(dlr.lose_reason_key, -1),
    COALESCE(dc.curriculum_key, -1),
    COALESCE(dpt.program_type_key, -1),
    COALESCE(dsch.school_key, -1),
    COALESCE(dprov.province_key, -1),
    COALESCE(dtg.target_group_key, -1),
    -- Degenerate
    cs.id,
    cs.opportunity_id,
    o.opportunity_no,
    o.student_id,
    -- Measures
    1,
    css.name_en = 'Won' OR css.name ILIKE '%ชนะ%' OR css.name ILIKE '%สำเร็จ%',
    -- Days calculations
    EXTRACT(DAY FROM (cs.closed_date - l.created_at))::INT,
    EXTRACT(DAY FROM (cs.closed_date - o.created_at))::INT,
    -- Aggregated activity counts
    interaction_counts.cnt,
    appointment_counts.cnt,
    -- Revenue
    COALESCE(oar.total_due, 0),
    COALESCE(oar.paid_amount, 0),
    COALESCE(oar.remaining_balance, 0)

FROM src.closed_sale cs

-- Core joins
INNER JOIN src.opportunity o ON o.id = cs.opportunity_id
INNER JOIN src.lead l ON l.id = o.lead_id
LEFT JOIN src.closed_sale_status css ON css.id = cs.closed_sale_status_id

-- Date keys
LEFT JOIN dim_date dd_closed ON dd_closed.full_date = cs.closed_date::DATE
LEFT JOIN dim_date dd_lead_created ON dd_lead_created.full_date = l.created_at::DATE

-- Dimension lookups
LEFT JOIN dim_staff ds ON ds.staff_id = cs.staff_id AND ds.is_current = TRUE
LEFT JOIN dim_lead dl ON dl.lead_id = o.lead_id AND dl.is_current = TRUE
LEFT JOIN dim_closed_sale_status dcss ON dcss.closed_sale_status_id = cs.closed_sale_status_id
LEFT JOIN dim_lose_reason dlr ON dlr.lose_reason_id = cs.lose_reason_type_id
LEFT JOIN dim_program_type dpt ON dpt.program_type_id = o.program_type_id
LEFT JOIN dim_school dsch ON dsch.school_id = l.school_id
LEFT JOIN dim_province dprov ON dprov.province_code = l.province_code
LEFT JOIN dim_target_group dtg ON dtg.target_group_id = l.target_group_id

-- Curriculum: first interest of the lead
LEFT JOIN LATERAL (
    SELECT dc2.curriculum_key
    FROM src.lead_interest li2
    INNER JOIN dim_curriculum dc2
        ON dc2.study_level_id = li2.study_level_id
        AND dc2.campus_id = li2.campus_id
        AND dc2.fac_type_id = li2.fac_type_id
        AND dc2.division_id = li2.division_id
        AND dc2.department_id = li2.department_id
        AND dc2.concentrate_id = li2.concentrate_id
        AND dc2.curriculum_id = li2.curriculum_id
    WHERE li2.lead_id = l.id AND li2.sequence = 1 AND li2.status = 'Active'
    LIMIT 1
) dc ON TRUE

-- Aggregated: interaction count for this lead
LEFT JOIN LATERAL (
    SELECT COUNT(*) AS cnt
    FROM src.lead_interaction li3
    WHERE li3.lead_id = l.id AND li3.status = 'Active'
) interaction_counts ON TRUE

-- Aggregated: appointment count
LEFT JOIN LATERAL (
    SELECT COUNT(*) AS cnt
    FROM src.appointment a2
    WHERE (a2.lead_id = l.id OR a2.opportunity_id = o.id) AND a2.status = 'Active'
) appointment_counts ON TRUE

-- Revenue from account remain
LEFT JOIN src.opportunity_account_remain oar ON oar.opportunity_id = o.id AND oar.status = 'Active'

WHERE cs.status = 'Active'
  AND NOT EXISTS (
    SELECT 1 FROM fact_closed_sale f WHERE f.closed_sale_id = cs.id
  );


-- ============================================
-- FACT 4: fact_payment
-- Source: opportunity_receipt_fee + opportunity_receipt
-- ============================================

-- Cleanup: remove rows whose source record is no longer Active
DELETE FROM fact_payment fp
WHERE NOT EXISTS (
    SELECT 1 FROM src.opportunity_receipt_fee orf
    WHERE orf.id = fp.receipt_fee_id AND orf.status = 'Active'
);

INSERT INTO fact_payment (
    receipt_date_key, staff_key, lead_key, opportunity_state_key,
    receipt_fee_id, opportunity_id, receipt_id, receipt_number,
    fee_id, fee_name,
    fee_unit_price, fee_qty, fee_total_amount, receipt_total_amount, payment_count
)
SELECT
    COALESCE(dd.date_key, -1),
    COALESCE(ds.staff_key, -1),
    COALESCE(dl.lead_key, -1),
    dos.opportunity_state_key,
    -- Degenerate
    orf.id,
    orf.opportunity_id,
    orf.opportunity_receipt_id,
    orf.receipt_number,
    orf.fee_id,
    orf.fee_name,
    -- Measures
    orf.fee_unit_price,
    orf.fee_qty,
    orf.fee_total_amount,
    orr.total_amount,
    1

FROM src.opportunity_receipt_fee orf

INNER JOIN src.opportunity_receipt orr ON orr.id = orf.opportunity_receipt_id
INNER JOIN src.opportunity o ON o.id = orf.opportunity_id
INNER JOIN src.lead l ON l.id = o.lead_id

LEFT JOIN dim_date dd ON dd.full_date = orr.receipt_datetime::DATE
LEFT JOIN dim_staff ds ON ds.staff_id = orr.created_by_id AND ds.is_current = TRUE
LEFT JOIN dim_lead dl ON dl.lead_id = o.lead_id AND dl.is_current = TRUE
LEFT JOIN dim_opportunity_state dos ON dos.opportunity_state_id = orr.opportunity_state_id

WHERE orf.status = 'Active'
  AND NOT EXISTS (
    SELECT 1 FROM fact_payment f WHERE f.receipt_fee_id = orf.id
  );


-- ============================================
-- FACT 5: fact_lead_pipeline (Accumulating Snapshot)
-- Full rebuild each run
-- ============================================

TRUNCATE fact_lead_pipeline;

INSERT INTO fact_lead_pipeline (
    lead_key, staff_key, school_key, province_key,
    program_type_key, lead_source_key, target_group_key,
    education_level_key, curriculum_key,
    lead_created_date_key, first_contact_date_key, first_appointment_date_key,
    opportunity_created_date_key, application_date_key, closed_date_key,
    lead_id, opportunity_id, opportunity_no, student_id,
    current_lead_state_key, current_opp_state_key, closed_sale_status_key,
    days_to_first_contact, days_to_first_appointment, days_to_opportunity,
    days_to_application, days_to_close, total_pipeline_days,
    total_interactions, total_appointments, total_calls, total_call_duration_sec,
    total_due, paid_amount, remaining_balance,
    is_won, is_lost, is_active, is_duplicate
)
SELECT
    COALESCE(dl.lead_key, -1),
    COALESCE(ds.staff_key, -1),
    COALESCE(dsch.school_key, -1),
    COALESCE(dprov.province_key, -1),
    COALESCE(dpt.program_type_key, -1),
    COALESCE(dls.lead_source_key, -1),
    COALESCE(dtg.target_group_key, -1),
    COALESCE(del.education_level_key, -1),
    COALESCE(dcur.curriculum_key, -1),
    -- Milestone dates
    dd_created.date_key,
    dd_first_contact.date_key,
    dd_first_appt.date_key,
    dd_opp_created.date_key,
    dd_app.date_key,
    dd_closed.date_key,
    -- Degenerate
    l.id,
    opp.id,
    opp.opportunity_no,
    opp.student_id,
    -- Current state
    dls_current.lead_state_key,
    dos_current.opportunity_state_key,
    dcss.closed_sale_status_key,
    -- Velocity
    EXTRACT(DAY FROM (milestones.first_contact - l.created_at))::INT,
    EXTRACT(DAY FROM (milestones.first_appointment - l.created_at))::INT,
    EXTRACT(DAY FROM (opp.created_at - l.created_at))::INT,
    EXTRACT(DAY FROM (milestones.application_date - l.created_at))::INT,
    EXTRACT(DAY FROM (cs.closed_date - l.created_at))::INT,
    EXTRACT(DAY FROM (COALESCE(cs.closed_date, NOW()) - l.created_at))::INT,
    -- Activity
    COALESCE(activity.total_interactions, 0),
    COALESCE(activity.total_appointments, 0),
    COALESCE(activity.total_calls, 0),
    COALESCE(activity.total_call_duration, 0),
    -- Revenue
    COALESCE(oar.total_due, 0),
    COALESCE(oar.paid_amount, 0),
    COALESCE(oar.remaining_balance, 0),
    -- Flags
    css.name_en = 'Won' OR css.name ILIKE '%ชนะ%' OR css.name ILIKE '%สำเร็จ%',
    css.name_en = 'Lost' OR css.name ILIKE '%แพ้%' OR css.name ILIKE '%ไม่สำเร็จ%',
    cs.id IS NULL,  -- Active if no closed_sale
    l.is_potential_duplicate

FROM src.lead l

-- Opportunity (latest per lead)
LEFT JOIN LATERAL (
    SELECT * FROM src.opportunity o2
    WHERE o2.lead_id = l.id AND o2.status = 'Active'
    ORDER BY o2.created_at DESC LIMIT 1
) opp ON TRUE

-- Closed sale
LEFT JOIN LATERAL (
    SELECT * FROM src.closed_sale cs2
    WHERE cs2.opportunity_id = opp.id AND cs2.status = 'Active'
    ORDER BY cs2.closed_date DESC LIMIT 1
) cs ON TRUE

LEFT JOIN src.closed_sale_status css ON css.id = cs.closed_sale_status_id

-- Milestone aggregation
LEFT JOIN LATERAL (
    SELECT
        MIN(li.contact_date) AS first_contact,
        MIN(a.scheduled_start) AS first_appointment,
        MIN(oaf.created_at) AS application_date
    FROM src.lead_interaction li
    LEFT JOIN src.appointment a ON a.lead_id = l.id AND a.status = 'Active'
    LEFT JOIN src.opportunity_application_form oaf
        ON oaf.opportunity_id = opp.id AND oaf.status = 'Active'
    WHERE li.lead_id = l.id AND li.status = 'Active'
) milestones ON TRUE

-- Activity counts
LEFT JOIN LATERAL (
    SELECT
        COUNT(*) AS total_interactions,
        COUNT(*) FILTER (WHERE li.appointment_id IS NOT NULL) AS total_appointments,
        COUNT(*) FILTER (WHERE li.total_duration_sec > 0) AS total_calls,
        COALESCE(SUM(li.total_duration_sec), 0) AS total_call_duration
    FROM src.lead_interaction li
    WHERE li.lead_id = l.id AND li.status = 'Active'
) activity ON TRUE

-- Revenue
LEFT JOIN src.opportunity_account_remain oar ON oar.opportunity_id = opp.id AND oar.status = 'Active'

-- First curriculum interest
LEFT JOIN LATERAL (
    SELECT dc2.curriculum_key
    FROM src.lead_interest li2
    INNER JOIN dim_curriculum dc2
        ON dc2.study_level_id = li2.study_level_id
        AND dc2.campus_id = li2.campus_id
        AND dc2.fac_type_id = li2.fac_type_id
        AND dc2.division_id = li2.division_id
        AND dc2.department_id = li2.department_id
        AND dc2.concentrate_id = li2.concentrate_id
        AND dc2.curriculum_id = li2.curriculum_id
    WHERE li2.lead_id = l.id AND li2.sequence = 1 AND li2.status = 'Active'
    LIMIT 1
) dcur ON TRUE

-- Dimension lookups
LEFT JOIN dim_lead dl ON dl.lead_id = l.id AND dl.is_current = TRUE
LEFT JOIN dim_staff ds ON ds.staff_id = l.staff_id AND ds.is_current = TRUE
LEFT JOIN dim_school dsch ON dsch.school_id = l.school_id
LEFT JOIN dim_province dprov ON dprov.province_code = l.province_code
LEFT JOIN dim_program_type dpt ON dpt.program_type_id = l.program_type_id
LEFT JOIN dim_lead_source dls ON dls.lead_from_type_id IS NOT DISTINCT FROM l.lead_from_type_id
    AND dls.source = COALESCE(l.source, 'N/A')
    AND dls.ads_campaign = COALESCE(l.ads_campaign, 'N/A')
    AND dls.social_media = COALESCE(l.social_media, 'N/A')
LEFT JOIN dim_target_group dtg ON dtg.target_group_id = l.target_group_id
LEFT JOIN dim_education_level del ON del.education_level_id = l.education_level_id
LEFT JOIN dim_lead_state dls_current ON dls_current.lead_state_id = l.lead_state_id
LEFT JOIN dim_opportunity_state dos_current ON dos_current.opportunity_state_id = opp.opportunity_state_id
LEFT JOIN dim_closed_sale_status dcss ON dcss.closed_sale_status_id = cs.closed_sale_status_id

-- Date key lookups
LEFT JOIN dim_date dd_created ON dd_created.full_date = l.created_at::DATE
LEFT JOIN dim_date dd_first_contact ON dd_first_contact.full_date = milestones.first_contact::DATE
LEFT JOIN dim_date dd_first_appt ON dd_first_appt.full_date = milestones.first_appointment::DATE
LEFT JOIN dim_date dd_opp_created ON dd_opp_created.full_date = opp.created_at::DATE
LEFT JOIN dim_date dd_app ON dd_app.full_date = milestones.application_date::DATE
LEFT JOIN dim_date dd_closed ON dd_closed.full_date = cs.closed_date::DATE

WHERE l.status = 'Active';


-- ============================================
-- FACT 6: fact_kpi_target
-- Source: target
-- ============================================

TRUNCATE fact_kpi_target;

INSERT INTO fact_kpi_target (
    curriculum_key, program_type_key, target_group_key, school_key,
    target_id, education_year, education_sem,
    target_students, plan_student_amount, monthly_target
)
SELECT
    COALESCE(dc.curriculum_key, -1),
    COALESCE(dpt.program_type_key, -1),
    COALESCE(dtg.target_group_key, -1),
    COALESCE(dsch.school_key, -1),
    t.id,
    t.education_year,
    t.education_sem,
    t.number_of_student,
    kpi.plan_student_amount,
    kpi.monthly_target

FROM src.target t

LEFT JOIN dim_curriculum dc
    ON dc.study_level_id = COALESCE(t.study_level_id, '-1')
    AND dc.campus_id = COALESCE(t.campus_id, '-1')
    AND dc.fac_type_id = COALESCE(t.fac_type_id, '-1')
    AND dc.division_id = COALESCE(t.division_id, '-1')
    AND dc.department_id = COALESCE(t.department_id, '-1')
    AND dc.concentrate_id = COALESCE(t.concentrate_id, '-1')
    AND dc.curriculum_id = COALESCE(t.curriculum_id, '-1')

LEFT JOIN dim_program_type dpt ON dpt.program_type_id = t.program_type_id
LEFT JOIN dim_target_group dtg ON dtg.target_group_id = t.target_group_id
LEFT JOIN dim_school dsch ON dsch.school_id = t.school_id

-- KPI config match
LEFT JOIN src.kpi_configuration kpi
    ON kpi.study_level_id = t.study_level_id
    AND kpi.campus_id = t.campus_id
    AND kpi.curriculum_id = t.curriculum_id
    AND kpi.education_year = t.education_year
    AND kpi.education_sem = t.education_sem
    AND kpi.status = 'Active'

WHERE t.status = 'Active';


-- ============================================
-- FACT 7: fact_lead_interest (Demand Analytics)
-- Source: lead_interest → ~46K rows. Full rebuild each run.
-- Must run AFTER fact_lead_pipeline (joins it for is_won/is_active/staff/program).
-- ============================================

TRUNCATE fact_lead_interest;

INSERT INTO fact_lead_interest (
    lead_key, curriculum_key, program_type_key, staff_key, created_date_key,
    lead_interest_id, lead_id, sequence, interest_count, is_won, is_active
)
SELECT
    COALESCE(dl.lead_key, -1),
    COALESCE(dc.curriculum_key, -1),
    COALESCE(fp.program_type_key, -1),
    COALESCE(fp.staff_key, -1),
    dd.date_key,
    li.id,
    li.lead_id,
    li.sequence,
    1,
    COALESCE(fp.is_won, FALSE),
    COALESCE(fp.is_active, FALSE)

FROM src.lead_interest li

LEFT JOIN dim_curriculum dc
    ON dc.study_level_id = li.study_level_id
    AND dc.campus_id = li.campus_id
    AND dc.fac_type_id = li.fac_type_id
    AND dc.division_id = li.division_id
    AND dc.department_id = li.department_id
    AND dc.concentrate_id = li.concentrate_id
    AND dc.curriculum_id = li.curriculum_id

LEFT JOIN dim_lead dl ON dl.lead_id = li.lead_id AND dl.is_current = TRUE
LEFT JOIN fact_lead_pipeline fp ON fp.lead_key = dl.lead_key
LEFT JOIN dim_date dd ON dd.full_date = li.created_at::DATE

WHERE li.status = 'Active';
