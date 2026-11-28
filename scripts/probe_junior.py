"""Dev helper (temporary): parse award pages with the current parser and print awards.json."""
import subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
subprocess.run([sys.executable, str(root / "awards.py"), "parse", sys.argv[1]], check=True)
print("AWARDS_JSON_BEGIN")
print((root / "awards.json").read_text())
print("AWARDS_JSON_END")
