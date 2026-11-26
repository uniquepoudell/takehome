"""Parse minimum pay rate tables out of Fair Work award viewer pages (awards.fairwork.gov.au/MAxxxxxx.html)."""
from __future__ import annotations

import html as htmllib
import re
from html.parser import HTMLParser


class _Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self._stack = [], []
        self.captions, self._recent = [], ""

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if not self._stack:
                ch = getattr(self, "_chunks", [])
                self._cap = " ".join(ch[-3:])
            self._stack.append([])
        elif tag == "tr" and self._stack:
            self._stack[-1].append([])
        elif tag in ("td", "th") and self._stack and self._stack[-1]:
            self._stack[-1][-1].append("")

    def handle_endtag(self, tag):
        if tag == "table" and self._stack:
            t = self._stack.pop()
            self.tables.append([[re.sub(r"\s+", " ", c).strip() for c in r] for r in t if r])
            self.captions.append(self._cap if not self._stack else "")
            if not self._stack:
                self._chunks = []

    def handle_data(self, data):
        if not self._stack:
            d = re.sub(r"\s+", " ", data).strip()
            if d and not re.search(r"varied by|ppc|inserted by|corrected by|substituted by|^\[|^\]$|^[,;.]$|^PR\d+", d, re.I):
                self._chunks = (getattr(self, "_chunks", []) + [d])[-6:]
        if self._stack and self._stack[-1] and self._stack[-1][-1]:
            self._stack[-1][-1][-1] += data


def tables(html: str, captions: bool = False):
    p = _Tables()
    p.feed(html)
    return list(zip(p.tables, p.captions)) if captions else p.tables


def title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    t = htmllib.unescape(m.group(1)) if m else ""
    return re.sub(r"\s*-\s*Fair Work Ombudsman.*", "", t).strip()


NUM = re.compile(r"^\$?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)$")


def _num(cell: str):
    m = NUM.match(cell.replace(" ", " ").strip())
    return float(m.group(1).replace(",", "")) if m else None


def _is_rate_header(head: str) -> bool:
    h = head.lower()
    bad = ("apprentic", "allowance", "% of", "age", "in charge", "trainee", "junior", "percentage")
    return ("weekly" in h or "per week" in h) and not any(b in h for b in bad)


def rate_tables(html: str):
    """Return list of tables, each a list of {name, detail, weekly, hourly}."""
    found = []
    for t, cap in tables(html, captions=True):
        if len(t) < 2:
            continue
        head = " ".join(t[0])
        if found and any(b in head.lower() for b in ("apprentic", "allowance")):
            break
        if not _is_rate_header(head):
            continue
        cols = [c.lower() for c in t[0]]
        wi = next((i for i, c in enumerate(cols) if "weekly" in c or "per week" in c), None)
        hi = next((i for i, c in enumerate(cols) if "hourly" in c), None)
        rows, group = [], ""
        for r in t[1:]:
            if wi is None or wi >= len(r):
                continue
            weekly = _num(r[wi])
            hourly = _num(r[hi]) if hi is not None and hi < len(r) else None
            if weekly is None:
                if r and r[0] and not any(_num(c) for c in r):
                    group = r[0]
                continue
            if not 500 <= weekly <= 5000:
                continue
            name = r[0] or group
            detail = " ".join(c for i, c in enumerate(r[1:wi], 1) if c and _num(c) is None)
            rows.append({"name": name, "group": group, "detail": detail.replace(";", "; ")[:400],
                         "weekly": weekly, "hourly": hourly if hourly else round(weekly / 38, 2)})
        if len(rows) >= 2:
            found.append({"caption": _clean_caption(cap), "rows": rows})
    return found


def _clean_caption(cap: str) -> str:
    cap = re.sub(r"\b\d{2}[A-Z][a-z]{2}\d{2}\]?", "", cap)
    cap = re.sub(r"\s+", " ", cap).strip(" :—-],")
    m = list(re.finditer(r"Table \d+\s*—\s*", cap))
    if m:
        cap = cap[m[-1].end():]
    elif ". " in cap:
        cap = cap.rsplit(". ", 1)[-1]
    cap = re.sub(r"^(\([a-z0-9]+\)|[A-Z]?\d+(\.\d+)+)\s*", "", cap).strip(" ,.")
    if len(cap) < 6 or cap.endswith(" by") or cap.lower() in ("as follows",) or cap.startswith(","):
        return ""
    return cap[:150]


def penalty_tables(html: str, limit: int = 2):
    out = []
    for t in tables(html):
        if len(t) < 3:
            continue
        head = " ".join(t[0]).lower()
        body = " ".join(" ".join(r) for r in t[1:]).lower()
        if ("time of ordinary hours" in head or "overtime" in head or ("saturday" in body and "%" in body)) and "allowance" not in head:
            if all(len(c) < 200 for r in t for c in r):
                out.append(t)
        if len(out) >= limit:
            break
    return out
