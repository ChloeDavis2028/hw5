"""Create the two TEST approver accounts for the local dashboard.

Writes data/approvers.json (salted hashes only) and output/test_accounts.md with the
test passwords. Both files are kept out of git (.gitignore). These are test
accounts for localhost only, never real credentials.

From My Work:  .venv/Scripts/python scripts/create_approvers.py
"""
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
import auth  # noqa: E402

ACCOUNTS = [("chloe", "Chloe", "owner"), ("pat", "Pat", "approver")]
lines = ["# Test approver accounts (localhost only, never commit)", "",
         "| Username | Name | Role | Test password |", "|---|---|---|---|"]
for username, name, role in ACCOUNTS:
    password = "test-" + secrets.token_urlsafe(9)
    auth.save_user(username, name, role, password)
    lines.append(f"| `{username}` | {name} | {role} | `{password}` |")
lines += ["", "Owner may approve a purchase order below the $500 cushion (override). Any approver can approve the rest.",
          "Payments over $1,000 need both people to sign in."]
(ROOT / "output" / "test_accounts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Created {len(ACCOUNTS)} test approvers; passwords saved in output/test_accounts.md (not printed here).")
