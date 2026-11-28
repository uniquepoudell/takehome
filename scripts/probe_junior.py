"""Dev helper: print junior/apprentice tables found in award pages (temporary)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from awardparse import tables
for f in sorted(Path(sys.argv[1]).glob("*.html")):
    html = f.read_text(encoding="utf-8", errors="replace")
    for i, (t, cap) in enumerate(tables(html, captions=True)):
        txt = (cap + " " + " ".join(" ".join(r) for r in t[:3])).lower()
        if any(k in txt for k in ("junior", "age", "apprentic", "under 16", "years of age")):
            if not any("%" in c for r in t for c in r) and "apprentic" not in txt:
                continue
            print("##", f.stem, i, "CAP:", cap[:160])
            for r in t[:12]:
                print("   ", json.dumps([c[:70] for c in r], ensure_ascii=False))
