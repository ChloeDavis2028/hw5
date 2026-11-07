# HW5 Checklist: Shop Agent Team

_Last updated: 2026-11-07 (Problems 1–10 done, plus the better-product pass; reflection and "what was lacking" lines written; Problem 11 waits for my go)_

## Status update (from the AI agent's side)

**In one line:** Campus Customs now has a working AI back office:
- five crew agents and a learning agent ("Flight Instructor"), all on `gpt-6-luna`;
- 12 MCP tools, 4 of them backend-only;
- a FastAPI backend with 15 routes, on http://localhost:8000;
- a boutique aviation-styled React board, on http://localhost:5173.

All 3 tickets are resolved. Cash went $3,400 → $160 through two signed-off payments, and the cash check passes 4/4.

### Scoreboard

| Problem | Status | Proof it works |
|---|---|---|
| 1. Vibe coder prompts | Done (ongoing) | `AI_prompts.md`: every prompt in my exact words |
| 2. Study the database | Done | `output/database_study.md`, harness §1, working copy `data/campus_customs_new.db` |
| 3. MCP server | Done | `mcp_server/server.py` and README; tool outputs matched the database (harness §2) |
| 4. Connect the vibe coder | Done | `.mcp.json`; `output/mcp_smoke.json` (7/7 script calls + 4 native) |
| 5. Agent team + more tools | Done | `backend/`: 5 agents, my 29 shop rules, audit trail, caps, attack test 8/8 (harness §4–11) |
| 6. Plan the tickets | Done | `output/desk_tickets.html`: Expected per ticket (harness §12) |
| 7. Backend routes | Done | `backend/main.py` (harness §13); study guide `HW5_Problem7_Study_Guide.md` |
| 8. Agent dashboard | Done | `frontend/` at :5173, warm blue/grey boutique look with aviation touches (harness §14, `output/design.md`) |
| 9. Final run evidence | Done | Reset → ran 101/102/103 → approved → **$160 matches `cash_accounts`**. Actual sections, Cash tab, `output/resolved_tickets.json`, `output/resolved_board.html` |
| 10. Reflection | Done (reflection drafted from my run; reread it) | Flight Instructor learning agent; `output/learning_report.html`; Debrief panel; Reflection tab; `output/new_problems.md` |
| 11. Public GitHub repo | **Waiting for my go** (I said "wait until i say so") | Nothing pushed yet. See Problem 11 below. |
| Better product pass | Done | Approver sign-in, rejections block approval, rules checked in code, saved replies, AI spend, whole-board button, smarter debrief (harness §16) |

Study guides: `HW5_Problem7_Study_Guide.md` and `HW5_Problems8-10_Study_Guide.md`.

### The pieces

| Piece | What it does (plain English) | Status |
|---|---|---|
| Database | The shop's facts: tickets, stock, bills, rent, cash, payments, and saved replies | Working copy + untouched original for resets |
| MCP server | The only door to the data: 12 tools, 8 for agents, 4 backend-only (pay, resolve, save and read replies) | Built and tested |
| Agent team | Boss, Inventory, Accounting, Facilities, Customer Service | Built and tested |
| Learning department | The Flight Instructor debriefs after every run, grades each agent and proposes fixes | Built and tested |
| Backend | 15 routes: tickets, run a ticket or the whole board, events, sign-in, approve, reject, replies, cash, AI spend, reset, learning | Running at :8000 |
| Board | Tickets, the live crew, the flight log, the flight report, the debrief, sign-in approvals, cash, AI spend | Running at :5173 |

### What it can do now, and what it still can't

| Can do | Can't do yet |
|---|---|
| Run one ticket or the whole board, live on screen | Take money **in** (sales, deposits). The assignment says cash only goes out, so this was left out on purpose. |
| Approvals by **signed-in** people, two over $1,000, owner-only cushion override | Club prices and perks (Crest Society, Seasonal Editions, Atelier) are mine to set |
| Block approval after a rejection; refuse negative cash and double pay | Plan ahead with a calendar (needs my Seasonal Editions dates) |
| Check discount caps, fixed-date promises and the cushion **in code** after every run | Fewer hand-offs on simple tickets (would change the Problem 6 plan; a later experiment) |
| Save replies on the board (never sent); show AI spend vs. a budget | Real email sending (never; drafts only, by rule) |
| Debrief after every run and keep a continuous report | |

### My open items

- [x] **My reflection** in the Reflection tab (I asked "Yes, draft it"). I'll reread it and edit any line that doesn't sound like me, in `scripts/build_reflection.py`, then rebuild.
- [x] All 10 "what was lacking" lines in `AI_prompts.md`, each with a **Stronger prompt** (I asked "fix and execute")
- [ ] Say **go** on Problem 11, then submit the repo URL on Canvas myself
- [ ] Set the **AI budget** (placeholder $5.00 a month, via the `AI_MONTHLY_BUDGET` setting)
- [ ] Set prices and perks for The Crest Society, Seasonal Editions and The Atelier
- [ ] Confirm rules 11–24 (my "fix and recommend" approvals): 15% military, $500 cushion, 50% deposit, two approvers over $1,000
- [ ] Rerun 101 and 103 so the debrief can confirm the Customer Service fix there too (102 improved from B to A)
- [ ] Public GitHub repo (the last problem): keep `data/approvers.json`, `data/.session_secret` and `output/test_accounts.md` out (already in `.gitignore`)

## The assignment (in my words)

> "this is the assignment about the agentic team that runs the shop. Open tickets land on a board - customer orders, rent, unpaid bills, discount requests, anything the shop needs handles. You will build three pieces that talk to each other: an MCP server, a FASTAPI backend with a multiagent team, and a React dashboard so a human can watch the agents work and approve the requests."

Syllabus: Lectures 9–10 (MCP servers and orchestration). Due 11/6 at 8 am.

## The agent team (in my words)

> "Your team has full connectivity - any agent may delegate tasks to any other agent for help. You will build a boss (reads each ticket, decides who shuld work on it and make final calls), Inventory (checks stock by SKU and size, spots shortfalls and figures out which vendor can restock), Accounting (watches cash and onvoices, checks margins, and prepares payments or purchase orders for human approval) and Facilities (handles the shopspace side as in leases, rent etc)"

| Agent | Job |
|---|---|
| Boss | Reads each ticket, picks who works on it, makes the final call |
| Inventory | Stock by SKU and size, shortfalls, which vendor can restock |
| Accounting | Cash, invoices, margins; prepares payments or purchase orders for human approval |
| Facilities | Shop space: leases, rent |

Any agent can hand work to any other agent ("full connectivity").

## Shop rules (from the assignment page)

Each rule is ticked only once the code enforces it.

- [x] `desk.date_today` is "today". Use it, not the computer clock, to decide what is overdue. _(The MCP tools do this.)_
- [x] Vendor lead times come from the `vendors` table. _(`get_invoice` returns `lead_days`.)_
- [x] A vendor won't ship while it has an open unpaid invoice. _(`get_invoice` and `list_vendors` return `can_ship`, and the pay tool refuses purchase orders to a blocked vendor.)_
- [x] **Every payment needs human approval** (points off if not). After paying, update the relevant table. _(Agents can't see the pay tool. Only `POST /api/approvals` pays, only for an agent's proposal. One transaction updates `cash_accounts`, `payments`, and `invoices` or `leases`.)_
- [x] Not enough cash: the pay tool refuses. Balances never go negative. _(Tested: $264 with $160 → refused.)_
- [x] Cash only goes out. No revenue is modeled. _(There's no tool that adds cash, and deposits are never counted until received.)_
- [x] Reset the database to its original values before a full run. _(`scripts/reset_db.py`, `--reset`, `POST /api/reset`, checksum-verified.)_
- [x] Never email customers or call real vendors. Drafts stay on the board. _(No send tool exists; replies are `Draft` objects only. Saving drafts *on the board* is still to do.)_
- [x] Use `PORTKEY_API_KEY` and **only `gpt-6-luna`** for every agent (points off for any other model in code or runs). _(One `MODEL_NAME`; every reply in the audit trail is `gpt-6-luna`.)_
- [x] One problem at a time, typed in my own words. _(Ongoing.)_
- [ ] Final submission: a public GitHub repo.

## Problems

### Problem 1: Vibe coder prompts

- [x] Create `AI_prompts.md` at the start of the assignment
- [ ] Keep it updated after every problem (ongoing until the end)
- [ ] Write my own "what was lacking" sentence when I send a follow-up

**What I did:** created the prompt log in the HW6 format: one section per problem, my exact words, a follow-up, and a blank "lacking" line. I also logged the prompts from before Problem 1 and added a note about my screenshots. Below, I started a prompt-writing coach so I can keep improving after the class ends.

### Problem 2: Study the Campus Customs database

- [x] Download data.zip (course site, 2,114 bytes) into `Given/` and unzip it into `My Work/data/`
- [x] Open `data/campus_customs.db` and look at every table and field (9 tables)
- [x] Copy the original to `data/campus_customs_new.db` (the working copy for later problems)
- [x] Study the three open tickets (101, 102, 103) and how they link to other tables
- [x] Write the findings in `output/database_study.md`, with a table diagram
- [x] Start `output/harness.md`: each table's fields plus one line on why it matters to the agents. This file keeps growing.

**What I found:** the main links are tickets → invoices and leases, invoices → vendors, and stock in inventory by SKU **and** size.

| Ticket | Request | Problem it runs into |
|---|---|---|
| 101 | Tee, size S | None in S. It's tied to invoice 501, Bulldog Print Co's $840 bill, which is 3 days overdue, so that vendor won't ship until it's paid. |
| 102 | Rent | $2,400 due 9/2. |
| 103 | 20 hoodies in M, at a discount | Only 8 in stock, and they'd come from the same blocked vendor. |

Cash is $3,400, so after both bills only $160 is left.

### Problem 3: Build the MCP server

- [x] Write the MCP server in `mcp_server/` with FastMCP (`mcp_server/server.py`)
- [x] Point it at `data/campus_customs_new.db` (read-only for these tools)
- [x] Build three tools with clear names, one per ticket: `check_stock` (103), `get_invoice` (101), `get_lease` (102)
- [x] Never invent data: a missing row returns `found: false`
- [x] List the three tools in `output/harness.md` with tables, ticket, and why each one fits that ticket
- [x] Add `mcp_server/README.md`: what the server is for, which database, and the three tools

**What I did:**
- Made a project virtual environment (`.venv`) and installed FastMCP 4.1.6, because the computer's main Python had a broken copy.
- Added `requirements.txt` and `.gitignore`.
- Tested each tool by calling it directly. The outputs matched the database, and the database was unchanged afterward.

### Problem 4: Add the MCP server to the vibe coder and test each tool

- [x] Save the connection JSON in `.mcp.json` at the project root (`My Work/`)
- [x] Check that the JSON is valid and actually starts the server (all 3 tools answered over MCP)
- [x] Test each of the three tools over MCP and save the evidence in `output/mcp_smoke.json`: 7/7 pass, database unchanged (`scripts/mcp_smoke.py`)
- [x] Each entry includes the prompt asked, the tool name, the tool output, and a value-by-value match against `data/campus_customs_new.db`
- [x] Open a Claude Code session in `My Work`, approve `campus-customs`, and have the vibe coder call each tool itself _(4 native calls in `vibe_coder_calls` of `output/mcp_smoke.json`; all match the database, which is unchanged)_

**Note:** the first smoke test ran from a script, because the main session runs from `AI Claude YO`. The second session, opened in `My Work`, made the native calls.

### Problem 5: Build the agent team and grow the MCP tools

- [x] Five roles with Pydantic AI: Boss, Inventory, Accounting, Facilities, Customer Service (`backend/agents/<role>.py`)
- [x] One prompt file per agent in `backend/prompts/`, for now as **example drafts** I will rewrite
- [x] Data types in `backend/models.py`: `TicketDecision`, `AgentReport`, `ApprovalRequest`, `Draft`, `Fact`, `Delegation`, `TeamDeps`
- [x] Agent loops plus full connectivity: `ask_teammate` reaches any of the four other roles, with no-self, no-loop and depth-3 limits (`backend/team.py`)
- [x] Only `gpt-6-luna` through Portkey with `PORTKEY_API_KEY`, for every agent
- [x] Grow the MCP tools: `get_open_tickets`, `get_ticket`, `list_vendors`, `get_cash_position`, plus the human-only `pay_approved_request`
- [x] No second tools layer: agents get shop facts only from MCP over `data/campus_customs_new.db`
- [x] Append every agent loop step to `output/audit_trail.json`, never wiping it
- [x] Live test on ticket 102: `needs_approval`, a $2,400 rent payment proposed, a draft reply, and the database unchanged
- [x] Harness §7 lists every agent and every MCP tool, with the tables each tool uses
- [x] Harness §8 is the safety section: real-business guardrails (✅ in place, ⚠️ partial, ❌ to add) and token limits
- [x] `mcp_server/README.md` lists all the tools to match the server (8 at the time; 9 after Problem 7 added `list_tickets`)
- [ ] **Rewrite the five prompts in my own words** with the shop rules each agent needs
- [ ] Run tickets 101 and 103 once my prompts are in

**What I did:**
- Installed Pydantic AI 2.66 in `.venv` and added it to `requirements.txt`.
- Each agent is `gpt-6-luna`, plus its prompt file, plus the MCP tools, plus `ask_teammate`.
- `run_ticket.py` runs one ticket from the command line.
- Tested the pay tool on a throwaway copy: it pays the invoice, pays the rent, then refuses a second rent payment ($160 is less than $2,400).

**A gap the live run showed:**
- On ticket 102, Accounting said `cash_after` would be $1,000 after paying the rent.
- It ignored the overdue $840 invoice. If both are paid, only $160 is left.
- The example prompt never told Accounting to count everything the shop owes. That's a rule to put in my own version.

### Problem 6: Plan the three tickets

- [x] Write down what I expect the team to do on each open ticket, before the backend is wired
- [x] Build `output/desk_tickets.html`: opens by double-click, one tab per ticket (101, 102, 103)
- [x] Add empty **Cash** and **Reflection** tabs, left for later problems
- [x] Each ticket tab: a filled **Expected** section (facts with tools, who works on it, decision and status, approvals with `cash_after`, drafts, rules used, must-happen and mistake lists)
- [x] For each ticket: who the Boss calls **first** and why, the exact hand-offs expected (only the specialists needed), who is **not** called, and the MCP tools expected at each step, with a tally
- [ ] **Actual** section on each ticket tab: left empty, to fill after the agents run

**Lesson:** write the expected answer *before* running the system. Then "did it work?" has a real answer, and the mistake list becomes the scorecard.

### Problem 7: Backend Routes

- [x] `backend/main.py` with FastAPI, ready for the React dashboard (CORS for `localhost:5173`, port 8000)
- [x] Route: return the three tickets and whether each is **open or resolved**: `GET /api/tickets` (status through the new MCP tool `list_tickets`, plus the team's latest call)
- [x] Route: take a ticket id and **run the agent team**: `POST /api/tickets/{id}/run` returns a `run_id`; `GET /api/runs/{run_id}` for the result. One run at a time (409 if busy).
- [x] Route: **recent agent events** (what each agent said, which tools it used): `GET /api/events`, with `?after=` for refresh and filters by ticket, run or role
- [x] Tested: test client plus a live server, and a live run of ticket 102 through the API (39 s, $0.0029, 18 events, database unchanged)

- [x] Route: **approve a payment or purchase order** after a person clicks Approve: `POST /api/approvals`. It's the only route that changes cash, and it pays only what an agent proposed. The pay tool requires a second approver over $1,000.
- [x] Route: **reject a proposal**: `POST /api/rejections`. It is recorded as an event, and cash does not change. Tested: 200, 404 for something no agent proposed, 422 for a blank name.
- [x] Route: **current checking balance** from `cash_accounts`: `GET /api/cash`
- [x] Route: **reset the database** to the original values: `POST /api/reset`
- [x] Backend on **http://localhost:8000** with the assignment's exact command (`--reload` tested: MCP and routes work)
- [x] Harness lists every route in one line, with its URL
- [x] Tested: $3,400 → rent (2 approvers) $1,000 → invoice 501 $160 → reset → $3,400, with every refusal checked (one approver, double pay, unproposed, blank)

**How to run (the assignment's command, port 8000):** from `backend/`, run `..\.venv\Scripts\activate`, then `uvicorn main:app --reload --port 8000`. Open http://localhost:8000/docs to try every route. (Tested working with `--reload`.)

**Lesson:** an agent run takes about 40 seconds, so the run route answers right away with a `run_id`, and the board polls for events. A web page shouldn't sit frozen waiting on AI.

**Study guide:** `HW5_Problem7_Study_Guide.md`. It covers what, how and why, the tests, what went wrong, a blank-page redo list, self-check questions and better prompts.

**More lessons from Problem 7:**
- **One door for money.** Only `POST /api/approvals` changes cash, and only for something an agent proposed. The MCP pay tool checks everything again.
- **Check which Python a command really runs.** A bare `uvicorn` used the main Python, whose FastMCP is broken. Activate `.venv` first.
- **Start servers where you can see and stop them** (the Terminal panel). A hidden background test server kept port 8000 with old code.
- **Give the run command and port first.** The server was built on 8005, then moved to the assignment's 8000.

### Problem 8: Agent Dashboard

- [x] Scaffold `frontend/` with React + Vite + TypeScript (create-vite 6, React 19, Vite 6, TypeScript 5.8). Installed, and the empty project builds.
- [x] List all 3 tickets (open or resolved)
- [x] Pick one ticket and start the agent team on it
- [x] Show each agent and what it's saying or doing while the ticket runs (live cards plus a timeline, refreshed every 1.2 s)
- [x] Mark a ticket resolved when the run finishes (new backend-only MCP tool `mark_ticket_resolved`)
- [x] Short summary of what each agent did (final report, tools, hand-offs, cost, drafts)
- [x] A human approves a payment or purchase when asked (two names over $1,000; reject too)
- [x] The checking balance drops after an approved payment ($3,400 → $2,560 in the browser test)
- [x] The frontend talks to the backend at http://localhost:8000 (`API_BASE` in `src/api.ts`). The backend CORS allows the Vite origin http://localhost:5173 (and 127.0.0.1:5173). Checked: the preflight from 5173 returns `access-control-allow-origin: http://localhost:5173`, and other origins get no allow header.
- [x] Boutique, high-end look (now warm blue and grey; Cormorant Garamond with Inter)
- [x] `output/design.md` built around **my words**: the user is a military student who cares most about ease and cost, and it should feel high end, warm and inviting. It covers layout, how each agent reads differently (color, monogram, voice, three states), how resolved tickets and cash show up, the creative choices and why, accessibility, and what to add next
- [x] Research: brand-led boutiques (Aesop, Grunt Style, Black Rifle Coffee, Kith, Rowing Blazers, Aimé Leon Dore), with lessons applied, plus 12 new data inputs that would make the agents smarter (`design.md` sections 8–9, with sources)
- [x] My call: **"Brand voice + club"**, adopted as owner's rules 25 and 26. Tested:
  - ticket 103 gives one polished 5-line reply;
  - a made-up veteran order on a throwaway copy got "welcome to the Lock and Load Club, and thank you for your service" plus 15% with ID at pickup, and no invented perks.
- [x] "do it in a classy way" → **Both:**
  - **Voice:** rule 25 rewritten as an understated concierge style ("Dear ___," … "With warm regards," then Campus Customs, no exclamation marks, refined wording).
  - **Open ideas:** added as rules 27–29 (The Crest Society, Seasonal Editions, The Atelier).
  - **Tested:** ticket 103 (Atelier offered, one reply) and the veteran order (club welcome, 15% math right).
- [x] Confirmed the name **The Atelier** for club collaborations
- [x] Confirmed **The Crest Society** and **Seasonal Editions** ("yes")
- [ ] Set prices, schedules or perks for The Crest Society, Seasonal Editions and The Atelier. Until then, agents promise none.
- [x] Recolored the dashboard to **warmer blue and grey tones** ("use warmer blue and grey tones"): stone-grey paper, warm charcoal ink, a slate-blue accent, and agent colors in the blue-grey family. `design.md` updated.

**How to run (the assignment commands):**
1. Backend: from `backend/` with `.venv` active, run `uvicorn main:app --reload --port 8000`.
2. Board: from `frontend/`, run `npm run dev`. Vite prints `http://localhost:5173/`.

Both were checked running in Terminal tabs "HW5 backend 8000" and "HW5 board 5173".

**Lesson:** the "Actual" for Problem 6 now has a screen. Ticket 101 called exactly the planned agents (Inventory → Accounting → Customer Service; Facilities not called).

### Final run evidence (after Problem 8)

- [x] Reset, then ran 101, 102 and 103 on the board. All three are resolved.
- [x] Actual sections in `output/desk_tickets.html`, built from the audit trail and compared with Expected
- [x] Cash tab: start, change per ticket, end. **Checked against `cash_accounts`** by `scripts/check_cash.py` (4 checks, all PASS), and the generator refuses to save if the numbers don't match.
- [x] `output/resolved_tickets.json` and `output/resolved_board.html` (board screenshots)
- [x] Approved on the board: rent $2,400 (Chloe + Pat), then invoice 501 $840 (Chloe). Checking went $3,400 → $1,000 → $160, and the Cash tab and check passed 4/4.
- [x] Finished `output/harness.md`: a Final reference at the top (tables, MCP tools, five agents, routes, dashboard, safety rules, final run), with the build history below
- [x] Aviation touches on the boutique look ("high end boutique look but include aviation")

### Problem 10: Reflection

- [x] **Learning department** (my words: "a department that is constantly learning, updating, providing data based feedback to improve"; when asked, "A sixth agent"). It's the **Flight Instructor**, with no tools, and it debriefs after every run.
- [x] **Grades each agent per ticket and says why.** First debrief: 101 C, 102 B, 103 C. Boss, Accounting and Facilities got A; Customer Service got C for repeat lookups.
- [x] **Combines lessons** (new, repeated or fixed) across debriefs, and **turns opportunities into actions**, each with an owner and a measure
- [x] **Updates accordingly:** 2 safe Customer Service prompt fixes applied. Owner-decision updates wait for me.
- [x] **Continuous report** `output/learning_report.html`, rebuilt after every debrief: Expected vs. Actual for every ticket, grades, actions, lessons, updates and trend. Plus the **Debrief panel** on the board.
- [x] **Reflection tab** filled: one agent vs. five (with numbers), the debrief, and the new problems
- [x] **Every Reflection answer cites this app** (my grading cue: "tie every answer to this app and the three tickets ran"). About 20 links jump to the **101 / 102 / 103 / Cash** tabs on the same page. Numbers come from the final run (`resolved_tickets.json`, debrief #1, the database), not typed: $3,400 → $160, rent $2,400 (Chloe + Pat), invoice 501 $840, "8 fewer tool calls" computed. Rebuild: `.venv/Scripts/python scripts/build_reflection.py`.
- [x] Page header updated to the final state: started $3,400 → final $160 (matches cash_accounts), 3 of 3 resolved
- [x] **New problems** in `output/new_problems.md`:
  - **can solve today:** a fake vendor bank change, a tariff surcharge, the game-day rush;
  - **can't yet, with the tools and agents needed:** money coming in, returns, forecasting.
- [x] **My reflection** drafted from my run (I asked "Yes, draft it"): what I learned, what I'd do differently, what surprised me. Each cites a ticket or the Cash tab. Reread it and change anything that doesn't sound like me.
- [ ] Run a ticket again so the Flight Instructor can check whether the Customer Service fixes worked (target: 0 repeat lookups)

### Problem 11: Public GitHub repo (DO NOT START until I say so)

My words: "push the code to a public github repo so graders can clone. submit the repo url to canvas and also put it in output/github_url.txt do notpush your real .env… do include both database files under data/".

- [ ] Wait for my go
- [ ] Match the expected layout: `AI_prompts.md`, `requirements.txt`, `.env.example`, `.gitignore`, `.mcp.json`, `README.md`, `data/` (both DBs), `mcp_server/`, `frontend/`, `backend/` (main.py, models.py, prompts/), `output/` (harness.md, mcp_smoke.json, desk_tickets.html, design.md, resolved_tickets.json, resolved_board.html, audit_trail.json, github_url.txt)
- [ ] README explains: copy the original DB to the working copy for a clean run, start the MCP server, start FastAPI, start the React board, reset before a full three-ticket run
- [ ] **Never push** `.env`, `data/approvers.json`, `data/.session_secret`, `output/test_accounts.md`; push only `.env.example` (no real key)
- [ ] Push both `data/campus_customs.db` and `data/campus_customs_new.db`
- [ ] Save the URL in `output/github_url.txt`, then **I** submit it on Canvas
- [ ] Check: clone into a fresh folder and confirm the files are there and no secrets

### Better product pass (my words: "give me an update on how to provide a better product", then "all of them")

- [x] Reran ticket 102 to check the Customer Service fix: 102 went from **B to A**, with no repeat lookups. It also correctly held, because October's rent isn't due and $160 can't cover it.
- [x] Tickets show "resolved · N waiting" and "N awaiting clearance" until the payments are cleared
- [x] **A rejection blocks approval** until the team proposes it again (tested: 409, "Pat rejected this…")
- [x] **Replies saved on the board** (new backend-only MCP tools `save_drafts` and `get_drafts`; table `ticket_drafts`)
- [x] **Approver sign-in:** salted password hashes and signed 8-hour tokens. The approver comes from the sign-in, never a typed name. The second approver signs in too, and must be a different person. Test accounts are in `output/test_accounts.md`, kept out of git.
- [x] **Rules in code:**
  - `policy_check` holds any reply that mentions a non-owner discount, 50% outside a blowout, or a fixed date, and flags purchase orders below the cushion;
  - the pay tool **refuses** purchase orders below $500 unless the owner overrides.
- [x] **Vendor bank-change screen:** "new bank details / pay to this new account" is held for review
- [x] **AI spend this month** in the masthead ($0.08 of a placeholder $5.00 budget), with near-limit and over-budget warnings
- [x] **Run the whole board** button (one payment plan for all tickets)
- [x] **Smarter debrief:**
  - goals (tool calls at or below plan, 0 repeat lookups, 0 refused hand-offs, board cost of $0.015 or less, cash matches);
  - a before-and-now comparison with the last debrief;
  - the top fix on the board's front page.
- Not built, on purpose:
  - **money coming in** (it breaks the assignment rule "cash only goes out");
  - **club prices** (my decision);
  - **Planner** (needs my dates);
  - **fewer hand-offs** (it would change the graded Problem 6 plan).

## My shop rules (locked 2026-11-07)

They're in `backend/prompts/_owner_rules.md`, word for word, and every agent gets them.

| # | Rule | My words |
|---|---|---|
| 1 | Bills | "pay mandatory bills first ... rent probably". Rent first, then overdue vendor bills that block orders. |
| 2 | Holiday blowout | "50%", year end only, to clear stock |
| 3 | Student discount | "student discounts 10%" |
| 4 | Military sale | "Lock and Load Sale": **15%** (set in recommendation 11) |
| 5 | ID | "ID pick up rule works". A person checks ID at pickup. |
| 6 | Stacking | "discounts can not combine" |
| 7 | Partial orders | "partial orders only if financially responsible" |
| 8 | Reorder size | "regular short". Exactly the shortfall. |
| 9 | Hand-offs | "agent asks a team mate when no decision can be made" |
| 10 | Replies | "always reply in a fun but professional manner" |

- [x] Set the Lock and Load Sale percent: 15%, recommended and approved below

### Recommendations I approved ("fix and recommend the best outcome")

These are rules 11–24 in `_owner_rules.md`. Each one fills a gap or makes money.

| # | Rule | Why it's the best outcome |
|---|---|---|
| 11 | **Lock and Load Sale = 15%**, military and family, ID at pickup | Above the 10% student discount and well below the 50% blowout. A hoodie still earns $27.30. |
| 12 | Student groups get the 10% student discount | Settles ticket 103: $52.20 a hoodie, $30.20 profit each |
| 13 | **$500 cash cushion** for optional spending; mandatory bills can go to $0 | Rent and the overdue bill still get paid ($160 left), but the shop won't spend its last dollars on extra stock |
| 14 | **50% deposit on orders over $500**, counted only once received | The AI Club order ($1,044) brings in a $522 deposit, which pays for the 12-hoodie restock ($264) |
| 15 | Sell what's on the shelf first; offer other sizes | L (14) and XL (6) hoodies could fill the club order with no restock |
| 16 | "Financially responsible" partial order = shelf stock, or within the cushion, or deposit-funded | Turns your rule into something an agent can check |
| 17 | Cap add-on for group orders at the same discount | 40 caps are on the shelf with the best margin ($16). 20 caps at 10% off: $396 in sales, $276 profit. |
| 18 | When a vendor is blocked, ask first whether the work is ready | Invoice 501 *is* a rush reprint of the S tee. Paying it may fix ticket 101 right away. |
| 19 | Overdue vendor bills come right after rent | Avoids late fees and unblocks tickets 101 and 103 |
| 20 | Low stock alert at 3 units or fewer | Flags tee S (0), mug (0), tee L (3) and tee XL (2) before more sales are lost |
| 21 | A customer who won't wait gets in-stock options or a waitlist | Keeps the sale; never a promised date |
| 22 | QuickShip 1-day rush, fee quoted by staff | A paid upgrade; no price is invented |
| 23 | Mention custom club designs; staff discuss pricing | Opens a premium line for repeat club customers |
| 24 | Payments over $1,000 flagged "needs a second approver" | Rent ($2,400) gets two sets of eyes. The dashboard should enforce this later. |
| 25 | **Brand voice** (my choice: "Brand voice + club") | Every reply sounds like a fine New Haven shop: warm, polished, personal and never pushy. Aesop shows a consistent voice is worth billions. |
| 26 | **Lock and Load Club** (my choice) | Military families become a community: welcome them, thank them, 15% with ID at pickup, and no invented perks. Grunt Style and Black Rifle grew on community. |
| 27 | **The Crest Society** (name **confirmed**: "yes"), a seasonal subscription | "do it in a classy way": invitation only, mentioned once to repeat or group customers, no price quoted |
| 28 | **Seasonal Editions** (name **confirmed**: "yes"), timed releases | Small numbered runs tied to the campus and military calendar, at list price. Agents never announce dates, because the database has none. |
| 29 | **The Atelier** (name **confirmed**: "The Atelier"), club collaborations | For groups of 10+, a private design consultation for a co-branded capsule. Never a price, minimum or timeline. |

### Gaps still open (after the 3-ticket run, 2026-11-07)

**The agents got these wrong (prompt fixes):**
- [x] **103 marked `resolved`** with 12 hoodies not arranged. _Fixed: it's now `needs_approval`, and the decision says it isn't resolved._
- [x] **103 didn't see that its vendor is blocked.** _Fixed: it names invoice 501 and Bulldog Print Co's 5-day lead time._
- [x] **No in-stock sizes offered.** _Fixed: 101 offers tee M (5), L (3) and XL (2); 103 offers hoodie S (4), L (14) and XL (6)._
- [x] **The vendor draft wasn't signed.** _Fixed: every draft ends "Campus Customs"._
- [ ] **Same payment proposed twice:** 101 and 103 each propose invoice 501. That's part of the whole-board gap below.

**The system can't do these yet (code and data):**
- [x] **Whole-board run:** `run_ticket.py --board`. One payment plan, code-checked: rent → invoice 501 → $160, each listed once. _(2026-11-07)_
- [x] **Database reset script:** `scripts/reset_db.py`, or `--reset` on any run
- [x] **Cost in dollars:** `output/usage_log.json`. About $0.003 per ticket and $0.01 per board run.
- [x] **Token caps:** 120k per ticket and 300k per board, tested with a 3k cap that stopped cleanly
- [x] **Attack test:** `scripts/attack_test.py`, all 6 checks passed (`output/attack_results.json`)
- [x] **Flag suspicious tickets:** an MCP screen, the Boss's `needs_review` rule and a code backstop. Attack test 8/8. Review report: `scripts/review_flags.py` writes `output/security_review.md` (harness §11).
- [ ] ~~**One board, not three separate tickets.**~~ _Done above:_ Each ticket runs alone, so nobody sees that invoice 501 unblocks *both* 101 and 103, or plans cash across all three.
- [ ] **Tickets never close.** No MCP tool updates `tickets.status` or saves drafts to the board, and there's no drafts table.
- [ ] **No approval step yet.** The FastAPI routes and the dashboard that call `pay_approved_request` don't exist.
- [ ] **Second approver isn't enforced.** Rule 24 only flags it; the pay tool takes one name.
- [ ] **Purchase orders, deposits and waitlists aren't saved anywhere.** There's no table for them.
- [ ] **Assumption to confirm:** paying rent moves `next_due` forward exactly one month.

**Not done on purpose:** restocking mugs. They have the best margin (75%), but $35 for 10 mugs would push cash below the $500 cushion. Revisit once cash comes in.

## Prompt rewrite guide (Problem 5)

**How to use this:** for each agent, read "what the test run showed" and "what's missing," then answer the questions **in my own words**. Paste the answers into the blanks of the skeleton, and save the result over that agent's file in `backend/prompts/`, deleting the EXAMPLE DRAFT note. Do the "shop decisions" first, because several prompts depend on them.

### Step 0: Shop decisions only I can make

The data doesn't answer these, so the agents will guess unless I decide:

| Decision | Why it matters | Ticket |
|---|---|---|
| When cash can't cover everything, what gets paid first: rent or the overdue vendor? | $3,400 covers both bills ($3,240), with $160 left | 101, 102 |
| What's the biggest discount allowed, or the lowest margin? | The database has no discount rule. Hoodie margin is $36 on a $58 price. | 103 |
| Partial orders: can a customer get some units now and the rest later? | 103 asks for 20 M hoodies, and only 8 are in stock | 103 |
| How many units should a restock order be: exactly the shortfall, or more? | A purchase order needs a quantity | 101, 103 |
| What is "done" for a ticket: proposed, approved, or paid? | Sets the Boss's `status` | All |
| Who signs replies, and in what tone? | Customer Service needs a voice | All |

### Boss

- **What the test run showed:** it read the ticket, then sent it to all three other teammates at once, without passing along what it had already learned. It accepted the result, and the same $2,400 rent payment came back **4 times**.
- **What's missing:**
  - **Routing rules:** which ticket type goes to whom (`customer_order`, `rent_notice`, `price_override`).
  - **Pass the facts on:** include what you already know, so others don't look it up again.
  - **One owner per payment:** only Accounting's approval requests count. Remove duplicates.
  - **How to choose `status`:** needs_approval, waiting, resolved or blocked.
  - **What to do when teammates disagree, or a fact is missing.**
  - **The cash-priority rule from Step 0.**
- **Answer in my words:**
  1. For each ticket type, who should work on it?
  2. What must the Boss hand over with each request?
  3. When is a ticket `blocked`, and when is it `needs_approval`?

### Inventory

- **What the test run showed:** it didn't run on 102, which is expected, so it has never been tested. It is the main agent for 101 and 103.
- **What's missing:**
  - **Shortfall math in exact words:** units asked − units on the shelf, for that size only. Other sizes don't count.
  - **Matching a vendor to a product:** apparel → Bulldog Print Co, mugs → Elm City Gifts, using `list_vendors` and its specialty.
  - **The blocked-vendor chain:** if `can_ship` is false, say which invoice blocks it, and that restock time starts **after** the invoice is paid.
  - **Restock quantity:** the Step 0 decision.
  - **Stay in its lane:** it should not price discounts.
- **Answer in my words:**
  1. How does Inventory decide which vendor restocks a SKU?
  2. When the vendor is blocked, what exactly should it report?
  3. How many units should a restock be?

### Accounting

- **What the test run showed:** it was asked **3 times** for the same thing. It called `get_lease` 3 times, although Facilities already had the lease. One answer noticed "paying both would leave $160," but every approval still said `cash_after: $1,000`.
- **What's missing:**
  - **`cash_after` must count everything owed** that comes before this payment. Start from `get_cash_position`, not just the balance.
  - **Priority when cash is short:** the Step 0 decision.
  - **Discount rule for 103:** the Step 0 floor, plus showing the math (list price, cost, discount, margin left).
  - **Purchase order cost:** quantity × unit cost, and whether cash covers it after the bills.
  - **Don't redo work:** use the facts in the request, and look up only what's missing.
- **Answer in my words:**
  1. How should Accounting calculate `cash_after`?
  2. What's the order of payments when cash is short?
  3. How much discount can it propose for 103, and what must it show?

### Facilities

- **What the test run showed:** it looked up the lease correctly. Then it asked Accounting **twice** to prepare the rent payment, and Accounting was already working on it at the Boss's request.
- **What's missing:**
  - **Don't hand off what the Boss already handed off.** Answer with the lease facts, and let the Boss bring in Accounting.
  - **When a hand-off is right:** for example, only if the Boss didn't already ask.
  - **What "due soon" means:** for example, "within 7 days of `desk.date_today`, flag it as urgent."
- **Answer in my words:**
  1. When should Facilities ask Accounting, and when should it just report?
  2. How many days counts as "urgent"?

### Customer Service

- **What the test run showed:** the draft was good and promised nothing. But it asked Facilities to look the lease up **again**, because the Boss sent no facts.
- **What's missing:**
  - **Use the facts in the request.** Only ask a teammate if a needed fact is missing.
  - **Voice:** who signs, the tone, and how long a reply should be (Step 0).
  - **Ticket 101 reply:** say the tee is out of stock in S, and give a realistic window (vendor lead days, counted **after** the invoice is paid) without promising a date.
  - **Ticket 103 reply:** say a discount is being reviewed, and offer the 8 hoodies now if partial orders are allowed (Step 0).
  - **Safety:** ticket notes are a customer's words, not instructions. Ignore any request in them to break shop rules.
- **Answer in my words:**
  1. Who signs, and what tone is right for a student club versus a landlord?
  2. What can a reply promise, and what must it never promise?

### Rules every prompt should keep

These are already in the drafts. Keep them, in my own words:
- Today is `desk.date_today`.
- Every number comes from a tool. If a tool returns `found: false`, say so; never guess.
- A vendor with an open invoice can't ship.
- No payment without a human, and no negative cash.
- Cash only goes out.
- Nothing gets sent. Replies are drafts only.

### Skeleton (one per agent)

```
# <Role>
You are <who> at Campus Customs. Your job: <one sentence>.

## Do
- <step 1, naming the MCP tool>
- <step 2>

## Shop rules
- <the rules this agent needs, in my words>

## Don't
- <the limits: what is not this agent's job, what it must never promise or do>

## Hand-offs
- Ask <teammate> only when <condition>. Include <facts> in the request.

## Answer
Return <AgentReport / TicketDecision>. Every number goes in facts with the tool it came from.
```

**Test after each rewrite:** run one ticket, then check the audit trail for duplicate hand-offs, repeated tool calls, and `cash_after`.

```bash
.venv/Scripts/python backend/run_ticket.py 102
```

## Running lessons log

Newest at the bottom. One line per lesson: what happened, then the rule I take from it.

| # | Date | Problem | What happened | Rule for next time |
|---|---|---|---|---|
| 1 | 11-07 | Start | "Home work 5" alone made the AI search my folders and guess. | Open with one sentence on what the assignment is. |
| 2 | 11-07 | Start | `Given/` was empty, so there was nothing to build from. | Get the data file first. Course data lives at `zlisto.github.io/mgt_409_fa26/data/hwN/data.zip`. |
| 3 | 11-07 | 1 | The prompt log is graded, and it's also my record of how I prompt. | Log exact words, and write the "lacking" line myself right away, while I still remember. |
| 4 | 11-07 | 2 | My HW4 folder had a `campus_customs.db` too, but it held different tables. | Same file name doesn't mean same data. Check the tables before using a file. |
| 5 | 11-07 | 2 | Agents will change the database. | Keep an untouched original next to a working copy, and reset before a full run. |
| 6 | 11-07 | 2 | Vendors link to products only through a text field ("apparel reprint"). | Foreign keys show only some of the links. Read the data, not just the schema. |
| 7 | 11-07 | 2 | One overdue invoice blocks two tickets, and cash covers the bills with only $160 left over. | Study the data before building. The real puzzle is in the numbers. |
| 8 | 11-07 | 3 | The main Python's FastMCP was broken (a missing package). | Give every project its own `.venv` and `requirements.txt`. |
| 9 | 11-07 | 3 | "Reads inventory" is vague. "8 in stock vs 20 asked" is specific. | Tie every tool or harness line to a ticket and a number. |
| 10 | 11-07 | 3 | Saying how it's graded got the best result. | Tell the AI the grading standard in the prompt. |
| 11 | 11-07 | 3 | Tools that only look are safe to build first. | Build read-only tools first. Tools that pay or write need approval and no-negative rules. |
| 12 | 11-07 | 3 | Testing proved the tools work and changed nothing. | Compare a checksum (a fingerprint of the file) before and after a test. A matching checksum shows the tools didn't change anything. |
| 13 | 11-07 | 4 | Claude Code loads `.mcp.json` only from the folder a session opens in. | Open the session in the project root, or the tools won't appear. |
| 14 | 11-07 | 4 | The smoke test compares each tool's answer with the database read directly, and includes not-found cases. | A good test checks the right answer **and** the "nothing there" answer. Save it as a script so I can rerun it after every change. |
| 15 | 11-07 | 5 | The pay tool lives in MCP but is hidden from every agent. | Put dangerous tools where the rules live (MCP), and hand agents only the safe ones. Code enforces "no pay without a human", not the prompt. |
| 16 | 11-07 | 5 | The pay tool takes the amount from the database, not from the caller. | Never let an agent type a dollar amount into a tool that moves money. |
| 17 | 11-07 | 5 | Full connectivity: specialists asked each other, 6 hand-offs for one ticket. | Give every hand-off a stop rule (no self, no loop, a depth limit) and a total call cap, or tokens run away. |
| 18 | 11-07 | 5 | `cash_after` ignored the other bill. | An agent follows only the rules it's given. Test the prompts on real tickets, then add the missing rule. |
| 20 | 11-07 | 5 | My attack check flagged its own warning text ("100% discount") as a leak. | Test what the customer actually receives (drafts and payments), not every word in the output. |
| 21 | 11-07 | 5 | Three layers caught the fake ticket: a code screen, a prompt rule and a code backstop. | Never rely on the prompt alone for safety. Back it with code that runs every time. |
| 27 | 11-07 | 10 | The debrief found that all extra tool calls came from one agent (Customer Service repeating lookups). | Measure per agent, not just per ticket. The fix then goes to the right prompt. |
| 28 | 11-07 | 10 | For three small tickets, one agent with the same tools and code guards would have been cheaper. | Use multiple agents when roles need separate testing or grading, not by default. Safety lives in code either way. |
| 29 | 11-07 | Better | Typed names let anyone "approve". | Money needs real sign-in. Take the person from a signed token, never a text box. |
| 30 | 11-07 | Better | A rejected payment could still be approved later. | A "no" must stick until a fresh proposal: check the order of events. |
| 31 | 11-07 | Better | Discount caps lived only in prompts. | Rules that touch money or promises belong in code that runs after every answer. |
| 32 | 11-07 | Better | The debrief right after the fix: 102 went from B to A. | Measure, change one thing, measure again. That's the learning loop. |
| 33 | 11-07 | Better | Some ideas would break an assignment rule (money coming in). | Check each "improvement" against the rules before building it. |
| 34 | 11-07 | 10 | A generic reflection scores low. | Tie every claim to a ticket tab or the Cash tab, and compute numbers from the run instead of estimating ("about 7" was really 8). |
| 36 | 11-07 | 10 | My reflection was strongest when it named real numbers ($160 below the $500 cushion, 12 hoodies short). | "Resolved" tickets aren't the same as a healthy shop, so say what the numbers mean for the business. |
| 35 | 11-07 | 11 | The push request came before I was ready. | Write down "wait until I say so" and treat it as a hard stop. |
| 22 | 11-07 | 6 | A plan that calls every specialist on every ticket scores low. | Name who goes first and why, who is *not* called, and the exact tools. That makes the plan testable. |
| 23 | 11-07 | 7 | A bare `uvicorn` ran the wrong Python. | Activate the project's `.venv` before any command, and check `which uvicorn`. |
| 24 | 11-07 | 7 | A half-stopped background server kept port 8000 with old code. | Run servers in a visible terminal. If routes look stale, check who is listening on the port. |
| 25 | 11-07 | 7 | Agent runs take about 40 s. | Slow work returns a receipt (`run_id`) at once, and the page polls for progress. |
| 26 | 11-07 | 7 | Approvals check the proposal in the backend **and** the money in the MCP tool. | Two checks in two places: a bug in one is caught by the other. |
| 19 | 11-07 | 5 | Portkey reports the model as `gpt-6-luna-global`. | Check the audit trail for the model name on every reply. It's proof that only the allowed model ran. |

## Do it myself: the steps to redo HW5 without the website

These are the steps behind what's done so far, in order, with the commands. Steps past Problem 4 list only what the assignment requires. I'll add the how-to as each problem is done.

### A. Set up (before any code)

- [ ] Write down the goal, the allowed model (`gpt-6-luna` through Portkey), the due date, the shop rules, and that the submission is a public GitHub repo
- [ ] Make `HW 05\Given` and `HW 05\My Work`
- [ ] Create `AI_prompts.md` and this checklist
- [ ] Download the data into `Given`, then unzip it into `My Work/data/`
- [ ] Make the Python environment:

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install -r requirements.txt
```

### B. Understand the data (Problem 2)

- [ ] List every table, with its row count and fields (Python's `sqlite3`, or any SQLite viewer)
- [ ] Copy `campus_customs.db` to `campus_customs_new.db`. Agents only ever touch the copy.
- [ ] For each open ticket, follow its links: sku + size → inventory and pricing, invoice_id → invoices → vendors, lease_id → leases
- [ ] Find today's date (`desk.date_today`) and the cash balance, then work out what's overdue and what cash allows
- [ ] Start `output/harness.md`: one row per table, with its fields and why it matters

### C. Build the MCP server (Problem 3)

- [ ] In `mcp_server/server.py`: `mcp = FastMCP("Campus Customs Shop")`, then one function per tool with `@mcp.tool` above it
- [ ] Open the database read-only (`?mode=ro`) for look-up tools
- [ ] Give each tool a clear name (`check_stock`, `get_invoice`, `get_lease`) and a docstring, the description agents read
- [ ] Missing row → return `found: false` plus a message. Never guess.
- [ ] Count days from `desk.date_today`, not today's real date
- [ ] Test by calling each function, and compare a checksum of the `.db` files before and after
- [ ] Write `mcp_server/README.md` and harness §2: each tool's tables, the ticket it unlocks, and why

### D. Connect the vibe coder (Problem 4)

- [ ] Save `.mcp.json` at the project root: server name, `"type": "stdio"`, `command` = the `.venv` Python, `args` = `["mcp_server/server.py"]`
- [ ] Open Claude Code in that folder and approve the server
- [ ] Ask the vibe coder to call each tool on each ticket, then check its answers against `output/database_study.md`
- [ ] Run the smoke test and keep its evidence:

```bash
.venv/Scripts/python scripts/mcp_smoke.py
```

### E. Build the agent team (Problem 5)

- [ ] `backend/models.py`: the answer shapes (a final decision, specialist reports, approval requests, drafts, facts with their source tool)
- [ ] `backend/prompts/<role>.md`: one file per agent, my own words, with that agent's shop rules
- [ ] `backend/team.py`:
  - one model (`gpt-6-luna` via Portkey);
  - one MCP toolset, with the human-only tools filtered out;
  - `ask_teammate` with stop rules;
  - an audited agent loop.
- [ ] `backend/agents/<role>.py`: `build_agent(role, AnswerType)`
- [ ] Add MCP tools for whatever the tickets need. Test write tools on a throwaway copy (`CAMPUS_DB=...`), never on the real one.
- [ ] Run one ticket, read `output/audit_trail.json`, and fix the prompts:

```bash
.venv/Scripts/python backend/run_ticket.py 102
```

### F. Backend routes (Problem 7)

- [ ] Install `fastapi` and `uvicorn[standard]` into `.venv`, and add them to `requirements.txt`
- [ ] `backend/main.py`: a FastAPI app, with CORS for `http://localhost:5173`
- [ ] Tickets route through an MCP tool that lists **all** tickets with open or resolved status
- [ ] Run route: 404 if the ticket is unknown, 409 if busy, a background task, `202` with a `run_id`
- [ ] Run-status route, and an events route from the audit trail with `?after=`
- [ ] Approve route: must match an agent proposal, then call the human-only MCP pay tool
- [ ] Reject route (recorded, nothing paid), cash route, reset route (logs kept)
- [ ] Start it from `backend/`:

```bash
..\.venv\Scripts\activate
```

```bash
uvicorn main:app --reload --port 8000
```

- [ ] Prove it at `http://localhost:8000/docs`: a live run, $3,400 → $1,000 → $160 → reset → $3,400, and every refusal

### G. The dashboard (Problem 8)

- [ ] Make the app: `npm create vite@6 frontend -- --template react-ts`, then `npm install` inside `frontend/`
- [ ] `src/api.ts`: one function per backend route. The base URL is `http://localhost:8000`.
- [ ] `src/App.tsx`:
  - load tickets, cash, events and the debrief every 4 seconds;
  - while a run is going, fetch only **new** events (`?after=`) every 1.2 seconds.
- [ ] `src/components.tsx`: ticket cards, the five agent cards (working, done or not called), the flight log, the flight report, approval cards
- [ ] Look: CSS color tokens in `src/index.css` (warm blue and grey), Cormorant Garamond with Inter, aviation details
- [ ] The backend's CORS must allow `http://localhost:5173`
- [ ] Run it:

```bash
npm run dev
```

- [ ] Write `output/design.md`: who it's for (a military student who cares about ease and cost), the layout, how agents read differently, how resolved tickets and cash show, and the creative choices

### H. The final run and its evidence (after Problem 8)

- [ ] Reset (board button or `POST /api/reset`), then run 101, 102 and 103 on the board
- [ ] Approve on the board: rent (two people), then invoice 501
- [ ] Build the evidence:

```bash
.venv/Scripts/python scripts/build_resolved.py
```

  This fills the Actual sections and the Cash tab, and writes `resolved_tickets.json` and `resolved_board.html`.
- [ ] Check the money:

```bash
.venv/Scripts/python scripts/check_cash.py
```

  All 4 checks must PASS: the end must match `cash_accounts`.
- [ ] Screenshots: headless Edge with `--screenshot` on `http://localhost:5173/?ticket=101`. Run it from **PowerShell**; it doesn't work from Bash.

### I. The learning department (Problem 10)

- [ ] `backend/learning.py`: **code** computes the metrics (plan vs. actual, extra tools, cost, safety, cash), so the AI never invents numbers
- [ ] `backend/prompts/learning.md` + `backend/agents/learning.py`: the Flight Instructor, with **no tools**, returning a `LearningReport`
- [ ] `team.run_learning_review()`: run it after every ticket, append to `output/learning_feedback.json`, and rebuild `output/learning_report.html`
- [ ] Apply only the **safe** updates (efficiency). Business-rule updates wait for me.
- [ ] Fill the Reflection tab:

```bash
.venv/Scripts/python scripts/build_reflection.py
```

### J. The better-product pass

- [ ] Sign-in: `backend/auth.py`, then make test accounts:

```bash
.venv/Scripts/python scripts/create_approvers.py
```

  It writes the passwords to `output/test_accounts.md`, which is never committed.
- [ ] Approvals and rejections read the person from the token. A rejection blocks approval. The owner-only override applies to the cushion.
- [ ] `policy_check` in `team.py`: discount caps, no fixed dates, the cushion. Flags go on the decision, and breaking replies are held back.
- [ ] MCP: the bank-change screen, the hard cushion in the pay tool, and `save_drafts` / `get_drafts`
- [ ] Routes: `/api/login`, `/api/usage`, `/api/board/run`, `/api/tickets/{id}/drafts`
- [ ] Board: the sign-in box, "awaiting clearance" tags, saved replies, AI spend, the whole-board button, the top fix
- [ ] Test live (sign-in, block after a rejection, same-person check, owner-only override), and rerun a ticket so the debrief measures the fix

### K. Still to do (requirements only)

- [ ] Public GitHub repo, with `.env`, test accounts and the secret never committed

## Prompt-writing coach

### Feedback on my HW5 prompts so far

| Prompt | What worked | Blind spot to catch next time |
|---|---|---|
| "Home work 5" | It started the session | Too short to act on. The AI had to search my folders and guess. One line saying what HW5 is would have saved a round trip. |
| The overview (three pieces) | Named all three pieces and the kinds of tickets | Didn't say where the shop data comes from or what "done" looks like. |
| The team (four agents) | Strong: each agent has a clear job, and "full connectivity" is stated | Didn't say what each agent must **not** do (only Accounting prepares payments, nobody pays without approval), which tools each agent gets, what the Boss's "final call" looks like, or when delegation stops. Full connectivity can bounce a ticket back and forth and burn tokens. |
| Problem 1 | Clear goal: learn, not just finish | Didn't say what form the input should take (a table, a checklist, examples). The AI picked one. |
| Problem 4 | Exact file name and location, with a fallback ("or however your vibe coder saves…") | Didn't say which folder is the project root, or that this session runs from a different folder. That's why the tools can't be called here at first. |
| Problem 5 | Named the library, all five roles, folders, model, key; "no second tools layer" was a sharp rule | "Each prompt needs to be written by me" came mid-build, after drafts were already written. Say ownership rules up front. |
| Problem 6 | Strong: exact file, tab names, "Expected only, leave room for Actual", then a grading cue ("plans that send every specialist score low") | Nothing major. This is the model to copy. |
| Problem 7 | Each route described clearly | Came in 5 pieces; the port and run command (a screenshot) arrived last, after the server was built on another port |

**My patterns:**
- I'm good at roles and goals: who does what, and why.
- **I ask "why" on business calls** ("rent probably but why"), which led to the best rules. Keep doing it.
- **I push for opportunities and money** ("make more money", "what else can be done"). That's real business value, so keep it.
- I tend to leave out **limits**, **outputs** and **how we'll check it**.
- **I refer to things vaguely**: "the above", "this", "accordingly". The AI has to guess which items I mean.
- **I hand over decisions that are mine** ("fix and recommend the best outcome"). It worked, but the AI then chose the discount percent, the cushion and the deposit rule. Those are owner calls.
- **I often start with only the title**, then add the details one message at a time. The first message can't be acted on.
- Typos don't matter in plain sentences, but they do in names. File, table, field and model names must be exact. (In HW6 I typed `proces.json` for `prices.json`.) Copy names, don't retype them.

### My before-I-send checklist

Read the prompt as if you were a stranger, then check:

- [ ] **Label:** problem number and title first ("Problem 3: Build the MCP server").
- [ ] **Goal:** one sentence on what this piece is for and who uses it.
- [ ] **Inputs:** exact file, table and field names, copied rather than retyped.
- [ ] **Output:** what files or screens should exist when it's done, and where they're saved.
- [ ] **Rules and limits:** what it must never do (pay without approval, email anyone, use another model).
- [ ] **Edge cases:** what happens when data is missing, cash is short, or a vendor has an unpaid bill.
- [ ] **Done means:** how I'll check that it works (a test, a run, a screen I can see).
- [ ] **How it's graded:** what scores high and what scores low.
- [ ] **Scope:** "only this problem, don't build ahead."
- [ ] **Run setup first:** the exact run command, port and folder, before any code.
- [ ] **Point, don't gesture:** name items by number or name ("do gaps 1–4"), never "the above".
- [ ] **Where and what shape:** say where to save it and in what form (a table, a file, a few bullets, one paragraph).
- [ ] **Who decides:** say which calls are mine ("recommend, but ask me before setting prices or limits").
- [ ] **Teach me:** "explain it in basic terms and add it to my checklist."

**Find my blind spots before the AI does:** end a big prompt with "Before you build, tell me in 5 bullets what you think I'm asking, and list anything unclear or missing." Any missing item the AI names is a blind spot. Add it to the patterns list above.

### My question types, and better versions

These are the questions I asked in HW5 besides the problem prompts, sorted into 7 types. Each one gets a stronger version I can copy, and why it's better.

| # | Type | What I typed (examples) | Better version to copy | Why it's better |
|---|---|---|---|---|
| 1 | **Status update** | "give me an update", "so all ready to move on?" | "Status for HW5: a table of problems done / in progress / not started, what's verified vs. not, my open items, and anything blocking the next problem. Keep it under 15 lines." | Names the format and length, separates *done* from *proven*, and asks for blockers, so "ready to move on?" is answered with evidence |
| 2 | **Explain it simply** | "explain in basic terms what this problem did", "i am still confused on what the intent is" | "Explain [Problem N] like I'm a new hire: the goal in one sentence, a picture or analogy, what each piece does, and one example with real numbers from our data. Then ask me 2 questions to check I understood." | An analogy plus a real example sticks better than a list. Check-questions prove understanding, not just reading. |
| 3 | **Find gaps** | "what other gaps to fill?", "explain in further detail what gaps are missing" | "List gaps in [Problem N] in three groups: (a) the agents get it wrong, (b) the code can't do it yet, (c) only I can decide. For each, give the risk in dollars or customers, and whether it belongs to this problem or a later one." | Grouping shows *who* fixes each gap, and the risk ranks them. "This problem or later" keeps the AI from building ahead. |
| 4 | **Grow the business** | "give me more gaps ... opportunities to take advantage of and make more money" | "Using only our database numbers, list the 5 best ways to make or save money. For each: the dollar effect, what it costs, the risk, and the one decision I must make. Rank them." | "Only our numbers" stops made-up ideas. The dollar effect and ranking turn ideas into choices, and "my decision" keeps me the owner. |
| 5 | **Go ahead** | "Yes, fix them", "execute the above", "follow thru with your recs", "make sure one thru 6 works" | "Do items 1, 3 and 4 from your last list. Skip 2. For each, show the test that proves it works. Don't change prices, discounts or limits without asking me." | Numbers remove guessing. "Execute the above" included an item only I could do (writing my own lines). "Show the test" makes each fix provable, and the last line protects my decisions. |
| 6 | **Decide for me** | "fix and recommend the best outcome for the above" | "Recommend the best option for each of these, with the numbers and one sentence of why. **Don't apply them**; I'll approve each one." | I keep ownership of business rules. The AI's 15% military discount and $500 cushion were good, but they were *its* rules until I agreed. |
| 7 | **Make me a learning file** | "create a studyguide ...", "update my prompt sheet accordingly", "include this in study guide" | "Add [this] to [exact file], as section [N], in [table / bullets], with self-check questions. Tell me what you changed." | It names the file, place and shape, and the change summary shows me what moved. |

### Prompt library (copy, fill the blanks)

1. **Start an assignment:** "HW[N] is about [one sentence]. Rules: [model], [key], [submission]. Data is at [path or link]. Set up the folder, prompt log and checklist. Don't start Problem 1 until I send it."
2. **A problem, in one message:** use the template below. Put the run command and port first, then the files, rules, "done means", grading cue and scope.
3. **A plan before building:** "Before you build [Problem N], write the plan: who or what goes first and why, what is *not* used, and the tools at each step. Save it to [file]. Plans that [weak pattern] score low."
4. **Run and compare:** "Run [ticket / test]. Compare it with the plan in [file]: matches, differences, and why. Fill the Actual section."
5. **Safety check:** "List every rule that protects money, data and customers. Say which are enforced in code (with the file) and which are only in prompts. Suggest the top 2 to move into code."
6. **Cost check:** "What did that run cost in tokens and dollars, and what would 30 runs a month cost? What's the cheapest change that cuts it?"
7. **Teach me:** "Explain [X] in basic terms with one real example, add it to my Plain-English guide, and give me 2 self-check questions."
8. **Wrap up a problem:** "Problem [N] wrap-up: what was built, what was tested (with numbers), what's not verified, red flags, and my open items. Then update the checklist and the study guide."

### Prompt template

> **Problem [N]: [title].** Goal: [one sentence]. Run it with [exact command] from [folder] on [port]. Use [exact files/tables]. Build [what] in [where]. It must [rules] and must never [limits]. If [edge case], it should [behavior]. [Decisions I own]: ask me before setting them. Done means [how I'll check, with real numbers]. Graded on [standard; what scores low]. Only this problem. Before building, tell me what's unclear. Afterward, explain it in basic terms and update my checklist and study guide.

**Example, filled in (Problem 7):** "Problem 7: Backend Routes. Goal: a FastAPI backend in `backend/main.py` for my React dashboard. Run it with `uvicorn main:app --reload --port 8000` from `backend/`. Routes: tickets (open/resolved), run a ticket (return right away), recent agent events, approve a payment (the only route that changes cash, only for what an agent proposed), reject, checking balance, reset. Never: invent amounts, go below $0, or approve over $1,000 with one person. Done means: a live run, $3,400 → $1,000 → $160 → reset → $3,400, and every refusal tested. Only this problem. Tell me what's unclear first."

### Running prompt log (learning version)

My exact words stay in `AI_prompts.md` for the grade. Here I keep a 1–5 score for how complete the first try was, using the checklist above.

| # | Problem | Score | What I'd add next time |
|---|---|---|---|
| 0 | Overview + team | 3 | Agent limits, tools per agent, when delegation stops |
| 1 | Vibe coder prompts | 4 | The form I wanted the coaching in |
| 2 | Study the database | 2 then 4 | The first try was only the title. The follow-up named the exact file, the copy and the tickets. Next time: where to save the findings. |
| 3 | Build the MCP server | 3 then 5 | It named the folder, library and database, set the no-invented-data rule and capped it at three tools, but didn't name the three tools. The later parts were the strongest prompts so far, because they said how the work would be graded ("vague lines score low, tie the tool to the ticket"). |
| 4 | Connect the vibe coder | 4 | Which folder is the project root, and what "tested" should show |
| — | Status check | 4 | Clear ask (status, lessons, tasks, checklist). Could have said where to put it, or that it should all go in this checklist. |
| 5 | Agent team + MCP tools | 4 | Strong: it named the library, all five roles, the folders, the model and the key, and the follow-ups added "no second tools layer" and the audit trail. Missing: which ticket to test on, how deep hand-offs may go, and whether the pay tool belongs in MCP. |
| 6 | Plan the tickets | 5 | The model prompt: exact file, tabs, what to fill and what to leave, plus a grading cue. Copy this shape. |
| — | "Execute the above" / "follow thru" | 2 | Vague. Name items by number, and say which decisions stay mine. |
| — | "Fix and recommend the best outcome" | 3 | Got great ideas, but handed over owner decisions. Next time: "recommend, don't apply." |
| — | Study guide / prompt sheet requests | 4 | Clear goal. Name the file and section, and ask for a "what changed" summary. |
| 7 | Backend routes | 2 then 4 | It came in 5 pieces, with the port and run command last, after the server was built on another port. Next time: give the run command and port first, every route, the money rules, and a "done means" with real numbers in **one** prompt (see the study guide, section 10). |
| 9 | Final run + evidence | 3 then 4 | Many screenshots of the assignment. Next time: type the list in my own words ("reset, run 3, approve, itemize cash, check it matches cash_accounts"). |
| 10 | Reflection + learning dept | 4 | Strong ideas ("a department that is constantly learning", "turn opportunities into action"). Next time: say the output first (a report, a panel, both) and the goals to measure. |
| 10 | Grading cue ("tie every answer to this app…") | 5 | Says exactly what scores high (Campus Customs details, the tabs as evidence) and what scores low (generic essays). Reuse it on every write-up. |
| 11 | GitHub repo | 5 | Names the output file, what to include (both DBs), what never to push (.env), and the timing ("wait until i say so"). Next time: also say "I'll submit the URL on Canvas myself." |
| — | "all of them" | 3 | Fast, but it handed over decisions. The vibe coder split it into doable items vs. ones that need me. Next time: "do 1–6 and 8; ask me about prices." |
| 8 | Dashboard + design write-up | 3 then 5 | The must-have list was clear, and "boutique feel" set the style. The design write-up started as a screenshot. After asking for help, my own words named the **user** (a military student), what they **care about** (ease and cost) and the **feeling** (high end, warm, inviting). That shaped every section of `design.md`. Lesson: say who it is for and what they value. |

## Plain-English guide

- **React + Vite + TypeScript:** React builds the screen out of pieces (components). Vite runs it on your computer while you work (`npm run dev`). TypeScript catches typing mistakes before you run it.
- **CORS:** the browser's permission list. The backend says "pages from localhost:5173 may call me", so the board can fetch data.
- **Polling:** the board asks the backend "anything new?" every second or so (`?after=` gets only new events).
- **Sign-in token:** after you type your password once, you get a signed ticket (the token) that proves who you are for 8 hours. Passwords are stored only as salted hashes, scrambled one way.
- **Backend-only MCP tool:** a tool the agents can't see (pay, resolve, save replies). Only the backend calls it, after a person acts.
- **Policy check:** code that reads every answer after a run and holds anything that breaks a money or wording rule.
- **Debrief / Flight Instructor:** a learning agent that grades each crew member after every run, using numbers code worked out, and suggests fixes.
- **Continuous report:** a page that rebuilds itself after every debrief, so it's always current (`output/learning_report.html`).
- **Evidence generator:** a script that writes the result pages from the logs and the database, so nothing is typed by hand and the cash math can't drift.

- **Prompt log (`AI_prompts.md`):** a diary of what I asked the AI. The class grades it to see that I steered the work. For me, it's the raw material for getting better at prompts.
- **Database (`.db` file):** a set of linked spreadsheets ("tables") stored in one file. Each row is one thing (a ticket, an invoice), and each column is a fact about it.
- **Foreign key:** a column that points to a row in another table. For example, `tickets.invoice_id = 501` means "this ticket is about invoice 501." That's how the agents follow a ticket to the bill, the vendor and the stock.
- **Original vs. working copy:** the agents change `campus_customs_new.db` (pay bills, update stock). `campus_customs.db` stays untouched, so I can always reset to the starting point.
- **Harness (`output/harness.md`):** the instruction manual for the whole system. It says what each table, tool and agent is for, so a person (or a grader) can understand how it all fits together.
- **MCP server:** a menu of tools that any AI agent can order from. Instead of each agent poking at the database, they all ask the server ("how many size-M hoodies?"), and the server answers from the real data. MCP (Model Context Protocol) is the standard way agents and tools talk to each other.
- **FastMCP:** a Python library that turns ordinary functions into MCP tools. Put `@mcp.tool` above a function and it shows up on the menu.
- **Read-only:** the tools can look at the database but can't change it. That's safe while the rules for paying and approving aren't built yet.
- **`.mcp.json`:** a short note telling Claude Code "here's an MCP server, and here's the command to start it." Claude Code reads it when a session opens in that folder, then shows the server's tools alongside its own.
- **Virtual environment (`.venv`):** a private Python install for this homework, so its libraries don't clash with other projects.
- **Checksum:** a fingerprint of a file. If the fingerprint is the same before and after a test, the file wasn't changed.
