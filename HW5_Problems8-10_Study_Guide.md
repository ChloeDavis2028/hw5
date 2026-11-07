# Study Guide: HW5 Problems 8–10, plus the "better product" pass

_For anyone redoing this work later. Plain words first; details after. Written 2026-11-07._

**In one sentence:**
- **Problem 8** gave the agent team a screen people can use.
- **Problem 9** proved it works with real runs and real money math.
- **Problem 10** added a learning department that keeps making the team better.
- **The better-product pass** made it safe enough for real use.

---

## 1. The big picture

```
 You ──► The board (React, :5173) ──► The backend (FastAPI, :8000) ──► The crew (5 agents) ──► MCP tools ──► database
           ▲   sign in, approve          ▲  15 routes                       │
           │   see cash, AI spend        │                                  ▼
           └──── Debrief panel ◄─────── Flight Instructor (learning agent) ◄── audit trail + numbers from code
```

- **The crew works tickets.** You approve the money, the Flight Instructor grades the crew, and code checks every rule.
- **Nothing moves money except a signed-in person,** and every step is logged.

---

## 2. Problem 8: the dashboard (what, how, why)

| What | How | Why |
|---|---|---|
| **A board of the 3 tickets** | `GET /api/tickets` every 4 seconds | You always see what's open or resolved |
| **Start the team on one ticket** | **Start the team**, which calls `POST /api/tickets/{id}/run` and gets a receipt | Runs take about 40 seconds, so the page never freezes |
| **Watch each agent live** | Five crew cards plus a **flight log**. The board asks for only *new* events every 1.2 seconds (`?after=`). | You see who is working and which tool they're using, as it happens |
| **Resolved when the run finishes** | The backend calls the backend-only MCP tool `mark_ticket_resolved` | The ticket list updates by itself |
| **What each agent did** | The **flight report**: each agent's report, its tools and its hand-offs | A quick, readable summary |
| **Approve a payment or purchase** | Approval cards, then `POST /api/approvals` | A person decides every dollar |
| **Cash drops after approval** | The masthead's **Checking**, with a "−$840" flash | You *see* the money leave |

**The look**, from my words: "boutique… high end aesthetiques", "warmer blue and grey", "include aviation".
- **Palette and type:** warm stone grey with charcoal and a slate-blue accent; Cormorant Garamond with Inter.
- **Aviation, done like a lounge:** KHVN, a dashed flight path, boarding-pass tickets, crew titles (Captain, Purser…), and the Flight log and Flight report.

**Who it's for**, in my words: "a military student… cares most about ease and cost… high end and warm and inviting".

Full write-up: `output/design.md`.

---

## 3. Problem 9: the final run and the evidence

1. **Reset**, so cash is $3,400 and every ticket is open.
2. **Run** 101, 102 and 103 on the board.
3. **Approve** rent ($2,400, two people), then invoice 501 ($840).
4. **Build the evidence** from the logs and the database (`scripts/build_resolved.py`):
   - **Actual** vs. **Expected** for each ticket in `desk_tickets.html`;
   - the **Cash tab:** start, change per ticket, end;
   - `resolved_tickets.json` and `resolved_board.html` (screenshots).
5. **Check the money** (`scripts/check_cash.py`), 4 checks. Ending at **$160 = `cash_accounts`** ✓.

| Ticket | Change | Why | Checking after |
|---|---|---|---|
| Start | — | After the reset | $3,400 |
| 101 | −$840 | Invoice 501 to Bulldog Print Co | $2,560 |
| 102 | −$2,400 | Rent to Elm City Properties | $160 |
| 103 | $0 | Invoice 501 already counted under 101 (each payment counts once) | $160 |

**Why a script, not typing:** typed numbers drift. The script reads the real data, refuses to save if the cash doesn't match, and can be rerun any time.

---

## 4. Problem 10: the learning department (the Flight Instructor)

**My idea:** "a department that is constantly learning, updating, providing data based feedback to improve". When asked, I chose a sixth agent.

| Part | What it does | Why it's built this way |
|---|---|---|
| `backend/learning.py` (**code**) | Works out the numbers: plan vs. actual, extra tools, cost, safety, cash | AI is bad at counting. Code counts; the AI judges. |
| The **Flight Instructor** agent (no tools) | Grades each agent on each ticket (A–F) **with reasons**, combines lessons (new, repeated or fixed), turns opportunities into **actions** (owner + measure), proposes prompt fixes | Feedback you can act on, tied to evidence |
| **After every run** | `run_learning_review()` runs automatically | "Constantly learning" |
| The **continuous report** | `output/learning_report.html`, rebuilt each time, with a trend table | One page that's always current |
| The **Debrief panel** + top fix | On the board | You see the most important fix without digging |

**What it found:**
- **Debrief 1:** Customer Service repeated lookups (9 extra tool calls), so 101 got C, 102 got B and 103 got C.
- **The fix:** "don't re-check facts you're given; never hand off to yourself", applied to the Customer Service prompt.
- **Debrief 2,** after rerunning 102: **102 went from B to A.** The fix worked.

**Reflection, one agent vs. five** (from the numbers):
- **One agent would be simpler for:** passing facts, hand-off rules, cost (each hand-off re-sends a prompt), and logging.
- **The same either way:** money and safety, because those rules live in code.
- **Five is better for:** clear roles and grading each role separately.
- **Honest takeaway:** for three small tickets, one agent would be cheaper. Five pays off as the work grows.

**Reflection tab = evidence, not an essay** (grading cue: "generic AI essays without Campus Customs details will score low"):
- Every answer links to the **101 / 102 / 103 / Cash** tabs on the same page.
- Every number is computed from the final run by `scripts/build_reflection.py`: $3,400 → $160, rent $2,400, invoice 501 $840, 8 fewer tool calls (6 on 101 + 2 on 102).
- Name real details: Tauhid, Elm City Properties, Bulldog Print Co, the Yale AI Club, 12 hoodies short.
- **My reflection** (the last section) has three parts: what I learned (code and people guard the money, $3,400 → $160), what I'd do differently (give agents their facts up front, write prompts in one message), and what surprised me (resolved but $160 is below the $500 cushion, so the AI Club restock waits for the $522 deposit).

**New problems** (`output/new_problems.md`):
- **Can solve today:** fake vendor bank-change emails, a tariff surcharge, the Yale–Harvard rush.
- **Can't yet:** money coming in, returns, forecasting. Each comes with the tables, tools and agent it would need.

---

## 5. The better-product pass

| Problem it fixes | Fix | Where |
|---|---|---|
| Anyone could type any name to approve | **Sign-in**: salted password hashes and 8-hour signed tokens. The name comes from the token. The second approver signs in too and must be different. | `backend/auth.py`, `POST /api/login`, the board's sign-in box |
| A "no" could be undone by a later "yes" | **A rejection blocks approval** until the team proposes it again | `main.py` `_rejected_since()` |
| Discount caps lived only in prompts | **`policy_check` in code**: it holds replies with a non-owner discount, 50% outside a blowout, or a fixed date, and flags purchase orders below the cushion | `team.py` |
| The cushion was only a warning | The **pay tool refuses** purchase orders below $500 unless the **owner** overrides | MCP `pay_approved_request` |
| Fake "new bank details" emails | **Screen** holds them for review | MCP `_SUSPICIOUS` |
| Replies were lost in the logs | **Saved on the board** (never sent) | MCP `save_drafts` / `get_drafts`, the board |
| No view of AI cost | **AI spend this month** vs. a budget (placeholder $5.00) | `GET /api/usage`, the masthead |
| Running tickets one by one | **Run the whole board** button | `POST /api/board/run` |
| "Resolved" hid unpaid items | **"resolved · N waiting"** and **"N awaiting clearance"** | `components.tsx` |

**Not built, on purpose:**
- **money coming in:** it breaks the assignment rule "cash only goes out";
- **club prices:** the owner's decision;
- **a Planner:** needs the owner's calendar;
- **fewer hand-offs:** it would change the graded Problem 6 plan.

---

## 6. What went wrong, and the lesson

| Problem | Lesson |
|---|---|
| Ticket 103 "resolved" while 12 hoodies weren't arranged (earlier) | Define "done" in words the code can check |
| The same invoice proposed by two tickets | Count each payment once, under the ticket it belongs to |
| My first attack check flagged its own warning text | Test what the *customer* receives, not every word |
| A hidden old server answered with old code | Run servers in a visible terminal. If results look stale, check what's listening on the port. |
| Long inline scripts broke in the shell (twice) | Write code to a file, then run the file |
| Screenshots didn't work from Bash | Use PowerShell for desktop apps like Edge |
| Approving right after a run hit "team is working" | The debrief runs after each ticket, so wait for "not busy" |
| A "better product" idea broke a rule | Check each improvement against the assignment rules first |

---

## 7. Redo it from a blank page

- [ ] Vite + React + TypeScript app in `frontend/`; the API client points at `http://localhost:8000`; CORS allows `:5173`
- [ ] Board sections: tickets, the live crew (working / done / not called), the flight log (`?after=` polling), the flight report, approvals, cash
- [ ] `output/design.md`: user, goals, layout, agent look, resolved and cash, creative choices
- [ ] Reset → run 3 tickets → approve → `build_resolved.py` → `check_cash.py` (4 PASS) → screenshots → `resolved_board.html`
- [ ] Learning: code metrics, then a tool-less learning agent with a typed report, auto after every run, a continuous report, safe fixes only
- [ ] Reflection tab: one vs. five with numbers, the debrief, new problems, *your own words*, with every answer linked to a ticket tab or the Cash tab
- [ ] `AI_prompts.md`: a "what was lacking" line and a stronger prompt under every problem
- [ ] Safety upgrades: sign-in, rejection blocks, policy check, hard cushion, bank-change screen
- [ ] Measure again: rerun a ticket and confirm the debrief shows the fix worked

## 8. Check yourself (answers below)

1. Why does the board ask for `?after=` events instead of all events?
2. Why does code count the numbers while the Flight Instructor only judges?
3. How did we prove the Customer Service fix worked?
4. Why can't a typed name approve a payment anymore?
5. What does `policy_check` do with a reply that says "25% off"?
6. Why was "track money coming in" not built?
7. Why must the ending cash match `cash_accounts`?

<details><summary>Answers</summary>

1. To fetch only what's new, which is faster and cheaper, and keeps the live view smooth.
2. Code doesn't miscount or invent numbers. The AI is good at explaining *why* and suggesting fixes.
3. Debrief 2, after rerunning 102: Customer Service made no repeat lookups, and 102 went from B to A.
4. The approver comes from a signed sign-in token. A forged or missing token gets 401, and the second approver must be a different signed-in person.
5. It holds the reply back from the board and adds a flag: "mentions 25% (owner discounts are 10%, 15% or 50% only)".
6. The assignment's shop rule says "cash only goes out… no money comes in." Building it could cost points.
7. That's the grading rule ("wrong cash math loses points"), and it proves the board, the logs and the database agree.

</details>

---

## 9. Better prompts for these problems, and why

| What I typed | Stronger version | Why it's better |
|---|---|---|
| "Problem 8: Agent Dashboard" (title only) | "Problem 8: build the board in `frontend/` (React + Vite + TS, `npm run dev`, :5173) calling :8000. At minimum: [list]. User: a military student who cares about ease and cost. Feel: high end, warm, aviation. Done means: run 101 live, approve 501, checking drops to $2,560." | One message has the run command, the list, the user and the test, so nothing gets redone |
| Screenshots of the assignment text | Type the list: "reset, run 3 tickets, approve, Cash tab (start, change per ticket, end = cash_accounts), save resolved_tickets.json and resolved_board.html" | The class grades my own words, and typing it makes me understand it |
| "lets build a department that is constantly learning…" | "Add a learning agent with no tools. Code computes the metrics; the agent grades each agent per ticket with reasons, combines lessons, and turns opportunities into actions. Run it after every ticket. Keep a continuous report. Goals: tool calls at or below plan, 0 repeat lookups." | It names the output, the safety limit and the goals up front |
| "tie every answer to this app…" | Keep it as is | Says what scores high and low, and where the evidence lives |
| "all of them" | "Do 1–3 and 5–9. Ask me about club prices and the budget. Don't break the assignment rules." | It protects my decisions and the grade |

**Reusable pattern:** *"Do [numbered items]. Ask me about [my decisions]. Don't break [rules]. Done means [numbers I can check]. Then update my checklist and study guide."*
