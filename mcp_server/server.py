"""Campus Customs MCP server.

Every agent on the team (Boss, Inventory, Accounting, Facilities, Customer
Service) gets its shop data through the tools in this file, over the working
copy data/campus_customs_new.db. No tool makes up a value: when a row is
missing, the tool says it was not found.

All tools are read-only except pay_approved_request, which is human-only:
the agents never receive it, and the backend calls it only after a person
approves a payment on the dashboard.

Set CAMPUS_DB to point the server at a different copy (used by tests).

"Today" for the shop is desk.date_today, never the computer clock.

Run it later with:  python mcp_server/server.py
"""

import os
import sqlite3
from datetime import date
from pathlib import Path

from fastmcp import FastMCP

DB_PATH = Path(os.environ.get("CAMPUS_DB") or
               Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db")

mcp = FastMCP("Campus Customs Shop")


# ---------- helpers ----------

def _connect() -> sqlite3.Connection:
    """Open the working database read-only, so these tools can never change it."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _shop_today(conn: sqlite3.Connection) -> date:
    """The shop's 'today' from desk.date_today."""
    row = conn.execute("SELECT date_today FROM desk").fetchone()
    return date.fromisoformat(row["date_today"])


def _cash_accounts(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT name, balance, date FROM cash_accounts").fetchall()
    return [dict(r) for r in rows]


# ---------- tools ----------

@mcp.tool
def check_stock(sku: str, size: str) -> dict:
    """Check how many units of one product (SKU) in one size the shop has on
    the shelf, plus its unit cost, list price and margin per unit.

    Use it for customer orders and bulk or discount requests.
    Reads: inventory, pricing.
    """
    with _connect() as conn:
        item = conn.execute(
            "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()
        if item is None:
            sizes = [r["size"] for r in conn.execute(
                "SELECT size FROM inventory WHERE sku = ?", (sku,))]
            return {
                "found": False,
                "message": f"No inventory row for sku={sku!r}, size={size!r}.",
                "sizes_on_file_for_sku": sizes,
            }
        price = conn.execute(
            "SELECT unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()

    result = {"found": True, **dict(item)}
    if price is None:
        result["pricing"] = None
        result["pricing_message"] = f"No pricing row for sku={sku!r}."
    else:
        unit_cost, list_price = price["unit_cost"], price["list_price"]
        margin = list_price - unit_cost
        result["pricing"] = {
            "unit_cost": unit_cost,
            "list_price": list_price,
            "margin_per_unit": round(margin, 2),
            "margin_pct_of_list": round(100 * margin / list_price, 1) if list_price else None,
        }
    return result


@mcp.tool
def get_invoice(invoice_id: int) -> dict:
    """Look up one vendor invoice: amount, due date, status, and how many days
    it is overdue (counted from desk.date_today). Also returns the vendor's
    details, whether that vendor has any open invoice (an open invoice means
    the vendor will not ship new product), and the shop's cash balance.

    Use it when a ticket points to an invoice, or before ordering from a vendor.
    Reads: invoices, vendors, desk, cash_accounts.
    """
    with _connect() as conn:
        inv = conn.execute(
            "SELECT id, vendor_id, amount, due_date, status, description "
            "FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
        if inv is None:
            return {"found": False, "message": f"No invoice with id={invoice_id}."}
        today = _shop_today(conn)
        vendor = conn.execute(
            "SELECT id, name, specialty, lead_days FROM vendors WHERE id = ?",
            (inv["vendor_id"],),
        ).fetchone()
        open_invoices = [dict(r) for r in conn.execute(
            "SELECT id, amount, due_date FROM invoices WHERE vendor_id = ? AND status = 'open'",
            (inv["vendor_id"],),
        )]
        cash = _cash_accounts(conn)

    days_past_due = (today - date.fromisoformat(inv["due_date"])).days
    return {
        "found": True,
        "shop_today": today.isoformat(),
        "invoice": dict(inv),
        "is_open": inv["status"] == "open",
        "days_overdue": max(days_past_due, 0),
        "is_overdue": inv["status"] == "open" and days_past_due > 0,
        "vendor": dict(vendor) if vendor else None,
        "vendor_open_invoices": open_invoices,
        "vendor_can_ship": len(open_invoices) == 0,
        "cash_accounts": cash,
    }


@mcp.tool
def get_lease(lease_id: int) -> dict:
    """Look up one shop lease: space, landlord, monthly rent, next due date,
    and how many days until rent is due (counted from desk.date_today).
    Also returns the shop's cash balance.

    Use it for rent notices and anything about the shop space.
    Reads: leases, desk, cash_accounts.
    """
    with _connect() as conn:
        lease = conn.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due, notes "
            "FROM leases WHERE id = ?",
            (lease_id,),
        ).fetchone()
        if lease is None:
            return {"found": False, "message": f"No lease with id={lease_id}."}
        today = _shop_today(conn)
        cash = _cash_accounts(conn)

    days_until_due = (date.fromisoformat(lease["next_due"]) - today).days
    return {
        "found": True,
        "shop_today": today.isoformat(),
        "lease": dict(lease),
        "days_until_due": days_until_due,
        "is_overdue": days_until_due < 0,
        "cash_accounts": cash,
    }


import re

# Phrases that try to give orders to the AI instead of asking the shop for
# something. Ticket text is a customer's words; a match marks it for a person.
_SUSPICIOUS = [
    (r"system\s*override|developer\s*mode|jailbreak", "claims system or developer authority"),
    (r"ignore (all |any |your |previous |the )*(rules|instructions)", "asks to ignore the rules"),
    (r"pre-?authori[sz]ed|no (human )?approval (is )?(needed|required)|skip (the )?approval",
     "tries to skip human approval"),
    (r"\bfrom the (shop )?owner\b|\bi am the owner\b|\bowner says\b", "claims to be the owner"),
    (r"pay_approved_request|approved_by|ref_id\s*=|call (the )?\w+_\w+ tool|\bcall pay", "names internal tools or fields"),
    (r"\b(send|wire|transfer|pay)\s+\$?\d[\d,]*(\.\d+)?\s+to\b", "asks to send money to someone"),
    (r"\b100\s*%\s*(off|discount)|\bfor free\b|\bfree of charge\b", "asks for a 100% discount or free goods"),
    (r"do not (mention|tell|report)|don't (mention|tell)|keep this (secret|quiet)", "asks to hide something"),
    (r"(new|updated|changed|different)\s+(bank|account|routing|wire|payment)\s*(details|number|info|information|account)?|pay (to|into) (this|our new|a new) account|wire (it|payment|funds) to", "asks to change where money is sent (call the vendor back first)"),
]


def _screen_text(*texts: str | None) -> list[str]:
    """Return a reason for each suspicious pattern found (empty list = clean)."""
    joined = " ".join(t for t in texts if t).lower()
    return [reason for pattern, reason in _SUSPICIOUS if re.search(pattern, joined)]


def _with_screen(ticket: dict) -> dict:
    flags = _screen_text(ticket.get("subject"), ticket.get("notes"), ticket.get("requester"))
    return {**ticket, "suspicious_text": flags, "needs_human_review": bool(flags)}


@mcp.tool
def get_open_tickets() -> dict:
    """List every open ticket on the board with its type, requester, subject and
    the links it carries (sku + size + qty, lease_id, invoice_id).

    The Boss starts here to see what needs handling.
    Reads: tickets, desk.
    """
    with _connect() as conn:
        today = _shop_today(conn)
        rows = [dict(r) for r in conn.execute(
            "SELECT id, type, requester, subject, sku, size, qty, lease_id, invoice_id, "
            "status, notes, created_at FROM tickets WHERE status = 'open' ORDER BY id"
        )]
    rows = [_with_screen(r) for r in rows]
    return {"shop_today": today.isoformat(), "count": len(rows), "tickets": rows,
            "flagged_for_review": [r["id"] for r in rows if r["needs_human_review"]]}


@mcp.tool
def list_tickets() -> dict:
    """List every ticket on the board, open or resolved, with its status and
    the same safety screen as get_ticket. The dashboard uses this to show
    which tickets are still open.
    Reads: tickets, desk.
    """
    with _connect() as conn:
        today = _shop_today(conn)
        rows = [_with_screen(dict(r)) for r in conn.execute(
            "SELECT id, type, requester, subject, sku, size, qty, lease_id, invoice_id, "
            "status, notes, created_at FROM tickets ORDER BY id"
        )]
    return {"shop_today": today.isoformat(), "count": len(rows), "tickets": rows,
            "open": sum(r["status"] == "open" for r in rows),
            "resolved": sum(r["status"] == "resolved" for r in rows)}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Read one ticket in full: who asked, what they want, and which SKU/size,
    lease or invoice it links to. Also screens the ticket's text: if it tries
    to give orders to the AI (fake authority, skip approval, pay someone, free
    goods, hide something), suspicious_text lists why and needs_human_review
    is true.

    Reads: tickets, desk.
    """
    with _connect() as conn:
        today = _shop_today(conn)
        row = conn.execute(
            "SELECT id, type, requester, subject, sku, size, qty, lease_id, invoice_id, "
            "status, notes, created_at FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()
    if row is None:
        return {"found": False, "message": f"No ticket with id={ticket_id}."}
    return {"found": True, "shop_today": today.isoformat(), "ticket": _with_screen(dict(row))}


@mcp.tool
def list_vendors() -> dict:
    """List every vendor with its specialty, lead time in days, its open invoices,
    and whether it can ship (a vendor with an open unpaid invoice cannot ship).

    Inventory uses this to pick who can restock a product and how fast.
    Reads: vendors, invoices.
    """
    with _connect() as conn:
        vendors = []
        for v in conn.execute("SELECT id, name, specialty, lead_days FROM vendors ORDER BY id"):
            open_inv = [dict(r) for r in conn.execute(
                "SELECT id, amount, due_date FROM invoices WHERE vendor_id = ? AND status = 'open'",
                (v["id"],),
            )]
            vendors.append({
                **dict(v),
                "open_invoices": open_inv,
                "can_ship": len(open_inv) == 0,
            })
    return {"count": len(vendors), "vendors": vendors}


@mcp.tool
def get_cash_position() -> dict:
    """Show the shop's cash and everything it owes: each cash account, every open
    invoice (with days overdue), every lease's next rent (with days until due),
    the total owed, and what cash would be left if all of it were paid.

    Accounting uses this before proposing any payment. Cash only goes out in
    this shop; no revenue is modeled.
    Also lists the most recent payments (newest first).
    Reads: cash_accounts, invoices, vendors, leases, payments, desk.
    """
    with _connect() as conn:
        today = _shop_today(conn)
        cash = _cash_accounts(conn)
        invoices = []
        for r in conn.execute(
            "SELECT i.id, i.amount, i.due_date, i.description, v.name AS vendor "
            "FROM invoices i JOIN vendors v ON v.id = i.vendor_id WHERE i.status = 'open' ORDER BY i.due_date"
        ):
            overdue = (today - date.fromisoformat(r["due_date"])).days
            invoices.append({**dict(r), "days_overdue": max(overdue, 0), "is_overdue": overdue > 0})
        rents = []
        for r in conn.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due FROM leases ORDER BY next_due"
        ):
            until = (date.fromisoformat(r["next_due"]) - today).days
            rents.append({**dict(r), "days_until_due": until, "is_overdue": until < 0})
        payments = [dict(r) for r in conn.execute(
            "SELECT id, kind, ref_id, amount, account, paid_at, approved_by FROM payments ORDER BY id DESC LIMIT 20"
        )]

    total_cash = sum(a["balance"] for a in cash)
    total_owed = sum(i["amount"] for i in invoices) + sum(r["monthly_rent"] for r in rents)
    return {
        "shop_today": today.isoformat(),
        "cash_accounts": cash,
        "total_cash": round(total_cash, 2),
        "open_invoices": invoices,
        "rent_due": rents,
        "total_owed": round(total_owed, 2),
        "cash_left_if_all_paid": round(total_cash - total_owed, 2),
        "recent_payments": payments,
    }


# ---------- backend-only tools ----------
# The agents never get these tools (backend/team.py filters them out). Only
# the backend calls them: the pay tool after a person clicks Approve, and the
# resolve tool when a team run on a ticket has finished.

HUMAN_ONLY_TOOLS = {"pay_approved_request", "mark_ticket_resolved", "save_drafts", "get_drafts"}


def _connect_write() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool
def mark_ticket_resolved(ticket_id: int) -> dict:
    """BACKEND-ONLY. Mark a ticket resolved after the agent team finished its run.
    Agents never get this tool. It changes only tickets.status (open -> resolved);
    any payment the run proposed still waits for a human on the dashboard.
    Reads and writes: tickets.
    """
    conn = _connect_write()
    try:
        row = conn.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"updated": False, "message": f"No ticket with id={ticket_id}."}
        if row["status"] == "resolved":
            return {"updated": False, "ticket_id": ticket_id, "status": "resolved",
                    "message": "Already resolved."}
        with conn:
            conn.execute("UPDATE tickets SET status = 'resolved' WHERE id = ?", (ticket_id,))
        return {"updated": True, "ticket_id": ticket_id, "status_before": row["status"], "status": "resolved"}
    finally:
        conn.close()


SECOND_APPROVER_OVER = 1000.0  # owner's rule 24: payments over $1,000 need two different people
CASH_CUSHION = 500.0          # owner's rule 13: optional spending should leave at least this much


@mcp.tool
def pay_approved_request(kind: str, ref_id: int, approved_by: str, account: str = "checking",
                         second_approver: str = "", sku: str = "", size: str = "", qty: int = 0,
                         owner_override_cushion: bool = False) -> dict:
    """HUMAN-ONLY. Pay an invoice, a month's rent, or a restock purchase order,
    after a person clicked Approve. Agents never get this tool.

    kind:
      "invoice"         ref_id = invoices.id  (amount = the invoice amount)
      "rent"            ref_id = leases.id    (amount = the monthly rent)
      "purchase_order"  ref_id = vendors.id, plus sku, size, qty
                        (amount = qty x pricing.unit_cost; the vendor must be able
                        to ship, i.e. have no open unpaid invoice)
    The amount always comes from the database, never from the caller.

    Refuses if: no approver; a payment over $1,000 without a different second
    approver; the account would go negative; the invoice is already paid; or the
    row doesn't exist. On success, in one transaction: lowers the cash balance,
    writes a payments row, and marks the invoice paid / moves the lease's
    next_due forward one month. A purchase order does not add stock yet: it
    arrives after the vendor's lead_days.
    Reads and writes: invoices, leases, vendors, pricing, inventory, cash_accounts, payments, desk.
    """
    approved_by = (approved_by or "").strip()
    second_approver = (second_approver or "").strip()
    if not approved_by:
        return {"paid": False, "message": "Refused: a person must approve (approved_by is blank)."}
    if kind not in ("invoice", "rent", "purchase_order"):
        return {"paid": False, "message": f"Refused: kind must be 'invoice', 'rent' or 'purchase_order', not {kind!r}."}

    conn = _connect_write()
    try:
        today = _shop_today(conn)
        detail: dict = {}
        if kind == "invoice":
            row = conn.execute("SELECT amount, status, vendor_id FROM invoices WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                return {"paid": False, "message": f"Refused: no invoice with id={ref_id}."}
            if row["status"] != "open":
                return {"paid": False, "message": f"Refused: invoice {ref_id} is already {row['status']}."}
            amount = row["amount"]
        elif kind == "rent":
            row = conn.execute("SELECT monthly_rent, next_due FROM leases WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                return {"paid": False, "message": f"Refused: no lease with id={ref_id}."}
            amount = row["monthly_rent"]
        else:
            vendor = conn.execute("SELECT id, name, lead_days FROM vendors WHERE id = ?", (ref_id,)).fetchone()
            if vendor is None:
                return {"paid": False, "message": f"Refused: no vendor with id={ref_id}."}
            blocking = conn.execute("SELECT id FROM invoices WHERE vendor_id = ? AND status = 'open'", (ref_id,)).fetchall()
            if blocking:
                return {"paid": False, "message": f"Refused: {vendor['name']} won't ship while invoice "
                                                  f"{', '.join(str(b['id']) for b in blocking)} is unpaid."}
            if not sku or not size or qty <= 0:
                return {"paid": False, "message": "Refused: a purchase order needs sku, size and qty > 0."}
            if conn.execute("SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)).fetchone() is None:
                return {"paid": False, "message": f"Refused: no inventory row for sku={sku!r}, size={size!r}."}
            price = conn.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)).fetchone()
            if price is None:
                return {"paid": False, "message": f"Refused: no unit cost for sku={sku!r}."}
            amount = round(qty * price["unit_cost"], 2)
            detail = {"vendor": vendor["name"], "sku": sku, "size": size, "qty": qty,
                      "unit_cost": price["unit_cost"], "lead_days": vendor["lead_days"]}

        if amount > SECOND_APPROVER_OVER and (not second_approver or second_approver.lower() == approved_by.lower()):
            return {"paid": False, "amount": amount,
                    "message": f"Refused: ${amount:,.2f} is over ${SECOND_APPROVER_OVER:,.0f}, so a second, "
                               "different person must approve too (owner's rule 24)."}

        acct = conn.execute("SELECT balance FROM cash_accounts WHERE name = ?", (account,)).fetchone()
        if acct is None:
            return {"paid": False, "message": f"Refused: no cash account named {account!r}."}
        if acct["balance"] - amount < 0:
            return {"paid": False, "balance": acct["balance"], "amount": amount,
                    "message": f"Refused: not enough cash. {account} has ${acct['balance']:.2f}, "
                               f"payment is ${amount:.2f}. Balances never go negative."}

        new_balance = round(acct["balance"] - amount, 2)
        if kind == "purchase_order" and new_balance < CASH_CUSHION and not owner_override_cushion:
            return {"paid": False, "amount": amount, "balance": acct["balance"],
                    "message": f"Refused: this purchase order would leave ${new_balance:,.2f}, below the ${CASH_CUSHION:,.0f} "
                               "cash cushion (owner's rule 13). Only the owner can override."}
        signers = approved_by + (f" + {second_approver}" if second_approver else "")
        with conn:  # one transaction: all of it happens, or none of it
            conn.execute("UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?",
                         (new_balance, today.isoformat(), account))
            if kind == "invoice":
                conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))
            elif kind == "rent":
                due = date.fromisoformat(row["next_due"])
                year, month = (due.year + 1, 1) if due.month == 12 else (due.year, due.month + 1)
                conn.execute("UPDATE leases SET next_due = ? WHERE id = ?",
                             (due.replace(year=year, month=month).isoformat(), ref_id))
            cur = conn.execute(
                "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
                (kind, ref_id, amount, account, today.isoformat(), signers),
            )
        result = {"paid": True, "payment_id": cur.lastrowid, "kind": kind, "ref_id": ref_id, "amount": amount,
                  "account": account, "balance_before": acct["balance"], "balance_after": new_balance,
                  "approved_by": signers, "paid_at": today.isoformat(), **detail}
        if kind == "purchase_order" and new_balance < CASH_CUSHION:
            result["warning"] = f"Owner override: cash is now ${new_balance:,.2f}, below the ${CASH_CUSHION:,.0f} cushion (owner's rule 13)."
        return result
    finally:
        conn.close()


@mcp.tool
def save_drafts(ticket_id: int, run_id: str, drafts: list[dict]) -> dict:
    """BACKEND-ONLY. Save a run's reply drafts on the board (table ticket_drafts).
    Drafts are never sent; staff read them on the dashboard. Replaces earlier drafts
    of the same ticket so the board always shows the latest set.
    Reads and writes: ticket_drafts (created if missing), tickets.
    """
    conn = _connect_write()
    try:
        if conn.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is None:
            return {"saved": 0, "message": f"No ticket with id={ticket_id}."}
        today = _shop_today(conn)
        with conn:
            conn.execute("CREATE TABLE IF NOT EXISTS ticket_drafts (id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL, "
                         "run_id TEXT NOT NULL, to_name TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL, "
                         "saved_on TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft', "
                         "FOREIGN KEY (ticket_id) REFERENCES tickets(id))")
            conn.execute("DELETE FROM ticket_drafts WHERE ticket_id = ?", (ticket_id,))
            for d in drafts:
                conn.execute("INSERT INTO ticket_drafts (ticket_id, run_id, to_name, subject, body, saved_on) VALUES (?, ?, ?, ?, ?, ?)",
                             (ticket_id, run_id, str(d.get("to", ""))[:200], str(d.get("subject", ""))[:300],
                              str(d.get("body", ""))[:5000], today.isoformat()))
        return {"saved": len(drafts), "ticket_id": ticket_id, "run_id": run_id}
    finally:
        conn.close()


@mcp.tool
def get_drafts(ticket_id: int) -> dict:
    """BACKEND-ONLY. The reply drafts saved on the board for one ticket (never sent).
    Reads: ticket_drafts.
    """
    with _connect() as conn:
        has = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ticket_drafts'").fetchone()
        if not has:
            return {"ticket_id": ticket_id, "drafts": []}
        rows = [dict(r) for r in conn.execute(
            "SELECT to_name, subject, body, saved_on, status, run_id FROM ticket_drafts WHERE ticket_id = ? ORDER BY id", (ticket_id,))]
    return {"ticket_id": ticket_id, "drafts": rows}


if __name__ == "__main__":
    mcp.run(show_banner=False)
