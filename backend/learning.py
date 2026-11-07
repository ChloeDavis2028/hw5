"""Run metrics for the learning department (the Flight Instructor).

Pure code, no AI: reads output/audit_trail.json, output/usage_log.json and the
working database (read-only) and turns them into numbers the Flight Instructor
can learn from. Plan vs. actual, wasted tool calls, cost trend, safety events, and
the cash check. Every number is computed here, so the agent never guesses.
"""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIL = ROOT / "output" / "audit_trail.json"
ORIGINAL_DB = ROOT / "data" / "campus_customs.db"
WORKING_DB = ROOT / "data" / "campus_customs_new.db"
SKIP_TOOLS = {"ask_teammate", "final_result"}
TICKETS = [101, 102, 103]

# The Problem 6 plan (Expected) for each real ticket.
EXPECTED = {
    101: {"first": "inventory", "handoffs": ["inventory", "accounting", "customer_service"], "not_called": ["facilities"],
          "tools": {"get_ticket": 1, "check_stock": 4, "list_vendors": 1, "get_cash_position": 1, "get_invoice": 1}},
    102: {"first": "facilities", "handoffs": ["facilities", "accounting", "customer_service"], "not_called": ["inventory"],
          "tools": {"get_ticket": 1, "get_lease": 1, "get_cash_position": 1}},
    103: {"first": "inventory", "handoffs": ["inventory", "accounting", "customer_service"], "not_called": ["facilities"],
          "tools": {"get_ticket": 1, "check_stock": 5, "list_vendors": 1, "get_cash_position": 1}},
}


def _ro(path: Path):
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def _trail() -> list[dict]:
    try:
        return json.loads(TRAIL.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _run_detail(trail: list[dict], done: dict) -> dict:
    rid = done["run_id"]
    entries = [e for e in trail if e["run_id"] == rid]
    tools: dict[str, dict[str, int]] = {}
    for e in entries:
        if e["event"] == "loop_step_reply":
            for p in e.get("parts", []):
                if p.get("kind") == "tool_call" and p.get("tool") not in SKIP_TOOLS:
                    tools.setdefault(e["role"], {})
                    tools[e["role"]][p["tool"]] = tools[e["role"]].get(p["tool"], 0) + 1
    flat: dict[str, int] = {}
    for per in tools.values():
        for k, v in per.items():
            flat[k] = flat.get(k, 0) + v
    cost = done.get("cost") or {}
    d = done.get("decision") or {}
    return {
        "run_id": rid, "ticket_id": done.get("ticket_id"), "at_utc": done["at_utc"],
        "status": d.get("status"), "drafts": len(d.get("drafts", [])), "approvals": len(d.get("approval_requests", [])),
        "handoffs": [x["to_role"] for x in done.get("delegations", []) if x["from_role"] == "boss" and x["outcome"] == "answered"],
        "side_handoffs": [f"{x['from_role']}->{x['to_role']}" for x in done.get("delegations", [])
                          if x["from_role"] != "boss" and x["outcome"] == "answered"],
        "refused": [f"{x['from_role']}->{x['to_role']} ({x['outcome']})" for x in done.get("delegations", []) if x["outcome"] != "answered"],
        "tools_by_agent": tools, "tools": flat, "tool_calls": sum(flat.values()),
        "model_calls": cost.get("requests"), "tokens": cost.get("total_tokens"), "cost_usd": cost.get("cost_usd"),
    }


def collect_metrics() -> dict:
    trail = _trail()
    resets = [i for i, e in enumerate(trail) if e["event"] == "database_reset"]
    since = trail[resets[-1] + 1:] if resets else trail

    all_runs = [_run_detail(trail, e) for e in trail if e["event"] == "ticket_done" and e.get("ticket_id") in TICKETS]
    latest = {}
    for e in since:
        if e["event"] == "ticket_done" and e.get("ticket_id") in TICKETS:
            latest[e["ticket_id"]] = _run_detail(trail, e)

    per_ticket = {}
    for tid, r in latest.items():
        exp = EXPECTED[tid]
        extra = {k: r["tools"].get(k, 0) - v for k, v in exp["tools"].items() if r["tools"].get(k, 0) != v}
        unexpected = {k: v for k, v in r["tools"].items() if k not in exp["tools"]}
        per_ticket[tid] = {
            **{k: r[k] for k in ("status", "model_calls", "tokens", "cost_usd", "tool_calls", "drafts", "refused", "side_handoffs")},
            "tools_by_agent": r["tools_by_agent"],
            "plan": {
                "first_ok": bool(r["handoffs"]) and r["handoffs"][0] == exp["first"],
                "handoffs_ok": r["handoffs"] == exp["handoffs"],
                "not_called_ok": all(n not in r["handoffs"] for n in exp["not_called"]),
                "tool_calls_expected": sum(exp["tools"].values()), "tool_calls_actual": r["tool_calls"],
                "tool_differences": extra, "unexpected_tools": unexpected,
            },
        }

    history = {}
    for tid in TICKETS:
        runs = [r for r in all_runs if r["ticket_id"] == tid and r["cost_usd"] is not None]
        if runs:
            history[tid] = {"runs": len(runs),
                            "first_cost_usd": runs[0]["cost_usd"], "latest_cost_usd": runs[-1]["cost_usd"],
                            "avg_cost_usd": round(sum(r["cost_usd"] for r in runs) / len(runs), 6),
                            "first_tool_calls": runs[0]["tool_calls"], "latest_tool_calls": runs[-1]["tool_calls"]}

    safety = {k: sum(1 for e in trail if e["event"] == k)
              for k in ("blocked_human_only_tool", "security_review_enforced", "cap_hit", "delegation_refused")}

    with _ro(WORKING_DB) as c:
        end = c.execute("SELECT balance FROM cash_accounts WHERE name='checking'").fetchone()[0]
        paid = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments").fetchone()[0]
        payments = [dict(zip(("kind", "ref_id", "amount", "approved_by"), r))
                    for r in c.execute("SELECT kind, ref_id, amount, approved_by FROM payments ORDER BY id")]
    with _ro(ORIGINAL_DB) as c:
        start = c.execute("SELECT balance FROM cash_accounts WHERE name='checking'").fetchone()[0]

    latest_costs = [r["cost_usd"] for r in latest.values() if r["cost_usd"] is not None]
    return {
        "tickets_since_reset": per_ticket,
        "board_cost_usd": round(sum(latest_costs), 6) if latest_costs else None,
        "history": history,
        "total_ticket_runs_logged": len(all_runs),
        "safety_events_all_time": safety,
        "cash": {"start": start, "end_cash_accounts": end, "payments_total": paid,
                 "matches": abs(start - paid - end) < 0.005, "payments": payments},
    }


# ---------------- the continuous report ----------------

LOG = ROOT / "output" / "learning_feedback.json"
REPORT = ROOT / "output" / "learning_report.html"
NAMES = {"boss": "Boss", "inventory": "Inventory", "accounting": "Accounting", "facilities": "Facilities",
         "customer_service": "Customer Service", "learning": "Flight Instructor"}
CREW = {"boss": "Captain", "inventory": "Cargo master", "accounting": "Purser", "facilities": "Ground crew",
        "customer_service": "Cabin crew"}

CSS = """
:root { --bg:#f1efec; --card:#fbfaf8; --ink:#23272e; --soft:#4b515b; --muted:#878a90; --line:#e0ddd8; --accent:#4f6f92; --deep:#355373; --wash:#e5ebf2; --ok:#5d7a6c; --okw:#e6eee9; --bad:#9a4a45; --badw:#f4e5e3; }
@media (prefers-color-scheme: dark) { :root { --bg:#16191e; --card:#1e2228; --ink:#e7e9ec; --soft:#c2c7ce; --muted:#9aa0a8; --line:#30353d; --accent:#8fb0d3; --deep:#a9c2dc; --wash:#243244; --ok:#8fc1a6; --okw:#1f3329; --bad:#e0a19c; --badw:#3a2422; } }
* { box-sizing:border-box; } body { margin:0; background:var(--bg); color:var(--ink); font:14.5px/1.55 "Segoe UI",-apple-system,Helvetica,Arial,sans-serif; }
header, main { max-width:1200px; margin:0 auto; padding:0 16px; } header { padding-top:28px; }
.eyebrow { font-size:10.5px; letter-spacing:.24em; text-transform:uppercase; color:var(--deep); font-weight:700; }
h1 { font:500 40px/1.1 Georgia,"Palatino Linotype",serif; margin:6px 0; } h1 em { color:var(--accent); }
h2 { font:500 24px Georgia,serif; margin:32px 0 10px; padding-bottom:6px; border-bottom:1px solid var(--line); }
.headline { font:italic 20px/1.45 Georgia,serif; color:var(--soft); max-width:900px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px; margin-bottom:12px; }
.scroll { overflow-x:auto; background:var(--card); border:1px solid var(--line); border-radius:14px; }
table { width:100%; border-collapse:collapse; font-size:13.5px; } th, td { text-align:left; padding:9px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
th { font-size:10.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); } .num { font-variant-numeric:tabular-nums; white-space:nowrap; }
.ok { color:var(--ok); font-weight:700; } .no { color:var(--bad); font-weight:700; } .ev { color:var(--muted); font-size:12.5px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:12px; }
.th { display:flex; gap:12px; align-items:flex-start; } .th p { margin:4px 0 0; }
.g { display:inline-grid; place-items:center; min-width:26px; height:22px; padding:0 6px; border-radius:6px; font:700 12px/1 "Segoe UI",sans-serif; background:var(--wash); color:var(--deep); }
.g.big { min-width:42px; height:42px; font:500 24px Georgia,serif; border-radius:50%; }
.gA { background:var(--okw); color:var(--ok); } .gD, .gF { background:var(--badw); color:var(--bad); } .gnotcalled { background:transparent; color:var(--muted); border:1px solid var(--line); }
.agents { list-style:none; padding:0; margin:12px 0 0; } .agents li { padding:6px 0; border-top:1px solid var(--line); } .crew { color:var(--muted); font-style:italic; }
.tag { display:inline-block; padding:2px 9px; border-radius:999px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; background:var(--wash); color:var(--deep); }
.tag.fixed { background:var(--okw); color:var(--ok); } .tag.repeated { background:var(--badw); color:var(--bad); }
.facts { display:flex; gap:28px; flex-wrap:wrap; } .fact b { display:block; font:500 24px Georgia,serif; } .fact span { font-size:10.5px; letter-spacing:.18em; text-transform:uppercase; color:var(--muted); }
footer { max-width:1200px; margin:24px auto 40px; padding:0 16px; color:var(--muted); font-size:12px; }
"""


def _e(s) -> str:
    import html as _h
    return _h.escape(str(s if s is not None else ""))


def _ok(b: bool) -> str:
    return '<span class="ok">✓</span>' if b else '<span class="no">✗</span>'


def _money4(x) -> str:
    return "—" if x is None else f"${x:.4f}"


def _ticket(m: dict, tid: int):
    t = m["tickets_since_reset"]
    return t.get(tid) or t.get(str(tid))


def build_report() -> Path:
    """Rebuild output/learning_report.html from every debrief so far (double-click to open)."""
    try:
        history = json.loads(LOG.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    if not history:
        REPORT.write_text("<!doctype html><meta charset='utf-8'><title>Crew Debrief</title><p>No debriefs yet.</p>", encoding="utf-8")
        return REPORT
    latest = history[-1]
    m, r = latest["metrics"], latest["report"]
    applied = latest.get("applied_updates", [])

    rows = []
    for tid in TICKETS:
        t = _ticket(m, tid)
        if not t:
            continue
        exp, p = EXPECTED[tid], t["plan"]
        diffs = ", ".join(f"{k} {'+' if v > 0 else ''}{v}" for k, v in p["tool_differences"].items()) or "none"
        rows.append(
            f"<tr><td><strong>{tid}</strong></td>"
            f"<td>{NAMES[exp['first']]} {_ok(p['first_ok'])}</td>"
            f"<td>{' → '.join(NAMES[x] for x in exp['handoffs'])} {_ok(p['handoffs_ok'])}</td>"
            f"<td>{', '.join(NAMES[x] for x in exp['not_called'])} {_ok(p['not_called_ok'])}</td>"
            f"<td class='num'>{p['tool_calls_expected']} → <strong>{p['tool_calls_actual']}</strong></td>"
            f"<td>{_e(diffs)}</td><td class='num'>{t['drafts']}</td>"
            f"<td>{_e(', '.join(t['refused']) or 'none')}</td>"
            f"<td class='num'>{_money4(t['cost_usd'])}</td></tr>")

    grades = []
    for tr in r["ticket_reviews"]:
        items = []
        for a in tr["agents"]:
            cls = "g g" + str(a["grade"]).replace(" ", "")
            items.append(f"<li><span class='{cls}'>{_e(a['grade'])}</span> <strong>{_e(NAMES.get(a['role'], a['role']))}</strong>"
                         f"<span class='crew'> · {_e(CREW.get(a['role'], ''))}</span>: {_e(a['why'])}</li>")
        grades.append(f"<article class='card'><div class='th'><span class='g big g{_e(tr['grade'])}'>{_e(tr['grade'])}</span>"
                      f"<div><div class='eyebrow'>Flight CC {tr['ticket_id']}</div><p>{_e(tr['why'])}</p></div></div>"
                      f"<ul class='agents'>{''.join(items)}</ul></article>")

    lessons = "".join(f"<tr><td><span class='tag {_e(l['status'])}'>{_e(l['status'])}</span></td><td>{_e(l['lesson'])}</td>"
                      f"<td class='ev'>{_e(l['evidence'])}</td></tr>" for l in r["lessons"])
    opps = "".join(f"<tr><td>{_e(o['opportunity'])}</td><td><strong>{_e(o['action'])}</strong></td><td>{_e(o['owner'])}</td>"
                   f"<td class='ev'>{_e(o['measure'])}</td></tr>" for o in r.get("opportunities", []))
    ups = []
    for u in r["prompt_updates"]:
        if u["owner_decision"]:
            status = "<span class='tag'>owner decides</span>"
        elif u["change"] in applied:
            status = "<span class='tag fixed'>applied</span>"
        else:
            status = "<span class='tag'>proposed</span>"
        ups.append(f"<tr><td>{_e(NAMES.get(u['agent'], u['agent']))}</td><td>{_e(u['change'])}</td>"
                   f"<td class='ev'>{_e(u['evidence'])}</td><td>{status}</td></tr>")
    trend = []
    for h in reversed(history):
        hm = h["metrics"]["tickets_since_reset"].values()
        trend.append(f"<tr><td>{_e(h['at_utc'][:16].replace('T', ' '))}</td><td>{_e(h['trigger'])}</td>"
                     f"<td class='num'>{_money4(h['metrics'].get('board_cost_usd'))}</td>"
                     f"<td class='num'>{sum(t['plan']['tool_calls_actual'] for t in hm)}</td>"
                     f"<td class='num'>{sum(t['plan']['tool_calls_expected'] for t in hm)}</td>"
                     f"<td>{_e(h['report']['headline'])}</td></tr>")
    cash = m["cash"]
    cash_txt = ("✓ " if cash["matches"] else "✗ ") + f"${cash['start']:,.0f} → ${cash['end_cash_accounts']:,.0f}"

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crew Debrief</title><style>{CSS}</style></head><body>
<header><div class="eyebrow">Campus Customs · The Back Office · KHVN</div><h1>Crew <em>Debrief</em></h1>
<p class="headline">“{_e(r['headline'])}”</p>
<div class="card facts">
<div class="fact"><span>Debriefs so far</span><b>{len(history)}</b></div>
<div class="fact"><span>Board cost (latest runs)</span><b>{_money4(m.get('board_cost_usd'))}</b></div>
<div class="fact"><span>Ticket runs logged</span><b>{m['total_ticket_runs_logged']}</b></div>
<div class="fact"><span>Cash check</span><b>{cash_txt}</b></div>
<div class="fact"><span>Security holds (all time)</span><b>{m['safety_events_all_time']['security_review_enforced']}</b></div>
</div></header>
<main>
<h2>Expected vs. actual, every ticket</h2>
<div class="scroll"><table><tr><th>Ticket</th><th>Boss calls first</th><th>Hand-offs</th><th>Not called</th><th>Tool calls (plan → actual)</th><th>Extra or missing tools</th><th>Drafts</th><th>Refused</th><th>Cost</th></tr>{''.join(rows)}</table></div>
<h2>How each agent performed, and why</h2><div class="grid">{''.join(grades)}</div>
<h2>Opportunities → actions</h2>
<div class="scroll"><table><tr><th>Opportunity</th><th>Action</th><th>Owner</th><th>How we'll measure it</th></tr>{opps or '<tr><td colspan="4">None this time.</td></tr>'}</table></div>
<h2>Lessons learned (combined across debriefs)</h2>
<div class="scroll"><table><tr><th>Status</th><th>Lesson</th><th>Evidence</th></tr>{lessons}</table></div>
<h2>Prompt updates</h2>
<div class="scroll"><table><tr><th>Agent</th><th>Change</th><th>Evidence</th><th>Status</th></tr>{''.join(ups) or '<tr><td colspan="4">None.</td></tr>'}</table></div>
<p class="ev">Next experiment: {_e(r['next_experiment'])}</p>
<h2>Trend, newest first</h2>
<div class="scroll"><table><tr><th>When (UTC)</th><th>Trigger</th><th>Board cost</th><th>Tool calls</th><th>Planned</th><th>Headline</th></tr>{''.join(trend)}</table></div>
</main><footer>Rebuilt automatically after every debrief by backend/learning.py. Numbers come from output/audit_trail.json and the database. Grades and lessons come from the Flight Instructor (gpt-6-luna). Full history: output/learning_feedback.json.</footer>
</body></html>"""
    REPORT.write_text(page, encoding="utf-8")
    return REPORT
