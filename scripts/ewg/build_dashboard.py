#!/usr/bin/env python3
"""
EWG Asset Monetization — build a self-contained iPad dashboard (HTML).

Queries the ewg.* dashboard views on Supabase Tokyo and renders ONE standalone
HTML file (data embedded, no backend, no CDN) optimized for iPadOS Safari.

Usage:  python3 scripts/ewg/build_dashboard.py
Output: dashboards/ewg_monetization.html
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "config"))
from local_settings import SUPABASE_DATABASE_URL  # noqa: E402

OUT = ROOT / "dashboards" / "ewg_monetization.html"


def fetch():
    conn = psycopg2.connect(SUPABASE_DATABASE_URL)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM ewg.v_dashboard_kpi")
        kpi = cur.fetchone()
        cur.execute("SELECT * FROM ewg.v_dashboard")
        cats = cur.fetchall()
        cur.execute("SELECT * FROM ewg.v_dashboard_domain")
        domain = cur.fetchall()
        cur.execute("SELECT * FROM ewg.v_dashboard_status")
        status = cur.fetchall()
        cur.execute("""SELECT entity_code, asset_code, description, category_name,
                              net_book_value FROM ewg.v_monetize_candidates LIMIT 12""")
        cand = cur.fetchall()
    finally:
        conn.close()
    # cast Decimals to float for JSON
    def f(v):
        return float(v) if v is not None else 0.0
    for r in cats:
        for k in ("book_value", "depreciation", "opex", "annual_cost", "bv_non_active", "opex_to_bv"):
            r[k] = f(r[k])
    for grp in (domain, status):
        for r in grp:
            for k in ("book_value", "depreciation", "opex"):
                r[k] = f(r[k])
    for r in cand:
        r["net_book_value"] = f(r["net_book_value"])
    kpi = {k: f(v) if k not in ("total_assets", "non_active_assets") else int(v)
           for k, v in kpi.items()}
    return {"kpi": kpi, "cats": cats, "domain": domain, "status": status, "cand": cand}


HTML = """<!DOCTYPE html>
<html lang="th"><head>
<meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>EWG · IT Asset Monetization</title>
<style>
  :root{ --bg:#0b1220; --card:#131c2e; --card2:#0f1726; --line:#22304a;
         --ink:#e8eefb; --mut:#8aa0c4; --teal:#2dd4bf; --cyan:#38bdf8;
         --amber:#fbbf24; --rose:#fb7185; --grid:#1b2740; }
  *{box-sizing:border-box; -webkit-tap-highlight-color:transparent}
  body{margin:0; background:linear-gradient(180deg,#0b1220,#0a0f1b 60%);
       color:var(--ink); font:16px/1.45 -apple-system,"SF Pro Text",Helvetica,Arial,sans-serif;
       padding:max(env(safe-area-inset-top),20px) 20px 60px; -webkit-text-size-adjust:100%}
  header{display:flex; align-items:baseline; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-bottom:4px}
  h1{font-size:22px; font-weight:700; margin:0; letter-spacing:.2px}
  .sub{color:var(--mut); font-size:13px}
  .asof{color:var(--teal); font-weight:600}
  section{margin-top:22px}
  .lbl{font-size:12px; letter-spacing:1.4px; text-transform:uppercase; color:var(--mut); margin:0 0 10px}
  .kpis{display:grid; grid-template-columns:repeat(4,1fr); gap:12px}
  .kpi{background:var(--card); border:1px solid var(--line); border-radius:16px; padding:16px}
  .kpi .v{font-size:23px; font-weight:700; letter-spacing:.3px}
  .kpi .k{font-size:12px; color:var(--mut); margin-top:4px}
  .kpi.accent .v{color:var(--teal)} .kpi.warn .v{color:var(--amber)} .kpi.deal .v{color:var(--cyan)}
  .grid2{display:grid; grid-template-columns:1.55fr 1fr; gap:16px}
  .card{background:var(--card); border:1px solid var(--line); border-radius:18px; padding:18px}
  table{width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums}
  th,td{text-align:right; padding:9px 8px; border-bottom:1px solid var(--grid); white-space:nowrap}
  th{font-size:11px; letter-spacing:.6px; color:var(--mut); text-transform:uppercase; font-weight:600}
  td.l,th.l{text-align:left}
  .cat{font-weight:600}
  .pill{font-size:10px; padding:2px 8px; border-radius:999px; border:1px solid var(--line); color:var(--mut)}
  .pill.ot{color:var(--amber); border-color:#5a4416} .pill.it{color:var(--cyan); border-color:#1e3a5a}
  .bar{height:8px; border-radius:6px; background:var(--grid); overflow:hidden; min-width:60px}
  .bar>i{display:block; height:100%; background:linear-gradient(90deg,var(--teal),var(--cyan))}
  .ratio{font-weight:700} .hot{color:var(--rose)} .warm{color:var(--amber)} .cool{color:var(--mut)}
  .donut{display:flex; align-items:center; gap:18px}
  .legend{font-size:13px; color:var(--mut)} .legend b{color:var(--ink); font-weight:600}
  .dot{display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:7px; vertical-align:middle}
  .cand td{border-bottom:1px solid var(--grid)}
  .foot{color:var(--mut); font-size:12px; margin-top:26px; text-align:center}
  @media (max-width:820px){ .kpis{grid-template-columns:repeat(2,1fr)} .grid2{grid-template-columns:1fr} }
</style></head><body>

<header>
  <div><h1>EWG · IT Asset Monetization</h1>
    <div class="sub">East Water Group — ทรัพย์สินทาง IT · ณ <span class="asof">31 มีนาคม 2569</span></div></div>
  <div class="sub">Deal Total <b style="color:var(--cyan)">฿355.0M</b> &nbsp;=&nbsp; Asset ฿175.0M + WIP ฿180.0M</div>
</header>

<section>
  <p class="lbl">ภาพรวม</p>
  <div class="kpis">
    <div class="kpi accent"><div class="v">฿[[bv]]</div><div class="k">Net Book Value</div></div>
    <div class="kpi"><div class="v">฿[[dep]]</div><div class="k">Depreciation / ปี</div></div>
    <div class="kpi warn"><div class="v">฿[[opex]]</div><div class="k">Opex / ปี</div></div>
    <div class="kpi deal"><div class="v">[[assets]]</div><div class="k">รายการทรัพย์สิน</div></div>
  </div>
</section>

<section class="grid2">
  <div class="card">
    <p class="lbl">รายหมวด — BV · Dep · Opex · ต้นทุนต่อปี (Dep+Opex)</p>
    <table>
      <thead><tr><th class="l">Category</th><th>BV</th><th>Dep/ปี</th><th>Opex/ปี</th>
        <th class="l">ต้นทุน/ปี</th><th>Opex/BV</th></tr></thead>
      <tbody>[[rows]]</tbody>
    </table>
  </div>
  <div class="card">
    <p class="lbl">สัดส่วน OT vs IT (BV)</p>
    <div class="donut">[[donut]]
      <div class="legend">[[legend]]</div>
    </div>
    <p class="lbl" style="margin-top:22px">Active vs Non-active</p>
    [[statusbars]]
  </div>
</section>

<section class="card">
  <p class="lbl">🎯 Monetization candidates — Non-active ที่ยังมีมูลค่า (idle capital ฿[[idle]])</p>
  <table class="cand">
    <thead><tr><th class="l">Asset</th><th class="l">รายการ</th><th class="l">หมวด</th><th>Net Book Value</th></tr></thead>
    <tbody>[[candrows]]</tbody>
  </table>
</section>

<p class="foot">Angela · EWG Asset Monetization &nbsp;·&nbsp; reconciled to DV sheet (BV ฿178.1M · Dep ฿47.2M · Opex ฿48.0M) &nbsp;·&nbsp; generated [[ts]]</p>
</body></html>"""


def m(v):  # ฿ millions
    return f"{v/1e6:,.1f}M"


def fullbaht(v):
    return f"{v:,.0f}"


def donut_svg(ot, it):
    total = ot + it or 1
    ot_frac = ot / total
    r, c = 52, 60
    circ = 2 * 3.14159265 * r
    ot_len = circ * ot_frac
    return f'''<svg width="120" height="120" viewBox="0 0 120 120">
      <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="#1b2740" stroke-width="16"/>
      <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="#fbbf24" stroke-width="16"
              stroke-dasharray="{ot_len:.1f} {circ:.1f}" transform="rotate(-90 {c} {c})" stroke-linecap="round"/>
      <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="#38bdf8" stroke-width="16"
              stroke-dasharray="{circ-ot_len:.1f} {circ:.1f}" stroke-dashoffset="{-ot_len:.1f}"
              transform="rotate(-90 {c} {c})" stroke-linecap="round"/>
      <text x="{c}" y="{c-2}" text-anchor="middle" fill="#e8eefb" font-size="15" font-weight="700">฿{total/1e6:,.0f}M</text>
      <text x="{c}" y="{c+15}" text-anchor="middle" fill="#8aa0c4" font-size="9">Book Value</text>
    </svg>'''


def build(d):
    k = d["kpi"]
    maxann = max((c["annual_cost"] for c in d["cats"]), default=1) or 1
    rows = ""
    for c in d["cats"]:
        ratio = c["opex_to_bv"]
        cls = "hot" if ratio >= 1 else "warm" if ratio >= 0.5 else "cool"
        dom = "ot" if c["domain"] == "OT" else "it"
        bw = int(100 * c["annual_cost"] / maxann)
        rows += f'''<tr>
          <td class="l cat">{c['category_name']}<br><span class="pill {dom}">{c['domain']}</span></td>
          <td>฿{m(c['book_value'])}</td><td>฿{m(c['depreciation'])}</td><td>฿{m(c['opex'])}</td>
          <td class="l"><div class="bar"><i style="width:{bw}%"></i></div>
              <span style="font-size:12px;color:var(--mut)">฿{m(c['annual_cost'])}</span></td>
          <td class="ratio {cls}">{ratio:.2f}</td></tr>'''

    dom = {r["domain"]: r["book_value"] for r in d["domain"]}
    ot, it = dom.get("OT", 0), dom.get("IT", 0)
    donut = donut_svg(ot, it)
    tot = ot + it or 1
    legend = (f'<div><span class="dot" style="background:#fbbf24"></span>'
              f'<b>OT</b> ฿{m(ot)} · {ot/tot*100:.0f}%</div>'
              f'<div style="margin-top:8px"><span class="dot" style="background:#38bdf8"></span>'
              f'<b>IT</b> ฿{m(it)} · {it/tot*100:.0f}%</div>')

    st = {r["status"]: r for r in d["status"]}
    smax = max((r["book_value"] for r in d["status"]), default=1) or 1
    sbars = ""
    for key, label, col in (("active", "Active", "#2dd4bf"), ("non_active", "Non-active", "#fb7185")):
        v = st.get(key, {}).get("book_value", 0)
        sbars += (f'<div style="margin:8px 0"><div style="display:flex;justify-content:space-between;'
                  f'font-size:13px"><span class="legend"><b>{label}</b></span>'
                  f'<span style="color:var(--mut)">฿{m(v)}</span></div>'
                  f'<div class="bar" style="margin-top:5px"><i style="width:{100*v/smax:.0f}%;'
                  f'background:{col}"></i></div></div>')

    candrows = ""
    for c in d["cand"]:
        desc = (c["description"] or "")[:42]
        candrows += (f'<tr><td class="l" style="color:var(--cyan)">{c["asset_code"]}</td>'
                     f'<td class="l">{desc}</td><td class="l" style="color:var(--mut)">{c["category_name"]}</td>'
                     f'<td>฿{fullbaht(c["net_book_value"])}</td></tr>')

    from datetime import datetime, timezone, timedelta
    ts = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M")
    subs = {
        "bv": m(k["total_bv"]), "dep": m(k["total_dep"]), "opex": m(k["total_opex"]),
        "assets": f'{k["total_assets"]:,}', "rows": rows, "donut": donut, "legend": legend,
        "statusbars": sbars, "idle": m(k["bv_non_active"]), "candrows": candrows, "ts": ts,
    }
    out = HTML
    for key, val in subs.items():
        out = out.replace("[[" + key + "]]", val)
    return out


def main():
    data = fetch()
    OUT.parent.mkdir(exist_ok=True)
    html = build(data)
    OUT.write_text(html, encoding="utf-8")
    # index.html for Vercel static deploy (same content)
    (OUT.parent / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote {OUT}  ({OUT.stat().st_size/1024:.1f} KB)  + index.html")


if __name__ == "__main__":
    main()
