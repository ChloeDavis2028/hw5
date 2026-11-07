"""The Campus Customs agent team: shared wiring for all five agents.

- One model for everyone: gpt-6-luna through Portkey (PORTKEY_API_KEY).
- One source of shop facts: the MCP server (mcp_server/server.py) over
  data/campus_customs_new.db. There is no second tools layer; every shop
  fact an agent sees comes back from an MCP tool call.
- Full connectivity: every agent has an ask_teammate tool that can hand work
  to any other role. Loops are stopped by three rules: no asking yourself,
  no asking someone already in the current chain, and a depth limit.
- Human-only tools (pay_approved_request) are filtered out, so no agent can
  move money. The backend calls that tool after a person approves.
- Every loop step of every agent is appended to output/audit_trail.json.
"""

import json
import os
import sys
import threading
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent, RunContext
from pydantic_ai import messages as msg
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import RunUsage, UsageLimits

from models import BoardPlan, Delegation, Role, TeamDeps, TicketDecision

BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parent
PROMPTS = BACKEND / "prompts"
SERVER_SCRIPT = ROOT / "mcp_server" / "server.py"
AUDIT_TRAIL = ROOT / "output" / "audit_trail.json"

MODEL_NAME = "gpt-6-luna"  # The only model this assignment allows, for every agent.
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
HUMAN_ONLY_TOOLS = {"pay_approved_request", "mark_ticket_resolved", "save_drafts", "get_drafts"}  # backend-only
DELEGATE_TOOL = "ask_teammate"
REQUEST_LIMIT = 60  # model calls per ticket, across the whole team
BOARD_REQUEST_LIMIT = 120  # model calls for a whole-board run
TICKET_TOKEN_LIMIT = 120_000  # hard token stop for one ticket (a normal ticket uses ~35-45k)
BOARD_TOKEN_LIMIT = 300_000   # hard token stop for the whole board
TEXT_LIMIT = 4000   # characters kept per text field in the audit trail
USAGE_LOG = ROOT / "output" / "usage_log.json"
PRICES = ROOT / "data" / "prices.json"  # gpt-6-luna price list (MGT 409 Lecture 11)
BOARD_PLAN = ROOT / "output" / "board_plan.json"


# ---------- model ----------

@lru_cache(maxsize=1)
def shop_model() -> OpenAIResponsesModel:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise SystemExit("PORTKEY_API_KEY is not set.")
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(base_url=PORTKEY_BASE_URL, api_key=api_key))


# ---------- audit trail (append-only) ----------

_audit_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _clip(value: Any) -> Any:
    if isinstance(value, str) and len(value) > TEXT_LIMIT:
        return value[:TEXT_LIMIT] + f"... [{len(value) - TEXT_LIMIT} more characters]"
    return value


def _plain(value: Any) -> Any:
    """Make tool arguments and results safe to write as JSON."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _append_json(path: Path, entry: dict) -> None:
    """Append one entry to a JSON list file. Never wipes earlier entries."""
    with _audit_lock:
        path.parent.mkdir(exist_ok=True)
        try:
            items = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        except json.JSONDecodeError:
            path.rename(path.with_suffix(f".corrupt-{uuid.uuid4().hex[:6]}.json"))
            items = []
        items.append(entry)
        path.write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")


def cost_of(usage: RunUsage) -> dict:
    """Dollar cost of a run from the gpt-6-luna price list (per 1M tokens).
    Cached input is billed at the cached rate; the rest of input at the normal rate."""
    p = json.loads(PRICES.read_text(encoding="utf-8"))[MODEL_NAME]
    cached = usage.cache_read_tokens or 0
    written = usage.cache_write_tokens or 0
    fresh = max((usage.input_tokens or 0) - cached - written, 0)
    parts = {
        "input": fresh * p["input_per_1m"] / 1e6,
        "cached_input": cached * p["cached_input_per_1m"] / 1e6,
        "cache_write": written * p["cache_write_per_1m"] / 1e6,
        "output": (usage.output_tokens or 0) * p["output_per_1m"] / 1e6,
    }
    return {
        "requests": usage.requests,
        "input_tokens": usage.input_tokens,
        "cached_input_tokens": cached,
        "output_tokens": usage.output_tokens,
        "total_tokens": (usage.input_tokens or 0) + (usage.output_tokens or 0),
        "cost_usd": round(sum(parts.values()), 6),
        "cost_parts_usd": {k: round(v, 6) for k, v in parts.items()},
        "model": MODEL_NAME,
    }


def log_usage(deps: TeamDeps, kind: str, usage: RunUsage, outcome: str) -> dict:
    """Append one line per run to output/usage_log.json (never wiped)."""
    entry = {"at_utc": _now(), "run_id": deps.run_id, "kind": kind, "ticket_id": deps.ticket_id,
             "outcome": outcome, "token_limit": deps.token_limit, **cost_of(usage)}
    _append_json(USAGE_LOG, entry)
    return entry


def audit(deps: TeamDeps, role: str, event: str, **details: Any) -> None:
    """Append one entry to output/audit_trail.json. Never wipes the file."""
    entry = {
        "at_utc": _now(),
        "run_id": deps.run_id,
        "ticket_id": deps.ticket_id,
        "role": role,
        "depth": deps.depth,
        "chain": list(deps.chain),
        "event": event,
        **{k: _clip(_plain(v)) for k, v in details.items()},
    }
    _append_json(AUDIT_TRAIL, entry)


# ---------- MCP toolset (the only source of shop facts) ----------

async def _guard_tool_call(ctx: RunContext[TeamDeps], call_tool, name: str, tool_args: dict):
    """Second lock on the door: even if a human-only tool slipped through the
    filter, an agent call to it is refused here."""
    if name in HUMAN_ONLY_TOOLS:
        role = ctx.deps.chain[-1] if ctx.deps.chain else "unknown"
        audit(ctx.deps, role, "blocked_human_only_tool", tool=name, args=tool_args)
        return {"refused": True, "message": f"{name} is human-only. Put the payment in approval_requests."}
    return await call_tool(name, tool_args)


def build_shop_toolset(db_path: str | os.PathLike | None = None) -> MCPToolset:
    env = {k: v for k, v in os.environ.items() if k != "PORTKEY_API_KEY"}  # the server needs no keys
    if db_path:
        env["CAMPUS_DB"] = str(db_path)
    transport = StdioTransport(command=sys.executable, args=[str(SERVER_SCRIPT)], env=env, cwd=str(ROOT))
    return MCPToolset(Client(transport), id="campus-customs", process_tool_call=_guard_tool_call)


SHOP_TOOLSET = build_shop_toolset(os.environ.get("CAMPUS_DB"))
AGENT_TOOLSET = SHOP_TOOLSET.filtered(lambda ctx, tool_def: tool_def.name not in HUMAN_ONLY_TOOLS)


# ---------- full connectivity: any agent can ask any other ----------

def _delegate_tool(caller: Role):
    async def ask_teammate(ctx: RunContext[TeamDeps], teammate: Role, request: str) -> str:
        """Hand a task to another teammate and get their report back.

        teammate: one of boss, inventory, accounting, facilities, customer_service.
        request: exactly what you need, including the ticket's SKU, size, qty,
        invoice_id or lease_id. You cannot ask yourself or anyone already
        working on this hand-off chain.
        """
        deps = ctx.deps
        refusal = None
        if teammate == caller:
            outcome, refusal = "refused_self", "You can't delegate to yourself. Use your own tools."
        elif teammate in deps.chain:
            outcome, refusal = "refused_loop", (
                f"{teammate} is already working on this chain ({' -> '.join(deps.chain)}). "
                "Answer with what you have instead of sending it back.")
        elif deps.depth >= deps.max_depth:
            outcome, refusal = "refused_depth", (
                f"Delegation limit ({deps.max_depth} hand-offs deep) reached. Answer with what you have.")
        if refusal:
            deps.delegations.append(Delegation(from_role=caller, to_role=teammate, request=request,
                                               depth=deps.depth, outcome=outcome))
            audit(deps, caller, "delegation_refused", to_role=teammate, request=request, outcome=outcome)
            return refusal

        sub = TeamDeps(run_id=deps.run_id, ticket_id=deps.ticket_id, max_depth=deps.max_depth,
                       token_limit=deps.token_limit, request_limit=deps.request_limit, depth=deps.depth + 1, chain=[*deps.chain, teammate], delegations=deps.delegations)
        audit(deps, caller, "delegation_start", to_role=teammate, request=request)
        output = await run_agent(teammate, f"Request from {caller}: {request}", sub, usage=ctx.usage)
        deps.delegations.append(Delegation(from_role=caller, to_role=teammate, request=request,
                                           depth=deps.depth, outcome="answered",
                                           answer_summary=getattr(output, "summary", None)
                                           or getattr(output, "decision", "")))
        audit(deps, caller, "delegation_done", to_role=teammate, answer=output)
        return output.model_dump_json()

    return ask_teammate


def build_agent(role: Role, output_type: type) -> Agent:
    """One agent: gpt-6-luna + its prompt file + the shop's MCP tools + ask_teammate."""
    return Agent(
        shop_model(),
        name=role,
        output_type=output_type,
        # Each agent gets its own role prompt plus the shared shop owner's rules.
        instructions=(PROMPTS / f"{role}.md").read_text(encoding="utf-8")
        + "\n\n" + (PROMPTS / "_owner_rules.md").read_text(encoding="utf-8"),
        deps_type=TeamDeps,
        toolsets=[AGENT_TOOLSET],
        tools=[_delegate_tool(role)],
    )


def build_learning_agent(output_type: type) -> Agent:
    """The Flight Instructor: gpt-6-luna + its prompt + the shop rules, and NO tools.
    It can't touch the shop, money or other agents; it only reads the metrics it is given."""
    return Agent(
        shop_model(),
        name="learning",
        output_type=output_type,
        instructions=(PROMPTS / "learning.md").read_text(encoding="utf-8")
        + "\n\n" + (PROMPTS / "_owner_rules.md").read_text(encoding="utf-8"),
        deps_type=TeamDeps,
    )


LEARNING_LOG = ROOT / "output" / "learning_feedback.json"


async def run_learning_review(trigger: str) -> dict:
    """Debrief: code computes the metrics, the Flight Instructor grades and teaches,
    and the result is appended to output/learning_feedback.json (never wiped).
    The continuous report output/learning_report.html is then rebuilt."""
    import learning

    metrics = learning.collect_metrics()
    try:
        history = json.loads(LEARNING_LOG.read_text(encoding="utf-8")) if LEARNING_LOG.exists() else []
    except json.JSONDecodeError:
        history = []
    previous = history[-1]["report"]["lessons"] if history else []
    prev_metrics = history[-1]["metrics"] if history else None
    metrics["goals"] = {"tool_calls_at_or_below_plan_on_every_ticket": True,
                        "customer_service_repeat_lookups": 0, "refused_handoffs": 0,
                        "board_cost_usd_at_most": 0.015, "cash_matches": True}
    if prev_metrics:
        def _tot(mm, key):
            return sum((v.get("plan", {}).get(key) if key.startswith("tool_calls") else v.get(key)) or 0
                       for v in mm["tickets_since_reset"].values())
        metrics["vs_previous_debrief"] = {
            "tool_calls": {"before": _tot(prev_metrics, "tool_calls_actual"), "now": _tot(metrics, "tool_calls_actual")},
            "board_cost_usd": {"before": prev_metrics.get("board_cost_usd"), "now": metrics.get("board_cost_usd")},
            "customer_service_tool_calls": {
                "before": sum(sum(v["tools_by_agent"].get("customer_service", {}).values()) for v in prev_metrics["tickets_since_reset"].values()),
                "now": sum(sum(v["tools_by_agent"].get("customer_service", {}).values()) for v in metrics["tickets_since_reset"].values())},
            "applied_updates_since": history[-1].get("applied_updates", []),
        }
    deps = TeamDeps(run_id=f"learn-{uuid.uuid4().hex[:8]}", chain=["learning"],
                    token_limit=60_000, request_limit=6)
    usage = RunUsage()
    audit(deps, "system", "learning_start", trigger=trigger)
    prompt = ("Debrief the crew. Data follows as JSON.\n\nmetrics = " + json.dumps(metrics)
              + "\n\nprevious_lessons = " + json.dumps(previous))
    report = await run_agent("learning", prompt, deps, usage=usage)
    cost = log_usage(deps, "learning", usage, outcome="debrief")
    entry = {"at_utc": _now(), "review_id": deps.run_id, "trigger": trigger,
             "metrics": metrics, "report": report.model_dump(), "cost": cost}
    _append_json(LEARNING_LOG, entry)
    audit(deps, "system", "learning_done", headline=report.headline, cost=cost)
    learning.build_report()
    return entry


# ---------- the agent loop, with every step audited ----------

def _request_parts(request: msg.ModelRequest) -> list[dict]:
    parts = []
    for p in request.parts:
        if isinstance(p, msg.UserPromptPart):
            parts.append({"kind": "user_prompt", "content": p.content})
        elif isinstance(p, msg.ToolReturnPart):
            parts.append({"kind": "tool_result", "tool": p.tool_name, "tool_call_id": p.tool_call_id,
                          "content": _plain(p.content)})
        elif isinstance(p, msg.RetryPromptPart):
            parts.append({"kind": "retry", "tool": p.tool_name, "content": _plain(p.content)})
        else:
            parts.append({"kind": type(p).__name__})
    return parts


def _response_parts(response: msg.ModelResponse) -> list[dict]:
    parts = []
    for p in response.parts:
        if isinstance(p, msg.ToolCallPart):
            parts.append({"kind": "tool_call", "tool": p.tool_name, "tool_call_id": p.tool_call_id,
                          "args": _plain(p.args_as_dict())})
        elif isinstance(p, msg.TextPart):
            parts.append({"kind": "text", "content": p.content})
        else:
            parts.append({"kind": type(p).__name__})
    return parts


async def run_agent(role: Role, prompt: str, deps: TeamDeps, usage: RunUsage | None = None,
                    output_type: type | None = None):
    """Run one agent's loop (model -> tools -> model ... -> answer), appending
    each step to the audit trail as it happens. The request and token caps in
    deps apply to the whole run, because every agent shares one usage counter."""
    from agents import AGENTS  # imported here so agent files can import this module

    agent = AGENTS[role]
    audit(deps, role, "agent_start", prompt=prompt, model=MODEL_NAME)
    step = 0
    limits = UsageLimits(request_limit=deps.request_limit, total_tokens_limit=deps.token_limit)
    async with agent.iter(prompt, deps=deps, usage=usage, usage_limits=limits,
                          output_type=output_type) as run:
        async for node in run:
            if Agent.is_model_request_node(node):
                step += 1
                audit(deps, role, "loop_step_send", step=step, parts=_request_parts(node.request))
            elif Agent.is_call_tools_node(node):
                r = node.model_response
                audit(deps, role, "loop_step_reply", step=step, model=r.model_name,
                      parts=_response_parts(r),
                      tokens={"input": r.usage.input_tokens, "output": r.usage.output_tokens,
                              "cache_read": r.usage.cache_read_tokens})
        output = run.result.output
        u = run.usage
    audit(deps, role, "agent_done", steps=step, output=output,
          team_usage_so_far={"requests": u.requests, "input_tokens": u.input_tokens,
                             "output_tokens": u.output_tokens})
    return output


async def _run_capped(deps: TeamDeps, kind: str, role: Role, prompt: str, usage: RunUsage,
                      output_type: type | None = None):
    """Run the Boss under the caps. If a cap is hit, record it and stop cleanly."""
    try:
        async with SHOP_TOOLSET:  # one MCP server connection for the whole team
            result = await run_agent(role, prompt, deps, usage=usage, output_type=output_type)
    except UsageLimitExceeded as exc:
        audit(deps, "system", "cap_hit", kind=kind, reason=str(exc),
              token_limit=deps.token_limit, request_limit=deps.request_limit)
        log_usage(deps, kind, usage, outcome=f"stopped: {exc}")
        raise SystemExit(f"Stopped by the safety cap: {exc}. See output/audit_trail.json.")
    return result


async def _mcp_call(name: str, args: dict) -> dict:
    """Call one MCP tool from code (never a second tools layer: it is the same server)."""
    async with SHOP_TOOLSET:
        result = await SHOP_TOOLSET.direct_call_tool(name, args)
    if isinstance(result, dict) and set(result) == {"result"}:
        result = result["result"]
    return result


def enforce_review(decision: TicketDecision, ticket: dict, deps: TeamDeps) -> TicketDecision:
    """Code backstop for suspicious tickets: if the MCP screen flagged the ticket,
    the decision becomes needs_review and any payments or drafts are held back,
    whatever the agents said."""
    if not ticket.get("needs_human_review"):
        return decision
    held = {"approval_requests": [a.model_dump() for a in decision.approval_requests],
            "drafts": [d.model_dump() for d in decision.drafts]}
    flags = list(dict.fromkeys([*decision.security_flags, *ticket.get("suspicious_text", [])]))
    fixed = decision.model_copy(update={
        "status": "needs_review",
        "security_flags": flags,
        "approval_requests": [],
        "drafts": [],
        "next_steps": [*decision.next_steps,
                       "HELD FOR HUMAN REVIEW: the ticket text looks like an attempt to give orders "
                       "to the AI (" + "; ".join(flags) + "). Nothing was proposed or drafted."],
    })
    audit(deps, "system", "security_review_enforced", ticket_id=decision.ticket_id, flags=flags,
          agent_status=decision.status, held_back=held)
    return fixed


# ---------- owner rules checked in code (not just prompts) ----------

import re as _re

ALLOWED_DISCOUNTS = {10, 15, 50}  # student, Lock and Load, holiday blowout (owner's rules 2, 3, 11)
CUSHION = 500.0                   # owner's rule 13
_MONTHS = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_PROMISE = _re.compile(r"(arriv|ship|deliver|ready|restock|in stock|available)\w*\s+(by|on|before)\s+"
                       r"(" + _MONTHS + r"\s+\d{1,2}|\d{1,2}/\d{1,2}|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                       _re.I)


def policy_check(decision: TicketDecision, deps: TeamDeps) -> TicketDecision:
    """Check the owner's money and wording rules in code after every run. Breaking
    replies are held back from the board, and every finding is listed in policy_flags."""
    flags, keep = [], []
    for d in decision.drafts:
        text = f"{d.subject} {d.body}"
        bad = []
        for pct in {int(x) for x in _re.findall(r"(\d{1,3})\s*%", text)}:
            if pct not in ALLOWED_DISCOUNTS:
                bad.append(f"mentions {pct}% (owner discounts are 10%, 15% or 50% only)")
            elif pct == 50 and "blowout" not in text.lower():
                bad.append("mentions 50% outside a holiday blowout")
        if _PROMISE.search(text):
            bad.append("promises a fixed date")
        if bad:
            flags += [f"Draft to {d.to}: {b}" for b in bad]
        else:
            keep.append(d)
    for a in decision.approval_requests:
        if a.kind == "purchase_order" and a.cash_after is not None and a.cash_after < CUSHION:
            flags.append(f"Purchase order to {a.payee} would leave ${a.cash_after:,.2f}, below the $500 cushion: owner override needed")
    if not flags:
        return decision
    audit(deps, "system", "policy_flags", ticket_id=decision.ticket_id, flags=flags,
          held_drafts=[d.model_dump() for d in decision.drafts if d not in keep])
    return decision.model_copy(update={"policy_flags": flags, "drafts": keep})


async def run_ticket(ticket_id: int, max_depth: int = 3, token_limit: int = TICKET_TOKEN_LIMIT,
                     run_id: str | None = None) -> tuple[TicketDecision, TeamDeps, RunUsage, dict]:
    """The Boss takes one ticket; the team delegates as needed; the Boss makes the call."""
    deps = TeamDeps(run_id=run_id or uuid.uuid4().hex[:12], ticket_id=ticket_id, max_depth=max_depth,
                    token_limit=token_limit, request_limit=REQUEST_LIMIT, chain=["boss"])
    usage = RunUsage()
    audit(deps, "system", "ticket_start", model=MODEL_NAME, token_limit=token_limit)
    decision = await _run_capped(
        deps, "ticket", "boss",
        f"Work ticket {ticket_id}. Read it with get_ticket first, then use your team.", usage)
    ticket = (await _mcp_call("get_ticket", {"ticket_id": ticket_id})).get("ticket", {})
    decision = enforce_review(decision, ticket, deps)
    decision = policy_check(decision, deps)
    cost = log_usage(deps, "ticket", usage, outcome=decision.status)
    audit(deps, "system", "ticket_done", decision=decision,
          delegations=[d.model_dump() for d in deps.delegations], cost=cost)
    return decision, deps, usage, cost


def check_board_plan(plan: BoardPlan, cash_position: dict) -> dict:
    """Code checks on the Boss's board plan, so the plan isn't trusted blindly:
    each payment appears once, amounts match the books, running cash never goes
    negative, and rent comes before vendor invoices (the owner's rule 1)."""
    owed = {("invoice_payment", i["id"]): i["amount"] for i in cash_position["open_invoices"]}
    owed.update({("rent_payment", r["id"]): r["monthly_rent"] for r in cash_position["rent_due"]})
    problems, seen, cash = [], set(), cash_position["total_cash"]
    for a in plan.payment_plan:
        key = (a.kind, a.ref_id)
        if key in seen:
            problems.append(f"duplicate payment {key}")
        seen.add(key)
        if key in owed and abs(owed[key] - a.amount) > 0.005:
            problems.append(f"{key} amount {a.amount} does not match the books ({owed[key]})")
        if a.kind != "purchase_order" and key not in owed:
            problems.append(f"{key} is not an open bill in the database")
        cash = round(cash - a.amount, 2)
        if a.cash_after is not None and abs(a.cash_after - cash) > 0.005:
            problems.append(f"{key} cash_after {a.cash_after} should be {cash}")
        if cash < 0:
            problems.append(f"{key} would make cash negative ({cash})")
    kinds = [a.kind for a in plan.payment_plan]
    if "rent_payment" in kinds and "invoice_payment" in kinds and kinds.index("invoice_payment") < kinds.index("rent_payment"):
        problems.append("an invoice is ordered before rent (owner's rule 1: rent first)")
    if abs(plan.cash_after_plan - cash) > 0.005:
        problems.append(f"cash_after_plan {plan.cash_after_plan} should be {cash}")
    return {"passed": not problems, "problems": problems, "computed_cash_after_plan": cash,
            "starting_cash_from_mcp": cash_position["total_cash"]}


async def run_board(max_depth: int = 3, token_limit: int = BOARD_TOKEN_LIMIT,
                    run_id: str | None = None) -> tuple[BoardPlan, dict, dict]:
    """The Boss works every open ticket at once and makes one shared payment plan."""
    deps = TeamDeps(run_id=run_id or uuid.uuid4().hex[:12], ticket_id=None, max_depth=max_depth,
                    token_limit=token_limit, request_limit=BOARD_REQUEST_LIMIT, chain=["boss"])
    usage = RunUsage()
    audit(deps, "system", "board_start", model=MODEL_NAME, token_limit=token_limit)
    plan = await _run_capped(
        deps, "board", "boss",
        "WHOLE BOARD MODE. Read every open ticket with get_open_tickets and the cash with "
        "get_cash_position, then work each ticket with your team and return one BoardPlan.",
        usage, output_type=BoardPlan)
    cash_position = await _mcp_call("get_cash_position", {})  # the check reads the books through MCP too
    board = {t["id"]: t for t in (await _mcp_call("get_open_tickets", {}))["tickets"]}
    plan = plan.model_copy(update={"tickets": [policy_check(enforce_review(t, board.get(t.ticket_id, {}), deps), deps)
                                               for t in plan.tickets]})
    checks = check_board_plan(plan, cash_position)
    cost = log_usage(deps, "board", usage, outcome="checks passed" if checks["passed"] else "checks failed")
    audit(deps, "system", "board_done", plan=plan, checks=checks,
          delegations=[d.model_dump() for d in deps.delegations], cost=cost)
    BOARD_PLAN.write_text(json.dumps({"run_id": deps.run_id, "at_utc": _now(), "plan": plan.model_dump(),
                                      "code_checks": checks, "cost": cost}, indent=2), encoding="utf-8")
    return plan, checks, cost
