| Date | Shipped | Health | Notes |
|---|---|---|---|
| 2026-11-26 | Site moved from gorkhapay /pay/ to its own repo | Build green; Pages waits on owner switching it on | |
| 2026-11-26 | Pay rates hub (minimum wage + 20 awards), 6 work tools, hourly rebuild | Tests pass | Award rates parsed from awards.fairwork.gov.au (cloud sandbox can't reach it; Actions can) |
| 2026-11-27 | 144 per-level award pages ("Retail Employee Level 1 pay rate") with take-home for resident, backpacker, foreign; 542 pages total | Build job green, awards.json has 20 of 20; deploy still fails until owner turns on Pages; no hourly scheduled runs seen yet | SCHADS, nurses, aged care, childcare skipped until labels are clearer |
| 2026-11-28 | Junior rates for 15 awards on award + level pages, new junior rates hub (543 pages) | Latest scheduled build green, tests pass, awards parsed 20 of 20 | Parser checked against real award pages via a temporary Actions probe (removed). Push builds on main still cannot deploy (Pages environment allows only the default branch, still claude/project-thread-dde1i2); synced that branch from main by PR again. GitHub runs the hourly cron only ~2x a day. |
