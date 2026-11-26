"""Work tools and pay-rate pages: minimum wage, penalty rates, casual vs permanent,
leave, notice and redundancy, salary packaging, pay converter. Facts come from work.json."""
from __future__ import annotations

import json
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = json.loads((HERE / "work.json").read_text(encoding="utf-8"))
MW = WORK["minimum_wage"]


def money2(v: float) -> str:
    return f"${v:,.2f}"


def sources(items) -> str:
    return '<p class="small muted">Sources: ' + " · ".join(f'<a href="{esc(u)}">{esc(t)}</a>' for t, u in items) + "</p>"


def field(id_, label, value, suffix="", kind="number", step="any"):
    return (f'<label class="field"><span>{label}</span><input id="{id_}" type="{kind}" inputmode="decimal" step="{step}" value="{value}">'
            f'{f"<small>{suffix}</small>" if suffix else ""}</label>')


def tool_box(tool: str, inner: str) -> str:
    return f'<form class="calc tool" data-tool="{tool}" onsubmit="return false">{inner}<div class="tool-out" aria-live="polite"></div></form>'


TOOLS = [
    ("penalty-rates", "Penalty rates and overtime calculator", "Work out a shift's pay with weekend, public holiday, night and overtime rates, plus casual loading."),
    ("casual-vs-permanent", "Casual vs permanent: which pays more?", "Compare a casual rate with a permanent job once paid leave and public holidays are counted."),
    ("leave", "Annual leave and sick leave calculator", "How much annual leave and personal (sick) leave you build up, and what leave loading adds."),
    ("notice-redundancy", "Notice period and redundancy pay calculator", "Minimum notice and redundancy pay under the National Employment Standards, by years of service."),
    ("salary-packaging", "Salary packaging calculator (hospitals and charities)", "How much more you take home by salary packaging at a hospital, ambulance service or charity."),
    ("pay-converter", "Hourly, weekly, fortnightly and yearly pay converter", "Convert an hourly rate to weekly, fortnightly, monthly and yearly pay, and back."),
]


def tool_pages(page, ad_slot, cross_sell, calc_link_salary) -> dict[str, str]:
    up = "../"
    out = {}
    nmw = MW["hourly"]

    bodies = {
        "penalty-rates": f"""<h1>Penalty rates and overtime calculator</h1>
<p class="lead">Enter your base hourly rate from your award or agreement and the hours you worked at each rate. The multipliers below are common in awards (for example retail and hospitality), but they differ by award and by casual or permanent status, so check yours and change them.</p>
{tool_box("penalty", '<div class="row">' + field("base", "Base hourly rate ($)", f"{nmw:.2f}") + '<label class="field"><span>Employment</span><select id="emp"><option value="perm">Full or part time</option><option value="casual">Casual (+25%)</option></select></label></div>'
  + '<div class="grid-hours">' + "".join(f'<div class="hr-row"><span>{lab}</span><input id="h_{k}" type="number" inputmode="decimal" step="any" value="{h}" aria-label="{lab} hours"><span>hrs at</span><input id="m_{k}" type="number" inputmode="decimal" step="any" value="{m}" aria-label="{lab} multiplier"><span>×</span></div>'
    for k, lab, h, m in [("ord", "Ordinary (weekday)", 30, 1), ("eve", "Weekday evening", 0, 1.25), ("sat", "Saturday", 6, 1.25), ("sun", "Sunday", 0, 1.5), ("ph", "Public holiday", 0, 2.25), ("ot1", "Overtime, first 2-3 hrs", 0, 1.5), ("ot2", "Overtime after that", 0, 2)]) + '</div>')}
<p class="small muted">Casual multipliers in many awards already include the casual loading (for example 150% on Saturday for retail casuals). When you pick Casual, we add 25% to the ordinary hours only and use your multipliers as written for the rest.</p>""",
        "casual-vs-permanent": f"""<h1>Casual vs permanent: which pays more?</h1>
<p class="lead">Casuals get a 25% loading instead of paid leave. Permanent staff get {WORK["annual_leave_weeks"]} weeks' paid annual leave, {WORK["personal_leave_days"]} days' paid personal leave, and paid public holidays. This compares the two over a year.</p>
{tool_box("casual", '<div class="row">' + field("base", "Permanent base hourly rate ($)", f"{nmw:.2f}") + field("hours", "Hours a week", 38) + field("phdays", "Public holidays that fall on your work days", 8) + field("sick", "Sick days you'd actually take", 5) + '</div>')}
<p class="small muted">Not counted: leave loading, job security, notice and redundancy pay (casuals usually get none), and casual conversion rights.</p>""",
        "leave": f"""<h1>Annual leave and personal leave calculator</h1>
<p class="lead">Full-time and part-time employees build up {WORK["annual_leave_weeks"]} weeks of annual leave ({WORK["shiftworker_leave_weeks"]} for some shift workers) and {WORK["personal_leave_days"]} days of paid personal (sick and carer's) leave a year, pro rata for part time. Leave builds up as you work, including while you're on paid leave. Casuals don't get paid leave.</p>
{tool_box("leave", '<div class="row">' + field("hours", "Ordinary hours a week", 38) + field("weeks", "Weeks worked", 52) + field("rate", "Hourly rate ($)", f"{nmw:.2f}") + '<label class="field"><span>Shift worker?</span><select id="shift"><option value="0">No (4 weeks)</option><option value="1">Yes (5 weeks)</option></select></label><label class="field"><span>Leave loading</span><select id="loading"><option value="0.175">17.5% (many awards)</option><option value="0">None</option></select></label></div>')}
<p>Also under the National Employment Standards: {WORK["compassionate_leave_days"]} days' compassionate leave per occasion, {WORK["family_violence_leave_days"]} days' paid family and domestic violence leave a year (casuals too), community service leave, unpaid parental leave and long service leave (set by state laws).</p>
{sources(WORK["nes_sources"])}""",
        "notice-redundancy": f"""<h1>Notice period and redundancy pay calculator</h1>
<p class="lead">Minimum notice and redundancy pay under the National Employment Standards. Your award, agreement or contract can give you more, never less.</p>
{tool_box("redundancy", '<div class="row">' + field("years", "Years of continuous service", 3) + field("weekly", "Weekly base pay ($)", f"{MW['weekly']:.2f}") + field("age", "Your age", 35) + '<label class="field"><span>Employer size</span><select id="small"><option value="0">15 or more employees</option><option value="1">Small business (under 15)</option></select></label></div>')}
<h2>The NES tables</h2>
<div class="tablewrap"><table class="result"><thead><tr><th>Service</th><th>Notice</th></tr></thead><tbody>
<tr><td>Up to 1 year</td><td>1 week</td></tr><tr><td>1 to 3 years</td><td>2 weeks</td></tr><tr><td>3 to 5 years</td><td>3 weeks</td></tr><tr><td>Over 5 years</td><td>4 weeks</td></tr></tbody></table></div>
<p>Add one week if you are over 45 and have at least 2 years' service. Employers can pay instead of notice.</p>
<div class="tablewrap"><table class="result"><thead><tr><th>Service</th><th>Redundancy pay</th></tr></thead><tbody>
{"".join(f"<tr><td>{lab}</td><td>{w} weeks</td></tr>" for lab, w in [("At least 1, less than 2 years", 4), ("2 to 3 years", 6), ("3 to 4 years", 7), ("4 to 5 years", 8), ("5 to 6 years", 10), ("6 to 7 years", 11), ("7 to 8 years", 13), ("8 to 9 years", 14), ("9 to 10 years", 16), ("10 years or more", 12)])}
</tbody></table></div>
<p class="small muted">Small businesses (under 15 employees) don't have to pay NES redundancy pay. Casuals and some fixed-term employees are excluded. Genuine redundancy payments are tax-free up to an ATO limit that rises each July.</p>
{sources(WORK["nes_sources"])}""",
        "salary-packaging": f"""<h1>Salary packaging calculator</h1>
<p class="lead">If you work for a public or not-for-profit hospital, a public ambulance service, or a charity (PBI), you can pay some everyday bills from your pre-tax salary. This shows how much more you take home in {WORK["salary_packaging"]["fbt_year"]} limits.</p>
{tool_box("packaging", '<div class="row">' + field("salary", "Yearly salary ($)", 85000) + '<label class="field"><span>Employer</span><select id="emp">' + "".join(f'<option value="{k}">{esc(v["label"])}</option>' for k, v in WORK["salary_packaging"]["caps"].items()) + '</select></label>' + field("amount", "Amount to package ($/year)", 9010) + field("fee", "Packaging admin fee ($/year)", 0) + '<label class="field"><span>HELP debt?</span><select id="help"><option value="0">No</option><option value="1">Yes</option></select></label></div>')}
<h2>How it works</h2>
<ul><li>Hospitals and ambulance services: up to ${WORK["salary_packaging"]["caps"]["hospital"]["taxable"]:,} a year tax-free (a ${WORK["salary_packaging"]["caps"]["hospital"]["grossed"]:,} grossed-up cap).</li>
<li>Charities (PBIs) and health promotion charities: up to ${WORK["salary_packaging"]["caps"]["pbi"]["taxable"]:,} a year (${WORK["salary_packaging"]["caps"]["pbi"]["grossed"]:,} grossed-up).</li>
<li>Meal entertainment and holiday accommodation can be packaged on top, up to a separate ${WORK["salary_packaging"]["meal_entertainment_grossed"]:,} grossed-up cap.</li>
<li>The packaged amount appears on your income statement as a reportable fringe benefit. It doesn't change your income tax, but it counts for HELP repayments, some government payments and the Medicare levy surcharge.</li></ul>
{sources(WORK["salary_packaging"]["sources"])}""",
        "pay-converter": f"""<h1>Pay converter: hourly to yearly and back</h1>
<p class="lead">Convert any pay amount between hourly, daily, weekly, fortnightly, monthly and yearly, before tax.</p>
{tool_box("convert", '<div class="row">' + field("amount", "Pay ($)", f"{nmw:.2f}") + '<label class="field"><span>per</span><select id="per"><option value="hour">hour</option><option value="day">day</option><option value="week">week</option><option value="fortnight">fortnight</option><option value="month">month</option><option value="year">year</option></select></label>' + field("hours", "Hours a week", 38) + field("days", "Days a week", 5) + '</div>')}
<p>See what that is after tax with the <a href="{up}index.html">take-home pay calculator</a>.</p>""",
    }
    for slug, title, desc in TOOLS:
        body = (f'<p class="crumbs"><a href="{up}index.html">Calculator</a> › <a href="{up}tools/index.html">Work tools</a> › {esc(title)}</p>'
                f'<article>{bodies[slug]}</article>{ad_slot()}{more_tools(up, slug)}{cross_sell(up)}')
        out[f"tools/{slug}.html"] = page(f"tools/{slug}.html", f"{title} ({WORK['minimum_wage']['from'][-4:]})", desc, body, up)

    cards = "".join(f'<a class="card" href="{slug}.html"><strong>{esc(t)}</strong><span>{esc(d)}</span><em>Open →</em></a>' for slug, t, d in TOOLS)
    out["tools/index.html"] = page("tools/index.html", "Free Australian work and pay tools", "Penalty rates, casual vs permanent, leave, notice and redundancy, salary packaging and pay conversion tools for Australian workers.",
                                   f'<h1>Work and pay tools</h1><p class="lead">Free tools for everyone working in Australia. Nothing you type leaves your device.</p><div class="cards">{cards}</div>{cross_sell(up)}', up)
    out["pay-rates/index.html"] = minimum_wage_page(page, ad_slot, cross_sell)
    return out


def more_tools(up: str, skip: str) -> str:
    links = "".join(f'<li><a href="{up}tools/{s}.html">{esc(t)}</a></li>' for s, t, _ in TOOLS if s != skip)
    return f'<section><h2>More work tools</h2><ul class="list">{links}</ul></section>'


def minimum_wage_page(page, ad_slot, cross_sell) -> str:
    up = "../"
    weekly, hourly = MW["weekly"], MW["hourly"]
    junior = "".join(f"<tr><td>{a}</td><td>{p}%</td><td>{money2(hourly * p / 100)}</td><td>{money2(hourly * p / 100 * 1.25)}</td></tr>" for a, p in MW["junior_pct"])
    awards_list = award_index_html(up)
    body = f"""<p class="crumbs"><a href="{up}index.html">Calculator</a> › Pay rates</p>
<h1>Minimum wage and award pay rates in Australia</h1>
<p class="lead">From {MW["from"]} the national minimum wage is <strong>{money2(hourly)} an hour</strong> or {money2(weekly)} for a 38-hour week, after a {MW["increase_pct"]}% rise. Casuals on the minimum wage get at least {money2(MW["casual_hourly"])} an hour, including the 25% casual loading.</p>
<div class="stats">
  <div><span>Minimum hourly</span><strong>{money2(hourly)}</strong></div>
  <div><span>Minimum weekly (38 hrs)</span><strong>{money2(weekly)}</strong></div>
  <div><span>Casual minimum</span><strong>{money2(MW["casual_hourly"])}</strong></div>
  <div><span>Full-time yearly</span><strong>${weekly * 52:,.0f}</strong></div>
</div>
<p>A new entry-level rate of {money2(MW["entry_hourly"])} an hour ({money2(MW["entry_weekly"])} a week) can apply only for the first six months of employment. Most workers are covered by an award, which sets a higher minimum for their industry and level.</p>
{ad_slot()}
<section><h2>Find your award</h2>{awards_list}</section>
<section><h2>Junior minimum rates (award-free)</h2>
<p>Workers under 21 who aren't covered by an award get a percentage of the adult minimum. Awards can set their own junior rates.</p>
<div class="tablewrap"><table class="result"><thead><tr><th>Age</th><th>% of adult</th><th>Hourly</th><th>Casual hourly</th></tr></thead><tbody>{junior}</tbody></table></div></section>
<section><h2>What full-time minimum wage takes home</h2><p>${weekly * 52:,.0f} a year is <a href="{up}tools/pay-converter.html">{money2(weekly)} a week before tax</a>. Use the <a href="{up}index.html">take-home calculator</a> to see it after tax for your visa.</p></section>
{sources(MW["sources"])}
{cross_sell(up)}"""
    return page("pay-rates/index.html", f"Minimum wage Australia {MW['from'][-4:]}: {money2(hourly)} an hour, and award pay rates",
                f"Australia's minimum wage from {MW['from']} is {money2(hourly)} an hour ({money2(weekly)} a week). Casual, junior and award pay rates by industry.", body, up)


def award_index_html(up: str) -> str:
    p = HERE / "awards.json"
    if not p.exists():
        return '<p>Award-by-award pay rates are coming soon. Until then, use the <a href="https://www.fairwork.gov.au/pay-and-wages/minimum-wages/pay-guides">Fair Work pay guides</a>.</p>'
    data = json.loads(p.read_text(encoding="utf-8"))
    return '<ul class="cards">' + "".join(
        f'<li><a class="card" href="{up}pay-rates/{a["slug"]}.html"><strong>{esc(a["short"])}</strong><span>From {money2(a["min_hourly"])} an hour. {esc(a["blurb"])}</span><em>See all levels →</em></a></li>'
        for a in data["awards"]) + "</ul>"
