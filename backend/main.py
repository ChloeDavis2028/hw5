"""Campus Customs Desk API: the backend the React dashboard calls.

Run from backend/ (activate the project venv first, so `uvicorn` is the one with FastMCP):
    ..\\.venv\\Scripts\\activate
    uvicorn main:app --reload --port 8000
Backend: http://localhost:8000    Docs (try every route in the browser): http://localhost:8000/docs

Routes
  GET  /api/tickets                  every ticket, open or resolved, plus the team's latest call on it
  POST /api/tickets/{id}/run         start the agent team on one ticket (returns a run_id right away)
  GET  /api/runs/{run_id}            is that run still going? its decision and cost when done
  GET  /api/events                   recent agent events: what each agent said and which tools it used
  POST /api/login                    an approver signs in (test accounts: scripts/create_approvers.py)
  POST /api/approvals                a signed-in person approves one proposed payment or purchase order (this is what moves cash)
  POST /api/rejections               a signed-in person rejects one proposal (blocks approval until a fresh proposal)
  GET  /api/tickets/{id}/drafts      the reply drafts saved on the board (never sent)
  GET  /api/usage                    AI spend this month vs. the budget
  POST /api/board/run                run the team on every open ticket at once (one payment plan)
  GET  /api/cash                     the current checking balance from cash_accounts
  POST /api/reset                    reset the database to the original values for a fresh run
  GET  /api/learning                 the Flight Instructor's latest debrief (grades, lessons, opportunities)
  POST /api/learning/review          run a debrief now (it also runs after every ticket)
  GET  /api/health                   quick check that the server is up

Shop facts come only from the MCP server (team._mcp_call). Events come from
output/audit_trail.json, which the agents append to as they run. Agents only
propose payments; the one route that moves money is POST /api/approvals, and it
only pays something an agent proposed, after a person approves it.
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from fastapi import FastAPI, Header, HTTPException, Query  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

import auth  # noqa: E402
import team  # noqa: E402
from models import TeamDeps  # noqa: E402

app = FastAPI(title="Campus Customs Desk API", version="1.0")
app.add_middleware(
    CORSMiddleware,  # the React dev server runs on another port
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

RUNS: dict[str, dict[str, Any]] = {}   # run_id -> status and result, for this server session
_run_lock = asyncio.Lock()              # one team run at a time: one MCP connection, one cash picture
_tasks: set[asyncio.Task] = set()        # keep background runs alive until they finish
PREVIEW = 300                            # characters of tool output shown per event


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _trail() -> list[dict]:
    try:
        return json.loads(team.AUDIT_TRAIL.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _short(value: Any, n: int = PREVIEW) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= n else text[:n] + "…"


# ---------- tickets ----------

def _latest_decisions() -> dict[int, dict]:
    """The team's most recent finished call on each ticket, from the audit trail."""
    latest: dict[int, dict] = {}
    for e in _trail():
        if e["event"] == "ticket_done" and e.get("ticket_id") is not None:
            d = e["decision"]
            latest[e["ticket_id"]] = {"run_id": e["run_id"], "at_utc": e["at_utc"], "agent_status": d["status"],
                                      "decision": d["decision"], "approval_requests": d["approval_requests"],
                                      "drafts": d["drafts"], "cost_usd": (e.get("cost") or {}).get("cost_usd"),
                                      "policy_flags": d.get("policy_flags", []), "security_flags": d.get("security_flags", [])}
    return latest


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "model": team.MODEL_NAME, "busy": _run_lock.locked(), "at_utc": _now()}


@app.get("/api/tickets")
async def list_tickets() -> dict:
    """Every ticket and whether it is open or resolved (tickets.status in the database,
    read through the MCP tool list_tickets), plus the team's latest call on it."""
    board = await team._mcp_call("list_tickets", {})
    latest = _latest_decisions()
    running = {r["ticket_id"] for r in RUNS.values() if r["status"] == "running"}
    tickets = [{
        "id": t["id"], "type": t["type"], "requester": t["requester"], "subject": t["subject"],
        "sku": t["sku"], "size": t["size"], "qty": t["qty"], "lease_id": t["lease_id"],
        "invoice_id": t["invoice_id"], "notes": t["notes"], "created_at": t["created_at"],
        "status": t["status"],                       # "open" or "resolved", from the database
        "needs_human_review": t["needs_human_review"], "suspicious_text": t["suspicious_text"],
        "running_now": t["id"] in running,
        "latest_run": latest.get(t["id"]),           # None until the team has worked it
    } for t in board["tickets"]]
    return {"shop_today": board["shop_today"], "count": board["count"],
            "open": board["open"], "resolved": board["resolved"], "tickets": tickets}


# ---------- run the team ----------

async def _run_job(run_id: str, ticket_id: int) -> None:
    job = RUNS[run_id]
    async with _run_lock:
        job["status"] = "running"
        try:
            decision, deps, usage, cost = await team.run_ticket(ticket_id, run_id=run_id)
            job.update(status="done", decision=decision.model_dump(), cost=cost,
                       delegations=[d.model_dump() for d in deps.delegations])
            # The run finished: mark the ticket resolved on the board. A ticket held for
            # human review (suspicious text) stays open until a person looks at it.
            if decision.status == "needs_review":
                job["ticket_status"] = "open (held for human review)"
            else:
                res = await team._mcp_call("mark_ticket_resolved", {"ticket_id": ticket_id})
                await team._mcp_call("save_drafts", {"ticket_id": ticket_id, "run_id": run_id,
                                                     "drafts": [d.model_dump() for d in decision.drafts]})
                job["ticket_status"] = "resolved"
                team.audit(deps, "system", "ticket_resolved", result=res, agent_status=decision.status)
            # The learning department debriefs after every run, so the report is always current.
            try:
                review = await team.run_learning_review(trigger=f"after ticket {ticket_id} run {run_id}")
                job["learning_headline"] = review["report"]["headline"]
            except BaseException as exc:  # a failed debrief never undoes the ticket
                job["learning_error"] = f"{type(exc).__name__}: {exc}"
        except BaseException as exc:  # includes the token cap's SystemExit; never crash the server
            job.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            if isinstance(exc, (KeyboardInterrupt, asyncio.CancelledError)):
                raise
        finally:
            job["finished_at_utc"] = _now()


@app.post("/api/tickets/{ticket_id}/run", status_code=202)
async def run_ticket(ticket_id: int) -> dict:
    """Start the agent team on one ticket. It takes about a minute, so this returns a
    run_id at once. Watch /api/events?run_id=... and /api/runs/{run_id} for progress."""
    found = await team._mcp_call("get_ticket", {"ticket_id": ticket_id})
    if not found.get("found"):
        raise HTTPException(404, f"No ticket with id={ticket_id}.")
    if _run_lock.locked():
        raise HTTPException(409, "The team is already working a ticket. Try again when it finishes.")
    run_id = uuid4().hex[:12]
    RUNS[run_id] = {"run_id": run_id, "ticket_id": ticket_id, "status": "queued", "started_at_utc": _now()}
    task = asyncio.create_task(_run_job(run_id, ticket_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return {"run_id": run_id, "ticket_id": ticket_id, "status": "queued",
            "watch": {"run": f"/api/runs/{run_id}", "events": f"/api/events?run_id={run_id}"}}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    if run_id not in RUNS:
        raise HTTPException(404, f"No run {run_id} in this server session.")
    return RUNS[run_id]


# ---------- recent agent events ----------

def _events_from(entry: dict, idx: int) -> list[dict]:
    """Turn one audit-trail entry into the board's simple events:
    said (what an agent said), tool_call, tool_result, handoff, decision,
    approval, reset, warning."""
    base = {"at_utc": entry["at_utc"], "run_id": entry["run_id"], "ticket_id": entry.get("ticket_id"),
            "role": entry["role"], "depth": entry.get("depth", 0)}
    ev, out = entry["event"], []

    def add(kind: str, n: int = 0, **kw):
        out.append({"id": f"{idx}.{n}", "seq": idx, "kind": kind, **base, **kw})

    if ev == "ticket_start":
        add("run_started", text=f"Team started on ticket {entry.get('ticket_id')}")
    elif ev == "board_start":
        add("run_started", text="Team started on the whole board")
    elif ev == "agent_start" and entry.get("depth", 0) == 0:
        add("said", text=f"Asked: {_short(entry.get('prompt', ''))}")
    elif ev == "loop_step_reply":
        for n, p in enumerate(entry.get("parts", [])):
            if p["kind"] == "text" and p.get("content", "").strip():
                add("said", n, text=_short(p["content"], 1000))
            elif p["kind"] == "tool_call" and p["tool"] == team.DELEGATE_TOOL:
                args = p.get("args", {})
                add("handoff", n, to_role=args.get("teammate"), text=_short(args.get("request", ""), 600))
            elif p["kind"] == "tool_call" and p["tool"] != "final_result":
                add("tool_call", n, tool=p["tool"], args=p.get("args", {}))
    elif ev == "loop_step_send":
        for n, p in enumerate(entry.get("parts", [])):
            if p["kind"] == "tool_result" and p.get("tool") not in (team.DELEGATE_TOOL, "final_result"):
                add("tool_result", n, tool=p["tool"], text=_short(p.get("content")))
    elif ev == "agent_done":
        o = entry.get("output") or {}
        add("said", text=_short(o.get("summary") or o.get("decision") or "", 1000),
            final=True, status=o.get("status"))
    elif ev == "delegation_refused":
        add("warning", to_role=entry.get("to_role"), text=f"Hand-off refused ({entry.get('outcome')})")
    elif ev == "ticket_done":
        d = entry.get("decision") or {}
        add("decision", status=d.get("status"), text=d.get("decision", ""),
            approvals=len(d.get("approval_requests", [])), drafts=len(d.get("drafts", [])),
            cost_usd=(entry.get("cost") or {}).get("cost_usd"))
    elif ev == "human_approval":
        r = entry.get("result") or {}
        add("approval", status="paid" if r.get("paid") else "refused", approved_by=entry.get("approved_by"),
            ref_kind=entry.get("kind"), ref_id=entry.get("ref_id"),
            text=(f"Paid {entry.get('kind')} {entry.get('ref_id')}: ${r.get('amount', 0):,.2f}, "
                  f"cash now ${r.get('balance_after', 0):,.2f}") if r.get("paid") else r.get("message", ""))
    elif ev == "human_rejection":
        add("approval", status="rejected", approved_by=entry.get("rejected_by"),
            ref_kind=entry.get("kind"), ref_id=entry.get("ref_id"),
            text=f"Rejected {entry.get('kind')} {entry.get('ref_id')}" + (f": {entry['reason']}" if entry.get("reason") else ""))
    elif ev == "ticket_resolved":
        add("resolved", text=f"Ticket {entry.get('ticket_id')} marked resolved")
    elif ev == "database_reset":
        add("reset", text=entry.get("message", "Database reset to the original values"))
    elif ev in ("security_review_enforced", "blocked_human_only_tool", "cap_hit"):
        add("warning", text=f"{ev}: {_short(entry.get('flags') or entry.get('reason') or entry.get('tool') or '')}")
    return out


@app.get("/api/events")
async def recent_events(
    limit: int = Query(100, ge=1, le=1000, description="newest events to return"),
    after: int | None = Query(None, description="only events after this seq (the board passes the last seq it saw)"),
    ticket_id: int | None = None,
    run_id: str | None = None,
    role: str | None = None,
) -> dict:
    """Recent agent events, oldest first: what each agent said and which tools it used.
    Poll with ?after=<latest_seq> so the board only fetches what's new."""
    events = []
    for idx, entry in enumerate(_trail()):
        if after is not None and idx <= after:
            continue
        if ticket_id is not None and entry.get("ticket_id") != ticket_id:
            continue
        if run_id and entry.get("run_id") != run_id:
            continue
        if role and entry.get("role") != role:
            continue
        events.extend(_events_from(entry, idx))
    events = events[-limit:]
    return {"count": len(events), "latest_seq": events[-1]["seq"] if events else after,
            "busy": _run_lock.locked(), "events": events}


# ---------- human approval: the only route that moves money ----------

TOOL_KIND = {"invoice_payment": "invoice", "rent_payment": "rent", "purchase_order": "purchase_order"}


# ---------- approver sign-in ----------

class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/api/login")
async def login(body: LoginIn) -> dict:
    """Sign in an approver. Returns a token the board sends with approvals (8 hours)."""
    user = auth.verify(body.username, body.password)
    if not user:
        raise HTTPException(401, "Wrong username or password.")
    return {"token": auth.make_token(user), **user}


def _approver(authorization: str | None) -> dict:
    token = (authorization or "").removeprefix("Bearer ").strip()
    user = auth.check_token(token)
    if not user:
        raise HTTPException(401, "Please sign in as an approver first.")
    return user


# ---------- human approval: the only route that moves money ----------

class ApprovalIn(BaseModel):
    kind: Literal["invoice_payment", "rent_payment", "purchase_order"]
    ref_id: int = Field(description="invoices.id, leases.id, or vendors.id for a purchase order")
    second_token: str = Field("", description="The second approver's sign-in token (required over $1,000)")
    owner_override_cushion: bool = Field(False, description="Owner only: allow a purchase order below the $500 cushion")
    sku: str | None = None
    size: str | None = None
    qty: int | None = None


def _proposals() -> list[dict]:
    """Every payment or purchase order an agent proposed, newest last, from the audit trail."""
    found = []
    for e in _trail():
        if e["event"] == "ticket_done":
            for a in (e.get("decision") or {}).get("approval_requests", []):
                found.append({**a, "ticket_id": e.get("ticket_id"), "run_id": e["run_id"], "at_utc": e["at_utc"]})
        elif e["event"] == "board_done":
            for a in (e.get("plan") or {}).get("payment_plan", []):
                found.append({**a, "ticket_id": None, "run_id": e["run_id"], "at_utc": e["at_utc"]})
    return found


def _matches(p: dict, kind: str, ref_id, sku=None, size=None, qty=None) -> bool:
    if p.get("kind") != kind or p.get("ref_id") != ref_id:
        return False
    if kind == "purchase_order":
        return (p.get("sku"), p.get("size"), p.get("qty")) == (sku, size, qty)
    return True


def _rejected_since(proposal: dict) -> dict | None:
    """A rejection of this payment made after the agents proposed it blocks approval,
    until the team runs again and proposes it fresh."""
    for e in reversed(_trail()):
        if e["event"] == "human_rejection" and e.get("kind") == proposal["kind"] and e.get("ref_id") == proposal.get("ref_id") \
                and e["at_utc"] > proposal["at_utc"]:
            return e
    return None


@app.post("/api/approvals")
async def approve(a: ApprovalIn, authorization: str | None = Header(None)) -> dict:
    """A signed-in person clicked Approve on one proposal. Agents only prepare payments; this is
    the route that actually changes cash. The approver's name comes from their sign-in, not a
    typed box. It pays only what an agent proposed and nobody has rejected since, and the MCP
    pay tool checks everything again (amount from the books, no negative cash, second approver
    over $1,000, vendor not blocked, $500 cushion for purchase orders)."""
    first = _approver(authorization)
    second = auth.check_token(a.second_token) if a.second_token else None
    if a.second_token and not second:
        raise HTTPException(401, "The second approver's sign-in has expired or is not valid.")
    if second and second["username"] == first["username"]:
        raise HTTPException(400, "The second approver must be a different person.")
    if a.owner_override_cushion and first["role"] != "owner":
        raise HTTPException(403, "Only the owner can override the $500 cash cushion.")
    if _run_lock.locked():
        raise HTTPException(409, "The team is working a ticket. Approve when it finishes, so cash does not change mid-run.")
    matches = [p for p in _proposals() if _matches(p, a.kind, a.ref_id, a.sku, a.size, a.qty)]
    if not matches:
        raise HTTPException(404, "No agent proposed this payment. Only proposals from the team can be approved.")
    proposal = matches[-1]
    rej = _rejected_since(proposal)
    if rej:
        raise HTTPException(409, f"{rej.get('rejected_by')} rejected this on {rej['at_utc'][:16].replace('T', ' ')} UTC. "
                                 "Run the team again for a fresh proposal before approving.")
    args = {"kind": TOOL_KIND[a.kind], "ref_id": a.ref_id, "approved_by": first["display_name"],
            "second_approver": second["display_name"] if second else "",
            "owner_override_cushion": a.owner_override_cushion}
    if a.kind == "purchase_order":
        args.update(sku=a.sku, size=a.size, qty=a.qty)
    async with _run_lock:  # no team run can start while money moves
        result = await team._mcp_call("pay_approved_request", args)
    deps = TeamDeps(run_id=f"approval-{uuid4().hex[:8]}", ticket_id=proposal.get("ticket_id"))
    team.audit(deps, "human", "human_approval", kind=a.kind, ref_id=a.ref_id, approved_by=first["display_name"],
               second_approver=second["display_name"] if second else "", signed_in=True,
               owner_override_cushion=a.owner_override_cushion, proposal=proposal, result=result)
    if not result.get("paid"):
        raise HTTPException(400, result.get("message", "Payment refused."))
    return {"paid": True, "proposal": proposal, "payment": result}


class RejectionIn(BaseModel):
    kind: Literal["invoice_payment", "rent_payment", "purchase_order"]
    ref_id: int
    reason: str = Field("", description="Why, in a few words (shown on the board)")
    sku: str | None = None
    size: str | None = None
    qty: int | None = None


@app.post("/api/rejections")
async def reject(r: RejectionIn, authorization: str | None = Header(None)) -> dict:
    """A signed-in person clicked Reject. Nothing is paid, and the payment can't be approved
    until the team runs again and proposes it fresh."""
    who = _approver(authorization)
    matches = [p for p in _proposals() if _matches(p, r.kind, r.ref_id, r.sku, r.size, r.qty)]
    if not matches:
        raise HTTPException(404, "No agent proposed this payment, so there is nothing to reject.")
    proposal = matches[-1]
    deps = TeamDeps(run_id=f"rejection-{uuid4().hex[:8]}", ticket_id=proposal.get("ticket_id"))
    team.audit(deps, "human", "human_rejection", kind=r.kind, ref_id=r.ref_id, rejected_by=who["display_name"],
               signed_in=True, reason=r.reason, proposal=proposal)
    return {"rejected": True, "paid": False, "proposal": proposal, "rejected_by": who["display_name"], "reason": r.reason}


# ---------- replies saved on the board ----------

@app.get("/api/tickets/{ticket_id}/drafts")
async def ticket_drafts(ticket_id: int) -> dict:
    """The reply drafts saved on the board for one ticket (never sent)."""
    return await team._mcp_call("get_drafts", {"ticket_id": ticket_id})


# ---------- AI spend ----------

@app.get("/api/usage")
async def usage() -> dict:
    """AI spend this month from output/usage_log.json, against the monthly budget
    (AI_MONTHLY_BUDGET, default $5.00, a placeholder the owner should set)."""
    import os
    try:
        log = json.loads(team.USAGE_LOG.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        log = []
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    this = [e for e in log if str(e.get("at_utc", "")).startswith(month)]
    spent = round(sum(e.get("cost_usd") or 0 for e in this), 4)
    budget = float(os.environ.get("AI_MONTHLY_BUDGET", "5.00"))
    return {"month": month, "spent_usd": spent, "budget_usd": budget, "runs": len(this),
            "by_kind": {k: round(sum(e.get("cost_usd") or 0 for e in this if e.get("kind") == k), 4)
                        for k in sorted({e.get("kind") for e in this})},
            "warning": spent >= 0.8 * budget, "over_budget": spent >= budget}


# ---------- whole board ----------

async def _run_board_job(run_id: str) -> None:
    job = RUNS[run_id]
    async with _run_lock:
        job["status"] = "running"
        try:
            plan, checks, cost = await team.run_board(run_id=run_id)
            job.update(status="done", plan=plan.model_dump(), checks=checks, cost=cost)
            for t in plan.tickets:
                if t.status != "needs_review":
                    await team._mcp_call("mark_ticket_resolved", {"ticket_id": t.ticket_id})
                    await team._mcp_call("save_drafts", {"ticket_id": t.ticket_id, "run_id": run_id,
                                                         "drafts": [d.model_dump() for d in t.drafts]})
            try:
                review = await team.run_learning_review(trigger=f"after whole-board run {run_id}")
                job["learning_headline"] = review["report"]["headline"]
            except BaseException as exc:
                job["learning_error"] = f"{type(exc).__name__}: {exc}"
        except BaseException as exc:
            job.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            if isinstance(exc, (KeyboardInterrupt, asyncio.CancelledError)):
                raise
        finally:
            job["finished_at_utc"] = _now()


@app.post("/api/board/run", status_code=202)
async def run_whole_board() -> dict:
    """Run the team on every open ticket at once: one shared payment plan, checked in code."""
    if _run_lock.locked():
        raise HTTPException(409, "The team is already working. Try again when it finishes.")
    run_id = uuid4().hex[:12]
    RUNS[run_id] = {"run_id": run_id, "ticket_id": None, "kind": "board", "status": "queued", "started_at_utc": _now()}
    task = asyncio.create_task(_run_board_job(run_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return {"run_id": run_id, "status": "queued", "watch": {"run": f"/api/runs/{run_id}", "events": f"/api/events?run_id={run_id}"}}


# ---------- cash and reset ----------

@app.get("/api/cash")
async def cash() -> dict:
    """The current checking balance from cash_accounts (through MCP), plus what is still owed."""
    pos = await team._mcp_call("get_cash_position", {})
    checking = next((c for c in pos["cash_accounts"] if c["name"] == "checking"), None)
    if checking is None:
        raise HTTPException(404, "No checking account in cash_accounts.")
    return {"account": "checking", "balance": checking["balance"], "as_of": checking["date"],
            "shop_today": pos["shop_today"], "open_invoices": pos["open_invoices"], "rent_due": pos["rent_due"],
            "total_owed": pos["total_owed"], "cash_left_if_all_paid": pos["cash_left_if_all_paid"],
            "recent_payments": pos["recent_payments"]}


@app.post("/api/reset")
async def reset_database() -> dict:
    """Copy data/campus_customs.db over data/campus_customs_new.db for a fresh run.
    The audit trail and usage log are kept (never wiped); a reset entry is added."""
    if _run_lock.locked():
        raise HTTPException(409, "The team is working a ticket. Reset when it finishes.")
    from reset_db import reset
    async with _run_lock:
        sha = reset()
    deps = TeamDeps(run_id=f"reset-{uuid4().hex[:8]}")
    team.audit(deps, "human", "database_reset", message="Database reset to the original values", sha256=sha)
    after = await cash()
    return {"reset": True, "sha256": sha, "checking_balance": after["balance"], "total_owed": after["total_owed"]}


# ---------- the learning department ----------

@app.get("/api/learning")
async def learning_latest() -> dict:
    """The latest debrief plus how many debriefs exist. Report page: output/learning_report.html"""
    try:
        history = json.loads(team.LEARNING_LOG.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    if not history:
        return {"count": 0, "latest": None}
    last = history[-1]
    return {"count": len(history), "latest": {"at_utc": last["at_utc"], "trigger": last["trigger"],
            "report": last["report"], "applied_updates": last.get("applied_updates", []),
            "board_cost_usd": last["metrics"].get("board_cost_usd"), "cash": last["metrics"]["cash"]}}


@app.post("/api/learning/review")
async def learning_review() -> dict:
    """Run a Flight Instructor debrief now."""
    if _run_lock.locked():
        raise HTTPException(409, "The team is working a ticket. The debrief runs after it finishes.")
    async with _run_lock:
        entry = await team.run_learning_review(trigger="requested on the dashboard")
    return {"headline": entry["report"]["headline"], "cost": entry["cost"]}
