-- ============================================================================
-- EWG Digital Transformation — pillar tagging + programme structure
-- CEO framing: 2 pillars (Maintenance / Create-NEW) on a DataWarehouse SSOT.
-- Rule: Booked assets (have Book Value, running) = Maintenance.
--       WIP (work-in-progress builds) = Create (NEW).
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE ewg.pillar AS ENUM ('maintenance', 'create');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---- tag every booked asset as Maintenance (they all carry Book Value) -----
ALTER TABLE ewg.asset ADD COLUMN IF NOT EXISTS pillar ewg.pillar;
UPDATE ewg.asset SET pillar = 'maintenance' WHERE pillar IS NULL;
ALTER TABLE ewg.asset ALTER COLUMN pillar SET DEFAULT 'maintenance';

-- ---- programme structure (workstreams under each pillar + the SSOT) --------
CREATE TABLE IF NOT EXISTS ewg.transformation_item (
    item_id      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    layer        TEXT NOT NULL,            -- 'foundation' | 'pillar'
    pillar       ewg.pillar,              -- NULL for foundation
    name         TEXT NOT NULL,
    kind         TEXT NOT NULL,           -- asset_portfolio | wip_build | optimization | ai | smart_water | scada | datawarehouse
    value_thb    NUMERIC(18,2),           -- book value or budget
    value_basis  TEXT,                    -- book_value | wip_budget | tbd
    status       TEXT,                    -- run | in_progress | planned
    horizon      TEXT,                    -- Y1 | Y2 | Y3
    note         TEXT,
    sort_order   SMALLINT DEFAULT 0,
    UNIQUE (name)
);

-- ---- seed the programme (values grounded in the ewg DB / DV sheet) ----------
INSERT INTO ewg.transformation_item
    (layer, pillar, name, kind, value_thb, value_basis, status, horizon, note, sort_order)
VALUES
    -- Foundation
    ('foundation', NULL, 'DataWarehouse — SSOT Data Blueprint', 'datawarehouse', NULL, 'tbd', 'in_progress', 'Y1',
     'Centralized DB & structure (Data Architecture). Single source of truth under all pillars.', 0),
    -- Maintenance pillar
    ('pillar', 'maintenance', 'IT Asset Portfolio (existing)', 'asset_portfolio',
     178126181.45, 'book_value', 'run', 'Y1',
     '1,233 booked IT assets. Opex ฿48.0M/yr, Dep ฿47.2M/yr. Monetization candidates inside.', 1),
    ('pillar', 'maintenance', 'Optimization Model — Water Operation', 'optimization',
     NULL, 'tbd', 'planned', 'Y2',
     'Operational optimization of existing water operations (analytics-driven).', 2),
    ('pillar', 'maintenance', 'AI / Advanced Analytics', 'ai',
     NULL, 'tbd', 'planned', 'Y2',
     'AI models on water-ops + asset telemetry (demand, leakage, predictive maintenance).', 3),
    ('pillar', 'maintenance', 'Smart Water', 'smart_water',
     NULL, 'tbd', 'planned', 'Y2',
     'Smart metering / sensor network feeding the DW.', 4),
    ('pillar', 'maintenance', 'SCADA / OT Integration', 'scada',
     NULL, 'tbd', 'run', 'Y1',
     'Existing OT/SCADA — ingest telemetry into the DW for optimization.', 5),
    -- Create (NEW) pillar
    ('pillar', 'create', 'WIP — New Builds', 'wip_build',
     180000000.00, 'wip_budget', 'in_progress', 'Y1',
     'Work-in-progress capital builds (new systems being created).', 6)
ON CONFLICT (name) DO UPDATE SET
    value_thb = EXCLUDED.value_thb, value_basis = EXCLUDED.value_basis,
    status = EXCLUDED.status, horizon = EXCLUDED.horizon, note = EXCLUDED.note,
    layer = EXCLUDED.layer, pillar = EXCLUDED.pillar, kind = EXCLUDED.kind,
    sort_order = EXCLUDED.sort_order;

-- ---- roll-up view: pillar totals (the executive number) --------------------
CREATE OR REPLACE VIEW ewg.v_transformation AS
SELECT layer, pillar, name, kind, value_thb, value_basis, status, horizon, note, sort_order
FROM ewg.transformation_item
ORDER BY sort_order;

CREATE OR REPLACE VIEW ewg.v_pillar_summary AS
SELECT
    CASE WHEN GROUPING(pillar) = 1 THEN 'TOTAL'
         WHEN pillar IS NULL       THEN 'foundation'
         ELSE pillar::text END             AS pillar,
    COUNT(*)                               AS workstreams,
    SUM(value_thb)                         AS quantified_value
FROM ewg.transformation_item
GROUP BY ROLLUP (pillar)
ORDER BY GROUPING(pillar), pillar NULLS FIRST;
