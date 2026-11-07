import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, money, API_BASE, ApiError } from "./api";
import type { LearningResponse } from "./api";
import type { AgentEvent, CashResponse, Ticket } from "./types";
import {
  AgentFloor, ApprovalCard, RunSummary, SavedDrafts, Timeline, TicketList, isPaid, proposalKey, ticketAsk,
} from "./components";
import type { Proposal } from "./components";
import { FlightPath } from "./components";

const TICKET_POLL_MS = 4000;
const EVENT_POLL_MS = 1200;

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [shopToday, setShopToday] = useState("");
  const [cash, setCash] = useState<CashResponse | null>(null);
  const [delta, setDelta] = useState<{ amount: number; key: number } | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [run, setRun] = useState<{ runId: string; ticketId: number } | null>(null);
  const [humanEvents, setHumanEvents] = useState<AgentEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [debrief, setDebrief] = useState<LearningResponse | null>(null);
  const [spend, setSpend] = useState<{ spent_usd: number; budget_usd: number; warning: boolean; over_budget: boolean } | null>(null);
  const [drafts, setDrafts] = useState<{ to_name: string; subject: string; body: string; saved_on: string }[]>([]);
  const [user, setUser] = useState<{ token: string; display_name: string; role: string } | null>(() => {
    try { const raw = sessionStorage.getItem("cc-approver"); return raw ? JSON.parse(raw) : null; } catch { return null; }
  });
  const [loginName, setLoginName] = useState("");
  const [loginPass, setLoginPass] = useState("");
  const [loginErr, setLoginErr] = useState<string | null>(null);
  const lastSeq = useRef<number | null>(null);

  const ticket = tickets.find((t) => t.id === selected) ?? null;
  const running = run !== null;

  /* ---------- board, cash and human decisions ---------- */
  const loadBoard = useCallback(async () => {
    try {
      const [t, c, h, l, u] = await Promise.all([api.tickets(), api.cash(), api.events({ role: "human", limit: 500 }),
        api.learning().catch(() => null), api.usage().catch(() => null)]);
      setDebrief(l);
      setSpend(u);
      setTickets(t.tickets);
      setShopToday(t.shop_today);
      setCash(c);
      setHumanEvents(h.events);
      // ?ticket=102 in the address opens that ticket (handy for links and screenshots).
      const fromUrl = Number(new URLSearchParams(window.location.search).get("ticket"));
      const wanted = t.tickets.find((x) => x.id === fromUrl)?.id;
      setSelected((cur) => cur ?? wanted ?? t.tickets[0]?.id ?? null);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    loadBoard();
    const id = setInterval(loadBoard, TICKET_POLL_MS);
    return () => clearInterval(id);
  }, [loadBoard]);

  useEffect(() => {
    if (selected == null) return;
    api.drafts(selected).then((r) => setDrafts(r.drafts)).catch(() => setDrafts([]));
  }, [selected, tickets]);

  /* ---------- events for the selected ticket ---------- */
  // Not running: show the ticket's latest finished run in full.
  const latestRunId = ticket?.latest_run?.run_id;
  useEffect(() => {
    if (running && run?.ticketId === selected) return;
    if (!latestRunId) { setEvents([]); return; }
    let live = true;
    api.events({ run_id: latestRunId, limit: 1000 }).then((r) => { if (live) setEvents(r.events); }).catch(() => {});
    return () => { live = false; };
  }, [latestRunId, selected, running, run?.ticketId]);

  // Running: poll only the new events, then the run's status.
  useEffect(() => {
    if (!run) return;
    let stop = false;
    const tick = async () => {
      try {
        const r = await api.events({ run_id: run.runId, after: lastSeq.current, limit: 1000 });
        if (r.events.length) {
          lastSeq.current = r.latest_seq;
          setEvents((prev) => [...prev, ...r.events]);
        }
        const s = await api.run(run.runId);
        if (s.status === "done" || s.status === "failed") {
          if (s.status === "failed") setError(`The run stopped: ${s.error}`);
          const rest = await api.events({ run_id: run.runId, after: lastSeq.current, limit: 1000 });
          if (rest.events.length) setEvents((prev) => [...prev, ...rest.events]);
          stop = true;
          setRun(null);
          await loadBoard();
          return;
        }
      } catch (e) {
        setError(e instanceof ApiError ? e.message : String(e));
      }
      if (!stop) timer = setTimeout(tick, EVENT_POLL_MS);
    };
    let timer = setTimeout(tick, 300);
    return () => { stop = true; clearTimeout(timer); };
  }, [run, loadBoard]);

  const startRun = async () => {
    if (!ticket) return;
    try {
      setError(null);
      const r = await api.runTicket(ticket.id);
      lastSeq.current = null;
      setEvents([]);
      setRun({ runId: r.run_id, ticketId: ticket.id });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    }
  };

  /* ---------- approvals ---------- */
  const proposals: Proposal[] = useMemo(() => {
    const seen = new Map<string, Proposal>();
    for (const t of tickets) {
      for (const a of t.latest_run?.approval_requests ?? []) {
        const key = proposalKey(a);
        if (!seen.has(key)) seen.set(key, { ...a, ticketId: t.id, key });
      }
    }
    return [...seen.values()];
  }, [tickets]);

  // A rejection counts only if it came after the last reset.
  const rejected = useMemo(() => {
    const lastReset = Math.max(-1, ...humanEvents.filter((e) => e.kind === "reset").map((e) => e.seq));
    const keys = new Set<string>();
    for (const e of humanEvents) {
      if (e.kind === "approval" && e.status === "rejected" && e.seq > lastReset) keys.add(`${e.ref_kind}:${e.ref_id}`);
    }
    return keys;
  }, [humanEvents]);

  const signIn = async () => {
    try {
      const r = await api.login(loginName.trim(), loginPass);
      const u = { token: r.token, display_name: r.display_name, role: r.role };
      setUser(u); setLoginPass(""); setLoginErr(null);
      try { sessionStorage.setItem("cc-approver", JSON.stringify(u)); } catch { /* private window */ }
    } catch (e) { setLoginErr(e instanceof ApiError ? e.message : String(e)); }
  };
  const signOut = () => { setUser(null); try { sessionStorage.removeItem("cc-approver"); } catch { /* ignore */ } };

  const approve = async (p: Proposal, second: { username: string; password: string } | null, override: boolean): Promise<string | null> => {
    if (!user) return "Sign in first.";
    try {
      let secondToken = "";
      if (second) secondToken = (await api.login(second.username, second.password)).token;
      const before = cash?.balance ?? 0;
      const r = await api.approve(p, user.token, secondToken, override);
      setDelta({ amount: r.payment.balance_after - before, key: Date.now() });
      await loadBoard();
      return null;
    } catch (e) {
      if (e instanceof ApiError && e.status === 401 && e.message.includes("sign in")) signOut();
      return e instanceof ApiError ? e.message : String(e);
    }
  };
  const reject = async (p: Proposal): Promise<string | null> => {
    if (!user) return "Sign in first.";
    try { await api.reject(p, user.token, "Rejected on the dashboard"); await loadBoard(); return null; }
    catch (e) { return e instanceof ApiError ? e.message : String(e); }
  };

  const runBoard = async () => {
    try {
      setError(null);
      const r = await api.runBoard();
      lastSeq.current = null; setEvents([]);
      setRun({ runId: r.run_id, ticketId: -1 });
    } catch (e) { setError(e instanceof ApiError ? e.message : String(e)); }
  };

  const resetShop = async () => {
    if (!window.confirm("Reset the shop to its original numbers? Payments and resolved tickets go back to the start. The audit trail is kept.")) return;
    try { await api.reset(); setDelta(null); setEvents([]); await loadBoard(); }
    catch (e) { setError(e instanceof ApiError ? e.message : String(e)); }
  };

  const pending = proposals.filter((p) => !isPaid(p, cash?.recent_payments ?? []) && !rejected.has(`${p.kind}:${p.ref_id}`));
  const waiting: Record<number, number> = {};
  for (const p of pending) waiting[p.ticketId] = (waiting[p.ticketId] ?? 0) + 1;

  return (
    <>
      <header className="masthead">
        <div className="masthead-inner">
          <div>
            <div className="eyebrow">Campus Customs · New Haven · KHVN</div>
            <h1 className="brand">The Back <em>Office</em></h1>
            <p className="tagline">A five-member crew works the board. Nothing is paid until you clear it.</p>
            <FlightPath />
            {debrief?.latest && <p className="topfix"><span className="eyebrow">Instructor's top fix</span> {debrief.latest.report.headline}</p>}
          </div>
          <div className="ledger">
            <div className="figure">
              <div className="label">Shop date</div>
              <div className="value small">{shopToday || "—"}</div>
            </div>
            <div className="figure">
              <div className="label">AI spend · this month</div>
              <div className={`value small ${spend?.over_budget ? "over" : spend?.warning ? "warn" : ""}`}>{spend ? `${money(spend.spent_usd)}` : "—"}</div>
              <div className="sub">of {spend ? money(spend.budget_usd) : "—"} budget{spend?.warning ? " · near limit" : ""}</div>
            </div>
            <div className="figure">
              <div className="label">Owed</div>
              <div className="value small">{money(cash?.total_owed)}</div>
            </div>
            <div className="figure">
              <div className="label">Checking</div>
              <div className="value">
                {money(cash?.balance)}
                {delta && delta.amount !== 0 && <span key={delta.key} className="delta">{delta.amount < 0 ? "−" : "+"}{money(Math.abs(delta.amount))}</span>}
              </div>
              <div className="sub">from cash_accounts</div>
            </div>
          </div>
        </div>
      </header>

      <main className="page">
        {error && <div className="banner" role="alert">{error}</div>}
        <div className="grid">
          <aside className="stack">
            <section>
              <div className="section-title"><h2>Departures <small>the board</small></h2><span className="count">{tickets.filter((t) => t.status === "open").length} open · {tickets.filter((t) => t.status === "resolved").length} resolved</span></div>
              <TicketList tickets={tickets} selected={selected} onSelect={setSelected} runningId={run?.ticketId ?? null} waiting={waiting} />
              <button className="btn ghost small wide" onClick={runBoard} disabled={running}>{run?.ticketId === -1 ? "Whole board in flight…" : "Run the whole board"}</button>
            </section>
            <section>
              <div className="section-title"><h2>Awaiting clearance <small>your approval</small></h2><span className="count">{pending.length} waiting</span></div>
              <div className="card signin">
                {user ? (
                  <div className="row" style={{ marginTop: 0, alignItems: "center", justifyContent: "space-between" }}>
                    <span>Signed in as <strong>{user.display_name}</strong> <span className="ticket-meta">({user.role})</span></span>
                    <button className="btn ghost small" onClick={signOut}>Sign out</button>
                  </div>
                ) : (
                  <>
                    <div className="eyebrow">Approver sign-in</div>
                    <input className="field" placeholder="Username" value={loginName} onChange={(e) => setLoginName(e.target.value)} aria-label="Username" autoComplete="username" />
                    <input className="field" type="password" placeholder="Password" value={loginPass} onChange={(e) => setLoginPass(e.target.value)} aria-label="Password" autoComplete="current-password"
                      onKeyDown={(e) => { if (e.key === "Enter") signIn(); }} />
                    <div className="row"><button className="btn small" onClick={signIn}>Sign in</button></div>
                    {loginErr && <div className="note err">{loginErr}</div>}
                  </>
                )}
              </div>
              {proposals.length === 0 && <div className="card empty">When the team proposes a payment or a purchase, it waits here for you.</div>}
              {proposals.map((p) => (
                <ApprovalCard key={p.key} p={p} busy={running} user={user}
                  paid={isPaid(p, cash?.recent_payments ?? [])} rejected={rejected.has(`${p.kind}:${p.ref_id}`)}
                  onApprove={approve} onReject={reject} />
              ))}
            </section>
          </aside>

          <div className="stack">
            {ticket ? (
              <section className="card detail">
                <div className="detail-head">
                  <div>
                    <div className="eyebrow">Flight CC {ticket.id} · Ticket No. {ticket.id}</div>
                    <h3>{ticket.subject}</h3>
                    <div className="ticket-meta">{ticket.requester} · opened {new Date(ticket.created_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}</div>
                  </div>
                  <div className="row" style={{ marginTop: 0 }}>
                    <span className={`pill ${running && run?.ticketId === ticket.id ? "live" : ticket.status}`}>{running && run?.ticketId === ticket.id ? "Team at work" : ticket.status}</span>
                    <button className="btn" onClick={startRun} disabled={running}>
                      {running ? "Team is working…" : ticket.latest_run ? "Run the team again" : "Start the team"}
                    </button>
                  </div>
                </div>
                <p className="ask"><strong>The ask:</strong> {ticketAsk(ticket)}. {ticket.notes}</p>
                {ticket.latest_run && !(running && run?.ticketId === ticket.id) && <p className="decision">“{ticket.latest_run.decision}”</p>}
                {ticket.latest_run && ticket.latest_run.policy_flags && ticket.latest_run.policy_flags.length > 0 && (
                  <div className="flags"><strong>Rules check (code):</strong><ul>{ticket.latest_run.policy_flags.map((f, i) => <li key={i}>{f}</li>)}</ul></div>
                )}
                <SavedDrafts drafts={drafts} />
              </section>
            ) : <div className="card empty">Loading the board…</div>}

            <section>
              <div className="section-title"><h2>The crew, live <small>the team</small></h2><span className="count">{running ? "updating every second" : ticket?.latest_run ? "latest run" : "not run yet"}</span></div>
              <AgentFloor events={events} running={running && run?.ticketId === selected} />
            </section>

            <section>
              <div className="section-title"><h2>Flight log <small>what they're saying</small></h2><span className="count">{events.length} events</span></div>
              <Timeline events={events} running={running && run?.ticketId === selected} />
            </section>

            <section>
              <div className="section-title"><h2>Flight report <small>what each agent did</small></h2><span className="count">summary</span></div>
              {ticket && !(running && run?.ticketId === ticket.id) ? <RunSummary ticket={ticket} events={events} />
                : <div className="card empty">The summary appears when the run finishes.</div>}
            </section>

            <section>
              <div className="section-title"><h2>Debrief <small>the flight instructor · learning department</small></h2>
                <span className="count">{debrief?.count ?? 0} debriefs · updates after every run</span></div>
              {debrief?.latest ? (() => {
                const rep = debrief.latest.report;
                const mine = rep.ticket_reviews.find((x) => x.ticket_id === selected);
                return (
                  <div className="card debrief">
                    <p className="decision">“{rep.headline}”</p>
                    {mine && (
                      <div className="grades">
                        <div className="grade-big">{mine.grade}</div>
                        <div>
                          <div className="eyebrow">Flight CC {mine.ticket_id} · grade</div>
                          <p>{mine.why}</p>
                          <ul>{mine.agents.map((a) => <li key={a.role}><strong>{a.grade}</strong> · {a.role.replace("_", " ")}: {a.why}</li>)}</ul>
                        </div>
                      </div>
                    )}
                    <div className="two-col">
                      <div><div className="eyebrow">Opportunities → actions</div>
                        <ul>{rep.opportunities.map((o, i) => <li key={i}>{o.action} <span className="ticket-meta">({o.owner})</span></li>)}</ul></div>
                      <div><div className="eyebrow">Lessons</div>
                        <ul>{rep.lessons.map((x, i) => <li key={i}><span className="pill quiet">{x.status}</span> {x.lesson}</li>)}</ul></div>
                    </div>
                    <p className="ticket-meta">Next experiment: {rep.next_experiment} · Full continuous report: output/learning_report.html</p>
                  </div>
                );
              })() : <div className="card empty">The first debrief appears after a run.</div>}
            </section>
          </div>
        </div>

        <footer className="colophon">
          <span>Backend {API_BASE} · every agent runs on gpt-6-luna · shop facts through MCP only</span>
          <button className="btn ghost small" onClick={resetShop} disabled={running}>Reset the shop</button>
        </footer>
      </main>
    </>
  );
}
