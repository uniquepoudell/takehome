"""Australian take-home pay engine. Mirrors static/calc.js exactly; tests check both agree."""
from __future__ import annotations

import json
from pathlib import Path

RATES = json.loads((Path(__file__).parent / "rates.json").read_text(encoding="utf-8"))

KINDS = {
    "resident": "Australian resident",
    "whm": "Working holiday maker (417/462)",
    "foreign": "Foreign resident",
}


def bracket_tax(income: float, brackets) -> float:
    tax, lower = 0.0, 0.0
    for upper, rate in brackets:
        top = income if upper is None else min(income, upper)
        if top > lower:
            tax += (top - lower) * rate
        if upper is None or income <= upper:
            break
        lower = upper
    return tax


def lito(income: float) -> float:
    p = RATES["lito"]
    if income <= p["full_to"]:
        return p["max"]
    if income <= p["mid_to"]:
        return p["max"] - (income - p["full_to"]) * 0.05
    if income <= p["zero_at"]:
        return max(0.0, p["mid_value"] - (income - p["mid_to"]) * 0.015)
    return 0.0


def medicare(income: float) -> float:
    m = RATES["medicare"]
    if income <= m["low"]:
        return 0.0
    return min(income * m["rate"], (income - m["low"]) * 0.10)


def help_repayment(income: float) -> float:
    h = RATES["help"]
    if income <= h["threshold"]:
        return 0.0
    if income <= h["band2"]:
        return (income - h["threshold"]) * h["rate1"]
    if income < h["top"]:
        return h["band2_base"] + (income - h["band2"]) * h["rate2"]
    return income * h["top_rate"]


def calculate(income: float, kind: str = "resident", has_help: bool = False) -> dict:
    """Yearly figures for a taxable income. Super is paid on top by the employer."""
    income = max(0.0, float(income))
    gross_tax = bracket_tax(income, RATES[kind])
    offset = lito(income) if kind == "resident" else 0.0
    income_tax = max(0.0, gross_tax - offset)
    levy = medicare(income) if kind == "resident" else 0.0
    loan = help_repayment(income) if has_help else 0.0
    total = income_tax + levy + loan
    return {
        "income": income,
        "income_tax": round(income_tax, 2),
        "medicare": round(levy, 2),
        "help": round(loan, 2),
        "total_tax": round(total, 2),
        "net": round(income - total, 2),
        "super": round(income * RATES["super_rate"], 2),
        "avg_rate": (total / income) if income else 0.0,
        "marginal": marginal_rate(income, kind),
    }


def marginal_rate(income: float, kind: str) -> float:
    for upper, rate in RATES[kind]:
        if upper is None or income <= upper:
            return rate
    return RATES[kind][-1][1]
