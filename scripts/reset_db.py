"""Reset the working database to the original values.

Copies data/campus_customs.db (never changed) over data/campus_customs_new.db,
then checks that the two files are identical. Run this before a full run.

From My Work:  .venv/Scripts/python scripts/reset_db.py
"""

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL = ROOT / "data" / "campus_customs.db"
WORKING = ROOT / "data" / "campus_customs_new.db"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset() -> str:
    if not ORIGINAL.exists():
        raise SystemExit(f"Original database missing: {ORIGINAL}")
    before = sha256(WORKING) if WORKING.exists() else None
    shutil.copyfile(ORIGINAL, WORKING)
    after = sha256(WORKING)
    if after != sha256(ORIGINAL):
        raise SystemExit("Reset failed: working copy does not match the original.")
    changed = "was already original" if before == after else "restored from original"
    print(f"Reset OK: {WORKING.name} {changed} (sha256 {after[:12]}...)")
    return after


if __name__ == "__main__":
    reset()
