"""Smoke test for the Campus Customs MCP server.

Starts the server exactly as .mcp.json says (stdio), calls each of the three
tools over MCP for the ticket it unlocks plus one not-found case, checks each
answer against the database read directly, and saves the evidence to
output/mcp_smoke.json.

Run from the project root:  .venv/Scripts/python scripts/mcp_smoke.py
"""

import asyncio
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import Client

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "campus_customs_new.db"
ORIGINAL = ROOT / "data" / "campus_customs.db"
OUT = ROOT / "output" / "mcp_smoke.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def db_row(sql: str, args=()) -> dict:
    """Read the expected values straight from the database (not through MCP)."""
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    row = conn.execute(sql, args).fetchone()
    conn.close()
    return dict(row) if row else {}


def server_config() -> dict:
    cfg = json.loads((ROOT / ".mcp.json").read_text())
    name, server = next(iter(cfg["mcpServers"].items()))
    server = {**server, "command": str(ROOT / server["command"]), "cwd": str(ROOT)}
    return name, {"mcpServers": {name: server}}


def check(label: str, actual, expected) -> dict:
    return {"check": label, "expected": expected, "actual": actual, "pass": actual == expected}


async def main():
    name, config = server_config()
    before = {"campus_customs_new.db": sha256(DB), "campus_customs.db": sha256(ORIGINAL)}

    tee = db_row("SELECT qty FROM inventory WHERE sku='CC-TEE-WHITE' AND size='S'")
    hood = db_row("SELECT qty FROM inventory WHERE sku='CC-HOOD-NAVY' AND size='M'")
    hood_price = db_row("SELECT unit_cost, list_price FROM pricing WHERE sku='CC-HOOD-NAVY'")
    inv = db_row("SELECT amount, due_date, status, vendor_id FROM invoices WHERE id=501")
    vendor = db_row("SELECT name, lead_days FROM vendors WHERE id=?", (inv["vendor_id"],))
    lease = db_row("SELECT monthly_rent, next_due FROM leases WHERE id=1")
    cash = db_row("SELECT balance FROM cash_accounts WHERE name='checking'")
    today = db_row("SELECT date_today FROM desk")["date_today"]

    plan = [
        {
            "ticket": 103,
            "prompt": "Ticket 103: the Yale AI Club wants 20 navy hoodies (CC-HOOD-NAVY) in size M "
                      "at a bulk discount. How many size-M hoodies are on the shelf, and what are "
                      "the unit cost, list price and margin per unit?",
            "why": "Yale AI Club wants 20 size-M hoodies at a discount: need stock and margin.",
            "tool": "check_stock",
            "args": {"sku": "CC-HOOD-NAVY", "size": "M"},
            "checks": lambda r: [
                check("found", r.get("found"), True),
                check("qty on shelf", r.get("qty"), hood["qty"]),
                check("unit_cost", r["pricing"]["unit_cost"], hood_price["unit_cost"]),
                check("list_price", r["pricing"]["list_price"], hood_price["list_price"]),
                check("margin_per_unit", r["pricing"]["margin_per_unit"],
                      hood_price["list_price"] - hood_price["unit_cost"]),
            ],
        },
        {
            "ticket": 101,
            "prompt": "Ticket 101: Tauhid Zaman ordered 1 Classic Bulldog Tee (CC-TEE-WHITE) in "
                      "size S. How many size-S tees are on the shelf?",
            "why": "Tauhid's size-S tee: confirm the shelf is empty.",
            "tool": "check_stock",
            "args": {"sku": "CC-TEE-WHITE", "size": "S"},
            "checks": lambda r: [
                check("found", r.get("found"), True),
                check("qty on shelf", r.get("qty"), tee["qty"]),
            ],
        },
        {
            "ticket": 101,
            "prompt": "Ticket 101 links to invoice 501. Is it open or overdue as of the shop's "
                      "date, which vendor is it for, what is that vendor's lead time, can the "
                      "vendor ship right now, and how much cash does the shop have?",
            "why": "The tee ticket links to invoice 501; an open invoice blocks the vendor.",
            "tool": "get_invoice",
            "args": {"invoice_id": 501},
            "checks": lambda r: [
                check("found", r.get("found"), True),
                check("shop_today from desk", r.get("shop_today"), today),
                check("amount", r["invoice"]["amount"], inv["amount"]),
                check("status", r["invoice"]["status"], inv["status"]),
                check("days_overdue", r.get("days_overdue"),
                      (datetime.fromisoformat(today) - datetime.fromisoformat(inv["due_date"])).days),
                check("vendor name", r["vendor"]["name"], vendor["name"]),
                check("vendor lead_days", r["vendor"]["lead_days"], vendor["lead_days"]),
                check("vendor_can_ship", r.get("vendor_can_ship"), False),
                check("cash balance", r["cash_accounts"][0]["balance"], cash["balance"]),
            ],
        },
        {
            "ticket": 102,
            "prompt": "Ticket 102: Elm City Properties says rent is due. Ticket 102 links to lease 1. "
                      "How much is the rent, when is it due, how many days away is that from the "
                      "shop's date, and how much cash does the shop have?",
            "why": "Elm City Properties rent notice links to lease 1.",
            "tool": "get_lease",
            "args": {"lease_id": 1},
            "checks": lambda r: [
                check("found", r.get("found"), True),
                check("monthly_rent", r["lease"]["monthly_rent"], lease["monthly_rent"]),
                check("next_due", r["lease"]["next_due"], lease["next_due"]),
                check("days_until_due", r.get("days_until_due"),
                      (datetime.fromisoformat(lease["next_due"]) - datetime.fromisoformat(today)).days),
                check("is_overdue", r.get("is_overdue"), False),
                check("cash balance", r["cash_accounts"][0]["balance"], cash["balance"]),
            ],
        },
        {
            "ticket": None,
            "prompt": "How many navy hoodies (CC-HOOD-NAVY) in size XXL are on the shelf?",
            "why": "No-invented-data check: a size that does not exist.",
            "tool": "check_stock",
            "args": {"sku": "CC-HOOD-NAVY", "size": "XXL"},
            "checks": lambda r: [check("found", r.get("found"), False)],
        },
        {
            "ticket": None,
            "prompt": "Look up invoice 999.",
            "why": "No-invented-data check: an invoice that does not exist.",
            "tool": "get_invoice",
            "args": {"invoice_id": 999},
            "checks": lambda r: [check("found", r.get("found"), False)],
        },
        {
            "ticket": None,
            "prompt": "Look up lease 99.",
            "why": "No-invented-data check: a lease that does not exist.",
            "tool": "get_lease",
            "args": {"lease_id": 99},
            "checks": lambda r: [check("found", r.get("found"), False)],
        },
    ]

    calls = []
    async with Client(config) as client:
        listed = [t.name for t in await client.list_tools()]
        for step in plan:
            res = await client.call_tool(step["tool"], step["args"])
            data = res.structured_content
            if isinstance(data, dict) and set(data) == {"result"}:
                data = data["result"]
            checks = step["checks"](data)
            calls.append({
                "prompt": step["prompt"],
                "tool": step["tool"],
                "arguments": step["args"],
                "output": data,
                "ticket": step["ticket"],
                "why": step["why"],
                "database_checks": checks,
                "matches_database": all(c["pass"] for c in checks),
                "pass": all(c["pass"] for c in checks),
            })

    after = {"campus_customs_new.db": sha256(DB), "campus_customs.db": sha256(ORIGINAL)}
    evidence = {
        "test": "MCP smoke test: each Campus Customs tool called over MCP",
        "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "how": "Server launched over stdio from .mcp.json; each prompt was answered by calling "
               "the named tool through an MCP client; every output value was compared with "
               "the same value read directly from data/campus_customs_new.db.",
        "database": "data/campus_customs_new.db",
        "server_name": name,
        "mcp_config": json.loads((ROOT / ".mcp.json").read_text()),
        "tools_listed": listed,
        "shop_today": today,
        "calls": calls,
        "database_sha256_before": before,
        "database_sha256_after": after,
        "database_unchanged": before == after,
        "summary": {
            "calls": len(calls),
            "passed": sum(c["pass"] for c in calls),
            "all_three_tools_called": sorted({c["tool"] for c in calls}) == sorted(listed),
            "all_pass": all(c["pass"] for c in calls) and before == after,
        },
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2))
    s = evidence["summary"]
    print(f"{s['passed']}/{s['calls']} calls passed; tools listed: {listed}; "
          f"database unchanged: {evidence['database_unchanged']}; saved {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
