"""Approver sign-in: who is really clicking Approve.

- Approvers live in data/approvers.json with salted PBKDF2 password hashes (never plain text).
- Signing in returns a signed token (HMAC with a secret in data/.session_secret) that lasts 8 hours.
- The approve and reject routes take the approver's name from the token, so nobody can
  type someone else's name. Payments over $1,000 need a second, different signed-in person.
- Roles: "owner" may approve a purchase order below the $500 cushion (an override);
  "approver" may approve everything else.

Create the test accounts with:  .venv/Scripts/python scripts/create_approvers.py
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPROVERS = ROOT / "data" / "approvers.json"
SECRET = ROOT / "data" / ".session_secret"
ITERATIONS = 200_000
TOKEN_HOURS = 8


def _secret() -> bytes:
    if not SECRET.exists():
        SECRET.write_text(secrets.token_hex(32), encoding="utf-8")
    return SECRET.read_text(encoding="utf-8").strip().encode()


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()


def load() -> dict:
    try:
        return {u["username"]: u for u in json.loads(APPROVERS.read_text(encoding="utf-8"))}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_user(username: str, display_name: str, role: str, password: str) -> None:
    users = load()
    salt = secrets.token_hex(16)
    users[username] = {"username": username, "display_name": display_name, "role": role,
                       "salt": salt, "hash": _hash(password, salt), "iterations": ITERATIONS}
    APPROVERS.write_text(json.dumps(list(users.values()), indent=2), encoding="utf-8")


def verify(username: str, password: str) -> dict | None:
    u = load().get((username or "").strip().lower())
    if not u or not password:
        return None
    if not hmac.compare_digest(_hash(password, u["salt"]), u["hash"]):
        return None
    return {"username": u["username"], "display_name": u["display_name"], "role": u["role"]}


def make_token(user: dict) -> str:
    payload = json.dumps({"u": user["username"], "exp": int(time.time()) + TOKEN_HOURS * 3600}).encode()
    body = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    sig = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def check_token(token: str | None) -> dict | None:
    """Return the signed-in approver, or None if the token is missing, forged or expired."""
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest(), sig):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    except (ValueError, json.JSONDecodeError):
        return None
    if data.get("exp", 0) < time.time():
        return None
    u = load().get(data.get("u"))
    return {"username": u["username"], "display_name": u["display_name"], "role": u["role"]} if u else None
