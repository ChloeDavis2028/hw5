// Thin client for the Problem 7 backend. Every shop fact the board shows comes from here.
import type {
  ApprovalRequest, CashResponse, EventsResponse, RunStatus, TicketsResponse,
} from "./types";

export interface LearningResponse {
  count: number;
  latest: null | {
    at_utc: string;
    trigger: string;
    applied_updates: string[];
    report: {
      headline: string;
      ticket_reviews: { ticket_id: number; grade: string; why: string; agents: { role: string; grade: string; why: string }[] }[];
      lessons: { lesson: string; evidence: string; status: string }[];
      opportunities: { opportunity: string; action: string; owner: string; measure: string }[];
      prompt_updates: { agent: string; change: string; owner_decision: boolean }[];
      next_experiment: string;
    };
  };
}

export const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(0, `Can't reach the backend at ${API_BASE}. Is uvicorn running?`);
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof body?.detail === "string" ? body.detail
      : Array.isArray(body?.detail) ? body.detail.map((d: { msg: string }) => d.msg).join("; ")
      : res.statusText;
    throw new ApiError(res.status, detail);
  }
  return body as T;
}

export const api = {
  tickets: () => call<TicketsResponse>("/api/tickets"),
  cash: () => call<CashResponse>("/api/cash"),
  runTicket: (id: number) => call<{ run_id: string }>(`/api/tickets/${id}/run`, { method: "POST" }),
  run: (runId: string) => call<RunStatus>(`/api/runs/${runId}`),
  events: (params: { run_id?: string; after?: number | null; limit?: number; role?: string }) => {
    const q = new URLSearchParams();
    if (params.run_id) q.set("run_id", params.run_id);
    if (params.after != null) q.set("after", String(params.after));
    if (params.role) q.set("role", params.role);
    q.set("limit", String(params.limit ?? 500));
    return call<EventsResponse>(`/api/events?${q}`);
  },
  login: (username: string, password: string) =>
    call<{ token: string; username: string; display_name: string; role: string }>("/api/login", {
      method: "POST", body: JSON.stringify({ username, password }),
    }),
  approve: (a: ApprovalRequest, token: string, secondToken: string, override: boolean) =>
    call<{ paid: boolean; payment: { amount: number; balance_after: number } }>("/api/approvals", {
      method: "POST", headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        kind: a.kind, ref_id: a.ref_id, second_token: secondToken, owner_override_cushion: override,
        sku: a.sku ?? null, size: a.size ?? null, qty: a.qty ?? null,
      }),
    }),
  reject: (a: ApprovalRequest, token: string, reason: string) =>
    call<{ rejected: boolean }>("/api/rejections", {
      method: "POST", headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ kind: a.kind, ref_id: a.ref_id, reason, sku: a.sku ?? null, size: a.size ?? null, qty: a.qty ?? null }),
    }),
  drafts: (ticketId: number) =>
    call<{ ticket_id: number; drafts: { to_name: string; subject: string; body: string; saved_on: string }[] }>(`/api/tickets/${ticketId}/drafts`),
  usage: () => call<{ month: string; spent_usd: number; budget_usd: number; runs: number; warning: boolean; over_budget: boolean }>("/api/usage"),
  runBoard: () => call<{ run_id: string }>("/api/board/run", { method: "POST" }),
  reset: () => call<{ checking_balance: number }>("/api/reset", { method: "POST" }),
  learning: () => call<LearningResponse>("/api/learning"),
};

export const money = (n: number | null | undefined) =>
  n == null ? "—" : n.toLocaleString("en-US", { style: "currency", currency: "USD" });

export const ROLE_LABEL: Record<string, string> = {
  boss: "The Boss",
  inventory: "Inventory",
  accounting: "Accounting",
  facilities: "Facilities",
  customer_service: "Customer Service",
  system: "Desk",
  human: "You",
};

export const KIND_LABEL: Record<string, string> = {
  invoice_payment: "Invoice payment",
  rent_payment: "Rent payment",
  purchase_order: "Purchase order",
};

// Which payment row (from /api/cash) settles which proposal.
export const PAY_KIND: Record<string, string> = {
  invoice_payment: "invoice", rent_payment: "rent", purchase_order: "purchase_order",
};
