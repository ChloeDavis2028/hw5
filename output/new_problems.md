# New problems for Campus Customs (Problem 10)

Research done 2026-11-07. Part A covers problems the team **can already solve** with the tools it has. Part B covers problems it **can't solve yet**, with the tools and agents each would need.

---

## Part A: Three new problems the team CAN solve today

### A1. A fake "new bank details, pay now" email from a vendor (invoice fraud)

**The real-world risk:**
- The FBI's crime center logged about **24,768 business-email-compromise complaints in 2025, with about $3 billion lost**.
- A common trick: an email that looks like it's from your supplier says "we changed banks, pay invoice 501 to this new account today."
- The standard advice is never to trust bank changes sent by email, and to verify by calling a number you already have.

**How the team handles it with today's tools:**
1. The ticket comes in, for example from "Bulldog Print Co" with "urgent, new account, pay now, don't tell anyone."
2. The **MCP screen** in `get_ticket` flags "asks to send money" and "asks to hide something". The Boss marks it **needs review**, and the code backstop removes any payment or reply.
3. Even if a person tried to pay it, `pay_approved_request` **only pays invoices already in the books, at the amount in the books**. A new account or a new amount can't be entered at all.
4. `get_invoice(501)` shows the real invoice, so Accounting can confirm it's the same $840 owed to the same vendor.

**Agents:** Boss → Accounting (the facts) → Customer Service (a draft asking the vendor to confirm by phone, held for review).

**Gap to note:** there's no "verified vendor phone number" field yet. The call-back itself is a human step.

### A2. A supplier adds a tariff surcharge to the next order

**The real-world risk:**
- Apparel import duties rose sharply in 2025.
- Blank-garment wholesalers such as Gildan and Bella+Canvas may pass costs on.
- More than half of small businesses surveyed say they can't negotiate prices to offset tariffs.

**How the team handles it:**
- **Inventory** (`check_stock`, `list_vendors`) confirms what's short and which vendor makes it.
- **Accounting** (`check_stock` pricing, `get_cash_position`) recalculates the margin with the higher cost. A hoodie at $22 → $26 cost still earns $32 at $58, or $26.20 at the 10% student price.
- Accounting then checks the restock against the **$500 cushion** before proposing a purchase order.
- **The owner decides** whether to raise prices (a business rule). The pay tool takes the cost from `pricing`, so the owner updates the price list first.

**Agents:** Boss → Inventory → Accounting → Customer Service (customer replies if prices change).

### A3. The Yale–Harvard game: a weekend demand rush

**The real-world pattern:**
- College stores report sales **spikes around homecoming and big games**, and sweatshirts and headwear are the best-sellers.
- One store sold about **$50,000** of spirit merchandise in 10 days around a big win.
- Licensed collegiate products are a market of roughly **$4.6 billion**, with about 65% in apparel.

**How the team handles it:**
- **Several orders at once:** run the **whole board** (`run_ticket.py --board`), so one payment plan covers all of them.
- **Inventory** checks every size (`check_stock` S/M/L/XL) and lead times (`list_vendors`: Bulldog Print Co, 5 days). It flags that a restock ordered after Wednesday won't arrive in time.
- **Accounting** proposes **purchase orders that fit the cushion**, and asks for deposits on big group orders (rule 14).
- **Customer Service** offers in-stock sizes first, and invites groups to **The Atelier** (rule 29).

**Gap to note:** the team can't *forecast* the rush. It only reacts to tickets (see B3 below).

---

## Part B: Three problems the team CANNOT solve yet, and what it would need

### B1. Taking money in: sales, deposits and refunds

**Why it can't today:** the homework models only cash going **out**. Nothing records a sale or the AI Club's $522 deposit, so the $500 cushion stays broken, and ticket 103 can never restock on its own.

| Needed | What it is |
|---|---|
| **Tables** | `sales` (item, size, qty, price, discount, date) and `deposits` (customer, amount, order, received_at, refunded_at) |
| **MCP tools** | `record_deposit(order, amount)` and `record_sale(...)`, both **human-only** like the pay tool. Plus `get_sales_summary(period)`, read-only, for agents. |
| **New agent** | **Point of Sale** (crew title: Gate agent). It turns approved orders into sales, tracks deposits, and tells Accounting when cash comes in. |
| **Safety** | Money-in still needs a person, and the amounts come from the order, never typed in. A payment processor runs in test mode only. |

### B2. Returns, exchanges and size swaps

**Why it can't today:** there's no `orders` or `customers` table. If Tauhid's tee arrives in the wrong size, nothing records the original sale, the swap, or putting stock back on the shelf.

| Needed | What it is |
|---|---|
| **Tables** | `orders` (customer, items, status), `customers` (name, contact, club or student status checked at pickup), `returns` (order, item, reason, outcome) |
| **MCP tools** | `get_order(id)`, read-only. `create_return(order, item, reason)`, which writes a proposal. `restock_return(item, size, qty)` and `issue_refund(order, amount)`, both **human-only**. |
| **New agent** | **Returns Desk** (crew title: Baggage services). It checks the return window and condition, offers an exchange first, and proposes refunds for approval. |
| **Safety** | A refund can't exceed what was paid, and it needs a person to approve it, exactly like payments. |

### B3. Planning ahead: forecasting demand and campus events

**Why it can't today:** the team only reacts to tickets. It has no sales history, no calendar and no weather data. It can't say "order 30 more hoodies now, because The Game is in 12 days and Bulldog Print Co needs 5."

| Needed | What it is |
|---|---|
| **Data inputs** | Sales history (from B1), a **campus and military calendar** (move-in, Homecoming, The Game, Veterans Day, commencement), a weather forecast, and web or social trend signals |
| **MCP tools** | `get_sales_history(sku, weeks)`, `get_calendar(days_ahead)`, `get_weather(days_ahead)`, all read-only. Plus a **Seasonal Editions** schedule (rule 28) the owner fills in. |
| **New agent** | **Planner** (crew title: Flight dispatcher). Each week it forecasts demand per SKU and size, compares it with stock and lead times, and proposes purchase orders that fit the cushion. |
| **Safety** | Forecasts are advice. Every purchase order still goes through human approval and the cushion check. The Flight Instructor grades forecast accuracy each week. |

---

## How these fit the learning loop

The **Flight Instructor** (Problem 10) would measure each new piece the same way it measures today's crew:
- plan vs. actual;
- wasted tool calls;
- cost per ticket;
- refusals;
- a cash check that must match `cash_accounts`.

New agents get added only when the debrief shows a gap the current crew can't close.

**Sources:**
- [Beancount: the FBI's $3 billion business-email-compromise figure and payment verification](https://beancount.io/blog/2026/08/13/business-email-compromise-3-billion-fbi-payment-verification-controls-guide)
- [PNC: protecting a small business from modern payment scams](https://www.pnc.com/insights/small-business/running-your-business/protect-your-small-business-from-modern-payment-scams.html)
- [Eftsure: US payment fraud index 2026](https://www.eftsure.com/statistics/payment-fraud-index/)
- [DecoNetwork: t-shirt tariffs](https://www.deconetwork.com/t-shirt-tariffs-how-to-navigating-uncertainty/)
- [Supply Chain Dive: small businesses and tariffs](https://www.supplychaindive.com/news/small-business-vulnerable-tariffs-us-based-smb/745028/)
- [ASI: apparel suppliers broaden supply chains](https://members.asicentral.com/news/strategy/august-2025/apparel-suppliers-broaden-supply-chains-amid-tariff-concerns/)
- [NRF: tariffs and small retailers](https://nrf.com/nrfcom/blog/sweeping-global-tariffs-represent-a-new-challenge-for-small-retailers)
- [AOL: ECU student stores see a homecoming sales spike](https://www.aol.com/ecu-student-stores-see-sales-202907709.html)
- [Barnes & Noble College case study](https://bncollege.com/?p=12591)
- [Seaside Retailer: college stores](https://issuu.com/seasideretailer.com/docs/sgn_january_2022/s/20886251)

Most of the small-business fraud and tariff figures come from secondary sources and vendor blogs; check them against the FBI IC3 2025 report before relying on them.
