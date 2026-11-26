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


def test_build():
    with tempfile.TemporaryDirectory() as d:
        n = build.build(Path(d) / "pay")
        assert n > 360, n
        page = (Path(d) / "pay" / "salary" / "100000.html").read_text()
        assert "$77,480" in page and "application/ld+json" in page


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
