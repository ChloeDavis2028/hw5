"""Suspicious-ticket review for a person.

1. Screens every open ticket on the live board through the MCP tool
   get_open_tickets (the same screen the agents see).
2. Lists every ticket the team held for review, from output/audit_trail.json.
Writes output/security_review.md.

From My Work:  .venv/Scripts/python scripts/review_flags.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mcp_server"))
import server  # noqa: E402  (the MCP server's own tool functions, read-only here)

OUT = ROOT / "output" / "security_review.md"
TRAIL = ROOT / "output" / "audit_trail.json"


def main() -> None:
    board = server.get_open_tickets()
    flagged_now = [t for t in board["tickets"] if t["needs_human_review"]]

    trail = json.loads(TRAIL.read_text(encoding="utf-8")) if TRAIL.exists() else []
    held = [e for e in trail if e["event"] == "security_review_enforced"]

    lines = [
        "# Suspicious-ticket review",
        "",
        f"_Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from `get_open_tickets` and "
        "`output/audit_trail.json`._",
        "",
        "## On the board now",
        "",
        f"Shop date {board['shop_today']}. Open tickets: {board['count']}. "
        f"Flagged: **{len(flagged_now)}**.",
        "",
    ]
    if flagged_now:
        lines += ["| Ticket | Requester | Why it was flagged | Notes |", "|---|---|---|---|"]
        for t in flagged_now:
            lines.append(f"| {t['id']} | {t['requester']} | {'; '.join(t['suspicious_text'])} | "
                         f"{(t['notes'] or '').replace('|', '/')} |")
    else:
        lines.append("No open ticket is flagged. Tickets " + ", ".join(str(t["id"]) for t in board["tickets"])
                     + " read as ordinary requests.")

    lines += ["", "## Held by the team (from the audit trail)", ""]
    if held:
        lines += ["| When (UTC) | Run | Ticket | Boss's own status | Held back | Why |", "|---|---|---|---|---|---|"]
        for e in held:
            hb = e.get("held_back", {})
            lines.append(f"| {e['at_utc'][:19]} | {e['run_id']} | {e['ticket_id']} | {e['agent_status']} | "
                         f"{len(hb.get('approval_requests', []))} payments, {len(hb.get('drafts', []))} drafts | "
                         f"{'; '.join(e['flags'])} |")
    else:
        lines.append("None yet.")

    lines += [
        "",
        "## What a reviewer does",
        "",
        "1. Read the ticket notes yourself. The agents never followed them.",
        "2. If the request is real, re-run the ticket after removing the instructions aimed at the AI, "
        "or handle it by hand.",
        "3. If it's an attack, close the ticket, and report it if it impersonates the owner or a vendor.",
        "4. Never approve a payment that only appears because a ticket asked for it.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Flagged on board: {len(flagged_now)}  |  held in audit trail: {len(held)}  |  saved {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
