# HW5: Campus Customs agent team

An agent team that runs the Campus Customs shop. Open tickets land on a board, and three pieces work them together:

- **MCP server** (`mcp_server/`, FastMCP). It holds the only tools that read or write the shop database.
- **FastAPI backend** (`backend/`, Pydantic AI). Five agents work each ticket: Boss, Inventory, Accounting, Facilities and Customer Service. A sixth, the Flight Instructor, grades each run afterwards. Every agent uses **gpt-6-luna** through Portkey.
- **React board** (`frontend/`, Vite + TypeScript). A person watches the agents work and **approves every payment**.

Final run: start at $3,400.00 → rent $2,400.00 → invoice 501 $840.00 → **$160.00**, which matches `cash_accounts`. See the Cash tab in `output/desk_tickets.html`.

## Setup (once)

Windows commands, run from this folder:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

1. Put your own `PORTKEY_API_KEY` in `.env`. Never commit `.env`.
2. Create the two local test approvers (`chloe` = owner, `pat` = approver):

```bash
.venv\Scripts\python scripts\create_approvers.py
```

The passwords are written to `output/test_accounts.md`, which is kept out of git.

Then install the board:

```bash
cd frontend
npm install
```

## 1. Copy the original database to the working copy (for a clean run)

- `data/campus_customs.db` is the **original**. It is never changed.
- `data/campus_customs_new.db` is the **working copy** the team reads and writes.

To start clean, copy the original over the working copy. The script does that, then checks the two files match:

```bash
.venv\Scripts\python scripts\reset_db.py
```

## 2. Start the MCP server

The backend starts the MCP server for you over stdio (`mcp_server/server.py`), so you don't run it separately for the board.

To test it alone, or to connect a vibe coder using `.mcp.json`:

```bash
.venv\Scripts\python mcp_server\server.py
```

Smoke test of every tool, saved to `output/mcp_smoke.json`:

```bash
.venv\Scripts\python scripts\mcp_smoke.py
```

## 3. Start the FastAPI backend (port 8000)

```bash
cd backend
..\.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

API docs are at http://localhost:8000/docs.

## 4. Start the React board (port 5173)

In a second terminal:

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. The board talks to the backend at http://localhost:8000.

## 5. Reset the database before a full three-ticket run

1. Reset, with either:
   - **Reset** on the board (`POST /api/reset`), or
   - `.venv\Scripts\python scripts\reset_db.py`
2. Run tickets **101**, **102** and **103** (or **Run the whole board**).
3. Sign in and approve the proposed payments:
   - rent ($2,400.00) needs two different approvers, because it is over $1,000;
   - invoice 501 ($840.00) needs one.
4. Rebuild and check the evidence:

```bash
.venv\Scripts\python scripts\build_resolved.py
```

```bash
.venv\Scripts\python scripts\check_cash.py
```

Command-line option, without the board: `cd backend` then `python run_ticket.py 101` (or `--board --reset`).

## Rules the code enforces

- **No money moves without a signed-in person.** `pay_approved_request` is backend-only, and a second, different approver is needed over $1,000.
- **No negative cash.** The pay tool refuses.
- **Purchase orders keep a $500 cushion** unless the owner overrides.
- **Cash only goes out.** Nothing records money coming in.
- **No real emails or vendor calls.** Replies are saved as drafts on the board.

## Where things are

| Path | What it is |
|---|---|
| `AI_prompts.md` | Every prompt I typed, word for word, with what was lacking |
| `output/harness.md` | Tables, tools, agents, routes, safety rules and the final run |
| `output/desk_tickets.html` | Expected vs. Actual for each ticket, plus the Cash and Reflection tabs |
| `output/resolved_tickets.json`, `output/resolved_board.html` | Final-run evidence |
| `output/audit_trail.json` | Every agent step (append-only) |
| `output/design.md` | Board design write-up |
| `output/github_url.txt` | This repo's URL |
