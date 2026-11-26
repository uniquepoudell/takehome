# TakeHome

Free Australian take-home pay calculator for every visa: residents (including most international students), working holiday makers (417/462) and foreign residents, with HELP repayments and super. Static site, Python standard library only, hosted on GitHub Pages.

- `rates.json`: tax figures for one income year. **Recheck every July** against the ATO links inside it.
- `tax.py` and `static/calc.js`: the same maths in Python (static pages) and JavaScript (live calculator). `tests/test_paycheck.py` checks they agree.
- `build.py`: writes the calculator, one page per salary ($20k–$300k) and hourly rate ($20–$100), visa guides and a sitemap.
- `work.json`: minimum wage, NES (notice, redundancy, leave) and salary packaging caps. `tools.py` + `static/tools.js` render the work tools.
- `awards.py` + `awardparse.py`: download and parse award pay rates from awards.fairwork.gov.au into `awards.json` (each hourly build; falls back to the committed file).
- `autopilot/`: playbook, roadmap and log for the daily improvement run.
- `config.json`: name, page ranges and income slots. Ads (`adsense_client`, `adsense_slot`) and the tax-return affiliate card stay hidden until filled in.

Build locally: `python tests/test_paycheck.py && python build.py --out public`

## Custom domain
1. Settings > Secrets and variables > Actions > Variables: add `CUSTOM_DOMAIN` (e.g. `takehomecalc.com`).
2. Settings > Pages: Source = GitHub Actions; enter the same custom domain and tick Enforce HTTPS once offered.
3. In Cloudflare DNS for the domain: CNAME `@` (and `www`) to `uniquepoudell.github.io`, DNS only (grey cloud).
