-- ============================================================================
-- EWG — Category cost breakdown (authoritative OPEX SSOT, from SUM EWG sheet)
--
-- WHY a separate table: the asset register (ewg.asset) carries Opex only on a
-- sparse ~24 rows (~22.3M) — it does NOT capture full Opex. The true Opex
-- (48,031,680.42) lives in SUM EWG at the grain:
--     category × placement(Back/Front) × hw_sw(HW/SW) × status(Active/Non/TBC)
-- BV & Dep here reconcile to the register; Opex is the unique addition.
-- All roll-ups (รวม / HW-SW totals / Total) are views, never stored.
-- ============================================================================

CREATE TABLE IF NOT EXISTS ewg.category_cost (
    cost_id      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    category_id  SMALLINT NOT NULL REFERENCES ewg.breakdown_category(category_id),
    placement    ewg.placement_type NOT NULL,   -- back_end / front_end
    hw_sw        ewg.hw_sw_type     NOT NULL,    -- hw / sw
    status       ewg.asset_status   NOT NULL,    -- active / non_active / tbc
    book_value   NUMERIC(18,2),
    depre        NUMERIC(18,2),
    opex         NUMERIC(18,2),
    source_file  TEXT,
    imported_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (category_id, placement, hw_sw, status)
);

CREATE INDEX IF NOT EXISTS idx_catcost_category ON ewg.category_cost(category_id);

-- ---- Category × cost roll-up (BV / Dep / Opex by category & status) --------
CREATE OR REPLACE VIEW ewg.v_category_cost AS
SELECT
    c.category_name,
    MAX(c.domain)      AS domain,        -- constant within a category
    cc.status,
    SUM(cc.book_value) AS book_value,
    SUM(cc.depre)      AS depre,
    SUM(cc.opex)       AS opex
FROM ewg.category_cost cc
JOIN ewg.breakdown_category c USING (category_id)
GROUP BY ROLLUP (c.category_name, cc.status)
ORDER BY c.category_name NULLS LAST, cc.status NULLS LAST;

COMMENT ON TABLE ewg.category_cost IS
  'SSOT for Opex (and BV/Dep cross-check) at category x placement x hw_sw x status. Source: SUM EWG sheet.';
