#!/usr/bin/env python3
"""Build the TakeHome pay calculator site (static, Python stdlib only).

python build.py --out public

Writes a calculator home page, one page per salary and hourly rate (for search),
visa tax guides, a sitemap and copies static/. SITE_BASE_URL (env) is the URL the
output folder is served from, used for canonical links and the sitemap.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tax import KINDS, RATES, calculate  # noqa: E402
import tools  # noqa: E402
import awards  # noqa: E402

CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
esc = html.escape


def money(v: float) -> str:
    return f"${v:,.0f}"


def pct(v: float) -> str:
    return f"{v * 100:.1f}%".replace(".0%", "%")


def base_url() -> str:
    b = os.environ.get("SITE_BASE_URL", "").strip()
    return (b.rstrip("/") + "/") if b else ""


def ad_slot() -> str:
    m = CFG["monetization"]
    if not (m["adsense_client"] and m["adsense_slot"]):
        return ""
    return (f'<div class="ad"><ins class="adsbygoogle" style="display:block" data-ad-client="{esc(m["adsense_client"])}" '
            f'data-ad-slot="{esc(m["adsense_slot"])}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
            '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></div>')


def cross_sell(up: str) -> str:
    cards = []
    aff = CFG["monetization"]["tax_return_affiliate"]
    if aff["url"]:
        cards.append({"title": "Get your tax refund", "text": aff["label"], "url": aff["url"], "cta": "Start your return", "sponsored": True})
    for prod in products_on_sale():
        cards.append({"title": f'{prod["title"]} (A${prod["price_aud"]:g})', "text": prod["card_text"],
                      "url": f'shop/{prod["slug"]}.html', "cta": "See what's inside"})
    cards += CFG["cross_sell"]
    out = []
    for c in cards:
        url = c["url"] if c["url"].startswith("http") else up + c["url"]
        rel = ' rel="sponsored noopener"' if c.get("sponsored") else (' rel="noopener"' if url.startswith("http") else "")
        out.append(f'<a class="card" href="{esc(url)}"{rel}><strong>{esc(c["title"])}</strong>'
                   f'<span>{esc(c["text"])}</span><em>{esc(c["cta"])} →</em></a>')
    return '<section><h2>Helpful next steps</h2><div class="cards">' + "".join(out) + "</div></section>"


def page(path: str, title: str, desc: str, body: str, up: str, jsonld: dict | None = None, noindex: bool = False) -> str:
    canon = base_url() + path if base_url() else ""
    m = CFG["monetization"]
    ads_js = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={esc(m["adsense_client"])}" crossorigin="anonymous"></script>'
              if m["adsense_client"] else "")
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    canon_tag = f'<link rel="canonical" href="{esc(canon)}"><meta property="og:url" content="{esc(canon)}">' if canon else ""
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
{canon_tag}
{'<meta name="robots" content="noindex">' if noindex else ""}
<link rel="icon" href="{up}static/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{up}static/style.css">
{ads_js}{ld}
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="{up}index.html"><img src="{up}static/icon.svg" alt="" width="30" height="30">{esc(CFG["name"])}</a>
  <nav><a href="{up}index.html">Tax calculator</a><a href="{up}pay-rates/index.html">Pay rates</a><a href="{up}tools/index.html">Work tools</a><a href="{up}salaries.html">Salaries</a><a href="{up}guides/index.html">Visa guides</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap small muted">
  <p>Estimates for the {RATES["year"]} income year ({RATES["year_long"]}) using ATO rates checked {RATES["checked"]}. This is general information, not tax advice: your payslip withholding and final tax return can differ. <a href="{up}how-it-works.html">How we calculate</a> · <a href="{up}about.html">About and privacy</a></p>
  <p>Sister site: <a href="{esc(CFG["gorkhapay_url"])}">GorkhaPay</a>, compare money transfers to Nepal. Updated {date.today().isoformat()}.</p>
</footer>
<script>window.RATES={json.dumps({k: v for k, v in RATES.items() if not k.startswith("_") and k != "sources"})};</script>
<script>window.WORK={json.dumps({k: v for k, v in tools.WORK.items() if not k.startswith("_")})};</script>
<script src="{up}static/calc.js"></script>
<script src="{up}static/tools.js"></script>
</body>
</html>
"""


def calc_form(amount: str = "70000", period: str = "year", kind: str = "resident", fixed: bool = False) -> str:
    def opt(v, label):
        return f'<option value="{v}"{" selected" if v == period else ""}>{label}</option>'

    def radio(v, label):
        return (f'<label class="pill"><input type="radio" name="kind" value="{v}"{" checked" if v == kind else ""}>'
                f'<span>{label}</span></label>')
    return f"""<form id="calc" class="calc"{' data-fixed="1"' if fixed else ''}>
  <div class="row">
    <label class="field"><span>Your pay</span><input id="amount" inputmode="decimal" value="{esc(amount)}" aria-label="Pay amount in dollars"></label>
    <label class="field"><span>per</span><select id="period">{opt("year","year")}{opt("month","month")}{opt("fortnight","fortnight")}{opt("week","week")}{opt("hour","hour")}</select></label>
    <label class="field" id="hours-wrap" hidden><span>hours a week</span><input id="hours" inputmode="decimal" value="38"></label>
  </div>
  <fieldset><legend>Your tax status</legend>
    {radio("resident","Resident (incl. most students)")}{radio("whm","Working holiday (417/462)")}{radio("foreign","Foreign resident")}
  </fieldset>
  <div class="row checks">
    <label><input type="checkbox" id="help"> I have a HELP / student loan</label>
    <label><input type="checkbox" id="incsuper"> My pay includes super</label>
  </div>
  <div class="headline"><strong id="headline">…</strong><span id="headline-sub"></span></div>
  <div class="tablewrap"><table id="result" class="result"></table></div>
  <noscript><p>Turn on JavaScript for the live calculator, or pick a salary from the salary list.</p></noscript>
</form>"""


def compare_table(income: float) -> str:
    rows = []
    for kind, label in KINDS.items():
        r = calculate(income, kind)
        rows.append(f"<tr><th>{label}</th><td>{money(r['total_tax'])}</td><td>{money(r['net'])}</td>"
                    f"<td>{money(r['net'] / 26)}</td><td>{money(r['net'] / 52)}</td><td>{pct(r['avg_rate'])}</td></tr>")
    return ('<div class="tablewrap"><table class="result"><thead><tr><th>Tax status</th><th>Tax + levy</th><th>Take-home / year</th>'
            '<th>/ fortnight</th><th>/ week</th><th>Average rate</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def salary_list(values, up: str, prefix="salary/") -> str:
    return '<ul class="chips">' + "".join(f'<li><a href="{up}{prefix}{v}.html">{money(v)}</a></li>' for v in values) + "</ul>"


def faq_ld(qas) -> dict:
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qas]}


def salary_page(v: int) -> tuple[str, str]:
    up = "../"
    r = calculate(v, "resident")
    w = calculate(v, "whm")
    f = calculate(v, "foreign")
    rh = calculate(v, "resident", True)
    title = f"{money(v)} after tax in Australia ({RATES['year']}): {money(r['net'])} take-home"
    desc = (f"On a {money(v)} salary in Australia you take home {money(r['net'])} a year, {money(r['net'] / 26)} a fortnight "
            f"or {money(r['net'] / 52)} a week as a resident in {RATES['year']}. Backpacker and foreign resident figures too.")
    s = CFG["salary_pages"]
    near = [x for x in range(v - 5 * s["step"], v + 6 * s["step"], s["step"]) if s["from"] <= x <= s["to"] and x != v]
    qas = [
        (f"How much is {money(v)} after tax in Australia?",
         f"As an Australian resident in {RATES['year']}, {money(v)} is about {money(r['net'])} after income tax and the Medicare levy: "
         f"{money(r['net'] / 12)} a month, {money(r['net'] / 26)} a fortnight or {money(r['net'] / 52)} a week."),
        (f"How much tax does a backpacker pay on {money(v)}?",
         f"A working holiday maker pays about {money(w['total_tax'])} tax on {money(v)}, taking home {money(w['net'])}."),
        (f"What is the super on a {money(v)} salary?",
         f"Your employer pays {pct(RATES['super_rate'])} super on top: about {money(r['super'])} a year."),
    ]
    body = f"""
<p class="crumbs"><a href="{up}index.html">Calculator</a> › <a href="{up}salaries.html">Salaries</a> › {money(v)}</p>
<h1>{money(v)} after tax in Australia</h1>
<p class="lead">On {money(v)} a year, an Australian resident takes home <strong>{money(r['net'])}</strong> in {RATES['year']}. That is {money(r['net'] / 12)} a month, {money(r['net'] / 26)} a fortnight or {money(r['net'] / 52)} a week. Your marginal rate is {pct(r['marginal'])} plus the 2% Medicare levy.</p>
<div class="stats">
  <div><span>Take-home / year</span><strong>{money(r['net'])}</strong></div>
  <div><span>Income tax</span><strong>{money(r['income_tax'])}</strong></div>
  <div><span>Medicare levy</span><strong>{money(r['medicare'])}</strong></div>
  <div><span>Super on top</span><strong>{money(r['super'])}</strong></div>
</div>
{ad_slot()}
<section><h2>By visa and tax status</h2>
<p>Working holiday makers and foreign residents get no tax-free threshold and pay no Medicare levy, so the same salary gives a different take-home.</p>
{compare_table(v)}
<p class="small muted">With a HELP or other student loan, a resident on {money(v)} repays {money(rh['help'])} a year, leaving {money(rh['net'])}.</p>
</section>
<section><h2>Try your exact numbers</h2>{calc_form(str(v), fixed=True)}</section>
<section><h2>Common questions</h2>{"".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in qas)}</section>
<section><h2>Nearby salaries</h2>{salary_list(near, up)}</section>
{cross_sell(up)}
"""
    return f"salary/{v}.html", page(f"salary/{v}.html", title, desc, body, up, faq_ld(qas))


def hourly_page(rate: int) -> tuple[str, str]:
    up = "../"
    hrs = CFG["hourly_pages"]["hours"]
    yearly = rate * hrs * 52
    r = calculate(yearly, "resident")
    w = calculate(yearly, "whm")
    title = f"${rate} an hour after tax in Australia: {money(r['net'] / 52)} a week take-home ({RATES['year']})"
    desc = (f"${rate}/hour full time ({hrs} hours) is {money(yearly)} a year. A resident takes home {money(r['net'] / 52)} a week; "
            f"a backpacker takes home {money(w['net'] / 52)}.")
    body = f"""
<p class="crumbs"><a href="{up}index.html">Calculator</a> › <a href="{up}salaries.html">Hourly rates</a> › ${rate}/hour</p>
<h1>${rate} an hour after tax</h1>
<p class="lead">At ${rate} an hour for {hrs} hours a week you earn {money(yearly)} a year. As a resident you take home about <strong>{money(r['net'] / 52)} a week</strong> ({money(r['net'])} a year). On a working holiday visa it is about {money(w['net'] / 52)} a week.</p>
{ad_slot()}
<section><h2>By visa and tax status</h2>{compare_table(yearly)}
<p class="small muted">Casual or part time? Change the hours below. Casual rates usually include a 25% loading instead of paid leave.</p></section>
<section><h2>Change the hours</h2>{calc_form(str(rate), "hour", fixed=True)}</section>
{cross_sell(up)}
"""
    return f"hourly/{rate}.html", page(f"hourly/{rate}.html", title, desc, body, up)


GUIDES = {
    "backpacker-tax": ("Backpacker tax in Australia 2026-27: rates, refunds and super",
        "How much tax working holiday makers (417 and 462 visas) pay in Australia in 2026-27, why there is no tax-free threshold, and getting your super back when you leave.",
        """<h1>Backpacker tax in Australia ({year})</h1>
<p class="lead">If you are on a working holiday visa (subclass 417 or 462), you pay 15% tax from your first dollar up to $45,000. There is no tax-free threshold and no Medicare levy.</p>
<h2>Working holiday maker rates</h2>{whm_table}
<p>Your employer must be registered with the ATO as an employer of working holiday makers to withhold at these rates. If they are not, they must withhold at foreign resident rates (30%). Ask your employer, or check your payslip.</p>
<h2>What 15% means for your pay</h2>{examples}
<h2>Getting money back when you leave</h2>
<ul><li><strong>Tax return:</strong> lodge one each year (or before you leave) to make sure you paid the right amount.</li>
<li><strong>Super:</strong> your employer pays {super} super on top of your pay. When you leave Australia and your visa ends, you can claim it through the Departing Australia Superannuation Payment (DASP). For working holiday makers the ATO taxes DASP at 65%.</li></ul>
<p class="small muted">Sources: <a href="https://www.ato.gov.au/tax-rates-and-codes/tax-rates-working-holiday-makers">ATO working holiday maker rates</a>.</p>"""),
    "student-visa-tax": ("International student tax in Australia 2026-27: are you a resident?",
        "How international students on a 500 visa are taxed in Australia, the tax-free threshold, work hour limits and how much you take home from part-time work.",
        """<h1>Tax for international students ({year})</h1>
<p class="lead">If you are studying in Australia for more than six months, the ATO usually treats you as an Australian resident for tax. That means the $18,200 tax-free threshold applies and you pay resident rates.</p>
<h2>Resident tax rates</h2>{res_table}
<p>Because of the low income tax offset, a resident can earn about $22,866 in {year} before paying any income tax.</p>
<h2>What part-time work pays</h2>{student_examples}
<h2>Things to check</h2>
<ul><li>Give your employer your Tax File Number (TFN) and tick the tax-free threshold on one job only. Without a TFN they must withhold 47%.</li>
<li>Student visa holders can usually work 48 hours a fortnight during study periods. Check your own visa conditions with Home Affairs.</li>
<li>Your employer pays {super} super on top. You can claim it back through DASP when you leave Australia.</li></ul>
<p class="small muted">Residency depends on your circumstances. Use the ATO residency tool if unsure: <a href="https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/your-tax-residency">ATO: your tax residency</a>.</p>"""),
    "foreign-resident-tax": ("Foreign resident tax rates Australia 2026-27",
        "Tax rates for foreign residents working in Australia in 2026-27: 30% from the first dollar, no tax-free threshold and no Medicare levy.",
        """<h1>Foreign resident tax rates ({year})</h1>
<p class="lead">Foreign residents pay 30% from the first dollar earned in Australia, with no tax-free threshold and no Medicare levy.</p>
{for_table}
<h2>Examples</h2>{for_examples}
<p class="small muted">Not sure if you are a foreign resident? See <a href="https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/your-tax-residency">ATO: your tax residency</a>.</p>"""),
}


def rate_table(kind: str) -> str:
    rows, lower = [], 0
    for upper, rate in RATES[kind]:
        band = f"{money(lower + (1 if lower else 0))} – {money(upper)}" if upper else f"{money(lower + 1)} and over"
        rows.append(f"<tr><td>{band}</td><td>{pct(rate)}</td></tr>")
        lower = upper or lower
    return '<div class="tablewrap"><table class="result"><thead><tr><th>Taxable income</th><th>Rate</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"


def examples(kind: str, values, up: str) -> str:
    rows = []
    for v in values:
        r = calculate(v, kind)
        rows.append(f'<tr><td><a href="{up}salary/{v}.html">{money(v)}</a></td><td>{money(r["total_tax"])}</td><td>{money(r["net"])}</td><td>{money(r["net"] / 52)}</td></tr>')
    return ('<div class="tablewrap"><table class="result"><thead><tr><th>Earned</th><th>Tax</th><th>Take-home</th><th>/ week</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def guide_page(slug: str) -> tuple[str, str]:
    up = "../"
    title, desc, tpl = GUIDES[slug]
    student = []
    for hrs in (20, 24):
        for rate in (26, 30):
            yearly = rate * hrs * 52
            r = calculate(yearly, "resident")
            student.append(f"<tr><td>${rate}/hr × {hrs} hrs/week</td><td>{money(yearly)}</td><td>{money(r['net'] / 52)}</td></tr>")
    student_tbl = ('<div class="tablewrap"><table class="result"><thead><tr><th>Work</th><th>Year</th><th>Take-home / week</th></tr></thead><tbody>'
                   + "".join(student) + "</tbody></table></div>")
    content = tpl.format(year=RATES["year"], super=pct(RATES["super_rate"]),
                         whm_table=rate_table("whm"), res_table=rate_table("resident"), for_table=rate_table("foreign"),
                         examples=examples("whm", [20000, 30000, 40000, 50000, 60000], up),
                         for_examples=examples("foreign", [40000, 60000, 80000, 100000, 150000], up),
                         student_examples=student_tbl)
    body = f'<p class="crumbs"><a href="{up}index.html">Calculator</a> › Guides</p><article class="prose">{content}</article>{ad_slot()}<section><h2>Work out your own pay</h2>{calc_form(kind={"backpacker-tax":"whm","foreign-resident-tax":"foreign"}.get(slug,"resident"))}</section>{cross_sell(up)}'
    return f"guides/{slug}.html", page(f"guides/{slug}.html", title, desc, body, up)


def guides_index() -> str:
    up = "../"
    cards = "".join(f'<a class="card" href="{slug}.html"><strong>{esc(t.split(":")[0])}</strong><span>{esc(d)}</span><em>Read →</em></a>' for slug, (t, d, _) in GUIDES.items())
    return page("guides/index.html", "Tax guides for visa holders in Australia", "Plain-English tax guides for backpackers, international students and foreign residents working in Australia.",
                f'<h1>Tax guides by visa</h1><p class="lead">Plain-English guides for people working in Australia on a visa.</p><div class="cards">{cards}</div>{cross_sell(up)}', up)


def index_page() -> str:
    up = ""
    popular = [40000, 50000, 60000, 65000, 70000, 75000, 80000, 85000, 90000, 100000, 110000, 120000, 130000, 150000, 200000]
    qas = [
        ("How much tax do I pay in Australia in 2026-27?",
         "Residents pay nothing on the first $18,200, then 15% to $45,000, 30% to $135,000, 37% to $190,000 and 45% above, plus a 2% Medicare levy."),
        ("Do backpackers pay more tax?",
         "Working holiday makers pay 15% from the first dollar up to $45,000, with no tax-free threshold, but no Medicare levy."),
        ("Is super included in my salary?",
         f"Usually not. Employers pay {pct(RATES['super_rate'])} super on top of your salary. If your offer says 'package' or 'including super', tick 'My pay includes super'."),
    ]
    body = f"""
<section class="hero">
  <h1>What will you actually take home?</h1>
  <p class="lead">Free Australian pay calculator for {RATES["year"]}. Works for residents, working holiday makers, international students and foreign residents. Nothing you type leaves your device.</p>
  {calc_form()}
</section>
{ad_slot()}
<section><h2>Popular salaries</h2>{salary_list(popular, up)}<p><a href="salaries.html">All salaries and hourly rates →</a></p></section>
<section><h2>Work and pay tools</h2><div class="cards">
  <a class="card" href="pay-rates/index.html"><strong>Minimum wage and award rates</strong><span>${tools.MW["hourly"]:.2f} an hour from {tools.MW["from"]}, plus your award's rates.</span><em>Check your pay →</em></a>
  <a class="card" href="tools/penalty-rates.html"><strong>Penalty rates and overtime</strong><span>Weekend, public holiday and overtime pay for a shift.</span><em>Calculate →</em></a>
  <a class="card" href="tools/salary-packaging.html"><strong>Salary packaging</strong><span>Nurses, paramedics and charity workers: see your extra take-home.</span><em>Calculate →</em></a>
  <a class="card" href="tools/casual-vs-permanent.html"><strong>Casual vs permanent</strong><span>Is the 25% loading worth giving up paid leave?</span><em>Compare →</em></a>
  <a class="card" href="tools/notice-redundancy.html"><strong>Notice and redundancy pay</strong><span>Your minimum payout by years of service.</span><em>Calculate →</em></a>
  <a class="card" href="tools/leave.html"><strong>Annual and sick leave</strong><span>How much leave you've built up, and leave loading.</span><em>Calculate →</em></a>
</div></section>
<section><h2>Guides by visa</h2><div class="cards">
  <a class="card" href="guides/backpacker-tax.html"><strong>Backpacker tax</strong><span>417 and 462 visas: 15% from the first dollar.</span><em>Read →</em></a>
  <a class="card" href="guides/student-visa-tax.html"><strong>International students</strong><span>Usually a resident for tax: the $18,200 tax-free threshold applies.</span><em>Read →</em></a>
  <a class="card" href="guides/foreign-resident-tax.html"><strong>Foreign residents</strong><span>30% from the first dollar, no Medicare levy.</span><em>Read →</em></a>
</div></section>
<section><h2>Common questions</h2>{"".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in qas)}</section>
{cross_sell(up)}
"""
    ld = faq_ld(qas)
    return page("index.html", f"Take-home pay calculator Australia {RATES['year']}: every visa | {CFG['name']}", CFG["description"], body, up, ld)


def salaries_page() -> str:
    s, h = CFG["salary_pages"], CFG["hourly_pages"]
    sal = list(range(s["from"], s["to"] + 1, s["step"]))
    hrs = list(range(h["from"], h["to"] + 1, h["step"]))
    hourly = '<ul class="chips">' + "".join(f'<li><a href="hourly/{r}.html">${r}/hr</a></li>' for r in hrs) + "</ul>"
    body = f"""<h1>Salaries and hourly rates after tax</h1>
<p class="lead">Pick your pay to see take-home for residents, backpackers and foreign residents in {RATES["year"]}.</p>
<section><h2>Hourly rates (full time, {h["hours"]} hours)</h2>{hourly}</section>
<section><h2>Yearly salaries</h2>{salary_list(sal, "")}</section>"""
    return page("salaries.html", f"Salary after tax Australia {RATES['year']}: every salary from $20k to $300k", "Take-home pay for every salary from $20,000 to $300,000 and every hourly rate from $20 to $100, for residents, backpackers and foreign residents.", body, "")


def how_page() -> str:
    src = "".join(f'<li><a href="{esc(u)}">{esc(t)}</a></li>' for t, u in RATES["sources"])
    body = f"""<article class="prose"><h1>How we calculate</h1>
<p>All figures are for the {RATES["year"]} income year and were checked against the ATO on {RATES["checked"]}.</p>
<h2>Residents</h2>{rate_table("resident")}
<p>Low income tax offset: up to ${RATES["lito"]["max"]} for incomes to ${RATES["lito"]["full_to"]:,}, reducing to nil at ${RATES["lito"]["zero_at"]:,}. Medicare levy: 2%, reduced for single people with taxable income under ${RATES["medicare"]["high"]:,} (we use the latest published single thresholds).</p>
<h2>Working holiday makers</h2>{rate_table("whm")}
<h2>Foreign residents</h2>{rate_table("foreign")}
<h2>HELP and student loans</h2><p>From 2025-26 repayments are marginal: nothing up to ${RATES["help"]["threshold"]:,}, then 15c per dollar above that, 17c above ${RATES["help"]["band2"]:,}, and 10% of total income from ${RATES["help"]["top"]:,}. We use taxable income as repayment income.</p>
<h2>Super</h2><p>Employers pay {pct(RATES["super_rate"])} super guarantee on top of ordinary pay.</p>
<h2>What we leave out</h2><p>Deductions, other offsets, family and spouse rules, the Medicare levy surcharge, and other income. Your actual payslip uses ATO withholding tables, which round differently.</p>
<h2>Sources</h2><ul>{src}</ul></article>"""
    return page("how-it-works.html", f"How the {CFG['name']} pay calculator works", "Tax rates, offsets and sources behind the calculator.", body, "")


def on_sale(prod: dict) -> bool:
    return bool(prod.get("price_aud")) and (prod.get("stripe_link") or "").strip().startswith("https://")


def products_on_sale() -> list[dict]:
    return [p for p in CFG.get("products", []) if on_sale(p)]


def product_page(prod: dict) -> tuple[str, str]:
    """Sales page for one of our own digital products. Hidden from search and menus until its Stripe link is set."""
    up = "../"
    path = f'shop/{prod["slug"]}.html'
    live = on_sale(prod)
    includes = "".join(f"<li>{esc(x)}</li>" for x in prod.get("includes", []))
    if live:
        buy = (f'<div class="buybox"><p class="big">A${prod["price_aud"]:g}</p><p class="small">One-off payment by card, Apple Pay or Google Pay '
               f'through Stripe. Your download link appears straight after payment, and Stripe emails you a receipt.</p>'
               f'<p><a class="btn" href="{esc(prod["stripe_link"].strip())}" rel="noopener">Buy now</a></p></div>')
    else:
        buy = '<div class="buybox"><p class="big">Coming soon</p><p class="small">This is not on sale yet.</p></div>'
    rows = "".join("<tr>" + "".join(f"<td>{esc(str(c))}</td>" for c in r) + "</tr>" for r in prod.get("preview_rows", []))
    preview = ""
    if rows:
        head = "".join(f"<th>{esc(h)}</th>" for h in prod.get("preview_head", []))
        preview = (f'<section><h2>What it looks like</h2><p class="small muted">{esc(prod.get("preview_note", ""))}</p>'
                   f'<div class="tablewrap"><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div></section>')
    jsonld = None
    if live:
        jsonld = {"@context": "https://schema.org", "@type": "Product", "name": prod["title"], "description": prod["summary"],
                  "brand": {"@type": "Brand", "name": CFG["name"]},
                  "offers": {"@type": "Offer", "price": f'{float(prod["price_aud"]):.2f}', "priceCurrency": "AUD",
                             "availability": "https://schema.org/InStock", "url": prod["stripe_link"].strip()}}
    body = f"""<p class="crumbs"><a href="{up}index.html">Calculator</a> › <a href="{up}tools/index.html">Work tools</a> › {esc(prod["title"])}</p>
<article class="prose">
<h1>{esc(prod["title"])}</h1>
<p class="lead">{esc(prod["summary"])}</p>
{buy}
<h2>What's inside</h2>
<ul>{includes}</ul>
<p><strong>Format:</strong> {esc(prod.get("format", ""))}</p>
<p><strong>Who it's for:</strong> {esc(prod.get("for_who", ""))}</p>
</article>
{preview}
<section class="prose"><h2>Please read before you buy</h2><p class="small">{esc(prod.get("notice", ""))} Because this is a digital download,
please ask us before you buy if you're unsure it suits you. Your rights under Australian Consumer Law still apply.</p>
<p class="small">Free first: work out a single shift with our <a href="{up}tools/penalty-rates.html">penalty rates calculator</a>, and find your award's rates under <a href="{up}pay-rates/index.html">Pay rates</a>.</p></section>"""
    return path, page(path, f'{prod["title"]} | {CFG["name"]}', prod["summary"], body, up, jsonld, noindex=not live)


def about_page() -> str:
    body = """<article class="prose"><h1>About and privacy</h1>
<p>TakeHome is a free, independent pay calculator for everyone working in Australia, built first for migrants, students and working holiday makers who are often left out of other calculators.</p>
<p><strong>Privacy:</strong> the calculator runs in your browser. Nothing you type is sent to us. If ads are shown, Google may use cookies to show them; see <a href="https://policies.google.com/technologies/ads">how Google uses cookies in advertising</a>.</p>
<p><strong>Links:</strong> some links may be affiliate links, marked as sponsored. They never change our numbers.</p>
<p><strong>Not advice:</strong> this is general information. For your situation, use the ATO's tools or a registered tax agent.</p></article>"""
    return page("about.html", "About TakeHome", "About this free Australian pay calculator and how your privacy is protected.", body, "")


ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0b6e4f"/><path d="M14 40h36v8H14z" fill="#ffd166"/><path d="M20 34l8-10 7 6 9-12" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>"""


def build(out: Path) -> int:
    if out.exists():
        shutil.rmtree(out)
    (out / "static").mkdir(parents=True)
    for f in (HERE / "static").iterdir():
        shutil.copy(f, out / "static" / f.name)
    (out / "static" / "icon.svg").write_text(ICON, encoding="utf-8")
    pages = {"index.html": index_page(), "salaries.html": salaries_page(), "how-it-works.html": how_page(), "about.html": about_page()}
    s, h = CFG["salary_pages"], CFG["hourly_pages"]
    for v in range(s["from"], s["to"] + 1, s["step"]):
        p, c = salary_page(v); pages[p] = c
    for r in range(h["from"], h["to"] + 1, h["step"]):
        p, c = hourly_page(r); pages[p] = c
    for slug in GUIDES:
        p, c = guide_page(slug); pages[p] = c
    pages["guides/index.html"] = guides_index()
    pages.update(tools.tool_pages(page, ad_slot, cross_sell, None))
    pages.update(awards.award_pages(page, ad_slot, cross_sell))
    hidden = set()
    for prod in CFG.get("products", []):
        p, c = product_page(prod); pages[p] = c
        if not on_sale(prod):
            hidden.add(p)
    for p, c in pages.items():
        (out / p).parent.mkdir(parents=True, exist_ok=True)
        (out / p).write_text(c, encoding="utf-8")
    domain = os.environ.get("CUSTOM_DOMAIN", "").strip()
    if domain:
        (out / "CNAME").write_text(domain + "\n", encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n" + (f"Sitemap: {base_url()}sitemap.xml\n" if base_url() else ""), encoding="utf-8")
    if base_url():
        urls = "".join(f"<url><loc>{esc(base_url() + p)}</loc></url>" for p in pages if p not in hidden)
        (out / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', encoding="utf-8")
    return len(pages)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="public")
    n = build(Path(ap.parse_args().out))
    print(f"paycheck: wrote {n} pages")
