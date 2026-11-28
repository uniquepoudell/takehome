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


AGE = re.compile(r"^(?:at\s+)?(under\s+\d{2}|\d{2})\s*years?(?:\s+of\s+age)?", re.I)
MONTHS = {m: i for i, m in enumerate(("january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"), 1)}
_SKIP_JUNIOR = ("deduct", "trainee", "tracer", "foundry", "cadet", "apprentic", "supported wage")


def _pct(cell: str):
    c = cell.strip().rstrip("%").strip()
    if re.match(r"^(the\s+)?(appropriate\s+|applicable\s+)?adult rate$", c, re.I):
        return 100.0
    try:
        v = float(c)
    except ValueError:
        return None
    return v if 10 <= v <= 100 else None


def _first_date(text: str):
    m = re.search(r"(\d{1,2})\s*([A-Za-z]+)\s*(\d{4})", text)
    if not m or m.group(2).lower() not in MONTHS:
        return None
    return f"{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"


def junior_tables(html: str, limit: int = 3):
    """Junior rate tables: [{caption, base, per_level, starts, rows: [{age, pcts}]}].

    Only tables in the body of the award (before the pay-guide schedules) whose rows are ages with a % of the
    adult rate. `starts` lists the date each % column takes effect (empty when there is one column).
    """
    out = []
    for t, cap in tables(html, captions=True):
        if len(t) < 3:
            continue
        if re.match(r"^\s*(?:B\.1\.2\s+)?B\.\d", cap):  # schedule B pay guides repeat the same rates in dollars
            continue
        low_cap = cap.lower()
        if any(k in low_cap for k in _SKIP_JUNIOR):
            continue
        head_rows, rows, starts = [], [], []
        for r in t:
            m = AGE.match(r[0]) if r else None
            if not m:
                if rows:
                    break
                head_rows.append(r)
                if any(_first_date(c) for c in r[1:]):
                    starts = [_first_date(c) for c in r[1:] if c]
                continue
            pcts = [_pct(c) for c in r[1:] if c.strip()]
            if not pcts or any(p is None for p in pcts):
                rows = []
                break
            rows.append({"age": re.sub(r"(?<=[a-z])\d$", "", r[0]).strip(), "pcts": pcts})
        head = " ".join(" ".join(r) for r in head_rows)
        if len(rows) < 2 or ("%" not in head and "percentage" not in head.lower()) or "$" in head:
            continue
        if starts and any(len(r["pcts"]) != len(starts) for r in rows):
            starts = []
        if not starts and any(len(r["pcts"]) != 1 for r in rows):
            continue
        base = re.sub(r"^(column \d+\s*)?", "", next((c for r in head_rows for c in r if "%" in c or "ercentage" in c), ""), flags=re.I).strip()
        caption, per_level, levels = junior_meta(_clean_caption(cap), base)
        out.append({"caption": caption, "base": base[:120], "per_level": per_level, "levels": levels,
                    "starts": starts, "rows": rows})
        if len(out) >= limit:
            break
    return out


def junior_meta(full: str, base: str):
    """(heading, per_level, levels) for a junior table. per_level means the % applies to every classification
    (or to the listed levels), so dollar rates can be shown; tables for one job stream only show percentages."""
    caption = _junior_caption(full)
    generic = re.sub(r"\(other than[^)]*\)", "", full, flags=re.I)
    levels = None
    m = re.search(r"levels? ([\d, and]+) only", generic, re.I)
    if m:
        levels = [int(n) for n in re.findall(r"\d+", m.group(1))]
    specific = re.search(r"support services|trolley|office|children|engaged on|level|stream", generic, re.I)
    per_level = not re.search(r"\b(grade \d|level \d|[CV]\d+)", base, re.I) and (levels is not None or not specific)
    if specific and levels is None and not re.search(specific.group(0), caption, re.I):
        caption = re.sub(r"\s+(will|must) be paid.*$", "", full[0].upper() + full[1:])
    return caption, per_level, levels


def _junior_caption(cap: str) -> str:
    """Short heading for a junior table: keep "Junior rates (...)" style captions, cut clause sentences."""
    m = re.search(r"\bjuniors?\b.*", cap, re.I)
    if not m:
        return "Junior rates"
    c = m.group(0)
    c = re.split(r"\s(?:A|An|The|will|must|is|are|as follows)\b|\s\([a-z]\)", c)[0].strip(" ,.:")
    c = c[0].upper() + c[1:]
    return c if len(c) <= 90 else "Junior rates"


def junior_pct(table: dict, row: dict, today: str) -> dict:
    """{pct, starts (set when that % only starts later), next, next_pct} for one junior row on a given date."""
    pcts, starts = row["pcts"], table.get("starts") or []
    if not starts:
        return {"pct": pcts[0], "starts": None, "next": None, "next_pct": None}
    future = today < starts[0]
    i = max([k for k, s in enumerate(starts) if s <= today] or [0])
    nxt = next(((starts[k], pcts[k]) for k in range(i + 1, len(starts)) if pcts[k] != pcts[i]), (None, None))
    return {"pct": pcts[i], "starts": starts[0] if future else None, "next": nxt[0], "next_pct": nxt[1]}
