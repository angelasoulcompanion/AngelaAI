-- ============================================================================
-- EWG — Derived reporting views (reproduce SUM EWG / PVT EWG sheets)
-- These are computed from ewg.asset — no duplicated data.
-- ============================================================================

-- ---- SUM EWG : roll-up by Breakdown category × status ---------------------
CREATE OR REPLACE VIEW ewg.v_sum_by_category AS
SELECT
    c.category_name,
    c.domain,
    a.status,
    COUNT(*)                       AS asset_count,
    SUM(a.net_book_value)          AS book_value,
    SUM(a.dep_year_2026)           AS dep_year_2026,
    SUM(COALESCE(a.opex, 0))       AS opex
FROM ewg.asset a
LEFT JOIN ewg.breakdown_category c ON c.category_id = a.category_id
GROUP BY GROUPING SETS (
    (c.category_name, c.domain, a.status),
    (c.category_name, c.domain),
    ()
)
ORDER BY c.category_name NULLS LAST, a.status NULLS LAST;

-- ---- PVT EWG : pivot by Breakdown × Back/Front × HW/SW --------------------
CREATE OR REPLACE VIEW ewg.v_pivot_breakdown AS
SELECT
    c.category_name,
    a.placement,
    a.hw_sw,
    COUNT(*)                  AS asset_count,
    SUM(a.net_book_value)     AS book_value,
    SUM(a.dep_year_2026)      AS dep_year_2026,
    SUM(COALESCE(a.opex, 0))  AS opex
FROM ewg.asset a
LEFT JOIN ewg.breakdown_category c ON c.category_id = a.category_id
GROUP BY ROLLUP (c.category_name, a.placement, a.hw_sw)
ORDER BY c.category_name NULLS LAST, a.placement NULLS LAST, a.hw_sw NULLS LAST;

-- ---- Monetization candidate shortlist -------------------------------------
-- Assets most attractive to monetize: still carry book value but Non-active,
-- or near end-of-life, ranked by net book value released.
CREATE OR REPLACE VIEW ewg.v_monetize_candidates AS
SELECT
    e.entity_code,
    a.asset_code,
    a.description,
    c.category_name,
    a.placement,
    a.hw_sw,
    a.status,
    a.net_book_value,
    a.dep_year_2026,
    a.opex,
    a.useful_life_years
FROM ewg.asset a
JOIN ewg.entity e ON e.entity_id = a.entity_id
LEFT JOIN ewg.breakdown_category c ON c.category_id = a.category_id
WHERE a.net_book_value > 0
  AND (a.status = 'non_active' OR a.opex > 0)
ORDER BY a.net_book_value DESC;
