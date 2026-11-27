"""Offline tests for the TakeHome pay calculator. Run: python paycheck/tests/test_paycheck.py"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from tax import calculate, help_repayment  # noqa: E402
import build  # noqa: E402


def close(a, b, tol=1.0):
    assert abs(a - b) <= tol, (a, b)


def test_resident():
    assert calculate(18200)["total_tax"] == 0
    # $45,000: 4,020 tax - 325 LITO = 3,695; Medicare 900
    r = calculate(45000)
    close(r["income_tax"], 3695); close(r["medicare"], 900)
    # $100,000: 4,020 + 16,500 = 20,520; no LITO; Medicare 2,000
    r = calculate(100000)
    close(r["income_tax"], 20520); close(r["medicare"], 2000); close(r["net"], 77480)
    close(calculate(200000)["income_tax"], 51370 + 4500)


def test_whm_foreign():
    close(calculate(45000, "whm")["total_tax"], 6750)
    close(calculate(60000, "whm")["total_tax"], 6750 + 4500)
    close(calculate(100000, "foreign")["total_tax"], 30000)


def test_help():
    close(help_repayment(86380), 2527.80, 0.05)  # ATO worked example 2026-27
    assert help_repayment(69528) == 0
    close(help_repayment(200000), 20000)


def test_js_matches_python():
    node = shutil.which("node")
    if not node:
        print("skip: node not installed"); return
    rates = json.loads((HERE / "rates.json").read_text())
    incomes = [0, 15000, 22866, 30000, 37500, 45000, 60000, 66667, 70000, 129717, 150000, 186051, 250000]
    script = (f"global.window=undefined;const P=require({json.dumps(str(HERE / 'static' / 'calc.js'))});const R={json.dumps(rates)};"
              f"const out=[];for(const k of ['resident','whm','foreign'])for(const h of [false,true])for(const x of {incomes})out.push(P.calculate(R,x,k,h).net);"
              "console.log(JSON.stringify(out));")
    js = json.loads(subprocess.check_output([node, "-e", script], text=True))
    py = [calculate(x, k, h)["net"] for k in ["resident", "whm", "foreign"] for h in [False, True] for x in incomes]
    for a, b in zip(js, py):
        close(a, b, 0.02)


def test_awards_data():
    data = json.loads((HERE / "awards.json").read_text())
    assert len(data["awards"]) >= 15
    work = json.loads((HERE / "work.json").read_text())
    floor = work["minimum_wage"]["entry_hourly"] - 1.0  # a few awards have junior-ish adult entry rows
    for a in data["awards"]:
        assert a["tables"] and a["min_hourly"] >= floor, (a["code"], a["min_hourly"])
        for t in a["tables"]:
            for r in t["rows"]:
                assert 500 <= r["weekly"] <= 5000 and r["hourly"] > 0


def test_awardparse_sample():
    from awardparse import rate_tables
    html = ("<p>Table 4—Minimum rates</p><table><tr><td>Employee classification</td><td>Minimum weekly rate</td><td>Minimum hourly rate</td></tr>"
            "<tr><td></td><td>$</td><td>$</td></tr><tr><td>Level 1</td><td>1056.80</td><td>27.81</td></tr><tr><td>Level 2</td><td>1081.00</td><td>28.45</td></tr></table>")
    t = rate_tables(html)
    assert t[0]["caption"] == "Minimum rates" and t[0]["rows"][1]["hourly"] == 28.45


def test_build():
    with tempfile.TemporaryDirectory() as d:
        n = build.build(Path(d) / "pay")
        assert n > 390, n
        page = (Path(d) / "pay" / "salary" / "100000.html").read_text()
        assert "$77,480" in page and "application/ld+json" in page



def test_level_pages():
    import awards
    from tax import calculate as calc
    data = json.loads((HERE / "awards.json").read_text())["awards"]
    retail = next(a for a in data if a["slug"] == "retail")
    rows = awards.level_rows(retail)
    assert len(rows) == len(retail["tables"][0]["rows"])
    assert all(not p.endswith("-.html") for _, _, p in rows)
    assert not awards.level_rows(next(a for a in data if a["slug"] == "schads"))
    assert awards.level_label({"slug": "hospitality", "short": "Hospitality"}, "Level 2") == "Hospitality Level 2"
    assert awards.level_label({"slug": "security", "short": "Security"}, "Security Officer Level 4") == "Security Officer Level 4"
    with tempfile.TemporaryDirectory() as d:
        build.build(Path(d) / "pay")
        row, label, path = rows[0]
        page = (Path(d) / "pay" / path).read_text()
        assert f"${row['hourly']:.2f} an hour" in page and label in page
        net_week = calc(row["hourly"] * 38 * 52, "whm")["net"] / 52
        assert f"${net_week:,.0f}" in page
        award = (Path(d) / "pay" / "pay-rates" / "retail.html").read_text()
        assert path.split("/", 1)[1] in award
        assert len(list((Path(d) / "pay" / "pay-rates").glob("*/*.html"))) > 100


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
