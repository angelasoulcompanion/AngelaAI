-- ============================================================================
-- EWG IT Asset Monetization — Schema & Tables
-- Source: Asset_DV_June 2026_19 June.xlsx  (ณ 31 มีนาคม 2569)
-- Target: Angela Supabase Tokyo (vdvjfivhvvmlpgdhjmga)
-- Design : Normalized register (fact) + dimensions + monetization model (DV sheet)
--          Derived summaries (SUM EWG / PVT EWG) are VIEWS, never duplicated.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS ewg;

-- ---- ENUM types (fixed domains) ------------------------------------------
DO $$ BEGIN
    CREATE TYPE ewg.placement_type AS ENUM ('back_end', 'front_end');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ewg.hw_sw_type AS ENUM ('hw', 'sw');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ewg.asset_status AS ENUM ('active', 'non_active', 'tbc');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ewg.tech_domain AS ENUM ('OT', 'IT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---- DIMENSION: sub-entity (EW = East Water, UU = Universal Utilities) ----
CREATE TABLE IF NOT EXISTS ewg.entity (
    entity_id    SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entity_code  TEXT NOT NULL UNIQUE,         -- 'EW', 'UU'
    entity_name  TEXT NOT NULL
);

-- ---- DIMENSION: breakdown cost category -----------------------------------
CREATE TABLE IF NOT EXISTS ewg.breakdown_category (
    category_id    SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name  TEXT NOT NULL UNIQUE,        -- e.g. 'Core Infrastructure'
    domain         ewg.tech_domain              -- OT vs IT (per DV sheet)
);

-- ---- FACT: IT asset register (1 row = 1 asset) ----------------------------
CREATE TABLE IF NOT EXISTS ewg.asset (
    asset_id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id         SMALLINT NOT NULL REFERENCES ewg.entity(entity_id),
    asset_no          INTEGER,                  -- running NO within sheet
    asset_code        TEXT NOT NULL,            -- SAP asset number e.g. 123020200023-0
    description       TEXT,
    cap_date          DATE,                     -- capitalization date
    useful_life_years INTEGER,                  -- 'Use' column
    acq_value         NUMERIC(18,2),            -- Curr.acq.value
    accum_dep         NUMERIC(18,2),            -- Accum.dep. (stored negative as source)
    net_book_value    NUMERIC(18,2),            -- Curr.net bk.val.
    dep_year_2026     NUMERIC(18,2),            -- Dep. Year 2026 (negative)
    placement         ewg.placement_type,       -- Back-end / Front-end
    hw_sw             ewg.hw_sw_type,           -- HW / SW
    status            ewg.asset_status,         -- Active / Non-active / TBC
    category_id       SMALLINT REFERENCES ewg.breakdown_category(category_id),
    opex              NUMERIC(18,2),            -- annual Opex (nullable)
    -- lineage
    source_file       TEXT,
    source_row        INTEGER,
    imported_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE (entity_id, asset_code)
);

CREATE INDEX IF NOT EXISTS idx_asset_entity     ON ewg.asset(entity_id);
CREATE INDEX IF NOT EXISTS idx_asset_category   ON ewg.asset(category_id);
CREATE INDEX IF NOT EXISTS idx_asset_status     ON ewg.asset(status);
CREATE INDEX IF NOT EXISTS idx_asset_placement  ON ewg.asset(placement);

-- ---- MONETIZATION model (DV sheet) ----------------------------------------
-- Header: a valuation snapshot/scenario (Book Value, WIP, Total)
CREATE TABLE IF NOT EXISTS ewg.monetization_scenario (
    scenario_id       UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scenario_name     TEXT NOT NULL,
    as_of_date        DATE,
    book_value_asset  NUMERIC(18,2),            -- DV: Asset 175,000,000
    wip               NUMERIC(18,2),            -- DV: WIP 180,000,000
    total_value       NUMERIC(18,2),            -- DV: 355,000,000
    note              TEXT,
    created_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE (scenario_name)
);

-- Lines: BV / Depre / Opex broken down by domain × placement × status
CREATE TABLE IF NOT EXISTS ewg.monetization_line (
    line_id      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scenario_id  UUID NOT NULL REFERENCES ewg.monetization_scenario(scenario_id) ON DELETE CASCADE,
    domain       ewg.tech_domain,              -- OT / IT (nullable for placement-only rows)
    placement    ewg.placement_type,           -- Back-end / Front-end (nullable)
    status       ewg.asset_status,             -- active / non_active / tbc (nullable = subtotal)
    book_value   NUMERIC(18,2),
    depre        NUMERIC(18,2),
    opex         NUMERIC(18,2)
);

CREATE INDEX IF NOT EXISTS idx_monet_line_scenario ON ewg.monetization_line(scenario_id);

COMMENT ON SCHEMA ewg IS 'EWG IT Asset Monetization — register + monetization model. Source: Asset_DV_June 2026.';
