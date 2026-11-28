"""Dev helper: print junior rate tables parsed from award pages (temporary)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from awardparse import junior_tables
for f in sorted(Path(sys.argv[1]).glob("*.html")):
    html = f.read_text(encoding="utf-8", errors="replace")
    print("##", f.stem, json.dumps(junior_tables(html), ensure_ascii=False))
    if f.stem in ("MA000003", "MA000002", "MA000016"):
        import re
        for m in re.finditer(r"junior", html, re.I):
            print("   ctx:", re.sub(r"<[^>]+>|\s+", " ", html[m.start()-200:m.start()+600])[:400])
            break
