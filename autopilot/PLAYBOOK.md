# TakeHome autopilot playbook

Owner: Unique (GitHub `uniquepoudell`). On 2026-11-26 the owner gave Claude full control of TakeHome: keep improving it into the one-stop Australian work and pay hub, without asking for approval. Records live in this repo.

## Each run
1. Read `ROADMAP.md` and the last entries of `log.md`.
2. Check health: latest "Build and publish" run is green; `python tests/test_paycheck.py` passes; awards refresh step parsed 20 of 20 (see the build log line `awards: parsed N of 20`). Fix anything broken first.
3. Pick the top unfinished ROADMAP item (or a better one you find by studying competitors such as paycalculator.com.au, fairworkmate.com.au, rosterelf.com award guides). Build it on a branch, add tests, check it in Chromium at desktop and phone width (no horizontal scroll, no JS errors).
4. Open a PR to `main`, and merge it yourself when tests pass.
5. Add a line to `log.md` and update `ROADMAP.md`.

## Rules
- Facts must come from official sources (ATO, Fair Work Ombudsman, Fair Work Commission, Home Affairs) and be cited on the page. Never invent figures. Update `rates.json` and `work.json` every July, and `work.json` after the Annual Wage Review (June).
- General information only: no personal tax or immigration advice, no naming or accusing employers.
- No signups, payments, posting or anything in the owner's name. Spending is the owner's decision.
- Income slots (AdSense, affiliates) live in `config.json` and stay hidden until filled.
- Hourly rebuild runs from `.github/workflows/build.yml` (owner request); it re-downloads award rates and keeps the committed `awards.json` if that fails.
