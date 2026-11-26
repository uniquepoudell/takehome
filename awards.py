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
from awardparse import penalty_tables, rate_tables, title  # noqa: E402

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
                         "source": f"https://awards.fairwork.gov.au/{code}.html", "fetched": date.today().isoformat()}
                ok += 1
        if entry is None and code in old:
            entry = old[code]
        if entry:
            result.append(entry)
    out_path.write_text(json.dumps({"awards": result}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"awards: parsed {ok} of {len(AWARDS)}, wrote {len(result)}")
    return {"awards": result}


def detail_html(r: dict) -> str:
    return f'<br><small class="muted">{esc(r["detail"])}</small>' if r.get("detail") else ""


def salary_link(up: str, weekly: float) -> str:
    yearly = int(round(weekly * 52 / 1000.0)) * 1000
    yearly = min(max(yearly, 20000), 300000)
    return f'<a href="{up}salary/{yearly}.html">${yearly // 1000}k salary after tax</a>'


def award_page(a: dict, page, ad_slot, cross_sell) -> tuple[str, str]:
    up = "../"
    parts = []
    for i, t in enumerate(a["tables"]):
        cap = t["caption"] or ("Minimum rates" if i == 0 else "More classifications")
        rows = "".join(
            f'<tr><td>{esc(r["name"])}{detail_html(r)}</td>'
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
<p class="small muted">Rates copied automatically from the official award on the Fair Work website (checked {esc(a["fetched"])}). Junior, apprentice and allowance rates are in the award itself. <a href="{esc(a["source"])}">Read the full award</a>.</p>
{ad_slot()}
<section><h2>Minimum pay by classification</h2>{"".join(parts)}</section>
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
    return out


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "parse":
        parse(Path(sys.argv[2]))
    else:
        print(__doc__)
