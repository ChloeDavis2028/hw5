import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import type { AgentEvent, ApprovalRequest, Payment, Ticket } from "./types";
import { KIND_LABEL, PAY_KIND, money } from "./api";
import { CREW, ROLE_COLOR, agentViews, describe, label } from "./agents";

const accent = (role: string) => ({ "--accent": ROLE_COLOR[role] ?? "#8a8174" }) as CSSProperties;
const time = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

export function ticketAsk(t: Ticket): string {
  if (t.type === "rent_notice") return `Rent notice · lease ${t.lease_id}`;
  const what = t.qty ? `${t.qty} × ${t.sku} · size ${t.size}` : t.subject;
  return t.invoice_id ? `${what} · invoice ${t.invoice_id}` : what;
}

const TYPE_LABEL: Record<string, string> = {
  customer_order: "Customer order", rent_notice: "Rent notice", price_override: "Price request",
};

/* ---------------- ticket list ---------------- */

export function TicketList({ tickets, selected, onSelect, runningId, waiting }: {
  tickets: Ticket[]; selected: number | null; onSelect: (id: number) => void; runningId: number | null;
  waiting: Record<number, number>;
}) {
  return (
    <div>
      {tickets.map((t) => (
        <button key={t.id} className={`ticket ${selected === t.id ? "selected" : ""}`} onClick={() => onSelect(t.id)}>
          <div className="ticket-top">
            <span className="ticket-no">Flight CC {t.id} · {TYPE_LABEL[t.type] ?? t.type}</span>
            {runningId === t.id ? <span className="pill live">Running</span>
              : <span className={`pill ${t.status}`}>{t.status}{t.status === "resolved" && waiting[t.id] ? ` · ${waiting[t.id]} waiting` : ""}</span>}
          </div>
          <div className="ticket-subject">{t.subject}</div>
          <div className="ticket-meta">{t.requester} · {ticketAsk(t)}</div>
          <div className="ticket-foot">
            {t.needs_human_review && <span className="pill alert">Held for review</span>}
            {t.latest_run && <span className="pill quiet">Team: {t.latest_run.agent_status.replace("_", " ")}</span>}
            {waiting[t.id] ? <span className="pill open">{waiting[t.id]} awaiting clearance</span>
              : t.latest_run && t.latest_run.approval_requests.length > 0 ? <span className="pill quiet">payments cleared</span> : null}
          </div>
        </button>
      ))}
    </div>
  );
}

/* ---------------- agent floor ---------------- */

export function AgentFloor({ events, running }: { events: AgentEvent[]; running: boolean }) {
  const views = agentViews(events, running);
  return (
    <div className="floor">
      {views.map((v) => (
        <div key={v.role} className={`card agent ${v.state}`} style={accent(v.role)}>
          <div className="agent-head">
            <div className="monogram">{label(v.role).replace("The ", "")[0]}</div>
            <div>
              <div className="agent-name">{label(v.role)}</div>
              <div className="crew">{CREW[v.role]}</div>
              <div className="agent-state">{v.state === "working" ? "Working…" : v.state === "done" ? "Done" : "Not called"}</div>
            </div>
          </div>
          <div className="agent-says">{v.says || (v.state === "idle" ? "Waiting at the desk." : "")}</div>
          <div className="tools">
            {[...v.tools.entries()].map(([name, n]) => (
              <span className="tool" key={name}>{name}{n > 1 ? <> <b>×{n}</b></> : null}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ---------------- live timeline ---------------- */

export function Timeline({ events, running }: { events: AgentEvent[]; running: boolean }) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [events.length]);
  const rows = events.map((e) => ({ e, d: describe(e) })).filter((r) => r.d);
  return (
    <div className="card timeline" ref={box} aria-live="polite">
      {rows.length === 0 && <div className="empty">{running ? "The team is taking its seats…" : "No activity yet. Start the team on this ticket."}</div>}
      {rows.map(({ e, d }) => (
        <div key={e.id} className={`tl-row ${e.kind}`} style={accent(e.role)}>
          <span className="tl-time">{time(e.at_utc)}</span>
          <span className="tl-who">{label(e.role)}</span>
          <span className="tl-what"><span className="verb">{d!.verb}</span>{d!.rest ? ` — ${d!.rest}` : ""}</span>
        </div>
      ))}
    </div>
  );
}

/* ---------------- run summary ---------------- */

export function RunSummary({ ticket, events }: { ticket: Ticket; events: AgentEvent[] }) {
  const run = ticket.latest_run;
  if (!run) return <div className="card empty">The summary appears here when the team finishes this ticket.</div>;
  const views = agentViews(events, false).filter((v) => v.state !== "idle");
  return (
    <div className="card">
      {views.map((v) => (
        <div className="summary-row" key={v.role} style={accent(v.role)}>
          <div className="who">
            <div className="monogram">{label(v.role).replace("The ", "")[0]}</div>
            <div className="agent-name">{label(v.role)}</div>
          </div>
          <div>
            <p>{v.finalSummary || v.says || "—"}</p>
            <div className="tools">
              {[...v.tools.entries()].map(([name, n]) => <span className="tool" key={name}>{name}{n > 1 ? <> <b>×{n}</b></> : null}</span>)}
              {v.tools.size === 0 && <span className="tool">no tools — worked from the facts it was given</span>}
            </div>
            {v.handoffsIn.length > 0 && (
              <div className="handoff">Asked by {[...new Set(v.handoffsIn.map((h) => label(h.from)))].join(", ")}</div>
            )}
            {v.handoffsOut.length > 0 && (
              <div className="handoff">Handed work to {v.handoffsOut.map((h) => label(h.to)).join(" → ")}</div>
            )}
          </div>
        </div>
      ))}
      <div className="facts">
        <div className="fact"><div className="label">Team's call</div><div className="value">{run.agent_status.replace("_", " ")}</div></div>
        <div className="fact"><div className="label">Ticket</div><div className="value">{ticket.status}</div></div>
        <div className="fact"><div className="label">Payments proposed</div><div className="value">{run.approval_requests.length}</div></div>
        <div className="fact"><div className="label">Replies drafted</div><div className="value">{run.drafts.length}</div></div>
        <div className="fact"><div className="label">Run cost</div><div className="value">{run.cost_usd != null ? `$${run.cost_usd.toFixed(4)}` : "—"}</div></div>
      </div>
      {run.drafts.length > 0 && (
        <details className="drafts">
          <summary>Read the drafted replies (never sent)</summary>
          {run.drafts.map((d, i) => (
            <div className="draft" key={i}><div className="to">To {d.to} · {d.subject}</div>{d.body}</div>
          ))}
        </details>
      )}
    </div>
  );
}

/* ---------------- approvals ---------------- */

export interface Proposal extends ApprovalRequest { ticketId: number; key: string }

export function proposalKey(a: ApprovalRequest): string {
  return [a.kind, a.ref_id, a.sku ?? "", a.size ?? "", a.qty ?? ""].join(":");
}

export function isPaid(a: ApprovalRequest, payments: Payment[]): boolean {
  return payments.some((p) => p.kind === PAY_KIND[a.kind] && p.ref_id === a.ref_id &&
    (a.kind !== "purchase_order" || Math.abs(p.amount - a.amount) < 0.01));
}

export function ApprovalCard({ p, paid, rejected, busy, user, onApprove, onReject }: {
  p: Proposal; paid: boolean; rejected: boolean; busy: boolean;
  user: { display_name: string; role: string } | null;
  onApprove: (p: Proposal, second: { username: string; password: string } | null, override: boolean) => Promise<string | null>;
  onReject: (p: Proposal) => Promise<string | null>;
}) {
  const [secondUser, setSecondUser] = useState("");
  const [secondPass, setSecondPass] = useState("");
  const [override, setOverride] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [working, setWorking] = useState(false);
  const needsTwo = p.amount > 1000;
  const belowCushion = p.kind === "purchase_order" && p.cash_after != null && p.cash_after < 500;

  const act = async (kind: "approve" | "reject") => {
    if (!user) { setMsg({ ok: false, text: "Sign in above to approve or reject." }); return; }
    if (kind === "approve" && needsTwo && (!secondUser.trim() || !secondPass)) {
      setMsg({ ok: false, text: "Over $1,000: a second, different approver must sign in here too." }); return;
    }
    setWorking(true); setMsg(null);
    const err = kind === "approve"
      ? await onApprove(p, needsTwo ? { username: secondUser.trim(), password: secondPass } : null, override)
      : await onReject(p);
    setWorking(false); setSecondPass("");
    setMsg(err ? { ok: false, text: err } : { ok: true, text: kind === "approve" ? "Cleared and paid. Checking updated." : "Rejected and recorded." });
  };

  return (
    <div className={`card approval ${paid || rejected ? "settled" : ""}`}>
      <div className="ticket-top">
        <span className="kind">{KIND_LABEL[p.kind]} · Ticket {p.ticketId}</span>
        {paid ? <span className="pill resolved">Paid</span> : rejected ? <span className="pill alert">Rejected</span> : <span className="pill open">Awaiting you</span>}
      </div>
      <div className="amount">{money(p.amount)}</div>
      <div className="payee">{p.payee}{p.kind === "purchase_order" && p.qty ? ` · ${p.qty} × ${p.sku} ${p.size}` : ""}</div>
      <div className="reason">{p.reason}</div>
      {p.cash_after != null && <div className="after">Checking after, as proposed: {money(p.cash_after)}</div>}
      {!paid && !rejected && (
        <>
          <div className="note">{user ? <>Approving as <strong>{user.display_name}</strong> ({user.role})</> : "Sign in above to act on this."}</div>
          {needsTwo && (
            <div className="second">
              <div className="note">Over $1,000: second approver signs in</div>
              <input className="field" placeholder="Second approver username" value={secondUser} onChange={(e) => setSecondUser(e.target.value)} aria-label="Second approver username" autoComplete="off" />
              <input className="field" type="password" placeholder="Second approver password" value={secondPass} onChange={(e) => setSecondPass(e.target.value)} aria-label="Second approver password" autoComplete="off" />
            </div>
          )}
          {belowCushion && user?.role === "owner" && (
            <label className="note"><input type="checkbox" checked={override} onChange={(e) => setOverride(e.target.checked)} /> Owner override: allow below the $500 cushion</label>
          )}
          <div className="row">
            <button className="btn brass small" disabled={busy || working || !user} onClick={() => act("approve")}>Approve &amp; pay</button>
            <button className="btn ghost small" disabled={busy || working || !user} onClick={() => act("reject")}>Reject</button>
          </div>
          {busy && <div className="note">The crew is working. Approvals open when it finishes.</div>}
        </>
      )}
      {rejected && !paid && <div className="note">Rejected. It can be approved only after the team proposes it again.</div>}
      {msg && <div className={`note ${msg.ok ? "ok" : "err"}`}>{msg.text}</div>}
    </div>
  );
}

/* ---------------- aviation flourish ---------------- */

/** A fine dashed flight path with a small aircraft, drawn in the accent color. */
export function FlightPath() {
  return (
    <svg className="flightpath" viewBox="0 0 320 28" role="img" aria-label="Flight path from New Haven">
      <path d="M4 22 C 90 22, 150 6, 290 8" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="3 5" />
      <circle cx="4" cy="22" r="2.4" fill="currentColor" />
      <g transform="translate(292 8) rotate(-4)" fill="currentColor">
        <path d="M0 0 L-9 -1.4 L-13 -6 L-15 -6 L-13 -1.6 L-19 -2 L-21 -4 L-22.5 -4 L-21.5 0 L-22.5 4 L-21 4 L-19 2 L-13 1.6 L-15 6 L-13 6 L-9 1.4 Z" />
      </g>
    </svg>
  );
}

/* ---------------- replies saved on the board ---------------- */

export function SavedDrafts({ drafts }: { drafts: { to_name: string; subject: string; body: string; saved_on: string }[] }) {
  if (!drafts.length) return null;
  return (
    <details className="saved-drafts">
      <summary>Replies on the board · {drafts.length} saved, never sent</summary>
      {drafts.map((d, i) => (
        <div className="draft" key={i}><div className="to">To {d.to_name} · {d.subject} · saved {d.saved_on}</div>{d.body}</div>
      ))}
    </details>
  );
}
