#!/usr/bin/env python3
"""
EWG IT Asset Monetization — Excel → Supabase importer.

Loads:
  * sheet 'EWG' -> ewg.asset       (raw IT asset register, total rows filtered out)
  * sheet 'DV'  -> ewg.monetization_scenario + ewg.monetization_line

Idempotent: re-runnable. Assets upsert on (entity_id, asset_code);
the DV scenario is replaced (delete + reinsert) per scenario_name.

Usage:
  python3 scripts/ewg/import_assets.py "/path/to/Asset_DV_June 2026_19 June.xlsx"
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# --- DB connection (Supabase Tokyo, from config/local_settings.py) ----------
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "config"))
from local_settings import SUPABASE_DATABASE_URL  # noqa: E402

DEFAULT_FILE = "/Users/davidsamanyaporn/Desktop/EWG Asset Monetize/Asset_DV_June 2026_19 June.xlsx"
SCENARIO_NAME = "DV June 2026"

# valid sub-entity codes that mark a real data row in col 0
ENTITY_CODES = {"EW", "UU"}


# --- normalizers ------------------------------------------------------------
def norm_placement(v):
    if v is None:
        return None
    s = str(v).strip().lower().replace(" ", "")
    if s.startswith("back"):
        return "back_end"
    if s.startswith("front"):
        return "front_end"
    return None


def norm_hw_sw(v):
    s = str(v).strip().upper()
    if s == "HW":
        return "hw"
    if s == "SW":
        return "sw"
    return None


def norm_status(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    if s == "active":
        return "active"
    if s in ("non-active", "nonactive", "non active"):
        return "non_active"
    if s == "tbc":
        return "tbc"
    return None


def norm_int(v):
    try:
        if pd.isna(v):
            return None
        return int(float(v))
    except (ValueError, TypeError):
        return None


def norm_num(v):
    try:
        if pd.isna(v) or str(v).strip() == "":
            return None
        return round(float(v), 2)
    except (ValueError, TypeError):
        return None


def norm_date(v):
    """Cap.date is 'DD.MM.YYYY' text (or a real datetime)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (pd.Timestamp,)):
        return v.date()
    s = str(v).strip()
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if m:
        d, mo, y = map(int, m.groups())
        try:
            return date(y, mo, d)
        except ValueError:
            return None
    return None


# --- load EWG register ------------------------------------------------------
def load_assets(conn, xlsx: str) -> int:
    df = pd.read_excel(xlsx, sheet_name="EWG", header=4)
    df.columns = [str(c).strip() for c in df.columns]
    col0 = df.columns[0]  # entity code column (unnamed)

    cur = conn.cursor()
    cur.execute("SELECT entity_code, entity_id FROM ewg.entity")
    entity_map = dict(cur.fetchall())
    cur.execute("SELECT category_name, category_id FROM ewg.breakdown_category")
    cat_map = dict(cur.fetchall())

    rows, skipped, current_entity = [], 0, None
    seen_codes: dict[tuple, int] = {}  # (entity_id, asset_code) -> next sub_seq
    for idx, r in df.iterrows():
        code0 = str(r[col0]).strip() if pd.notna(r[col0]) else ""
        if code0 in ENTITY_CODES:
            current_entity = code0  # entity marker carries forward down the block

        asset_code = str(r["Asset"]).strip() if pd.notna(r["Asset"]) else ""
        # skip non-asset rows: blanks, total rows (Use in {รวม,EW,UU}), missing code
        use_raw = str(r["Use"]).strip() if pd.notna(r["Use"]) else ""
        if not asset_code or use_raw in ("รวม", "EW", "UU") or current_entity is None:
            skipped += 1
            continue
        if not re.match(r"^\d", asset_code):  # asset codes start with a digit
            skipped += 1
            continue

        cat = str(r["Breakdown cost"]).strip() if pd.notna(r["Breakdown cost"]) else ""
        ent_id = entity_map[current_entity]
        sub_seq = seen_codes.get((ent_id, asset_code), 0)
        seen_codes[(ent_id, asset_code)] = sub_seq + 1
        rows.append((
            ent_id,
            sub_seq,
            norm_int(r["NO"]),
            asset_code,
            str(r["Asset description"]).strip() if pd.notna(r["Asset description"]) else None,
            norm_date(r["Cap.date"]),
            norm_int(r["Use"]),
            norm_num(r["Curr.acq.value"]),
            norm_num(r["Accum.dep."]),
            norm_num(r["Curr.net bk.val."]),
            norm_num(r["Dep. Year 2026"]),
            norm_placement(r["Back-end / Front-end"]),
            norm_hw_sw(r["HW/SW"]),
            norm_status(r["Active / Non-active"]),
            cat_map.get(cat),
            norm_num(r["Opex"]),
            Path(xlsx).name,
            int(idx) + 6,  # 1-based incl. header offset
        ))

    execute_values(cur, """
        INSERT INTO ewg.asset (
            entity_id, sub_seq, asset_no, asset_code, description, cap_date,
            useful_life_years, acq_value, accum_dep, net_book_value, dep_year_2026,
            placement, hw_sw, status, category_id, opex, source_file, source_row)
        VALUES %s
        ON CONFLICT (entity_id, asset_code, sub_seq) DO UPDATE SET
            asset_no=EXCLUDED.asset_no, description=EXCLUDED.description,
            cap_date=EXCLUDED.cap_date, useful_life_years=EXCLUDED.useful_life_years,
            acq_value=EXCLUDED.acq_value, accum_dep=EXCLUDED.accum_dep,
            net_book_value=EXCLUDED.net_book_value, dep_year_2026=EXCLUDED.dep_year_2026,
            placement=EXCLUDED.placement, hw_sw=EXCLUDED.hw_sw, status=EXCLUDED.status,
            category_id=EXCLUDED.category_id, opex=EXCLUDED.opex,
            source_file=EXCLUDED.source_file, source_row=EXCLUDED.source_row,
            imported_at=now()
    """, rows)
    conn.commit()
    print(f"  assets: inserted/updated {len(rows)} | skipped {skipped} non-asset rows")
    return len(rows)


# --- load DV monetization model --------------------------------------------
def load_monetization(conn, xlsx: str):
    dv = pd.read_excel(xlsx, sheet_name="DV", header=None)
    cur = conn.cursor()

    # header block: Asset 175M (row2,col3), WIP 180M (row3,col3), total (row5,col3)
    book = norm_num(dv.iat[2, 3])
    wip = norm_num(dv.iat[3, 3])
    total = norm_num(dv.iat[5, 3])

    cur.execute("DELETE FROM ewg.monetization_scenario WHERE scenario_name=%s", (SCENARIO_NAME,))
    cur.execute("""
        INSERT INTO ewg.monetization_scenario
            (scenario_name, as_of_date, book_value_asset, wip, total_value, note)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING scenario_id
    """, (SCENARIO_NAME, date(2026, 3, 31), book, wip, total,
          "Imported from DV sheet — Asset_DV_June 2026"))
    scenario_id = cur.fetchone()[0]

    # Back-End / Front-End / Total block: rows 18-31, label col=2, BV=3,Dep=4,Opex=5
    placement_now = None
    lines = []
    for i in range(18, 32):
        label = str(dv.iat[i, 2]).strip() if pd.notna(dv.iat[i, 2]) else ""
        if label in ("Back-End", "Front-End", "Total"):
            placement_now = norm_placement(label) if label != "Total" else "TOTAL"
            base = label
        else:
            base = label  # Active / Non-Active / TBC
        status = norm_status(label)
        bv, dep, opx = norm_num(dv.iat[i, 3]), norm_num(dv.iat[i, 4]), norm_num(dv.iat[i, 5])
        if bv is None and dep is None and opx is None:
            continue
        # only store placement-scoped rows (skip the grand Total roll-up; it's a view)
        if placement_now in ("back_end", "front_end"):
            lines.append((scenario_id, None,
                          placement_now,
                          status,  # None on the header row, set on Active/Non-Active/TBC
                          bv, dep, opx))

    # OT / IT domain block: rows 11-12. col9=Total Opex, col10=Total Depre.
    # Stored as domain-level totals (no book value at this granularity).
    for i, dom in ((11, "OT"), (12, "IT")):
        lines.append((scenario_id, dom, None, None,
                      None,                     # book_value (n/a at domain level)
                      norm_num(dv.iat[i, 10]),  # Total Depre
                      norm_num(dv.iat[i, 9])))  # Total Opex

    execute_values(cur, """
        INSERT INTO ewg.monetization_line
            (scenario_id, domain, placement, status, book_value, depre, opex)
        VALUES %s
    """, lines)
    conn.commit()
    print(f"  monetization: scenario '{SCENARIO_NAME}' "
          f"(BV={book:,.0f} WIP={wip:,.0f} total={total:,.0f}) + {len(lines)} lines")


# atomic placement × hw_sw column groups (BV, Dep, Opex) in the SUM EWG band
_SUM_ATOM = {
    ("back_end", "hw"): (2, 3, 4),
    ("back_end", "sw"): (5, 6, 7),
    ("front_end", "hw"): (11, 12, 13),
    ("front_end", "sw"): (14, 15, 16),
}


def load_category_cost(conn, xlsx: str):
    """SUM EWG sheet -> ewg.category_cost (authoritative Opex SSOT)."""
    s = pd.read_excel(xlsx, sheet_name="SUM EWG", header=None)
    cur = conn.cursor()
    cur.execute("SELECT category_name, category_id FROM ewg.breakdown_category")
    cat_map = dict(cur.fetchall())

    rows, cat = [], None
    for i in range(4, s.shape[0]):
        c0, c1 = s.iat[i, 0], s.iat[i, 1]
        c1 = str(c1).strip() if pd.notna(c1) else ""
        if pd.notna(c0) and str(c0).strip().replace(".0", "").isdigit():
            cat = c1            # category header row = roll-up of its statuses, skip
            continue
        st = norm_status(c1)
        if not st or cat is None or cat not in cat_map:
            continue
        for (pl, hw), (b, d, o) in _SUM_ATOM.items():
            bv, dep, opx = norm_num(s.iat[i, b]), norm_num(s.iat[i, d]), norm_num(s.iat[i, o])
            if bv is None and dep is None and opx is None:
                continue
            rows.append((cat_map[cat], pl, hw, st, bv, dep, opx, Path(xlsx).name))

    cur.execute("TRUNCATE ewg.category_cost")
    execute_values(cur, """
        INSERT INTO ewg.category_cost
            (category_id, placement, hw_sw, status, book_value, depre, opex, source_file)
        VALUES %s
    """, rows)
    conn.commit()
    cur.execute("SELECT sum(opex), sum(depre), sum(book_value) FROM ewg.category_cost")
    so, sd, sb = cur.fetchone()
    print(f"  category_cost: {len(rows)} rows | opex={so:,.2f} dep={sd:,.2f} bv={sb:,.2f}")


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE
    if not Path(xlsx).exists():
        sys.exit(f"file not found: {xlsx}")
    print(f"Importing: {xlsx}")
    conn = psycopg2.connect(SUPABASE_DATABASE_URL)
    try:
        load_assets(conn, xlsx)
        load_category_cost(conn, xlsx)
        load_monetization(conn, xlsx)
    finally:
        conn.close()
    print("done.")


if __name__ == "__main__":
    main()
