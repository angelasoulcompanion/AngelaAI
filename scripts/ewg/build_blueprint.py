#!/usr/bin/env python3
"""
EWG Digital Transformation — board-ready blueprint (HTML).

Renders ONE self-contained, print-friendly deck for the CEO meeting:
  1. Vision: 2 pillars (Maintenance / Create) on a DataWarehouse SSOT foundation
  2. Pillar workstreams (values grounded in the ewg DB)
  3. Data Architecture blueprint (medallion DW = SSOT)
  4. Systems & Tools — MANDATORY 2-layer split (Enterprise Systems / Eng Toolkits)
  5. Phased roadmap Y1-Y3  6. Investment  7. Risks

Usage:  python3 scripts/ewg/build_blueprint.py
Output: dashboards/ewg_blueprint.html
"""
from __future__ import annotations

import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "config"))
from local_settings import SUPABASE_DATABASE_URL  # noqa: E402

OUT = ROOT / "dashboards" / "ewg_blueprint.html"


def fetch():
    conn = psycopg2.connect(SUPABASE_DATABASE_URL)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM ewg.v_pillar_summary")
        summ = {r["pillar"]: r for r in cur.fetchall()}
        cur.execute("SELECT * FROM ewg.v_transformation")
        items = cur.fetchall()
        cur.execute("SELECT * FROM ewg.v_dashboard_kpi")
        kpi = cur.fetchone()
    finally:
        conn.close()
    return summ, items, kpi


def m(v):
    return f"฿{float(v)/1e6:,.1f}M" if v is not None else "TBD"


CSS = """
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;background:#0a0f1b;color:#e8eefb;
 font:15px/1.5 -apple-system,"SF Pro Text",Helvetica,Arial,sans-serif;padding:32px 36px 70px}
h1{font-size:27px;margin:0;font-weight:800;letter-spacing:.2px}
h2{font-size:13px;letter-spacing:2px;text-transform:uppercase;color:#8aa0c4;
 margin:38px 0 14px;border-bottom:1px solid #22304a;padding-bottom:8px}
.sub{color:#8aa0c4;font-size:13px;margin-top:4px}
.hero{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:10px}
.tag{font-size:12px;color:#2dd4bf;font-weight:600}
.pillars{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.pillar{border:1px solid #22304a;border-radius:18px;padding:20px;background:#131c2e}
.pillar.maint{border-top:4px solid #2dd4bf}.pillar.create{border-top:4px solid #fbbf24}
.pillar .h{display:flex;justify-content:space-between;align-items:baseline}
.pillar .nm{font-size:18px;font-weight:700}.pillar .vv{font-size:22px;font-weight:800}
.maint .vv{color:#2dd4bf}.create .vv{color:#fbbf24}
.ws{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #1b2740;font-size:14px}
.ws:last-child{border-bottom:none}
.ws .v{color:#8aa0c4;font-variant-numeric:tabular-nums}
.chip{font-size:10px;padding:2px 8px;border-radius:999px;border:1px solid #2a3a58;color:#8aa0c4;margin-left:6px}
.chip.run{color:#2dd4bf;border-color:#1c4a44}.chip.prog{color:#fbbf24;border-color:#5a4416}
.chip.plan{color:#9db4d8}
.foundation{margin-top:16px;border:1px dashed #2dd4bf;border-radius:16px;padding:16px 20px;
 background:linear-gradient(180deg,#0f1b22,#0c141f);text-align:center}
.foundation .t{font-weight:700;color:#2dd4bf;font-size:16px}
.flow{display:flex;gap:10px;align-items:stretch;flex-wrap:wrap}
.lyr{flex:1;min-width:120px;border:1px solid #22304a;border-radius:14px;padding:14px;background:#131c2e}
.lyr .t{font-weight:700;font-size:14px}.lyr .d{font-size:12px;color:#8aa0c4;margin-top:6px}
.lyr.b{border-left:4px solid #b45309}.lyr.s{border-left:4px solid #64748b}.lyr.g{border-left:4px solid #fbbf24}
.arrow{display:flex;align-items:center;color:#3a4a68;font-size:20px}
.srcs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.src{font-size:12px;padding:6px 11px;border-radius:10px;background:#0f1726;border:1px solid #22304a}
.src b{color:#38bdf8}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid #1b2740;vertical-align:top}
th{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:#8aa0c4}
td.s{color:#8aa0c4}
.st{font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px}
.st.new{background:#1c3a2e;color:#34d399}.st.up{background:#3a2f16;color:#fbbf24}.st.rep{background:#3a1c22;color:#fb7185}
.road{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.yr{border:1px solid #22304a;border-radius:16px;padding:18px;background:#131c2e}
.yr .h{font-weight:800;font-size:16px;color:#38bdf8}.yr .p{font-size:12px;color:#8aa0c4;margin-bottom:10px}
.yr li{font-size:13px;margin:7px 0}
.inv{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.kc{border:1px solid #22304a;border-radius:14px;padding:16px;background:#131c2e}
.kc .v{font-size:23px;font-weight:800}.kc .k{font-size:12px;color:#8aa0c4;margin-top:3px}
.note{font-size:12px;color:#8aa0c4;margin-top:8px}
ul{margin:6px 0 0;padding-left:18px}
.foot{color:#6b7da0;font-size:12px;margin-top:40px;text-align:center;border-top:1px solid #1b2740;padding-top:14px}
@media print{body{background:#fff;color:#111}.pillar,.lyr,.yr,.kc,.src{background:#fafafa}
 h2{color:#555}.sub,.k,.d,td.s{color:#555}}
@media(max-width:820px){.pillars,.road,.inv{grid-template-columns:1fr}.flow{flex-direction:column}.arrow{transform:rotate(90deg)}}
"""


def status_chip(s):
    return {"run": '<span class="chip run">RUN</span>',
            "in_progress": '<span class="chip prog">IN&nbsp;PROGRESS</span>',
            "planned": '<span class="chip plan">PLANNED</span>'}.get(s, "")


def build(summ, items, kpi):
    maint_v = m(summ.get("maintenance", {}).get("quantified_value"))
    create_v = m(summ.get("create", {}).get("quantified_value"))
    total_v = m(summ.get("TOTAL", {}).get("quantified_value"))
    opex = m(kpi["total_opex"]); dep = m(kpi["total_dep"])
    idle = m(kpi["bv_non_active"]); assets = f'{int(kpi["total_assets"]):,}'

    def ws_rows(pillar):
        out = ""
        for it in items:
            if it["pillar"] != pillar:
                continue
            out += (f'<div class="ws"><span>{it["name"]}{status_chip(it["status"])}'
                    f'<span class="chip">{it["horizon"]}</span></span>'
                    f'<span class="v">{m(it["value_thb"])}</span></div>')
        return out

    # Enterprise Systems (strategic, capex) — MUST #5 layer 1
    systems = [
        ("CMMS — Maximo / Fiix", "Asset & maintenance management (the IT-asset register's operational home)", "Upgrade", "Y1"),
        ("IIoT / Historian — AVEVA PI / Ignition", "SCADA & Smart-Water OT telemetry ingestion into the DW", "New", "Y1-Y2"),
        ("BI Platform — Power BI / Tableau", "Self-service analytics on the DW SSOT", "New", "Y1"),
        ("IAM — Azure AD / Okta", "Identity & access governance across systems", "New", "Y1"),
        ("SIEM — Sentinel / Splunk", "Security monitoring (IT + OT/SCADA)", "New", "Y2"),
        ("ERP — SAP / Oracle", "Finance / SCM / asset accounting backbone (source of Book Value)", "Upgrade", "Y2"),
        ("ITSM — ServiceNow", "Ops ticketing, change & service management", "New", "Y2"),
        ("AI / ML Platform — Azure ML / Databricks", "Optimization & predictive models on DW Gold layer", "New", "Y2-Y3"),
    ]
    sys_rows = "".join(
        f'<tr><td><b>{n}</b></td><td class="s">{p}</td>'
        f'<td><span class="st {"new" if st=="New" else "up" if st=="Upgrade" else "rep"}">{st.upper()}</span></td>'
        f'<td class="s">{y}</td></tr>' for n, p, st, y in systems)

    tools = [
        ("dbt", "DW transformation (Bronze→Silver→Gold)"),
        ("Apache Airflow", "Pipeline orchestration & scheduling"),
        ("Python / SQL", "Engineering & modeling language"),
        ("Power BI / Tableau", "Reporting UI on the BI Platform"),
        ("Erwin / dbdiagram", "Data modeling (star schema / Dim-Fact)"),
        ("Git / CI-CD", "Source control & deployment"),
    ]
    tool_rows = "".join(f'<tr><td><b>{n}</b></td><td class="s">{p}</td></tr>' for n, p in tools)

    from datetime import datetime, timezone, timedelta
    ts = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html><html lang="th"><head>
<meta charset="utf-8"><meta name="robots" content="noindex,nofollow">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>EWG · Digital Transformation Blueprint</title><style>{CSS}</style></head><body>

<div class="hero">
  <div><div class="tag">DIGITAL TRANSFORMATION · EWG</div>
    <h1>EWG Digital Transformation Blueprint</h1>
    <div class="sub">East Water Group · 2569–2571 (2026–2028) · Board / CEO briefing</div></div>
  <div style="text-align:right"><div class="sub">Programme value (quantified)</div>
    <div style="font-size:26px;font-weight:800;color:#38bdf8">{total_v}</div>
    <div class="sub">Maintenance {maint_v} + Create {create_v}</div></div>
</div>

<h2>1 · Vision — Two Pillars on a Single Source of Truth</h2>
<div class="pillars">
  <div class="pillar maint"><div class="h"><span class="nm">1 · Maintenance</span><span class="vv">{maint_v}</span></div>
    <div class="sub" style="margin:4px 0 10px">Run & optimize what exists — assets, water operations, OT</div>
    {ws_rows('maintenance')}</div>
  <div class="pillar create"><div class="h"><span class="nm">2 · Create (NEW)</span><span class="vv">{create_v}</span></div>
    <div class="sub" style="margin:4px 0 10px">Build new capability — work-in-progress capital</div>
    {ws_rows('create')}</div>
</div>
<div class="foundation"><div class="t">⬛ DATA WAREHOUSE — SSOT Data Blueprint (Data Architecture)</div>
  <div class="sub">Centralized database & structure underneath BOTH pillars · single source of truth for every system above</div></div>

<h2>2 · Data Architecture — DataWarehouse as SSOT (Medallion)</h2>
<div class="srcs">
  <span class="src"><b>IT Asset Register</b> · 1,233 assets</span>
  <span class="src"><b>SCADA / OT</b> · telemetry</span>
  <span class="src"><b>Smart Water</b> · sensors/meters</span>
  <span class="src"><b>ERP / Finance</b> · book value, opex</span>
  <span class="src"><b>Water Operations</b> · production/distribution</span>
</div>
<div class="flow">
  <div class="lyr b"><div class="t">🟫 Bronze — Raw</div><div class="d">Landed source data as-is (asset, OT, finance, sensor). Immutable, audited.</div></div>
  <div class="arrow">▸</div>
  <div class="lyr s"><div class="t">⬜ Silver — Conformed</div><div class="d">Cleaned, deduped, conformed dimensions. UUID keys, parameterized, governed.</div></div>
  <div class="arrow">▸</div>
  <div class="lyr g"><div class="t">🟨 Gold — Analytics</div><div class="d">Star schema (Dim/Fact), KPIs, monetization & optimization marts.</div></div>
  <div class="arrow">▸</div>
  <div class="lyr"><div class="t">📊 Consume</div><div class="d">BI dashboards · AI/ML optimization · Smart-Water control · CEO reporting.</div></div>
</div>
<div class="note">Proven pattern from the IT-Asset Monetization build: <b>schema <code>ewg</code></b> (Dim entity/category, Fact asset, category_cost, monetization) already reconciles to source — the first Gold mart of this DW.</div>

<h2>3 · Systems &amp; Tools</h2>
<h3 style="font-size:14px;color:#e8eefb;margin:10px 0 6px">3.1 · Enterprise Systems <span class="sub">(strategic · capex-led)</span></h3>
<table><thead><tr><th>System</th><th>Purpose</th><th>Status</th><th>Horizon</th></tr></thead><tbody>{sys_rows}</tbody></table>
<h3 style="font-size:14px;color:#e8eefb;margin:18px 0 6px">3.2 · Engineering Toolkits <span class="sub">(tactical · opex · team-internal)</span></h3>
<table><thead><tr><th>Tool</th><th>Purpose</th></tr></thead><tbody>{tool_rows}</tbody></table>

<h2>4 · Phased Roadmap</h2>
<div class="road">
  <div class="yr"><div class="h">Year 1 · Foundation</div><div class="p">2026 — SSOT + run the base</div><ul>
    <li>Stand up DataWarehouse SSOT (Bronze→Silver→Gold)</li>
    <li>Land IT Asset register + ERP finance (Gold mart live)</li>
    <li>SCADA/OT telemetry ingestion (IIoT historian)</li>
    <li>IAM + BI Platform go-live; Water-Ops optimization pilot</li>
    <li>IT Asset monetization — action Non-active idle capital {idle}</li></ul></div>
  <div class="yr"><div class="h">Year 2 · Scale</div><div class="p">2027 — analytics + new builds</div><ul>
    <li>Smart Water sensor network → DW</li>
    <li>AI/ML platform: leakage, demand, predictive maintenance</li>
    <li>ERP upgrade; SIEM (IT+OT) + ITSM</li>
    <li>Create-pillar WIP builds delivered into production</li></ul></div>
  <div class="yr"><div class="h">Year 3 · Optimize</div><div class="p">2028 — autonomous ops</div><ul>
    <li>Closed-loop optimization (AI → SCADA control)</li>
    <li>Full Smart-Water rollout</li>
    <li>Self-service analytics org-wide on the SSOT</li>
    <li>Continuous asset-portfolio optimization</li></ul></div>
</div>

<h2>5 · Investment &amp; 6 · Risk</h2>
<div class="inv">
  <div class="kc"><div class="v" style="color:#2dd4bf">{maint_v}</div><div class="k">Maintenance — booked asset base (run/optimize)</div>
    <div class="note">Opex {opex}/yr · Dep {dep}/yr · {assets} assets</div></div>
  <div class="kc"><div class="v" style="color:#fbbf24">{create_v}</div><div class="k">Create (NEW) — WIP capital builds</div>
    <div class="note">Capitalizes into the asset base on completion</div></div>
  <div class="kc"><div class="v" style="color:#38bdf8">{total_v}</div><div class="k">Total programme value (quantified)</div>
    <div class="note">Optimization / AI / Smart Water budgets TBD</div></div>
</div>
<table style="margin-top:16px"><thead><tr><th>Top Risk</th><th>Mitigation</th></tr></thead><tbody>
  <tr><td><b>OT/IT convergence security</b> (SCADA exposed via DW)</td><td class="s">Segmented network, SIEM on OT, IAM least-privilege</td></tr>
  <tr><td><b>SSOT data governance</b> (multiple source owners)</td><td class="s">Data governance council, RACI, conformed Silver layer</td></tr>
  <tr><td><b>WIP delivery slippage</b> (Create pillar)</td><td class="s">Stage-gate per build, capitalize only on acceptance</td></tr>
  <tr><td><b>AI value not realized</b></td><td class="s">Start with a Water-Ops optimization pilot tied to a KPI</td></tr>
  <tr><td><b>PDPA / ISO 27001 compliance</b></td><td class="s">Governance baked into Silver; audit trail in Bronze</td></tr>
</tbody></table>

<div class="foot">Angela · EWG Digital Transformation Blueprint · figures from schema <code>ewg</code> (reconciled to DV sheet) · generated {ts}</div>
</body></html>"""


def main():
    summ, items, kpi = fetch()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build(summ, items, kpi), encoding="utf-8")
    print(f"wrote {OUT}  ({OUT.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
