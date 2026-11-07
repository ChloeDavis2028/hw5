# Campus Customs · The Back Office (dashboard)

React + Vite + TypeScript dashboard for the agent team. It calls the Problem 7 backend at `http://localhost:8000`. Override that with `VITE_API_BASE` if needed.

## Run

1. Start the backend first. From `backend/`, with `.venv` active: `uvicorn main:app --reload --port 8000`
2. Then start the dashboard from `frontend/`:

```bash
npm install
npm run dev
```

The dashboard opens at http://localhost:5173.

## What it does

| On screen | Backend route |
|---|---|
| The board: all 3 tickets, open or resolved | `GET /api/tickets` |
| Pick a ticket → **Start the team** | `POST /api/tickets/{id}/run` |
| The team, live: five agent cards (working / done / not called), what each is saying and which MCP tools it used | `GET /api/events?run_id=…&after=…` every 1.2 s, plus `GET /api/runs/{id}` |
| A ticket turns **resolved** when its run finishes | The backend calls MCP `mark_ticket_resolved` |
| **What each agent did:** a summary per agent, tools with counts, hand-offs, the team's call, cost, drafted replies | Events for that run |
| **Awaiting approval:** approve or reject each proposed payment or purchase order. Two names over $1,000. | `POST /api/approvals`, `POST /api/rejections` |
| **Checking** in the masthead drops after an approved payment (with a −$ flash) | `GET /api/cash` |
| Reset the shop | `POST /api/reset` |
| **Approver sign-in** (test accounts from `scripts/create_approvers.py`) | `POST /api/login`; approvals send the token |
| **Replies on the board** (saved, never sent) | `GET /api/tickets/{id}/drafts` |
| **AI spend this month** vs. budget | `GET /api/usage` |
| **Run the whole board** | `POST /api/board/run` |
| **Debrief panel** + the instructor's top fix | `GET /api/learning` |

## Files

- `src/App.tsx`: layout, polling, run, approve and reset
- `src/components.tsx`: ticket list, agent floor, live timeline, run summary, approval cards
- `src/agents.ts`: turns events into "what each agent is doing" and summaries
- `src/api.ts`: backend client
- `src/types.ts`: response shapes
- `src/index.css`: the boutique look (warm blues and greys; Cormorant Garamond with Inter)
