#!/usr/bin/env python3
"""Turn downloaded award pages into awards.json, and render one pay-rate page per award.

  python awards.py parse RAW_DIR   # writes awards.json (keeps the old entry for any award that fails)
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from awardparse import junior_pct, junior_tables, penalty_tables, rate_tables, title  # noqa: E402
from tax import KINDS, calculate  # noqa: E402

# Awards whose first table mixes streams or lacks labels; their level pages wait for clearer labels (see ROADMAP).
LEVEL_SKIP = {"schads", "nurses", "aged-care", "childcare"}

AWARDS = {
    "MA000004": ("retail", "Retail", "Shops and supermarkets: sales assistants, checkout operators, shelf stackers, store managers."),
    "MA000009": ("hospitality", "Hospitality", "Hotels, pubs, motels, casinos and resorts: bar, kitchen, housekeeping and front office staff."),
    "MA000003": ("fast-food", "Fast food", "Takeaway and fast food shops: counter staff, cooks and delivery drivers."),
    "MA000119": ("restaurant", "Restaurants and cafes", "Restaurants, cafes and catering: waiters, baristas, cooks and kitchen hands."),
    "MA000002": ("clerks", "Office and admin (clerks)", "Office workers in private businesses: receptionists, admin assistants, data entry, accounts clerks."),
    "MA000022": ("cleaning", "Cleaning", "Commercial cleaners working for cleaning contractors."),
    "MA000018": ("aged-care", "Aged care", "Residential aged care: personal care workers, cooks, cleaners, laundry and admin staff."),
    "MA000100": ("schads", "Social, community, home care and disability (SCHADS)", "Community services, disability support, home care and crisis accommodation workers."),
    "MA000120": ("childcare", "Childcare", "Early childhood educators and staff in long day care, preschools and OSHC."),
    "MA000034": ("nurses", "Nurses", "Registered nurses, enrolled nurses and nursing assistants."),
    "MA000027": ("health-professionals", "Health professionals and support", "Allied health, dental assistants, pathology collectors and health support staff."),
    "MA000016": ("security", "Security", "Security officers, crowd controllers and patrol staff."),
    "MA000028": ("horticulture", "Farm work (horticulture)", "Fruit, vegetable, flower and nursery farm work, including picking and packing."),
    "MA000010": ("manufacturing", "Manufacturing", "Factory, production, engineering and process workers."),
    "MA000020": ("construction", "Building and construction", "On-site construction labourers, tradespeople and plant operators."),
    "MA000025": ("electrical", "Electrical contracting", "Electricians, electrical apprentices and communications workers."),
    "MA000038": ("transport", "Truck driving and warehousing (road transport)", "Truck drivers, couriers and distribution centre workers."),
    "MA000084": ("storage", "Warehouse and wholesale (storage services)", "Storeworkers and wholesale employees."),
    "MA000005": ("hair-beauty", "Hair and beauty", "Hairdressers, barbers, beauty therapists and salon staff."),
    "MA000058": ("clubs", "Clubs", "Registered and licensed clubs: RSLs, sports and leagues clubs."),
}


def parse(raw_dir: Path) -> dict:
    out_path = HERE / "awards.json"
    old = {a["code"]: a for a in json.loads(out_path.read_text())["awards"]} if out_path.exists() else {}
    result, ok = [], 0
    for code, (slug, short, blurb) in AWARDS.items():
        f = raw_dir / f"{code}.html"
        entry = None
        if f.exists():
            html = f.read_text(encoding="utf-8", errors="replace")
            tables = rate_tables(html)
            if tables:
                hourly = [r["hourly"] for t in tables for r in t["rows"]]
                entry = {"code": code, "slug": slug, "short": short, "blurb": blurb,
                         "name": re.sub(r"\s*\[MA\d+\]", "", title(html)),
                         "min_hourly": min(hourly), "tables": tables, "penalties": penalty_tables(html),
                         "juniors": junior_tables(html),
                         "source": f"https://awards.fairwork.gov.au/{code}.html", "fetched": date.today().isoformat()}
                ok += 1
        if entry is None and code in old:
            entry = old[code]
        if entry:
            result.append(entry)
    out_path.write_text(json.dumps({"awards": result}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"awards: parsed {ok} of {len(AWARDS)}, wrote {len(result)}")
    return {"awards": result}


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def clean_name(n: str) -> str:
    return re.sub(r"(?<=[a-z])\d$", "", n.strip())  # drop footnote markers like "Educator1"


LEVEL_PREFIX = {"clerks": "Clerk", "restaurant": "Restaurant", "construction": "Construction",
                "health-professionals": "Health professional", "horticulture": "Horticulture"}


def level_label(a: dict, name: str) -> str:
    """Names like "Level 2" or "C10 / V5" need the award in front; "Security Officer Level 4" does not."""
    n = clean_name(name)
    if re.match(r"(level|introductory|grade|[a-z]\d)", n, re.I):
        return f"{LEVEL_PREFIX.get(a['slug'], a['short'])} {n[0].lower() + n[1:] if n.startswith('Introductory') else n}"
    return n


TODAY = date.today().isoformat()


def nice_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def junior_rate(weekly: float, pct: float) -> float:
    """Fair Work works junior rates out from the adult weekly rate, then divides by 38."""
    return round(round(weekly * pct / 100, 2) / 38, 2)


def junior_note(info: dict) -> str:
    bits = []
    if info["starts"]:
        bits.append(f"from {nice_date(info['starts'])}")
    if info["next"]:
        bits.append(f"{info['next_pct']:g}% from {nice_date(info['next'])}")
    return f'<br><small class="muted">{"; ".join(bits)}</small>' if bits else ""


def junior_table_html(a: dict, jt: dict, row: dict | None, label: str, today: str = "") -> str:
    """One junior table. With a classification row, show dollar rates for it; otherwise only the percentages."""
    today = today or TODAY
    trs = []
    for jr in jt["rows"]:
        info = junior_pct(jt, jr, today)
        pct = info["pct"]
        cells = f"<td>{pct:g}%{junior_note(info)}</td>"
        if row:
            h = junior_rate(row["weekly"], pct)
            cells += f"<td>${h:.2f}</td><td>${h * 1.25:.2f}</td><td>${h * 38:,.2f}</td>"
        trs.append(f"<tr><td>{esc(jr['age'])}</td>{cells}</tr>")
    heads = "<th>Age</th><th>% of adult rate</th>" + ("<th>Hourly</th><th>Casual hourly</th><th>Weekly (38 hrs)</th>" if row else "")
    cap = jt["caption"] if jt["caption"] and "junior" in jt["caption"].lower() else "Junior rates"
    base = f' <span class="muted small">({esc(jt["base"])})</span>' if jt.get("base") and not jt["per_level"] else ""
    for_ = f" for {esc(label)}" if row else ""
    return (f'<h3>{esc(cap)}{for_}{base}</h3><div class="tablewrap"><table class="result award junior"><thead><tr>{heads}</tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div>')


def junior_section(a: dict, row: dict | None, label: str, up: str, level_page: bool = False) -> str:
    js = a.get("juniors") or []
    if not js:
        return ""
    parts = []
    for i, jt in enumerate(js):
        use_row = row if (jt["per_level"] and (i == 0 or not level_page)) else None
        if level_page and not use_row:
            continue
        parts.append(junior_table_html(a, jt, use_row, label))
    if not parts:
        return ""
    who = esc(label) if level_page else f"the first level in the table ({esc(label)})"
    return (f'<section id="junior"><h2>Junior pay rates (under 21)</h2>'
            f'<p>Under the {esc(a["name"])} workers under 21 can be paid a percentage of the adult rate. Dollar amounts below are for {who}; '
            f'other levels get the same percentage of their own adult rate. Some awards set different junior rules for particular jobs, so check the award.</p>'
            f'{"".join(parts)}<p class="small muted">Worked out from the adult weekly rate times the junior percentage, divided by 38, as in the award pay guides. '
            f'Casual rates add the 25% casual loading. Source: <a href="{esc(a["source"])}">{esc(a["name"])}</a>, junior rates clause (checked {esc(a["fetched"])}).</p></section>')


def level_rows(a: dict) -> list[tuple[dict, str, str]]:
    """(row, label, path) for each classification that gets its own page: first table, unique short names."""
    if a["slug"] in LEVEL_SKIP or not a["tables"]:
        return []
    rows = a["tables"][0]["rows"]
    names = [r["name"] for r in rows]
    out, seen = [], set()
    for r in rows:
        if names.count(r["name"]) > 1 or len(r["name"]) > 60:
            continue
        label = level_label(a, r["name"])
        path = f"pay-rates/{a['slug']}/{slugify(clean_name(r['name']))}.html"
        if path in seen:
            continue
        seen.add(path)
        out.append((r, label, path))
    return out


def m0(v: float) -> str:
    return f"${v:,.0f}"


def level_page(a: dict, row: dict, label: str, path: str, siblings, page, ad_slot, cross_sell) -> str:
    up = "../../"
    h, wk = row["hourly"], row["weekly"]
    yearly = wk * 52
    scen = [("Full time 38h", h, 38), ("Casual 38h", h * 1.25, 38), ("Part time 25h", h, 25), ("Casual 15h", h * 1.25, 15)]
    trs = []
    for name, rate, hrs in scen:
        gross_w = rate * hrs
        cells = "".join(f"<td>{m0(calculate(gross_w * 52, k)['net'] / 52)}</td>" for k in KINDS)
        trs.append(f"<tr><th>{name}</th><td class='gross'>{m0(gross_w)}</td>{cells}</tr>")
    heads = "<th>Resident</th><th>Backpacker</th><th>Foreign</th>"
    table = (f'<div class="tablewrap"><table class="result compact"><thead><tr><th>Week</th><th class="gross">Gross</th>{heads}</tr></thead>'
             f'<tbody>{"".join(trs)}</tbody></table></div>')
    r_ft = calculate(yearly, "resident")
    sib = "".join(f'<li><a href="{up}{p}">{esc(lab)}: ${r["hourly"]:.2f}</a></li>' for r, lab, p in siblings if p != path)
    body = f"""<p class="crumbs"><a href="{up}index.html">Calculator</a> › <a href="{up}pay-rates/index.html">Pay rates</a> › <a href="{up}pay-rates/{a["slug"]}.html">{esc(a["short"])}</a> › {esc(clean_name(row["name"]))}</p>
<h1>{esc(label)} pay rate 2026-27</h1>
<p class="lead">The minimum pay for a {esc(label)} under the {esc(a["name"])} is <strong>${h:.2f} an hour</strong> (${wk:,.2f} for a 38-hour week, about {m0(yearly)} a year). Casuals get at least ${h * 1.25:.2f} an hour with the 25% casual loading. Full time, an Australian resident takes home about <strong>{m0(r_ft["net"] / 52)} a week</strong>.</p>
{detail_html(row) and f'<p class="small muted">{esc(row["detail"])}</p>'}
<div class="stats">
  <div><span>Hourly</span><strong>${h:.2f}</strong></div>
  <div><span>Casual hourly</span><strong>${h * 1.25:.2f}</strong></div>
  <div><span>Weekly (38 hrs)</span><strong>${wk:,.0f}</strong></div>
  <div><span>Yearly</span><strong>{m0(yearly)}</strong></div>
</div>
{ad_slot()}
<section><h2>Take-home pay each week by visa</h2>
<p>Working holiday makers (417/462) and foreign residents have no tax-free threshold and pay no Medicare levy. International students in Australia for more than six months are usually taxed as residents.</p>
{table}
<p class="small muted">Casual rows include the 25% casual loading. Backpacker means working holiday maker (417/462). Weekly take-home after income tax and the Medicare levy, worked out on a full year at the same hours. Super of 12% is paid on top. Weekend, night, public holiday and overtime rates are extra: see the <a href="{up}tools/penalty-rates.html">penalty rates calculator</a>.</p></section>
{junior_section(a, row, label, up, level_page=True)}
<section><h2>Other {esc(a["short"])} levels</h2><ul class="list">{sib}</ul>
<p><a href="{up}pay-rates/{a["slug"]}.html">All {esc(a["short"])} award rates, penalty rates and overtime</a></p></section>
<section><h2>Check your pay</h2><ul class="list">
<li>Your exact take-home: <a href="{up}index.html">tax calculator for every visa</a></li>
<li>Not sure of your level? The classification definitions are in the award itself: <a href="{esc(a["source"])}">read the {esc(a["short"])} award</a>.</li>
<li>Think you're underpaid? The <a href="https://www.fairwork.gov.au/contact-us">Fair Work Ombudsman</a> (13 13 94) helps for free, including visa holders.</li></ul>
<p class="small muted">Sources: adult minimum rate from the <a href="{esc(a["source"])}">{esc(a["name"])}</a> on the Fair Work Commission award viewer (checked {esc(a["fetched"])}); tax from <a href="https://www.ato.gov.au/tax-rates-and-codes">ATO tax rates</a>. Apprentice and allowance rates differ. General information only.</p></section>
{cross_sell(up)}"""
    title_ = f"{label} pay rate 2026-27: ${h:.2f} an hour, {m0(r_ft['net'] / 52)} a week take-home"
    desc = (f"{label} minimum pay from 1 July 2026: ${h:.2f}/hour, ${h * 1.25:.2f} casual, ${wk:,.2f} a week. "
            f"Take-home pay for residents, backpackers and foreign residents.")
    return page(path, title_, desc, body, up)


def detail_html(r: dict) -> str:
    return f'<br><small class="muted">{esc(r["detail"])}</small>' if r.get("detail") else ""


def name_cell(r: dict, links: dict, up: str) -> str:
    p = links.get(id(r))
    return f'<a href="{up}{p}">{esc(r["name"])}</a>' if p else esc(r["name"])


def salary_link(up: str, weekly: float) -> str:
    yearly = int(round(weekly * 52 / 1000.0)) * 1000
    yearly = min(max(yearly, 20000), 300000)
    return f'<a href="{up}salary/{yearly}.html">${yearly // 1000}k salary after tax</a>'


def award_page(a: dict, page, ad_slot, cross_sell) -> tuple[str, str]:
    up = "../"
    parts = []
    links = {id(r): p for r, _, p in level_rows(a)}
    for i, t in enumerate(a["tables"]):
        cap = t["caption"] or ("Minimum rates" if i == 0 else "More classifications")
        rows = "".join(
            f'<tr><td>{name_cell(r, links, up)}{detail_html(r)}</td>'
            f'<td>${r["hourly"]:.2f}</td><td>${r["hourly"] * 1.25:.2f}</td><td>${r["weekly"]:,.2f}</td><td>{salary_link(up, r["weekly"])}</td></tr>'
            for r in t["rows"])
        parts.append(f'<h3>{esc(cap)}</h3><div class="tablewrap"><table class="result award"><thead><tr><th>Classification</th><th>Hourly</th><th>Casual hourly</th><th>Weekly (38 hrs)</th><th>Take-home</th></tr></thead><tbody>{rows}</tbody></table></div>')
    pens = ""
    for t in a.get("penalties", []):
        head = "".join(f"<th>{esc(re.sub(r'^Column \d+\s*', '', c))}</th>" for c in t[0])
        body = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in t[1:])
        pens += f'<div class="tablewrap"><table class="result award raw"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    pen_section = f'<section><h2>Penalty and overtime rates (from the award)</h2>{pens}<p>Use these percentages in the <a href="{up}tools/penalty-rates.html">penalty rates calculator</a>.</p></section>' if pens else ""
    first = a["tables"][0]["rows"][0]
    body = f"""<p class="crumbs"><a href="{up}index.html">Calculator</a> › <a href="{up}pay-rates/index.html">Pay rates</a> › {esc(a["short"])}</p>
<h1>{esc(a["short"])} award pay rates 2026-27</h1>
<p class="lead">{esc(a["blurb"])} Under the {esc(a["name"])} the lowest adult rate is <strong>${a["min_hourly"]:.2f} an hour</strong> (${a["min_hourly"] * 1.25:.2f} for casuals, including the 25% casual loading).</p>
<p class="small muted">Rates copied automatically from the official award on the Fair Work website (checked {esc(a["fetched"])}). {"Junior rates are below; apprentice" if a.get("juniors") else "Junior, apprentice"} and allowance rates are in the award itself. <a href="{esc(a["source"])}">Read the full award</a>.</p>
{ad_slot()}
<section><h2>Minimum pay by classification</h2>{"".join(parts)}</section>
{junior_section(a, first, level_label(a, first["name"]), up)}
{pen_section}
<section><h2>Check your pay</h2><ul class="list">
<li>Find your take-home pay: <a href="{up}index.html">tax calculator for every visa</a></li>
<li>Weekend, night and public holiday pay: <a href="{up}tools/penalty-rates.html">penalty rates calculator</a></li>
<li>Casual or permanent? <a href="{up}tools/casual-vs-permanent.html">Compare</a></li>
<li>Think you're underpaid? Talk to the <a href="https://www.fairwork.gov.au/contact-us">Fair Work Ombudsman</a> on 13 13 94. It's free and available to visa holders.</li></ul></section>
{cross_sell(up)}"""
    title_ = f"{a['short']} award pay rates 2026-27: from ${a['min_hourly']:.2f} an hour"
    desc = f"Minimum pay rates under the {a['name']} from 1 July 2026: hourly, casual and weekly rates for every level, penalty rates and take-home pay."
    return f"pay-rates/{a['slug']}.html", page(f"pay-rates/{a['slug']}.html", title_, desc, body, up)


def award_pages(page, ad_slot, cross_sell) -> dict[str, str]:
    p = HERE / "awards.json"
    if not p.exists():
        return {}
    out = {}
    for a in json.loads(p.read_text(encoding="utf-8"))["awards"]:
        path, html = award_page(a, page, ad_slot, cross_sell)
        out[path] = html
        levels = level_rows(a)
        for row, label, lp in levels:
            out[lp] = level_page(a, row, label, lp, levels, page, ad_slot, cross_sell)
    return out


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "parse":
        parse(Path(sys.argv[2]))
    else:
        print(__doc__)
