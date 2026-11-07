"""Independent cash check: does the Cash tab add up, and does it match cash_accounts?

It reads the numbers back from output/desk_tickets.html (what a grader sees) and
compares them with the working database, read-only. Three checks:
  1. The page's start + every per-ticket change = the page's end    (the math adds up)
  2. The page's end = cash_accounts.balance in the working database (it matches the books)
  3. The original start - every payments row = cash_accounts         (the books agree with themselves)
Exits with code 1 if anything is off.

From My Work:  .venv/Scripts/python scripts/check_cash.py
"""

import html
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "output" / "desk_tickets.html"
WORKING = ROOT / "data" / "campus_customs_new.db"
ORIGINAL = ROOT / "data" / "campus_customs.db"


def ro(path: Path):
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def num(text: str) -> float:
    text = text.strip().replace(",", "").replace("$", "")
    return 0.0 if text in ("—", "") else float(text)


def main() -> int:
    page = PAGE.read_text(encoding="utf-8")
    i = page.index('<section class="tab" id="cash"')
    cash = page[i:page.index("</section>", i)]
    rows = []
    for row in re.findall(r"<tr>(.*?)</tr>", cash, re.S):
        cells = [html.unescape(re.sub("<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        if len(cells) == 4 and cells[0] in ("Start", "End") or (len(cells) == 4 and cells[0].startswith("Ticket")):
            rows.append(cells)
    start = num(next(r[3] for r in rows if r[0] == "Start"))
    end = num(next(r[3] for r in rows if r[0] == "End"))
    changes = [(r[0], num(r[2])) for r in rows if r[0].startswith("Ticket")]

    with ro(WORKING) as c:
        books = c.execute("SELECT balance FROM cash_accounts WHERE name='checking'").fetchone()[0]
        paid = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments").fetchone()[0]
    with ro(ORIGINAL) as c:
        original = c.execute("SELECT balance FROM cash_accounts WHERE name='checking'").fetchone()[0]

    checks = [
        ("Page math: start + changes = end", round(start + sum(ch for _, ch in changes), 2), end),
        ("Page end = cash_accounts (working database)", end, round(books, 2)),
        ("Books: original start - payments = cash_accounts", round(original - paid, 2), round(books, 2)),
        ("Page start = original cash_accounts (after reset)", start, round(original, 2)),
    ]
    print(f"Page:  start ${start:,.2f}  " + "  ".join(f"{t} {'+' if ch >= 0 else ''}{ch:,.2f}" for t, ch in changes) + f"  end ${end:,.2f}")
    print(f"Books: cash_accounts ${books:,.2f}   payments total ${paid:,.2f}   original ${original:,.2f}")
    ok = True
    for name, a, b in checks:
        good = abs(a - b) < 0.005
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {name}: {a:,.2f} vs {b:,.2f}")
    print("CASH CHECK PASSED" if ok else "CASH CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
