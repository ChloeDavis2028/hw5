# Dashboard design: Campus Customs · *The Back Office*

The React desk in `frontend/` opens at http://localhost:5173 and calls the backend at http://localhost:8000.

## Who it's for, and what they care about (my words)

> "The user is a military student and they care most about **ease** and **cost**. I wanted it to feel **high end** and **warm and inviting**."

- **The person:** a student who also serves. Their time is short and split between class, duty and the shop. They're used to clear chains of command, short briefings, and two-person sign-off on anything that matters.
- **What they care about most:**
  - **Ease:** understand the shop in one glance, act in one click, never have to decode the AI.
  - **Cost:** always know what the shop is spending, both the cash leaving checking and what the AI team itself costs to run.
- **How it should feel:** **high end** (polished, calm, trustworthy) and **warm and inviting** (friendly words, soft colors, never cold or "techy").

Every choice below is tied back to **ease**, **cost**, or **warm and high end**.

## The idea in one line

**A warm, high-end back office: easy enough to run between classes, honest enough to show every dollar.** Campus Customs sells Yale apparel, so the desk feels like the quiet room behind a nice shop: stone-grey paper, warm charcoal ink and a soft slate blue. Calm and well kept, with every number easy to trust. The user should *want* to open it, and should never feel they're babysitting robots.

---

## 1. Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ CAMPUS CUSTOMS · NEW HAVEN                         Shop date   Owed   Checking│
│ The Back Office                                    2026-08-31 $3,240  $3,400 │
├───────────────────────┬──────────────────────────────────────────────────────┤
│ The board             │  Ticket No. 101 · Bulldog tee        [Start the team] │
│  ▢ 101 Bulldog tee    │  The ask: 1 × CC-TEE-WHITE · size S · invoice 501      │
│  ▢ 102 Rent due       │  "The team's last call, in italics"                   │
│  ▢ 103 Hoodie discount├──────────────────────────────────────────────────────┤
│                       │  The team, live   [Boss][Inventory][Accounting]...    │
│ Awaiting approval     ├──────────────────────────────────────────────────────┤
│  $840.00 Bulldog Print│  What they're saying (live timeline)                  │
│  [name] [Approve][Rej]├──────────────────────────────────────────────────────┤
│  $2,400.00 Elm City   │  What each agent did (summary, cost, drafted replies) │
└───────────────────────┴──────────────────────────────────────────────────────┘
                                                         [Reset the shop]
```

| Zone | What it holds | Why it sits there | Serves |
|---|---|---|---|
| **Masthead ledger** (top right) | Shop date, total owed, **checking balance** | Money is the first thing a cost-minded owner checks, so it always stays in view | **Cost** |
| **Left rail** | The board (3 tickets), then **Awaiting approval** | Everything the user *acts on* sits on one side: pick work, then sign off on money. No menus, no second page. | **Ease** |
| **Main column** | The selected ticket, then the team live, then the timeline, then the summary | It reads top to bottom like a briefing: the ask (the situation), who's on it (the team), what they're saying (the reports), what they did (the after-action summary) | **Ease** |
| **Footer** | Reset the shop, plus the line "gpt-6-luna · shop facts through MCP only" | Rare or risky actions stay out of the way, behind a confirm dialog | **Ease** (no accidents) |

On a narrow screen (under 980 px) the rail stacks above the main column, and the agent cards drop from 5 across to 3, then to 1.

---

## 2. How each agent reads differently

Each agent has **its own color, a monogram, and a voice**, so you can tell who's talking without reading a label.

| Agent | Color | Why that color |
|---|---|---|
| **The Boss** | Deep warm navy `#253a55` | Authority and the final call |
| **Inventory** | Grey-sage `#5d7a6c` | Shelves, stock, steady |
| **Accounting** | Warm slate blue `#4f6f92` | Money, in the shop's accent color |
| **Facilities** | Heather grey-violet `#77708a` | The building and the lease, a quieter role |
| **Customer Service** | Dusty teal-blue `#4a7d8a` | Warm and open, the voice to customers |

The same color carries everywhere that agent appears:
- the thin bar across the top of its card and its round **monogram** (B, I, A, F, C, set in the serif);
- its name in the **timeline**;
- its row in the **summary**.

### Three states, readable at a glance

| State | How it looks | Why |
|---|---|---|
| **Not called** | Faded to 50% with "Waiting at the desk." | It shows *who the Boss chose not to bother*. Seeing Facilities sit out ticket 101 is part of the story, not a gap. |
| **Working…** | A color glow around the card and a colored state label | Your eye goes to whoever is active right now |
| **Done** | Full color, settled, with its final report | Finished work looks calm |

### Words vs. actions

- **What an agent says** is set in an **italic serif**, like a quote, so it reads as a person's voice: *"The requested size S is out of stock…"*
- **What an agent does** shows as small **monospace tool chips**, like `check_stock ×4` and `list_vendors`, so you can see the machine work underneath the words.
- **Hand-offs read as plain English:** "Picked up a request from The Boss…" and "Asked Accounting: …".

---

## 3. How resolved tickets show up

- **Status pills** use calm, distinct colors, and each one also has a **word**, so color is never the only signal:
  - **Open** is warm amber;
  - **Resolved** is sage green;
  - **Running** is navy with a softly pulsing dot;
  - **Held for review** is rouge.
- When a run finishes, the ticket card flips from *Running* to **Resolved**, and the board's count updates (for example "2 open · 1 resolved").
- Each card also shows the **team's call** ("needs approval", "waiting") and how many items wait for approval. *Resolved* means the team finished its work, and the money still waits for a person.
- The summary ends in a small **facts strip**: the team's call, the ticket status, payments proposed, replies drafted, and the **run cost** (for example $0.0050). That builds trust in what the team spent.

## 4. How cash shows up (built for **cost**)

- **Checking** is the largest number on the page: 40 px Cormorant Garamond with even-width digits, so the figures line up. A small caption says where it comes from ("from cash_accounts").
- **After an approved payment**, the balance refreshes and a small rouge **"−$840.00"** rises next to it and fades out over 4 seconds. You *see* the money leave, which is the moment that matters.
- **Owed** sits beside it ($3,240 → $2,400 after the invoice), so the next decision is obvious.
- **Approval cards** lead with the amount in large serif type, then the payee, then the agent's one-line reason. Each card also shows "Checking after, as proposed: $160.00", so you know the consequence *before* clicking.
- **Over $1,000, a second name field appears.** The two-person rule is visible in the screen itself, not hidden in a rulebook.
- **Refusals land right on the card**, in plain words: "a second, different person must approve too." A paid card turns **Paid** and softens, so finished money no longer competes for attention.
- **Two-person sign-off over $1,000** will feel familiar to a military user: it's the same idea as two-person integrity for anything high-stakes.
- **The AI's own cost is shown too.** Each run's summary gives its price (about **$0.005** a ticket), and "Not called" agents show the team didn't spend effort it didn't need. A cost-minded owner can see that running the team costs less than a cent.

---

## 5. The creative choices that make it feel special

### Ease, for a busy military student

- **One click to run.** Pick a ticket, then press **Start the team**, and that's it.
- **Glanceable status.** Each agent shows Working, Done or Not called, the way a status board shows who's on task.
- **Plain words, not AI jargon.** "Picked up a request from The Boss…" and "Asked Accounting: …".
- **Nothing to remember.** Your approver name is saved, and the timeline scrolls itself.
- **Clear help when something's off.** If the backend is down, the banner says what to do ("Is uvicorn running?").

### Warm and inviting, and high end

1. **A boutique, not a cockpit, in warm blues and greys** (my words: "use warmer blue and grey tones"). Stone-grey paper (`#f1efec`), warm white cards (`#fbfaf8`), warm charcoal ink (`#23272e`) and one soft slate-blue accent (`#4f6f92`), with hairline rules instead of heavy boxes. Blue and grey read calm, trustworthy and quietly expensive, like a tailored navy blazer on a grey flannel day. That suits a shop for Yale and military customers, and it keeps money screens feeling steady, not loud.
2. **Editorial typography.** *Cormorant Garamond* for headings, numbers and agent voices, with *Inter* for small print. Labels are spaced small caps ("THE BOARD", "AWAITING APPROVAL"). Two well-paired fonts do the work, instead of icons and badges.
3. **A name with a wink:** *The Back Office*, with *Office* in slate-blue italics. The tagline sets the tone and the rule at once: "Five agents work the board. Nothing is paid until you approve it."
4. **The agents feel like colleagues.** Monograms, a voice and hand-offs written as sentences ("Asked Accounting: …"). Watching a run feels like watching a small team pass a folder down the hall.
5. **Calm motion only where it means something:**
   - a pulse while running;
   - a glow on the active agent;
   - the cash "−$" flash;
   - cards lift 1 px on hover.

   Nothing else moves, so motion always signals something real.
6. **The human is the star of money moments.** "Awaiting you" on every unpaid card and "Approve & pay" in slate blue: money moves when *you* decide, and the screen says so.
7. **Honest by default.**
   - Drafted replies sit behind "Read the drafted replies (never sent)".
   - Every agent's tools are listed.
   - The run cost is shown.
   - Agents that weren't needed are visibly "not called".

   People trust what they can see.
8. **Small kindnesses:**
   - the approver name is remembered on this computer;
   - the live timeline auto-scrolls to the newest line;
   - Reset asks first and says the audit trail is kept;
   - if the backend is off, a banner says exactly what to do: "Is uvicorn running?"

## 6. Accessibility and practical choices

- **Status:** every status pairs a color with a word or label.
- **Contrast:** body text in charcoal on stone grey is high contrast, and muted text is used only for captions.
- **Keyboard:** tickets and buttons are real `<button>`s, with visible slate-blue focus rings.
- **Screen readers:** the live timeline is `aria-live="polite"`, so new lines are announced.
- **Responsive:** it works down to phone width (see the layout notes above).
- **Fonts:** load from Google Fonts. Without internet they fall back to Palatino or Georgia and Segoe UI, so the look survives offline.

## 7. What I'd add next

- **Cost:** a running "AI spend this month" figure next to checking, and a warning before a run would go over a set budget
- **Ease:** a "Run the whole board" button that works all three tickets and shows one payment plan (the backend can already do this)
- A dark "after hours" theme for late study nights (charcoal paper, pale blue type)
- A small run replay: scrub through a finished run like a timeline
- Sign-in for approvers, so names can't be typed in by anyone (a red flag from Problem 7)
- Show the Problem 6 **Expected** plan next to the live run: expected agents faded in, actual agents lit, mismatches highlighted

---

## 8. Learning from brand-led boutique businesses

Research, 2026-11-07. Most of these companies are private, so the revenue figures are **reported estimates**; where sources disagree, the range is given.

| Business | Scale (reported) | What their brand does that earns money | How Campus Customs can use it |
|---|---|---|---|
| **Aesop** (skincare) | About $537M in sales in 2022; bought by L'Oréal for about $2.5B in 2023 | **Design-led:** every store is designed with local architects. Brass and ceramic details, calm and consistent. The look *is* the brand. | It confirms the ivory, ink and brass desk. Keep every customer-facing draft in one warm, polished voice, and treat the dashboard and the shop as one experience. |
| **Grunt Style** (veteran-operated apparel) | Estimates range from about $14M to $134M a year; 400+ employees | **Identity and community:** patriotic, veteran-operated, and grown into a monthly box club, a fitness app and even bourbon | The **Lock and Load Sale** is a real lever. Grow it into a *community*: a military and student-veteran line, and a "Bulldog Brigade" monthly box. |
| **Black Rifle Coffee** (veteran-founded) | NYSE-listed; 2M+ lifetime direct customers and 271K+ subscription members (2023 filing) | **Mission plus subscription:** a Coffee Club for recurring revenue. A public give-back: $34M of veteran medical debt cleared with a partner in 2025. | Add a **subscription** (a new crest item each term) and a visible **give-back**, such as a share of Lock and Load sales to a student-veteran group. Recurring revenue would ease the cash squeeze. |
| **Kith** (streetwear retail) | About $300M (2024 estimate) | **Drops and collaborations:** a weekly release program, partners from Nike to Coca-Cola, and "retail theater" | Run **drops on a calendar** (move-in, Homecoming, The Game, Veterans Day), and **collaborate with clubs**. The Yale AI Club order could become a co-branded capsule. |
| **Rowing Blazers** (collegiate prep) | About $10–25M; around 70% yearly growth since 2018 (reported) | **Heritage storytelling** for a new generation; a women's line drove a big jump; a Target collaboration widened reach | Tell the **Yale and New Haven story** in product copy. Expand **women's** and gift lines. One partner collab can bring in new buyers. |
| **Aimé Leon Dore** (NYC menswear) | Revenue undisclosed; one report says about $30M. LVMH took a minority stake in 2022. | **Place-based story:** an homage to the founder's Queens upbringing, mixing art, sport and music | Root the brand in **New Haven and campus life**, not just "Yale merch", with a story for each product. |

### What this means for the product

**Adopted by the owner ("Brand voice + club", then "do it in a classy way" for both):** items 1–5 are now owner's rules 25–29: a classy concierge voice, the Lock and Load Club, The Crest Society subscription, Seasonal Editions and The Atelier collaborations. The names are proposed and awaiting the owner's confirmation. Rules 25 and 26 were first tested in `backend/prompts/_owner_rules.md`, tested on ticket 103 and a sample veteran order.

1. **Brand voice is a rule, not decoration.** Add it to the owner's rules for Customer Service: "write like a fine New Haven shop: warm, polished, never pushy." Aesop shows a consistent voice is worth billions.
2. **Community beats discounts.** Grunt Style and Black Rifle grew on identity and membership. Lock and Load becomes a *club*, not just 15% off.
3. **Recurring revenue fixes cash.** The shop's real problem was **$160 left after bills**. Subscriptions and deposits (rule 14) bring cash in *before* restocking.
4. **Drops create urgency without deep discounts.** A small, timed release sells at full margin, unlike the 50% holiday blowout.
5. **Collaborations are free marketing.** Each student club (the AI Club, rowing, ROTC) is a potential co-branded capsule.

---

## 9. Other inputs that would make the product smarter

These are data the agents don't have today. The database has no sales, customers or calendar.

| Input | What it adds | Agent that uses it | Ease, cost or brand |
|---|---|---|---|
| **Sales and order history** (point-of-sale or online store) | Real revenue (the homework models cash going out only), best sellers, and which sizes run out first | Inventory, Accounting | Cost |
| **Customer profiles** (student, military or veteran status checked once, club membership, past orders) | Correct discounts without asking every time, plus loyalty and "welcome back" replies | Customer Service, Accounting | Ease, brand |
| **Campus and military calendar** (move-in, Homecoming, The Game, commencement, Veterans Day on Nov 11, holiday breaks) | Timed drops, restocks before rushes, and when the 50% blowout really applies | Inventory, Boss | Brand, cost |
| **Vendor quotes and invoices from email** (the HW6 vendor desk) | Fresh prices and lead times, and invoices that arrive by themselves | Accounting, Inventory | Ease, cost |
| **Real shipping tracking and lead-time history** | Honest "arrives in X days" instead of a waitlist guess | Customer Service | Ease |
| **Weather forecast** | Hoodie demand jumps when it turns cold, so restock early | Inventory | Cost |
| **Product photos and reviews** (HW3 image skills) | Richer replies, size advice ("runs large") and fewer returns | Customer Service | Brand |
| **Web traffic and social mentions** | Spot a trend before stock runs out | Inventory, Boss | Brand |
| **Competitor prices** (the campus bookstore and online shops) | Smarter discount floors | Accounting | Cost |
| **Club rosters and orders** (with permission) | Group orders, custom capsules and deposits | Customer Service, Accounting | Brand, cost |
| **Payment processor in test mode** (deposits, refunds) | Money coming **in**, so the cash squeeze can actually be fixed | Accounting | Cost |
| **AI usage log** (already exists: `output/usage_log.json`) | An "AI spend this month" figure on the dashboard | Dashboard | Cost |

**Sources:**
- [L'Oréal: agreement to acquire Aesop](https://www.loreal.com/en/press-release/group/l-oreal-signs-an-agreement-with-natura-and-co-to-acquire-aesop/)
- [Forbes Australia: L'Oréal acquires Aesop](https://www.forbes.com.au/life/lifestyle/loreal-acquires-melbourne-luxury-beauty-brand-aesop-for-us2-5b/)
- [Aesop on Wikipedia](https://Www.wikipedia.org/wiki/Aesop_(brand))
- [Grunt Style: about](https://www.gruntstyle.com/pages/about)
- [Zippia: Grunt Style revenue](https://www.zippia.com/grunt-style-careers-1411130/revenue)
- [ECDB: Grunt Style](https://ecdb.com/resources/sample-data/retailer/gruntstyle)
- [BusinessWire: Black Rifle Coffee long-range targets](https://www.businesswire.com/news/home/20250114168237/en/Black-Rifle-Coffee-Company-Announces-Long-Range-Financial-Targets-and-Reaffirms-2024-Guidance/)
- [BusinessWire: Black Rifle Coffee and veteran medical debt](https://www.businesswire.com/news/home/20251124609072/en/)
- [Black Rifle Coffee SEC filing (CapEdge)](https://capedge.com/filing/1891101/0001104659-23-035128/POSAM)
- [Latterly: Kith marketing strategy](https://www.latterly.org/kith-marketing-strategy/)
- [Business of Fashion: the hustle behind Kith](https://www.businessoffashion.com/articles/retail/the-hustle-behind-kith-ronnie-fiegs-self-made-sneaker-empire)
- [Glossy: Rowing Blazers](https://www.glossy.co/fashion/rowing-blazers-helped-revitalize-preppy-fashion-now-its-founder-is-stepping-away/)
- [Yahoo/WWD: Rowing Blazers and the prep revival](https://www.yahoo.com/lifestyle/rowing-blazers-proving-prep-revival-170000222.html)
- [Retail Dive: LVMH stake in Aimé Leon Dore](https://www.retaildive.com/news/lvmh-investment-arm-takes-minority-stake-in-streetwear-brand-aime-leon-dore/617282)
- [Substack: "Clothes don't need to mean anything"](https://alecleach.substack.com/p/clothes-dont-need-to-mean-anything)

---

## 10. Aviation touches (my words: "high end boutique look but include aviation")

Aviation, the way a private-aviation lounge does it: quiet details, never a cockpit.

| Touch | Where | Why |
|---|---|---|
| **KHVN** (New Haven's airport code) in the eyebrow | Masthead | A small insider detail; it places the shop in New Haven |
| A **dashed flight path ending in a small plane**, in slate blue | Under the tagline | One graceful line instead of icons everywhere |
| **Boarding-pass tickets**: "✈ Flight CC 101", a perforated stub line, punched notches | The board | Every ticket is a journey to a resolution, recognized at a glance |
| **Crew titles**: Captain (Boss), Cargo master (Inventory), Purser (Accounting), Ground crew (Facilities), Cabin crew (Customer Service) | Agent cards | The agents feel like a professional crew with clear roles. That fits a military user used to chains of command. |
| **Section names**: Departures, The crew live, Flight log, Flight report, Awaiting clearance, each with a plain subtitle | Everywhere | It's themed, but the plain subtitle ("the board", "your approval") keeps it easy |
| "Nothing is paid until you **clear** it" | Tagline | You give the clearance; the crew never moves money on its own |

The warm blue and grey palette already reads like a navy-and-silver aircraft livery, so the aviation details sit naturally in it.

## 11. The Debrief panel and the continuous report (Problem 10)

- **On the board:** a "Debrief" section under the Flight report. It shows the Flight Instructor's headline as a quote, then a big round **grade** for the selected flight with the reason. Each crew member's grade follows, then **Opportunities → actions** and **Lessons** side by side.
- **Why:** the owner cares about **ease** and **cost**. The debrief says in one line what to fix next, with numbers, so improving the team takes no digging.
- **The continuous report** (`output/learning_report.html`, double-click to open) uses the same warm blue-grey style. Grades are color-coded (A in sage, D or F in rouge, "not called" as an outline). Its trend table grows with every debrief, so you can see the team getting better or worse over time.

## 12. The better-product pass, on screen

- **Approver sign-in** sits at the top of *Awaiting clearance*: you sign in once. Cards say "Approving as Chloe (owner)". Over $1,000, a second sign-in appears inside the card. **Ease:** no retyping names. **Trust:** names can't be faked.
- **AI spend · this month** sits in the masthead next to Owed and Checking ("$0.08 of $5.00 budget"). It turns brass near the limit and rouge over it. **Cost:** the owner sees AI cost as clearly as cash.
- **The instructor's top fix** sits under the title in italic serif. It's the one thing to improve next.
- **"Awaiting clearance" tags** on ticket cards replace "to approve" once payments are cleared, so nothing looks unpaid when it isn't.
- **"Replies on the board · N saved, never sent"** is a quiet fold-out under each ticket, so staff can read and send by hand.
- **"Run the whole board"** is a full-width quiet button under Departures. One click, one shared payment plan.
- **Rules-check flags** show in a soft rouge box on the ticket when code held back a reply.

