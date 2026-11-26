#!/usr/bin/env python3
"""Download modern award pages from the Fair Work award viewer (run in GitHub Actions)."""
import sys, time, urllib.request
from pathlib import Path

CODES = sys.argv[2:] or []
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for code in CODES:
    url = f"https://awards.fairwork.gov.au/{code}.html"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; TakeHomeBot/1.0)"})
        data = urllib.request.urlopen(req, timeout=60).read()
        (out / f"{code}.html").write_bytes(data)
        print(code, len(data))
    except Exception as e:  # keep going
        print(code, "ERROR", e)
    time.sleep(1)
