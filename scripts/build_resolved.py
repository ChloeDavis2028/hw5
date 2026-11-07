"""Build the 'after the run' evidence from real data (never hand-edited):

  - output/desk_tickets.html : fills each ticket's Actual section (agents, hand-offs,
                               tools, compared with Expected) and the Cash tab
  - output/resolved_tickets.json : per ticket: status, outcome, each agent's part, approvals
  - output/resolved_board.html : double-click page with a board screenshot per ticket
                                 (screenshots come from output/screenshots/ticket_<id>.png)

Data comes from output/audit_trail.json (runs since the last reset) and the
database (read-only). Run from My Work after resetting, running all three
tickets, and approving on the board:

    .venv/Scripts/python scripts/build_resolved.py
"""

import base64
import html
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
TRAIL = OUT / "audit_trail.json"
DESK = OUT / "desk_tickets.html"
SHOTS = OUT / "screenshots"
ORIGINAL_DB = ROOT / "data" / "campus_customs.db"
WORKING_DB = ROOT / "data" / "campus_customs_new.db"
TICKETS = [101, 102, 103]
SKIP_TOOLS = {"ask_teammate", "final_result"}
LABEL = {"boss": "Boss", "inventory": "Inventory", "accounting": "Accounting",
         "facilities": "Facilities", "customer_service": "Customer Service"}
KIND = {"invoice_payment": "Invoice payment", "rent_payment": "Rent payment", "purchase_order": "Purchase order"}

# The Problem 6 plan (Expected), so the comparison is checked in code, not by eye.
EXPECTED = {
    101: {"first": "inventory", "handoffs": ["inventory", "accounting", "customer_service"], "not_called": ["facilities"],
          "tools": {"get_ticket": 1, "check_stock": 4, "list_vendors": 1, "get_cash_position": 1, "get_invoice": 1}},
    102: {"first": "facilities", "handoffs": ["facilities", "accounting", "customer_service"], "not_called": ["inventory"],
          "tools": {"get_ticket": 1, "get_lease": 1, "get_cash_position": 1}},
    103: {"first": "inventory", "handoffs": ["inventory", "accounting", "customer_service"], "not_called": ["facilities"],
          "tools": {"get_ticket": 1, "check_stock": 5, "list_vendors": 1, "get_cash_position": 1}},
}


def db_one(path: Path, sql: str, args=()):
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def money(x: float) -> str:
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def collect() -> dict:
    trail = json.loads(TRAIL.read_text(encoding="utf-8"))
    resets = [i for i, e in enumerate(trail) if e["event"] == "database_reset"]
    start_idx = resets[-1] + 1 if resets else 0
    after = trail[start_idx:]
    reset_at = trail[resets[-1]]["at_utc"] if resets else None

    runs = {}
    for e in after:  # latest finished run per ticket since the reset
        if e["event"] == "ticket_done" and e.get("ticket_id") in TICKETS:
            runs[e["ticket_id"]] = e
    resolved_at = {e["ticket_id"]: e["at_utc"] for e in after if e["event"] == "ticket_resolved"}

    approvals = [e for e in after if e["event"] in ("human_approval", "human_rejection")]
    # Credit each payment to the ticket it belongs to: the ticket that links to that
    # invoice or lease. Two tickets can propose the same invoice, and it counts once.
    links = {r["id"]: dict(r) for r in db_one(WORKING_DB, "SELECT id, invoice_id, lease_id FROM tickets")}
    for a in approvals:
        owner = None
        for tid in TICKETS:
            l = links.get(tid, {})
            if (a.get("kind") == "invoice_payment" and l.get("invoice_id") == a.get("ref_id")) or \
               (a.get("kind") == "rent_payment" and l.get("lease_id") == a.get("ref_id")):
                owner = tid
                break
        a["ticket_id"] = owner or a.get("ticket_id")

    tickets = {}
    for tid in TICKETS:
        done = runs.get(tid)
        if not done:
            tickets[tid] = None
            continue
        rid = done["run_id"]
        entries = [e for e in after if e["run_id"] == rid]
        worked = []
        for e in entries:
            if e["event"] == "agent_start" and e["role"] not in worked:
                worked.append(e["role"])
        tools: dict[str, dict[str, int]] = {}
        for e in entries:
            if e["event"] == "loop_step_reply":
                for p in e.get("parts", []):
                    if p.get("kind") == "tool_call" and p.get("tool") not in SKIP_TOOLS:
                        tools.setdefault(e["role"], {})
                        tools[e["role"]][p["tool"]] = tools[e["role"]].get(p["tool"], 0) + 1
        final_words = {}
        for e in entries:
            if e["event"] == "agent_done":
                o = e.get("output") or {}
                final_words[e["role"]] = o.get("summary") or o.get("decision") or ""
        d = done["decision"]
        tickets[tid] = {
            "run_id": rid, "finished_at_utc": done["at_utc"], "resolved_at_utc": resolved_at.get(tid),
            "decision": d, "delegations": done.get("delegations", []), "cost": done.get("cost") or {},
            "worked": worked, "tools": tools, "final_words": final_words,
            "approvals": [a for a in approvals if a.get("ticket_id") == tid],
        }

    start_cash = db_one(ORIGINAL_DB, "SELECT balance FROM cash_accounts WHERE name='checking'")[0]["balance"]
    end_cash = db_one(WORKING_DB, "SELECT balance FROM cash_accounts WHERE name='checking'")[0]["balance"]
    payments = [dict(r) for r in db_one(WORKING_DB, "SELECT * FROM payments ORDER BY id")]
    statuses = {r["id"]: r["status"] for r in db_one(WORKING_DB, "SELECT id, status FROM tickets")}
    return {"reset_at": reset_at, "tickets": tickets, "start_cash": start_cash, "end_cash": end_cash,
            "payments": payments, "statuses": statuses, "links": links}


def compare(tid: int, t: dict) -> dict:
    exp = EXPECTED[tid]
    handoffs = [d["to_role"] for d in t["delegations"] if d["from_role"] == "boss" and d["outcome"] == "answered"]
    side = [d for d in t["delegations"] if d["from_role"] != "boss" and d["outcome"] == "answered"]
    refused = [d for d in t["delegations"] if d["outcome"] != "answered"]
    flat: dict[str, int] = {}
    for per in t["tools"].values():
        for k, v in per.items():
            flat[k] = flat.get(k, 0) + v
    return {
        "first_expected": exp["first"], "first_actual": handoffs[0] if handoffs else None,
        "first_match": bool(handoffs) and handoffs[0] == exp["first"],
        "handoffs_expected": exp["handoffs"], "handoffs_actual": handoffs, "handoffs_match": handoffs == exp["handoffs"],
        "not_called_expected": exp["not_called"],
        "not_called_respected": all(r not in t["worked"] for r in exp["not_called"]),
        "specialist_to_specialist": [f"{d['from_role']}->{d['to_role']}" for d in side],
        "refused_attempts": [f"{d['from_role']}->{d['to_role']} ({d['outcome']})" for d in refused],
        "tools_expected": exp["tools"], "tools_actual": flat,
    }


def mark(ok: bool) -> str:
    return '<span class="ok">✓ matches</span>' if ok else '<span class="miss">✗ differs</span>'


def actual_html(tid: int, t: dict | None, cmp: dict | None) -> str:
    if not t:
        return '<h3><span class="label act">Actual</span></h3><p class="blank">No run since the last reset.</p>'
    d = t["decision"]
    rows = []
    for role in t["worked"]:
        tl = t["tools"].get(role, {})
        tools = " ".join(f"<code>{esc(k)}</code>{' ×' + str(v) if v > 1 else ''}" for k, v in tl.items()) or "<em>none</em>"
        rows.append(f"<tr><td><strong>{esc(LABEL.get(role, role))}</strong></td><td class='tools'>{tools}</td>"
                    f"<td>{esc(t['final_words'].get(role, ''))[:260]}</td></tr>")
    deleg = "".join(f"<li>{esc(LABEL.get(x['from_role']))} → <strong>{esc(LABEL.get(x['to_role']))}</strong> "
                    f"<span class='meta'>({esc(x['outcome'])})</span>: {esc(x['request'])[:200]}</li>" for x in t["delegations"])
    tool_rows = []
    names = list(dict.fromkeys(list(cmp["tools_expected"]) + list(cmp["tools_actual"])))
    for n in names:
        e, a = cmp["tools_expected"].get(n, 0), cmp["tools_actual"].get(n, 0)
        tool_rows.append(f"<tr><td><code>{esc(n)}</code></td><td class='num'>{e}</td><td class='num'>{a}</td>"
                         f"<td>{mark(e == a)}</td></tr>")
    side = ", ".join(cmp["specialist_to_specialist"]) or "none"
    appr = "".join(f"<li>{esc(a['event'].replace('human_', '').title())}: {esc(KIND.get(a.get('kind'), a.get('kind')))} "
                   f"{esc(a.get('ref_id'))} by {esc(a.get('approved_by') or a.get('rejected_by'))}"
                   f"{' → ' + money((a.get('result') or {}).get('amount', 0)) + ' paid, checking ' + money((a.get('result') or {}).get('balance_after', 0)) if (a.get('result') or {}).get('paid') else ''}</li>"
                   for a in t["approvals"]) or "<li>None yet. Payments still wait on the board.</li>"
    return f"""<h3><span class="label act">Actual</span> <span class="meta">run {esc(t['run_id'])} · {esc(t['finished_at_utc'][:19].replace('T', ' '))} UTC · from output/audit_trail.json</span></h3>
    <p><span class="pill {'needs' if d['status'] == 'needs_approval' else 'wait'}">{esc(d['status'])}</span> <strong>Ticket: {esc('resolved' if t['resolved_at_utc'] else 'open')}</strong>. {esc(d['decision'])}</p>
    <h4>Expected vs. actual</h4>
    <div class="scroll"><table>
      <tr><th>Check</th><th>Expected (Problem 6)</th><th>Actual (this run)</th><th></th></tr>
      <tr><td>Boss calls first</td><td>{esc(LABEL[cmp['first_expected']])}</td><td>{esc(LABEL.get(cmp['first_actual'], cmp['first_actual']))}</td><td>{mark(cmp['first_match'])}</td></tr>
      <tr><td>Hand-offs from the Boss</td><td>{' → '.join(LABEL[x] for x in cmp['handoffs_expected'])}</td><td>{' → '.join(LABEL.get(x, x) for x in cmp['handoffs_actual'])}</td><td>{mark(cmp['handoffs_match'])}</td></tr>
      <tr><td>Not called</td><td>{', '.join(LABEL[x] for x in cmp['not_called_expected'])}</td><td>{'not called' if cmp['not_called_respected'] else 'was called'}</td><td>{mark(cmp['not_called_respected'])}</td></tr>
      <tr><td>Specialist → specialist hand-offs</td><td>none</td><td>{esc(side)}</td><td>{mark(not cmp['specialist_to_specialist'])}</td></tr>
      <tr><td>Hand-offs refused by the loop guard</td><td>none</td><td>{esc(', '.join(cmp['refused_attempts']) or 'none')}</td><td>{mark(not cmp['refused_attempts'])}</td></tr>
    </table></div>
    <h4>Which agents worked and which tools they used</h4>
    <div class="scroll"><table><tr><th>Agent</th><th>MCP tools</th><th>What it reported</th></tr>{''.join(rows)}</table></div>
    <h4>What they delegated</h4><ul>{deleg or '<li>none</li>'}</ul>
    <h4>MCP tool calls: expected vs. actual</h4>
    <div class="scroll"><table><tr><th>Tool</th><th>Expected</th><th>Actual</th><th></th></tr>{''.join(tool_rows)}</table></div>
    <h4>Payments proposed · human approvals</h4>
    <ul>{''.join(f"<li>{esc(KIND.get(a['kind'], a['kind']))} {esc(a.get('ref_id'))}: {esc(a['payee'])} {money(a['amount'])} (cash after, as proposed: {money(a['cash_after']) if a.get('cash_after') is not None else '—'})</li>" for a in d.get('approval_requests', [])) or '<li>No payment proposed.</li>'}</ul>
    <ul>{appr}</ul>
    <div class="tally"><span>{len(t['delegations'])} hand-offs</span><span>{sum(cmp['tools_actual'].values())} MCP calls</span><span>{t['cost'].get('requests', '—')} model calls</span><span>cost ${t['cost'].get('cost_usd', 0):.4f}</span></div>"""


def owner_of(p: dict, data: dict):
    """Which ticket a proposed payment belongs to (the ticket linked to that invoice or lease)."""
    for tid, l in data["links"].items():
        if (p.get("kind") == "invoice_payment" and l.get("invoice_id") == p.get("ref_id")) or \
           (p.get("kind") == "rent_payment" and l.get("lease_id") == p.get("ref_id")):
            return tid
    return None


def cash_html(data: dict) -> str:
    rows, bal = [], data["start_cash"]
    order = sorted([tid for tid in TICKETS if data["tickets"].get(tid)],
                   key=lambda x: data["tickets"][x]["resolved_at_utc"] or data["tickets"][x]["finished_at_utc"])
    for tid in order:
        t = data["tickets"][tid]
        paid = [a for a in t["approvals"] if a["event"] == "human_approval" and (a.get("result") or {}).get("paid")]
        change = -sum(a["result"]["amount"] for a in paid)
        why = "; ".join(f"{KIND.get(a['kind'], a['kind'])} {a['ref_id']} to {a['proposal']['payee']} approved by {a['result']['approved_by']} ({money(a['result']['amount'])})" for a in paid)
        if not why:
            props = t["decision"].get("approval_requests", [])
            owned = [p for p in props if owner_of(p, data) in (tid, None)]
            shared = [p for p in props if owner_of(p, data) not in (tid, None)]
            parts = []
            if owned:
                parts.append("No payment approved yet. Proposed and waiting: " +
                             "; ".join(f"{KIND.get(p['kind'])} {p.get('ref_id')} {money(p['amount'])}" for p in owned))
            if shared:
                parts.append("; ".join(f"{KIND.get(p['kind'])} {p.get('ref_id')} ({money(p['amount'])}) also unblocks this ticket, "
                                       f"but it is counted once, under ticket {owner_of(p, data)}" for p in shared))
            why = " ".join(parts) if parts else "No payment or purchase needed for this ticket."
        bal = round(bal + change, 2)
        rows.append(f"<tr><td>Ticket {tid}</td><td>{esc(why)}</td><td class='num'>{money(change) if change else '$0.00'}</td><td class='num'><strong>{money(bal)}</strong></td></tr>")
    match = abs(bal - data["end_cash"]) < 0.005
    if not match:  # never save a statement that disagrees with the books
        raise SystemExit(f"Cash mismatch: itemized end ${bal:,.2f} vs cash_accounts ${data['end_cash']:,.2f}. "
                         "Nothing was written. Check the approvals in output/audit_trail.json.")
    pays = "".join(f"<tr><td>{p['id']}</td><td>{esc(p['kind'])}</td><td>{p['ref_id']}</td><td class='num'>{money(p['amount'])}</td><td>{esc(p['approved_by'])}</td><td>{esc(p['paid_at'])}</td></tr>" for p in data["payments"]) or "<tr><td colspan='6'>No rows. Nothing has been paid since the reset.</td></tr>"
    return f"""<div class="card">
    <h3><span class="label exp">Cash</span> <span class="meta">built from output/audit_trail.json and data/campus_customs_new.db · {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC</span></h3>
    <div class="scroll"><table>
      <tr><th>Step</th><th>Why cash changed (which payment or purchase, dollar amount)</th><th>Change</th><th>Checking after</th></tr>
      <tr><td>Start</td><td>Checking after the reset ({esc((data['reset_at'] or '')[:19].replace('T', ' '))} UTC), from <code>cash_accounts</code></td><td class='num'>—</td><td class='num'><strong>{money(data['start_cash'])}</strong></td></tr>
      {''.join(rows)}
      <tr><td><strong>End</strong></td><td>Itemized ending balance</td><td class='num'>{money(round(bal - data['start_cash'], 2))}</td><td class='num'><strong>{money(bal)}</strong></td></tr>
    </table></div>
    <p class="{'okbox' if match else 'missbox'}">{'✓' if match else '✗'} Ending checking <strong>{money(bal)}</strong> {'matches' if match else 'does NOT match'} <code>cash_accounts</code> in the working database: <strong>{money(data['end_cash'])}</strong>.</p>
    <h4>payments table (working database)</h4>
    <div class="scroll"><table><tr><th>#</th><th>Kind</th><th>Ref</th><th>Amount</th><th>Approved by</th><th>Paid (shop date)</th></tr>{pays}</table></div>
  </div>"""


EXTRA_CSS = """
  /* added by scripts/build_resolved.py */
  .ok { color: var(--ok); font-weight: 700; white-space: nowrap; }
  .miss { color: var(--bad); font-weight: 700; white-space: nowrap; }
  .okbox { margin-top: 12px; padding: 10px 14px; border-radius: 10px; background: var(--ok-bg); color: var(--ok); }
  .missbox { margin-top: 12px; padding: 10px 14px; border-radius: 10px; background: var(--bad-bg); color: var(--bad); }
  .actual { border-style: solid; }
"""


def fill_desk(data: dict, comparisons: dict) -> None:
    page = DESK.read_text(encoding="utf-8")
    if "added by scripts/build_resolved.py" not in page:
        page = page.replace("</style>", EXTRA_CSS + "</style>", 1)
    for tid in TICKETS:
        sec_start = page.index(f'<section class="tab" id="t{tid}"')
        sec_end = page.index("</section>", sec_start)
        sec = page[sec_start:sec_end]
        a = sec.index('<div class="card actual">')
        inner_start = a + len('<div class="card actual">')
        inner_end = sec.rindex("</div>")
        new_sec = sec[:inner_start] + "\n    " + actual_html(tid, data["tickets"].get(tid), comparisons.get(tid)) + "\n  " + sec[inner_end:]
        page = page[:sec_start] + new_sec + page[sec_end:]
    c_start = page.index('<section class="tab" id="cash"')
    c_open_end = page.index(">", c_start) + 1
    c_end = page.index("</section>", c_start)
    page = page[:c_open_end] + "\n  " + cash_html(data) + "\n" + page[c_end:]
    DESK.write_text(page, encoding="utf-8")


def resolved_json(data: dict, comparisons: dict) -> list:
    out = []
    for tid in TICKETS:
        t = data["tickets"].get(tid)
        if not t:
            out.append({"id": tid, "final_status": data["statuses"].get(tid), "outcome": "not run since the last reset"})
            continue
        d = t["decision"]
        out.append({
            "id": tid,
            "final_status": data["statuses"].get(tid),
            "team_call": d["status"],
            "outcome": d["decision"],
            "run_id": t["run_id"],
            "agents": [{"role": r, "tools": t["tools"].get(r, {}), "contribution": t["final_words"].get(r, "")} for r in t["worked"]],
            "delegations": [{"from": x["from_role"], "to": x["to_role"], "outcome": x["outcome"]} for x in t["delegations"]],
            "payments_proposed": d.get("approval_requests", []),
            "human_approvals": [{"action": a["event"].replace("human_", ""), "kind": a.get("kind"), "ref_id": a.get("ref_id"),
                                 "by": a.get("approved_by") or a.get("rejected_by"),
                                 "second_approver": a.get("second_approver") or None,
                                 "paid": (a.get("result") or {}).get("paid"), "amount": (a.get("result") or {}).get("amount"),
                                 "checking_after": (a.get("result") or {}).get("balance_after"),
                                 "message": (a.get("result") or {}).get("message"), "at_utc": a["at_utc"]} for a in t["approvals"]],
            "drafts": d.get("drafts", []),
            "cost_usd": t["cost"].get("cost_usd"),
            "expected_vs_actual": comparisons[tid],
        })
    (OUT / "resolved_tickets.json").write_text(json.dumps(
        {"built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "reset_at_utc": data["reset_at"],
         "checking_start": data["start_cash"], "checking_end_cash_accounts": data["end_cash"], "tickets": out}, indent=2),
        encoding="utf-8")
    return out


def board_page(summary: list) -> None:
    cards = []
    for t in summary:
        shot = SHOTS / f"ticket_{t['id']}.png"
        img = (f'<img alt="React board showing ticket {t["id"]}" src="data:image/png;base64,{base64.b64encode(shot.read_bytes()).decode()}">'
               if shot.exists() else '<p class="missing">Screenshot missing: run the screenshot step.</p>')
        appr = ", ".join(f"{a['action']} {a['kind']} {a['ref_id']} by {a['by']}" for a in t.get("human_approvals", [])) or "none yet"
        cards.append(f"""<section><div class="head"><div><div class="eyebrow">Ticket No. {t['id']}</div>
<h2>{esc(t.get('final_status', '')).title()} · team call: {esc(t.get('team_call', ''))}</h2></div>
<div class="facts"><span>Agents: {esc(', '.join(LABEL.get(a['role'], a['role']) for a in t.get('agents', [])))}</span>
<span>Approvals: {esc(appr)}</span><span>Cost: ${t.get('cost_usd') or 0:.4f}</span></div></div>
<p class="outcome">“{esc(t.get('outcome', ''))}”</p>{img}</section>""")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Resolved Board</title><style>
:root {{ --bg:#f1efec; --card:#fbfaf8; --ink:#23272e; --muted:#878a90; --line:#e0ddd8; --accent:#355373; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#16191e; --card:#1e2228; --ink:#e7e9ec; --muted:#9aa0a8; --line:#30353d; --accent:#a9c2dc; }} }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.55 "Segoe UI", -apple-system, Helvetica, Arial, sans-serif; }}
header {{ max-width:1200px; margin:0 auto; padding:28px 16px 8px; }} h1 {{ font:500 38px/1.1 Georgia, "Palatino Linotype", serif; margin:6px 0; }}
.eyebrow {{ font-size:11px; letter-spacing:.24em; text-transform:uppercase; color:var(--accent); font-weight:700; }}
main {{ max-width:1200px; margin:0 auto; padding:8px 16px 48px; }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:20px; margin:18px 0; }}
.head {{ display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; align-items:flex-end; }}
h2 {{ font:500 24px Georgia, serif; margin:4px 0; }} .facts {{ display:flex; flex-direction:column; gap:2px; color:var(--muted); font-size:13px; text-align:right; }}
.outcome {{ font:italic 17px/1.45 Georgia, serif; color:var(--ink); }}
img {{ width:100%; height:auto; border:1px solid var(--line); border-radius:10px; display:block; }}
.missing {{ color:#9a4a45; }} @media (max-width:700px) {{ .facts {{ text-align:left; }} }}
</style></head><body><header><div class="eyebrow">Campus Customs · The Back Office</div><h1>The resolved board</h1>
<p>One screenshot of the React board per resolved ticket, taken after the reset and the real agent runs. Built {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC by <code>scripts/build_resolved.py</code>.</p></header>
<main>{''.join(cards)}</main></body></html>"""
    (OUT / "resolved_board.html").write_text(page, encoding="utf-8")


def main() -> None:
    data = collect()
    comparisons = {tid: compare(tid, t) for tid, t in data["tickets"].items() if t}
    fill_desk(data, comparisons)
    summary = resolved_json(data, comparisons)
    board_page(summary)
    print(f"start {money(data['start_cash'])} -> end (cash_accounts) {money(data['end_cash'])}; "
          f"payments {len(data['payments'])}; tickets {data['statuses']}")
    for tid, c in comparisons.items():
        print(f"  {tid}: first {c['first_actual']} ({'ok' if c['first_match'] else 'DIFF'}), handoffs "
              f"{'ok' if c['handoffs_match'] else 'DIFF ' + str(c['handoffs_actual'])}, side {c['specialist_to_specialist'] or 'none'}, "
              f"refused {c['refused_attempts'] or 'none'}, "
              f"tools actual {c['tools_actual']}")


if __name__ == "__main__":
    main()
