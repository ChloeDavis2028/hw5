# Campus Customs MCP server

## What it's for

This server is the agent team's only way into the shop's data. The Boss, Inventory, Accounting, Facilities and Customer Service agents never open the database themselves. They call these tools, so every agent sees the same facts and nothing is made up. A missing row comes back as `found: false`.

## Database

- **Uses:** `data/campus_customs_new.db`, the working copy. Look-up tools open it **read-only**. Only the human-only pay tool writes.
- **Leaves alone:** `data/campus_customs.db`, the untouched original kept for resets.
- **Today:** all day counts use `desk.date_today`, not the computer clock.
- **Tests:** set `CAMPUS_DB` to point the server at a throwaway copy.

## The tools (12)

| # | Tool | Returns | Tables | Ticket | Who gets it |
|---|---|---|---|---|---|
| 1 | `check_stock(sku, size)` | Units on the shelf for that SKU and size, plus unit cost, list price and margin | `inventory`, `pricing` | 103 (8 size-M hoodies vs 20 asked, $36 margin), 101 | All agents |
| 2 | `get_invoice(invoice_id)` | The invoice, days overdue, the vendor and its lead time, whether the vendor can ship, cash | `invoices`, `vendors`, `desk`, `cash_accounts` | 101 (invoice 501, $840, 3 days overdue) | All agents |
| 3 | `get_lease(lease_id)` | The lease, rent, next due date, days until due, cash | `leases`, `desk`, `cash_accounts` | 102 ($2,400 due 2026-09-02) | All agents |
| 4 | `get_open_tickets()` | Every open ticket and its links | `tickets`, `desk` | 101, 102, 103 | All agents |
| 5 | `get_ticket(ticket_id)` | One ticket in full | `tickets`, `desk` | Each ticket | All agents |
| 6 | `list_vendors()` | Vendors, specialty, lead days, open invoices, `can_ship` | `vendors`, `invoices` | 101, 103 (Bulldog Print Co can't ship) | All agents |
| 7 | `get_cash_position()` | Cash, every open invoice and rent due, total owed, cash left if all are paid | `cash_accounts`, `invoices`, `vendors`, `leases`, `desk` | 101, 102 ($3,400 − $3,240 = $160) | All agents |
| 8 | `pay_approved_request(kind, ref_id, approved_by, second_approver, sku, size, qty)` | Pays an invoice, a month's rent, or a restock purchase order (qty × unit cost). The amount comes from the database. Refuses if cash would go negative, the invoice is already paid, no approver is given, a payment over $1,000 lacks a different second approver, or the vendor still has an unpaid invoice. | Writes `invoices` or `leases`, `cash_accounts`, `payments`; reads `vendors`, `pricing`, `inventory` | 101, 102, 103 restock, after a person approves | **Human-only.** Only `POST /api/approvals` calls it. Agents never get it. |
| 9 | `list_tickets()` | Every ticket, open or resolved, with the safety screen | `tickets`, `desk` | 101, 102, 103 (the dashboard's board) | Backend routes, all agents |
| 10 | `mark_ticket_resolved(ticket_id)` | Sets a ticket resolved when its run finishes | writes `tickets` | all | **Backend only** |
| 11 | `save_drafts(ticket_id, run_id, drafts)` | Saves a run's replies on the board (never sent) | writes `ticket_drafts` | all | **Backend only** |
| 12 | `get_drafts(ticket_id)` | The saved replies for one ticket | `ticket_drafts` | all | **Backend only** |

The pay tool also **refuses purchase orders that would leave less than $500** (owner's rule 13), unless the owner overrides through the signed-in approve route. Ticket screens also flag "new bank details" requests.

## Run

```bash
pip install -r requirements.txt
python mcp_server/server.py
```

Claude Code connects through `.mcp.json` at the project root. The agent team connects through `backend/team.py`.
