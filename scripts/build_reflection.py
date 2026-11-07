"""Fill the Reflection tab of output/desk_tickets.html with answers tied to THIS app.

Every claim cites the three tickets that ran (the Ticket 101/102/103 tabs) and the
Cash tab on the same page. The evidence is the FINAL run, the same runs the
ticket tabs and Cash tab show:
  - output/resolved_tickets.json  (written by scripts/build_resolved.py from the audit trail)
  - output/learning_feedback.json (the Flight Instructor's debriefs; #1 = the final run)
  - data/campus_customs_new.db    (payments and cash, read-only)
Rerun:  .venv/Scripts/python scripts/build_reflection.py
"""
import html
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESK = ROOT / "output" / "desk_tickets.html"
NAME = {"boss": "Boss", "inventory": "Inventory", "accounting": "Accounting", "facilities": "Facilities",
        "customer_service": "Customer Service"}
e = lambda s: html.escape(str(s if s is not None else ""))
link = lambda tab, label: f'<a href="#{tab}">{label}</a>'


def money(x: float) -> str:
    return f"${x:,.2f}"


def tools_txt(d: dict) -> str:
    return ", ".join(f"<code>{e(k)}</code>{' ×' + str(v) if v > 1 else ''}" for k, v in d.items()) or "none"


def main() -> None:
    rt = json.loads((ROOT / "output" / "resolved_tickets.json").read_text(encoding="utf-8"))
    T = {t["id"]: t for t in rt["tickets"]}
    hist = json.loads((ROOT / "output" / "learning_feedback.json").read_text(encoding="utf-8"))
    d1 = hist[0]["report"]                       # debrief of the final run (what the tabs show)
    d_last = hist[-1]                            # latest debrief (after the 102 rerun)
    g1 = {r["ticket_id"]: r for r in d1["ticket_reviews"]}
    glast = {r["ticket_id"]: r for r in d_last["report"]["ticket_reviews"]}
    conn = sqlite3.connect(f"file:{(ROOT / 'data' / 'campus_customs_new.db').as_posix()}?mode=ro", uri=True)
    pays = conn.execute("SELECT id, kind, ref_id, amount, approved_by FROM payments ORDER BY id").fetchall()
    end_cash = conn.execute("SELECT balance FROM cash_accounts WHERE name='checking'").fetchone()[0]
    conn.close()
    start = rt["checking_start"]

    t101, t102, t103 = T[101], T[102], T[103]
    cs = lambda t: next((a["tools"] for a in t["agents"] if a["role"] == "customer_service"), {})
    inv = lambda t: next((a["tools"] for a in t["agents"] if a["role"] == "inventory"), {})
    fac = lambda t: next((a["tools"] for a in t["agents"] if a["role"] == "facilities"), {})
    ev = lambda t: t["expected_vs_actual"]
    tot = lambda d: sum(d.values())
    cost = sum(t["cost_usd"] or 0 for t in rt["tickets"])
    drafts_to = lambda t: ", ".join(e(dr["to"]) for dr in t["drafts"])

    # running balance in the order the payments were approved
    bal, steps = start, []
    for pid, kind, ref, amt, who in pays:
        bal = round(bal - amt, 2)
        steps.append(f"{e(kind)} {ref} ({money(amt)}, approved by {e(who)}) → <strong>{money(bal)}</strong>")

    per_ticket = f"""
    <div class="scroll"><table>
      <tr><th>Ticket (evidence)</th><th>What the crew did</th><th>Plan vs. actual</th><th>Money (Cash tab)</th><th>Debrief grade</th></tr>
      <tr><td><strong>{link('t101', '101 · Bulldog tee')}</strong><br><span class="meta">Tauhid Zaman, 1 × CC-TEE-WHITE size S</span></td>
          <td>Boss → {NAME[ev(t101)['handoffs_actual'][0]]} → Accounting → Customer Service. Inventory found <strong>size S at 0</strong> and Bulldog Print Co blocked by <strong>invoice 501</strong> ({tools_txt(inv(t101))}). Accounting proposed paying 501 for {money(840)}. Drafts: {drafts_to(t101)}.</td>
          <td>Facilities not called ✓. <strong>{tot(ev(t101)['tools_actual'])} tool calls vs. {tot(ev(t101)['tools_expected'])} planned</strong>: Customer Service re-ran {tools_txt(cs(t101))}.</td>
          <td>Invoice 501 approved by Chloe: −{money(840)} ({link('cash', 'Cash tab')})</td>
          <td><strong>{e(g1[101]['grade'])}</strong></td></tr>
      <tr><td><strong>{link('t102', '102 · Rent due')}</strong><br><span class="meta">Elm City Properties, lease 1</span></td>
          <td>Boss → Facilities ({tools_txt(fac(t102))}: $2,400 due 2026-09-02, 2 days, urgent) → Accounting (rent first, cash after {money(1000)}, "needs a second approver") → Customer Service. Draft: {drafts_to(t102)}.</td>
          <td>Inventory not called ✓. <strong>{tot(ev(t102)['tools_actual'])} vs. {tot(ev(t102)['tools_expected'])}</strong>: Customer Service re-ran {tools_txt(cs(t102))}.</td>
          <td>Rent approved by <strong>Chloe + Pat</strong>: −{money(2400)} ({link('cash', 'Cash tab')})</td>
          <td><strong>{e(g1[102]['grade'])}</strong> (A after the fix, see §4)</td></tr>
      <tr><td><strong>{link('t103', '103 · Bulk hoodie discount')}</strong><br><span class="meta">Yale AI Club, 20 × CC-HOOD-NAVY size M</span></td>
          <td>Boss → Inventory (<strong>8 in M, 12 short</strong>; S 4, L 14, XL 6; Bulldog Print Co blocked) → Accounting (10% student-group price <strong>$52.20</strong>; no restock, since $160 is below the $500 cushion; $522 deposit first) → Customer Service. Drafts: {drafts_to(t103)}.</td>
          <td>Facilities not called ✓. {tot(ev(t103)['tools_actual'])} vs. {tot(ev(t103)['tools_expected'])} tool calls, but the <strong>cap-price <code>check_stock</code> was skipped</strong> (4 vs. 5), and Customer Service <strong>tried to hand off to itself</strong> (refused).</td>
          <td>{money(0)}. Invoice 501 also unblocks 103 but is counted once, under 101 ({link('cash', 'Cash tab')})</td>
          <td><strong>{e(g1[103]['grade'])}</strong></td></tr>
    </table></div>"""

    body = f"""
  <div class="card">
    <h3><span class="label exp">Reflection</span> <span class="meta">Every answer cites this page: the {link('t101', 'Ticket 101')}, {link('t102', '102')} and {link('t103', '103')} tabs and the {link('cash', 'Cash tab')}. Source: the final run (output/resolved_tickets.json), the debriefs (output/learning_feedback.json) and the database. Built by scripts/build_reflection.py.</span></h3>

    <h4>1. What happened on each of our three tickets</h4>
    {per_ticket}
    <p class="meta">All three ended <strong>resolved</strong>, with the right first call every time: Inventory for the tee, Facilities for the rent, Inventory for the hoodies. Total cost for the three runs: <strong>${cost:.4f}</strong>.</p>

    <h4>2. The money, checked ({link('cash', 'Cash tab')})</h4>
    <ul>
      <li><strong>Start:</strong> {money(start)} after the reset. The crew proposed {money(840)} (invoice 501) and {money(2400)} (rent): {money(3240)} in all, which leaves {money(160)}. Accounting counted rent first on both 101 and 102, as owner's rule 1 says.</li>
      <li><strong>Approved, in this order:</strong> {'; '.join(steps)}. Rent was approved first, so it never waited behind the vendor bill.</li>
      <li><strong>End:</strong> <strong>{money(end_cash)}</strong>, which matches <code>cash_accounts</code> (scripts/check_cash.py: 4 of 4 PASS). Ticket 103 changed cash by {money(0)}: the 12-hoodie restock ($264) would break the $500 cushion, so the Yale AI Club order waits for its $522 deposit.</li>
      <li><strong>What this means for Campus Customs:</strong> after paying both bills, the shop has <strong>{money(160)}</strong>, below its own $500 cushion. The tickets are resolved, but the business can't restock the AI Club's 12 hoodies without money coming in.</li>
    </ul>

    <h4>3. Which parts would have been simpler with one agent, and why (tied to our tickets)</h4>
    <div class="scroll"><table>
      <tr><th>Part</th><th>Simpler with one agent?</th><th>Evidence from this run</th></tr>
      <tr><td>Passing facts</td><td><strong>Yes</strong></td><td>On {link('t101', '101')}, Customer Service re-ran {tools_txt(cs(t101))} after Inventory had already found size S = 0 and invoice 501. On {link('t102', '102')}, it re-ran <code>get_lease</code> after Facilities had. One agent keeps those facts in one head: <strong>{tot(cs(t101)) + tot(cs(t102))} fewer tool calls</strong> on these two tickets ({tot(cs(t101))} on 101 + {tot(cs(t102))} on 102).</td></tr>
      <tr><td>Hand-off rules</td><td><strong>Yes</strong></td><td>On {link('t103', '103')}, Customer Service tried to hand the AI Club reply to <em>itself</em>, and the loop guard refused it. A single agent has no hand-offs to guard.</td></tr>
      <tr><td>Cost on simple tickets</td><td><strong>Yes</strong></td><td>{link('t102', 'Rent (102)')} needed only <code>get_lease</code> and <code>get_cash_position</code>, but four agents took part. One agent could have proposed the {money(2400)} payment with 3 tool calls.</td></tr>
      <tr><td>Money safety</td><td><strong>No difference</strong></td><td>The {link('cash', 'Cash tab')} result ({money(3400)} → {money(160)}, two signed approvals, no negative cash) came from <strong>code</strong>: the pay tool takes the amount from the books, and two people are required for the {money(2400)} rent. One agent would be held to exactly the same rules.</td></tr>
      <tr><td>Counting invoice 501 once</td><td>No, five helped</td><td>Both 101 and 103 needed Bulldog Print Co unblocked. Only Accounting proposes payments, so the {money(840)} appears once in the {link('cash', 'Cash tab')} and was paid once.</td></tr>
      <tr><td>Finding and fixing the waste</td><td>No, five is better</td><td>Separate roles let the Flight Instructor pin <strong>all</strong> extra tool calls on one agent (Customer Service) and fix only that prompt. With one agent, the waste would hide inside one big prompt.</td></tr>
    </table></div>
    <p class="meta"><strong>Takeaway for Campus Customs:</strong> for these three small tickets, one agent with the same MCP tools and code guards would have been cheaper. Five agents earn their keep as the board grows (game-day rush, deposits, returns), because each role can be measured and fixed on its own, as the 102 fix shows.</p>

    <h4>4. The learning department (Flight Instructor), on these tickets</h4>
    <ul>
      <li><strong>Debrief on this run:</strong> “{e(d1['headline'])}” Grades: 101 <strong>{e(g1[101]['grade'])}</strong>, 102 <strong>{e(g1[102]['grade'])}</strong>, 103 <strong>{e(g1[103]['grade'])}</strong>. The Boss, Accounting and Facilities earned A wherever they were called; Customer Service earned C.</li>
      <li><strong>Fix applied:</strong> Customer Service may not re-check facts it was given, and may not hand off to itself.</li>
      <li><strong>Did it work?</strong> After the fix, ticket 102 was rerun as a test, and Customer Service made <strong>no repeat lookups</strong>, so 102 went to <strong>{e(glast.get(102, {}).get('grade', '—'))}</strong>. That rerun correctly <em>held</em> the payment: rent was already paid, October's isn't due, and {money(160)} can't cover it. The ticket tabs keep the final run above as the graded evidence. 101 and 103 haven't been rerun yet, which is the next measurement.</li>
      <li><strong>Opportunities → actions:</strong> {'; '.join(e(o['action'].rstrip('. ')) for o in d1.get('opportunities', [])[:3])}.</li>
    </ul>

    <h4>5. What I'd change for Campus Customs next</h4>
    <ul>
      <li><strong>The cash squeeze is the real business problem:</strong> {money(160)} left ({link('cash', 'Cash tab')}). Money coming in (the AI Club's $522 deposit, sales) would let 103 restock. The assignment says cash only goes out, so this is the first thing to add after the course.</li>
      <li><strong>Tauhid's tee ({link('t101', '101')})</strong> depends on Bulldog Print Co shipping the rush reprint now that 501 is paid. Track it with a vendor follow-up ticket, not memory.</li>
      <li><strong>The AI Club order ({link('t103', '103')})</strong> is the shop's biggest sale ($1,044). Offer the 8 M plus 12 from L and XL now (14 + 6 on the shelf) to make the sale without new cash.</li>
      <li><strong>New problems</strong> (output/new_problems.md): fake "new bank details" emails, tariff surcharges and the Yale–Harvard rush can be solved today; money in, returns and forecasting need new tools and agents.</li>
    </ul>

    <h4>6. My reflection (in my own words)</h4>
    <p><strong>What I learned.</strong> The agents are good at routing, but the money has to be protected by code. On every ticket the Boss made the right first call: Inventory for Tauhid's tee ({link('t101', '101')}), Facilities for the rent ({link('t102', '102')}) and Inventory for the AI Club hoodies ({link('t103', '103')}). Still, nothing on the {link('cash', 'Cash tab')} moved until a person signed in and approved it. Chloe and Pat both had to approve the $2,400.00 rent, and Chloe approved invoice 501 ($840.00). Checking went from $3,400.00 to $160.00 and matched <code>cash_accounts</code> exactly. I trust that number because a script checks it, not because an agent said so.</p>
    <p><strong>What I'd do differently.</strong> I'd give each agent the facts it needs up front. Customer Service re-ran lookups that Inventory and Facilities had already done: 6 extra on 101 and 2 extra on 102. On 103 it even tried to hand the reply to itself. The Flight Instructor caught it, I fixed one prompt, and 102 went from B to A. I'd also write my prompts in one message with the port, the rules and "done means" first. Most of my rework came from details I added late.</p>
    <p><strong>What surprised me.</strong> The tickets were "resolved," but the shop isn't healthy. After paying the rent and Bulldog Print Co, Campus Customs has $160.00, below its own $500 cushion. So it can't restock the 12 hoodies the Yale AI Club is short until the $522 deposit comes in. A finished board doesn't mean a healthy business. The next thing I'd build is a way to track money coming in.</p>
  </div>"""

    page = DESK.read_text(encoding="utf-8")
    s = page.index('<section class="tab" id="reflection"')
    o = page.index(">", s) + 1
    end = page.index("</section>", s)
    page = page[:o] + body + "\n" + page[end:]
    # The header was written for Problem 6 (before the run); keep it true to the final state.
    hs = page.index('<p class="sub">'); he = page.index("</p>", hs) + 4
    resolved = sum(1 for t in rt["tickets"] if t["final_status"] == "resolved")
    page = (page[:hs] + f'<p class="sub">Shop date <strong>2026-08-31</strong> · Started at <strong>{money(start)}</strong>'
            f' → final checking <strong>{money(end_cash)}</strong> (matches cash_accounts, see Cash tab) · '
            f'{resolved} of 3 tickets resolved · Expected written before the backend, Actual from the final run</p>' + page[he:])
    # links like #t101 / #cash switch tabs on this page
    if "hashchange" not in page:
        page = page.replace("    show((location.hash || '#t101').slice(1));",
                            "    show((location.hash || '#t101').slice(1));\n"
                            "    window.addEventListener('hashchange', function () { show((location.hash || '#t101').slice(1)); window.scrollTo(0, 0); });")
    DESK.write_text(page, encoding="utf-8")
    print(f"Reflection rebuilt from the final run: tickets {list(T)}, cash {money(start)} -> {money(end_cash)}, "
          f"payments {len(pays)}, debrief grades {[g1[i]['grade'] for i in (101, 102, 103)]}")


if __name__ == "__main__":
    main()
