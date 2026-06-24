-- ============================================================================
-- EWG — Consolidated dashboard view (BV + Dep + Opex unified per category)
-- Money grain = ewg.category_cost (reconciles to DV); asset_count from register.
-- ============================================================================

-- ---- Per-category unified line --------------------------------------------
CREATE OR REPLACE VIEW ewg.v_dashboard AS
WITH cnt AS (
    SELECT category_id,
           COUNT(*)                                          AS asset_count,
           COUNT(*) FILTER (WHERE status = 'non_active')     AS non_active_count
    FROM ewg.asset
    GROUP BY category_id
),
cost AS (
    SELECT category_id,
           SUM(book_value) AS bv,
           SUM(depre)      AS dep,
           SUM(opex)       AS opex,
           SUM(book_value) FILTER (WHERE status = 'non_active') AS bv_non_active
    FROM ewg.category_cost
    GROUP BY category_id
)
SELECT
    c.category_name,
    c.domain,
    COALESCE(n.asset_count, 0)        AS asset_count,
    COALESCE(n.non_active_count, 0)   AS non_active_count,
    COALESCE(k.bv, 0)                 AS book_value,
    COALESCE(k.dep, 0)                AS depreciation,
    COALESCE(k.opex, 0)               AS opex,
    COALESCE(k.dep, 0) + COALESCE(k.opex, 0)          AS annual_cost,   -- Dep+Opex
    COALESCE(k.bv_non_active, 0)      AS bv_non_active,                 -- idle capital
    ROUND(COALESCE(k.opex, 0) / NULLIF(k.bv, 0), 4)   AS opex_to_bv     -- monetize signal
FROM ewg.breakdown_category c
LEFT JOIN cnt  n USING (category_id)
LEFT JOIN cost k USING (category_id)
ORDER BY annual_cost DESC;

-- ---- KPI strip: grand totals ----------------------------------------------
CREATE OR REPLACE VIEW ewg.v_dashboard_kpi AS
SELECT
    (SELECT COUNT(*) FROM ewg.asset)                                   AS total_assets,
    (SELECT COUNT(*) FROM ewg.asset WHERE status = 'non_active')       AS non_active_assets,
    (SELECT SUM(book_value) FROM ewg.category_cost)                    AS total_bv,
    (SELECT SUM(depre)      FROM ewg.category_cost)                    AS total_dep,
    (SELECT SUM(opex)       FROM ewg.category_cost)                    AS total_opex,
    (SELECT SUM(net_book_value) FROM ewg.asset WHERE status='non_active') AS bv_non_active,
    (SELECT wip FROM ewg.monetization_scenario WHERE scenario_name='DV June 2026') AS wip,
    (SELECT total_value FROM ewg.monetization_scenario WHERE scenario_name='DV June 2026') AS deal_total;

-- ---- By domain (OT vs IT) -------------------------------------------------
CREATE OR REPLACE VIEW ewg.v_dashboard_domain AS
SELECT c.domain,
       SUM(cc.book_value) AS book_value,
       SUM(cc.depre)      AS depreciation,
       SUM(cc.opex)       AS opex
FROM ewg.category_cost cc
JOIN ewg.breakdown_category c USING (category_id)
GROUP BY c.domain ORDER BY c.domain;

-- ---- By status (Active / Non-active) --------------------------------------
CREATE OR REPLACE VIEW ewg.v_dashboard_status AS
SELECT status,
       SUM(book_value) AS book_value,
       SUM(depre)      AS depreciation,
       SUM(opex)       AS opex
FROM ewg.category_cost
GROUP BY status ORDER BY status;
