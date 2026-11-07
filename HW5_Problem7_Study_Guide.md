# Study Guide: HW5 Problem 7, Backend Routes

_For anyone redoing this task later. What was built, how, and why. Written 2026-11-07._

---

## 1. The job in one sentence

Give the React dashboard (Problem 8) a **backend it can call**: a small web server whose addresses ("routes") show the tickets, run the AI team, stream what the agents are doing, and let a person approve or reject the money they propose.

**The assignment's run command:**

```bash
uvicorn main:app --reload --port 8000
```

You run it from `backend/`, and the backend then lives at `http://localhost:8000`.

---

## 2. The big picture

```
  Person at the dashboard (Problem 8)
        │  clicks: show tickets · run ticket · approve · reject · reset
        ▼
  ┌─────────────────────────────────────────────┐
  │ FastAPI backend   backend/main.py   :8000   │   ← Problem 7
  │  /api/tickets  /api/tickets/{id}/run        │
  │  /api/runs/{id}  /api/events                │
  │  /api/approvals  /api/rejections            │
  │  /api/cash  /api/reset  /api/health         │
  └───────┬───────────────────────┬─────────────┘
          │ runs                   │ reads/writes shop facts ONLY through MCP
          ▼                        ▼
  Agent team (backend/team.py)   MCP server (mcp_server/server.py)
  Boss · Inventory · Accounting      │
  Facilities · Customer Service      ▼
          │ every step logged     data/campus_customs_new.db
          ▼
  output/audit_trail.json  ──► feeds /api/events and /api/tickets "latest run"
```

**The one rule that shapes everything:** agents **propose** money moves, and only `POST /api/approvals`, after a person clicks Approve, **makes** them.

---

## 3. The routes: what, how, why

| Route | What it does | How it works | Why it was built this way |
|---|---|---|---|
| `GET /api/tickets` | All tickets, each **open or resolved**, plus the team's latest decision | Calls the MCP tool `list_tickets`, then adds the latest `ticket_done` decision from the audit trail | The status comes from the database, the single source of truth, through MCP, so there's no second tools layer. The decision comes from the log, so the board can show it without rerunning AI. |
| `POST /api/tickets/{id}/run` | Starts the agent team on one ticket | Checks the ticket exists, then starts a **background task** and returns `202` with a `run_id` at once | A run takes about 40 seconds, and a web page shouldn't freeze. Returning a receipt right away is the standard pattern for slow work. |
| `GET /api/runs/{run_id}` | queued → running → done or failed, with the decision and cost | Reads an in-memory dictionary of runs | So the board knows when to stop showing a spinner |
| `GET /api/events` | What each agent **said** and which **tools** it used, plus hand-offs, decisions and warnings | Reads `output/audit_trail.json` and turns raw log entries into simple events. `?after=<seq>` returns only new ones. | The agents already log every step, so the backend just translates. `after` lets the board refresh cheaply. |
| `POST /api/approvals` | A person approves one payment or purchase order. **The only route that changes cash.** | (1) refuses while a run is going, (2) **refuses anything no agent proposed** (searched in the audit trail), (3) calls the human-only MCP tool `pay_approved_request`, which checks again and pays in one transaction | Layered safety: the backend checks the proposal is real, and the MCP tool checks the money. The amount is always taken from the database, never from the click. |
| `POST /api/rejections` | A person rejects a proposal | Checks it was proposed, then writes a `human_rejection` event | It leaves a record of the human decision, and cash never changes |
| `GET /api/cash` | The checking balance from `cash_accounts`, plus what's owed and recent payments | Calls the MCP tool `get_cash_position` | One call gives the board everything for a Cash panel |
| `POST /api/reset` | Puts the database back to the original values | Runs `scripts/reset_db.py`, which copies the original over the working copy and checks they match | The assignment requires a reset before a full run. Logs are **kept**, never wiped. |
| `GET /api/health` | Up? Busy? Which model? | Simple check | Lets the board show "server offline" |

### Safety built into the pay tool (MCP `pay_approved_request`)

| Situation | What happens |
|---|---|
| No approver name | Refused |
| Over $1,000 without a **different** second approver (owner's rule 24) | Refused |
| Cash would go below $0 | Refused |
| Invoice already paid | Refused |
| Purchase order to a vendor that still has an unpaid invoice | Refused |
| A successful payment | Lowers cash, writes a `payments` row, and marks the invoice paid or moves rent's due date forward a month, **all together or not at all** (one transaction) |
| A purchase order leaves less than the $500 cushion | Paid, but with a warning |

---

## 4. How it was built, step by step

1. **Install** FastAPI and Uvicorn into the project's own Python, `.venv`, and add them to `requirements.txt`.
2. **Add the MCP tool `list_tickets`**, because the existing tool only listed *open* tickets and the board needs open **and** resolved.
3. **Write `backend/main.py`:**
   - the FastAPI app;
   - **CORS**, the permission for the React page on port 5173 to call port 8000;
   - the routes in section 3.
4. **Make runs non-blocking:** `asyncio.create_task` runs the team in the background, plus a **lock** so only one run happens at a time. One cash picture means no mixed-up payments.
5. **Translate the audit trail into events**, giving each a number (`seq`) so the board can ask for "everything after #625."
6. **Extend the pay tool** with purchase orders and the second approver, and let agents' payment proposals carry SKU, size and qty.
7. **Add approve, reject, cash and reset** routes.
8. **Switch to port 8000** and the exact assignment command, and test that `--reload` doesn't break the MCP connection.

---

## 5. How it was tested

| Test | Result |
|---|---|
| FastAPI test client: health, tickets, events, errors | 200s; a bad ticket or run → 404; `after=` returns only new events |
| **Live run of ticket 102** through `POST /run` | 202 and then done in 39 s, $0.0029, 18 events: Boss → Facilities (`get_lease`) → Accounting (`get_cash_position`) → Customer Service → decision |
| A second run while busy | 409 "busy" |
| **Money flow on the working database** | $3,400 → rent (Chloe + Pat) **$1,000** → invoice 501 **$160** → reset → **$3,400**, database byte-identical to the original |
| Refusals | One approver on rent (400), double pay (400), not proposed by an agent (404), blank name (422) |
| Pay tool on a throwaway copy | Purchase order to a blocked vendor refused; $264 order with $160 cash refused; $8 tee order paid with a cushion warning |
| Reject | Recorded, cash unchanged, an event shown |
| The exact command with `--reload` | Works. Activate `.venv` first. |

**How to rerun:**
1. From `backend/`, run `..\.venv\Scripts\activate`, then `uvicorn main:app --reload --port 8000`.
2. Open `http://localhost:8000/docs` and use "Try it out" on each route.

---

## 6. What went wrong, and the lesson

| Problem | Cause | Fix and lesson |
|---|---|---|
| A bare `uvicorn` failed | It ran the computer's main Python, whose FastMCP is broken | **Activate the project's `.venv` first.** Always check *which* Python a command uses. |
| The port 8000 server answered with **old code** | A test server I started in the background (from a sandboxed shell) half-stopped. Its worker kept the port and stopped reloading, and it was invisible to the user's tools. | Ended it with the user's OK. **Start servers only where you can see and stop them** (the Terminal panel), never as a hidden background job. |
| A checklist command turned into gibberish (`\a` became a bell character) | An inline script on Windows collapsed a backslash | Edit files with a real editor tool. **Scan for control characters** after scripted edits. |
| Customer Service called `get_lease` | The plan expected no tools from it, but it looked up a fact itself | Noted for the Problem 6 "Actual" comparison: prompts need "use the facts you're given." |
| Attack-test ticket 901 shows up in events | The audit trail is shared by every run, including tests | The dashboard should filter to tickets 101–103 |

---

## 7. Why these design choices matter in a real business

- **One door for money.** If cash can only change through one route, you only have to secure and audit one place.
- **Check twice, in different places.** The backend checks the proposal is real, and the MCP tool checks the money. A bug in one is caught by the other.
- **Amounts come from the books.** A screen, an agent or a hacker can't type a new dollar figure into a payment.
- **Two people over $1,000.** Separation of duties is basic fraud control.
- **Don't freeze the screen.** Slow AI work goes in the background with a receipt and live progress.
- **Logs are forever.** The audit trail is never wiped, even on reset. That's how you answer "who approved this, and why?" months later.

---

## 8. Redo it from a blank page (no help)

- [ ] Make a FastAPI app in `backend/main.py`, with CORS for `http://localhost:5173`
- [ ] `GET /api/tickets` through an MCP tool that lists **all** tickets with status
- [ ] `POST /api/tickets/{id}/run`: 404 if unknown, 409 if busy, a background task, and `202` with a `run_id`
- [ ] `GET /api/runs/{run_id}` for status and result
- [ ] `GET /api/events`: read the audit trail, translate it into said / tool_call / handoff / decision, and support `after`
- [ ] `POST /api/approvals`: must match an agent proposal, then call the human-only MCP pay tool
- [ ] The pay tool: amount from the database, no negative cash, no double pay, a second approver over $1,000, blocked vendors refused, one transaction
- [ ] `POST /api/rejections`: record it, pay nothing
- [ ] `GET /api/cash` and `POST /api/reset` (logs kept)
- [ ] Run `uvicorn main:app --reload --port 8000` from `backend/` with `.venv` active
- [ ] Prove it: a live run, plus $3,400 → $1,000 → $160 → reset → $3,400, plus every refusal

## 9. Check yourself (answers below)

1. Why does `POST /run` return immediately instead of waiting for the answer?
2. Which single route can change cash, and what two checks happen before money moves?
3. Where does the payment amount come from, and why not from the click?
4. Why is there a lock so only one run happens at a time?
5. What does `?after=625` on `/api/events` do?
6. Why must you activate `.venv` before `uvicorn`?
7. What does reset change, and what does it keep?

<details><summary>Answers</summary>

1. A run takes about 40 seconds. Returning a `run_id` keeps the page responsive while it polls for progress.
2. `POST /api/approvals`. (a) An agent must have proposed it (checked in the audit trail). (b) The MCP pay tool re-checks the amount, cash, double pay, the second approver and the vendor block.
3. From the database (invoice amount, rent, or qty × unit cost). A click or an agent could be wrong, or tampered with.
4. So cash and stock don't change in the middle of a run, and so two runs don't propose the same payment at the same moment.
5. It returns only events newer than #625, so the board fetches just what's new.
6. A bare `uvicorn` runs the computer's main Python, which has a broken FastMCP. `.venv` has the right libraries.
7. It copies the original database over the working copy (cash, invoices, leases, payments, stock). It keeps the audit trail and usage log.

</details>

---

## 10. Better prompts for this problem, and why

**My actual prompts:**
- "problem 7: Backend Routes"
- "Your React frntend dashboard … needs a backend it can call … return the three tickets … run your agent … return recent agent events"
- "approve a payment or purchase after human clicks approve …; return the current checking balance …; reset the database …"
- a screenshot of the run command
- "list each route in one line …"

They worked, but the details arrived in **five pieces**, and two important facts (port 8000 and the exact run command) came last, after the server was already built on another port.

### A stronger single prompt

> **Problem 7: Backend Routes.** Goal: a FastAPI backend in `backend/main.py` that my React dashboard (next problem) will call.
> **Run it with exactly:** `uvicorn main:app --reload --port 8000` from `backend/`, so it lives at `http://localhost:8000`. Allow the React dev server (`localhost:5173`).
> **Routes:**
> (1) list the three tickets and whether each is open or resolved;
> (2) take a ticket id and run the agent team, returning right away because runs are slow;
> (3) recent agent events, showing what each agent said and which tools it used, refreshable;
> (4) approve a payment or purchase order after a human clicks Approve. Agents only prepare payments, so this route is the only one that changes cash, and it must only pay what an agent proposed;
> (5) reject a proposal (recorded, nothing paid);
> (6) the current checking balance from `cash_accounts`;
> (7) reset the database to the original values.
> **Rules:**
> - shop facts only through the MCP server;
> - amounts from the database;
> - no negative cash;
> - a second approver over $1,000.
>
> **Done means:**
> - a live run of one ticket through the API;
> - $3,400 → approve rent and invoice → $160 → reset → $3,400;
> - every refusal tested;
> - each route listed in one line with its URL in `output/harness.md`.
>
> Only this problem. Before building, tell me what's unclear. Afterward, explain it in basic terms and update my checklist.

### Why each part helps

| Part of the prompt | Why it matters |
|---|---|
| **The exact run command and port first** | It avoids rebuilding later. Here, 8005 had to be switched to 8000 after the fact. |
| **"Returning right away because runs are slow"** | It names the design need, not just the feature |
| **"Only route that changes cash" + "only pay what an agent proposed"** | It turns a grading rule into something code can enforce |
| **Rules (MCP only, amounts from the database, no negatives, second approver)** | Limits are the part I tend to leave out (my pattern from Problem 1) |
| **"Done means" with real numbers** | It gives a pass or fail I can check myself, not "it works" |
| **"Tell me what's unclear first"** | It catches blind spots before code is written |
| **"Explain in basic terms, update my checklist"** | It keeps the learning loop going every time |

**More:** the full prompt sheet is the "Prompt-writing coach" section of `HW5_Checklist.md`. It has my question types with better versions, an 8-prompt library and the before-I-send checklist.

### Reusable prompt patterns from this problem

1. **"Use this exact command: ___. Check which Python and libraries it really runs."** This catches the wrong-Python problem early.
2. **"Slow work returns a receipt now, and progress comes from ___."** Use it for any AI step a web page triggers.
3. **"Only route ___ may change ___, and only after ___."** Use it for any money, delete or send action.
4. **"Test the happy path with these numbers: ___, and these refusals: ___."** It makes testing specific.
5. **"Start servers in my Terminal panel so I can see and stop them."** It avoids hidden leftover servers.
6. **"List what's still risky (red flags) and what new opportunities this opens."** It builds the business judgment the class is really teaching.

---

## 11. Biggest lessons from HW5 so far

1. **Never trust the prompt alone for anything that matters. Back it with code.** The fake "owner" ticket was stopped by three layers: a code screen, a prompt rule and a code backstop.
2. **One door for money, checked twice.** Agents only propose, and one route moves cash. The backend checks that an agent really proposed it, and the MCP tool checks the money again.
3. **An agent follows only the rules it's given.** The first run ignored the $840 bill when it worked out cash. Test on real tickets, find the gap, then write the rule.
4. **Full connectivity needs stop rules.** 6 hand-offs fell to 3 with "no self, no loop, depth limit" plus clear routing.
5. **Study the data before building.** One overdue invoice blocked two tickets, and paying both bills leaves only $160. An "Expected" plan made the results testable.
6. **The business decisions are the owner's, not the AI's.** Bill priority, discounts and partial orders were all decided by the owner, and the agents improved right away.
7. **Give the key facts first, in one prompt.** The port and run command arriving last caused rework.
8. **Check what's really running.** A bare `uvicorn` used the wrong Python, and a hidden old server answered with old code.
9. **Prove it with numbers and keep the evidence.** Checksums, $3,400 → $1,000 → $160 → $3,400, an audit trail that's never wiped, and tests you can rerun.

**Takeaway:** let AI do the legwork, but keep people in charge of decisions and money. Enforce that in code, and prove it with tests.

---

## 12. Every safety rule enforced in code

### 12.1 Money: AI proposes, people decide

| Rule | Where in the code | How it's enforced | Proven by |
|---|---|---|---|
| **Agents can't pay** | `backend/team.py`: `AGENT_TOOLSET = SHOP_TOOLSET.filtered(...)` | The pay tool is removed from every agent's tool list | The agents' tool list has 7 tools, without `pay_approved_request` |
| **Backup lock if the filter ever fails** | `team.py`: `_guard_tool_call` | Any agent call to a human-only tool is refused and logged (`blocked_human_only_tool`) | Attack test: "agents never called pay tool" ✅ |
| **Only one route moves cash** | `backend/main.py`: `POST /api/approvals` | It's the only code path that calls `pay_approved_request` | Route list; the money test |
| **You can only approve what an agent proposed** | `main.py`: `_proposals()` + `_matches()` | Searches the audit trail for a matching proposal, or returns 404 | "Not proposed by any agent" → 404 |
| **An approver name is required** | `main.py`: `ApprovalIn.approved_by` (`min_length=1`) and the pay tool | A blank name is refused at the route (422) and in the tool | Blank approver → 422 |
| **Two different people over $1,000** | `mcp_server/server.py`: `SECOND_APPROVER_OVER = 1000` | Refused without a *different* second name; "Chloe" + "chloe" is refused | One approver on rent → refused; Chloe + Pat → paid |
| **The amount comes from the books, never the click** | `pay_approved_request` | Reads the invoice amount, the rent, or qty × `unit_cost` from the database | Every payment matched the database |
| **Cash never goes negative** | `pay_approved_request` | Refused if balance minus amount is below 0 | $264 order with $160 cash → refused |
| **No double payment** | `pay_approved_request` | Refused if the invoice isn't `open` | Invoice 501 a second time → refused |
| **No orders from a vendor you still owe** | `pay_approved_request` (purchase orders) | Refused if the vendor has any open invoice | Hoodie order while invoice 501 was unpaid → refused |
| **All or nothing** | `pay_approved_request`: `with conn:` | Cash, the payments row, and the invoice or lease update happen in one transaction | The payments table and the balance always agreed |
| **Every payment says who approved it** | The `payments.approved_by` column | Saves "Chloe + Pat" | Payments rows after the test |
| **No money moves mid-run** | `main.py`: `_run_lock` | Approve and reset return 409 while the team is working | Second run while busy → 409 |
| **A rejection pays nothing** | `main.py`: `POST /api/rejections` | It only writes a log entry | Cash stayed $3,400 |

### 12.2 Facts: no made-up data

| Rule | Where | How |
|---|---|---|
| **One source of shop facts** | `team.py`: agents get only the MCP toolset plus `ask_teammate` | No second tools layer. The backend reads through MCP too (`_mcp_call`). |
| **Look-up tools can't change data** | `server.py`: `_connect()` opens with `?mode=ro` | The database is opened read-only, so a write is impossible |
| **Missing means missing** | Every MCP tool | Returns `found: false` instead of guessing (size XXL, invoice 999, lease 99) |
| **"Today" is the shop's date** | `server.py`: `_shop_today()` | Every overdue or due-soon count uses `desk.date_today` |
| **The board plan is checked against the books** | `team.py`: `check_board_plan()` | Flags duplicate payments, amounts that don't match, wrong running cash, negative cash, and invoices ordered before rent |
| **Answers have a fixed shape** | `backend/models.py` (Pydantic) | Agents must return `TicketDecision` or `AgentReport`, and status must be one of the allowed values |

### 12.3 Attacks: ticket text is data, not orders

| Rule | Where | How | Proven by |
|---|---|---|---|
| **Screen every ticket** | `server.py`: `_SUSPICIOUS` patterns plus `_with_screen()` | Flags fake authority, "skip approval", tool names, "send $X to", free goods, "don't mention" | Attack flagged 7 ways; real tickets 0 |
| **The code backstop** | `team.py`: `enforce_review()` | A flagged ticket is forced to `needs_review`, and any payments or drafts are removed, whatever the agents said | Attack test: "flagged" ✅, "no reply drafted" ✅ |
| **Attack testing on a copy** | `scripts/attack_test.py` | A poisoned ticket in a throwaway database, scored on 8 checks | 8 of 8 passed, real databases unchanged |

### 12.4 Runaway costs and loops

| Rule | Where | Setting |
|---|---|---|
| **No asking yourself** | `team.py`: `ask_teammate` | `refused_self` |
| **No sending work back up the chain** | `ask_teammate`, using `chain` | `refused_loop` |
| **Hand-off depth limit** | `TeamDeps.max_depth` | 3 |
| **Model-call cap** | `UsageLimits(request_limit=...)` | 60 per ticket, 120 per board |
| **Token cap** | `UsageLimits(total_tokens_limit=...)` | 120,000 per ticket, 300,000 per board. The 3,000-token test stopped cleanly and was logged as `cap_hit`. |
| **One run at a time** | `main.py`: `_run_lock` | A second run gets 409 |

### 12.5 The model rule and secrets

| Rule | Where | How |
|---|---|---|
| **Only `gpt-6-luna`** | `team.py`: `MODEL_NAME`, used by every agent through `build_agent()` | One name in one place. Every reply's model is logged, and the attack test checks it. |
| **The API key stays private** | `team.py`: `build_shop_toolset()` | `PORTKEY_API_KEY` is removed before the MCP server starts. The key is only checked as set, never printed. |
| **No secrets in the repo** | `.gitignore` | `.env` and `.venv` are excluded |
| **No real emails** | By design | No send tool exists anywhere. Replies are only `Draft` objects. |

### 12.6 Records that can't be erased

| Rule | Where | How |
|---|---|---|
| **The audit trail is append-only** | `team.py`: `_append_json()` | Each write adds one entry. A damaged file is set aside, never deleted. |
| **The usage log is append-only** | `log_usage()` | Tokens and dollars per run |
| **A reset keeps the logs** | `main.py`: `/api/reset` and `scripts/reset_db.py` | Only the database is restored, checksum-verified. A reset event is added. |
| **The original is never touched** | `campus_customs.db` plus `CAMPUS_DB` for tests | Write tests ran on throwaway copies, and checksums proved it |

### 12.7 The honest part: rules that live only in prompts

These are **not** enforced in code yet. An agent *could* break them, and nothing would stop it:

| Rule | Risk | How to move it into code |
|---|---|---|
| **10% student / 15% military / 50% holiday discount caps; no combining** | An agent could promise 30% in a draft | Check the discount in drafts and decisions against the rules |
| **$500 cash cushion** | Only a warning, not a refusal | Refuse optional purchase orders below $500 unless the owner overrides |
| **Rent first, then vendor bills** | Checked only in the whole-board plan, not in single tickets | Order approvals by priority in the approve route |
| **Reorder exactly the shortfall** | An agent could propose 50 hoodies | Compare purchase-order qty with stock vs. asked |
| **Never promise a fixed date** | Draft wording isn't checked | Screen drafts for dates before showing them |
| **Who the Boss calls first; no specialist-to-specialist hand-offs** | Only prompts and the depth limit | Compare the audit trail to the Problem 6 plan |
| **Approvers are real people** | Anyone can type any name | Sign-in on the dashboard |
| **A rejection blocks a later approval** | Not enforced | Make approve refuse anything rejected since its last proposal |

**The pattern:** everything involving **money, data and attacks** is enforced in code and tested. **Business judgment** (discounts, wording, priorities) is still trusted to the prompts. That's the next layer to harden.

### Check yourself (more)

8. Name the two layers that stop an agent from paying, and where each lives.
9. Which safety rules are still only in prompts, and which one would you move into code first?

<details><summary>Answers</summary>

8. The tool filter (`AGENT_TOOLSET` in `team.py`) removes the pay tool, and `_guard_tool_call` refuses it if it ever slips through. The human route and the MCP tool then check the money again.
9. Discount caps, the $500 cushion, rent-first in single tickets, reorder size, no fixed dates, call order, real approver identity, and reject-blocks-approve. A good first pick is discount caps or reject-blocks-approve, because both touch money directly.

</details>
