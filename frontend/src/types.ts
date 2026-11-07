// Shapes returned by the Problem 7 backend (backend/main.py).

export type Role = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";
export const ROLES: Role[] = ["boss", "inventory", "accounting", "facilities", "customer_service"];

export type ApprovalKind = "invoice_payment" | "rent_payment" | "purchase_order";

export interface ApprovalRequest {
  kind: ApprovalKind;
  ref_id: number | null;
  payee: string;
  amount: number;
  reason: string;
  cash_after: number | null;
  sku?: string | null;
  size?: string | null;
  qty?: number | null;
}

export interface Draft {
  to: string;
  subject: string;
  body: string;
}

export interface LatestRun {
  run_id: string;
  at_utc: string;
  agent_status: string;
  decision: string;
  approval_requests: ApprovalRequest[];
  drafts: Draft[];
  cost_usd: number | null;
  policy_flags?: string[];
  security_flags?: string[];
}

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  lease_id: number | null;
  invoice_id: number | null;
  notes: string | null;
  created_at: string;
  status: "open" | "resolved";
  needs_human_review: boolean;
  suspicious_text: string[];
  running_now: boolean;
  latest_run: LatestRun | null;
}

export interface TicketsResponse {
  shop_today: string;
  count: number;
  open: number;
  resolved: number;
  tickets: Ticket[];
}

export interface AgentEvent {
  id: string;
  seq: number;
  kind: "run_started" | "said" | "tool_call" | "tool_result" | "handoff" | "decision" |
        "approval" | "reset" | "resolved" | "warning";
  at_utc: string;
  run_id: string;
  ticket_id: number | null;
  role: string;
  depth: number;
  text?: string;
  tool?: string;
  args?: Record<string, unknown>;
  to_role?: string;
  final?: boolean;
  status?: string;
  approved_by?: string;
  ref_kind?: string;
  ref_id?: number;
  approvals?: number;
  drafts?: number;
  cost_usd?: number;
}

export interface EventsResponse {
  count: number;
  latest_seq: number | null;
  busy: boolean;
  events: AgentEvent[];
}

export interface RunStatus {
  run_id: string;
  ticket_id: number;
  status: "queued" | "running" | "done" | "failed";
  started_at_utc: string;
  finished_at_utc?: string;
  decision?: { status: string; decision: string; approval_requests: ApprovalRequest[]; drafts: Draft[] };
  cost?: { cost_usd: number; total_tokens: number; requests: number };
  ticket_status?: string;
  error?: string;
}

export interface Payment {
  id: number;
  kind: "invoice" | "rent" | "purchase_order";
  ref_id: number;
  amount: number;
  account: string;
  paid_at: string;
  approved_by: string;
}

export interface CashResponse {
  account: string;
  balance: number;
  as_of: string;
  shop_today: string;
  open_invoices: { id: number; amount: number; vendor: string; days_overdue: number; is_overdue: boolean }[];
  rent_due: { id: number; monthly_rent: number; next_due: string; days_until_due: number }[];
  total_owed: number;
  cash_left_if_all_paid: number;
  recent_payments: Payment[];
}
