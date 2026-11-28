# Roadmap (top = next)

- [ ] Apprentice rates per award (tables have year-of-apprenticeship % and, in some awards, $ columns; Retail Table 6-9, Hospitality Table 7-11, Hair and beauty Table 6-11)
- [ ] Junior rates on the hub for job-specific tables (childcare L1-2, health support services, trolley collectors, storage % of grade 1)
- [ ] SCHADS, Nurses, Aged care, Childcare: clearer labels for pay point tables, then turn on their level pages (remove from LEVEL_SKIP in awards.py)
- [ ] Super calculator (balance projection, concessional cap, salary sacrifice)
- [ ] Tax refund estimator (withheld vs actual tax, work deductions incl. new $1,000 standard deduction from 2026-27)
- [ ] Payslip checker: enter payslip lines, compare with award minimum and tax withheld
- [ ] Novated lease calculator (EV FBT exemption)
- [ ] Pay rise calculator and "pay increase from 1 July" pages per award
- [ ] Occupation pages (nurse, chef, electrician, truck driver...) linking award + salary pages
- [ ] Student visa 48-hours-a-fortnight earnings planner
- [ ] Working holiday 88-day regional work guide
- [ ] Public holiday list by state, with penalty pay examples
- [ ] Nepali, Hindi, Chinese, Vietnamese translations of the main calculator
- [ ] Email "pay rate change" alerts (needs owner to pick a newsletter tool)

## Done
- 2026-11-28: shop page for the A$5 Shift and Pay Tracker spreadsheet (shop/shift-and-pay-tracker.html, config products); hidden until the owner adds the Stripe link. Spreadsheet source is in the private project files, not this repo
- 2026-11-28: junior pay rates (under 21) parsed from 15 awards; shown on award pages, level pages (respecting "levels 1-3 only"), and a new hub /pay-rates/junior.html with hourly pay by age; Retail and Fast Food phase-in to 2029 shown
- 2026-11-27: 144 per-level award pay pages (16 awards) with weekly take-home by visa, linked from each award table
- 2026-11-26: take-home calculator for every visa, 362 salary/hourly pages, visa guides
- 2026-11-26: minimum wage page, 20 award pay-rate pages (auto-refreshed hourly from Fair Work), penalty rates, casual vs permanent, leave, notice and redundancy, salary packaging, pay converter
