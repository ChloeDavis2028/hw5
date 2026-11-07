# AI Prompts Log — HW5: The Shop's Agent Team

This file is the log of what I typed to my vibe coder. There is one section for each problem. Each section has the problem number and title, at least one prompt I typed in my own words, and one follow-up prompt if I needed it, with one sentence on what was lacking after the first.

## A note on my screenshots

I sent some assignment instructions as screenshots. These were setup rules, not problems to solve, so retyping them would not have added anything. I used them only for those rules. I still worked one problem at a time and directed the work in my own words.

- **Shop rules:** today is `desk.date_today`; lead times come from the `vendors` table; a vendor won't ship while it has an unpaid invoice; every payment needs human approval; no negative cash; no revenue; reset the database before a full run; no real emails or vendor calls; only `gpt-6-luna` through Portkey.
- **Problem 1, the log rules:** create this file at the start and keep it updated as the record of what I typed.

## Getting started (before the numbered problems)

**Prompt:**
> Home work 5

**Prompt:**
> this is the assignment about the agentic team that runs  the shop. Open tickets land on a board - customer orders, rent, unpaid bills, discount requests, anything the shop needs handles.  You will build three pieces that talk to each other: an MCP server, a FASTAPI backend with a multiagent team, and a React dashboard so a human can watch the agents work and approve the requests.

**Prompt (sent with three screenshots of the shop rules):**
> Your team has full connectivity - any agent may delegate tasks to any other agent for help. You will build a boss (reads each ticket, decides who shuld work on it and make final calls), Inventory (checks stock by SKU and size, spots shortfalls and figures out which vendor can restock), Accounting (watches cash and onvoices, checks margins, and prepares payments or purchase orders for human approval) and Facilities (handles the shopspace side as in leases, rent etc)

## Problem 1: Vibe coder prompts

**Prompt (sent with one screenshot of the AI_prompts.md instructions):**
> the first Probem is about the Vibe Coder prompts:  I do need to learn how to write them better, be more specific, and figure out my blind spots before you do.  Creating the AI_prompts.md helps the assignment but still continue my own checklist and Prompt running log from previous assignments so I can learn too.  Give me input and create a checklist so I can continue to do this without the class.

**Follow-up prompt:**

**What was lacking after the first:**
I asked for a prompt log and a checklist but didn't name the files or say what goes in each, so the format had to be guessed.

**Stronger prompt:**
> Create AI_prompts.md that logs every prompt I type word for word, with a blank "What was lacking" line under each problem, and HW5_Checklist.md with the assignment rules and a status table.


## Problem 2: Study the Campus Customs database

**Prompt:**
> Problem 2: Study the Campus Customs database

**Follow-up prompt:**
> open data/campus_customs.db and look thru every table and its fields.  Copy the original file to data/campus_customs_new.db - later problems update the working copy.  study the three open tickets so you can see how they link to other tables.

**Prompt (second part):**
> start output/harness.md. for each table, list the fields and one short line on why that table matters for the agents.  this harness file will keep growing in later problems

**What was lacking after the first:**
I said "open the database" without saying what to look for or where to save it. The download and harness.md came in later messages.

**Stronger prompt:**
> Open data/campus_customs.db, list every table with row counts and the columns tickets 101-103 need, save it to output/database_study.md, make the working copy campus_customs_new.db, and start output/harness.md.


## Problem 3: Build the MCP server

**Prompt:**
> Problem 3:  Build the MCP server

**Follow-up prompt:**
> write an MCP server in mcp_server/ using FastMCP. it talks to data/campus_customs_new.db. you dont have to connect or run it in this problem. Every agent in this HW uses the tools in theis MCP server. More tools will be added but for now only three tools will need for the tickets in the database.  Keep the names clear. never invent any data, only use info in the database

**Prompt (second part):**
> in output/harness.md, list each of the three MCP tools. for every tool include:  which table it reads, which ticket it helps unlock (101,102,or 103) and one sentence on why that tool is the right one for that ticket.

**Prompt (third part):**
> vague lines like "reads inventory" score low - tie the tool to the ticket. also add a short mcp_server/README.md file that explains what the MCP server is for, which database file it uses, and the three tools has it

**What was lacking after the first:**
My first tool list was vague ("reads inventory"). It didn't tie each tool to ticket 101, 102 or 103, and I asked for the README later.

**Stronger prompt:**
> Build three read-only FastMCP tools in mcp_server/server.py that never invent data. In harness.md list each tool, the table it reads and the ticket that needs it. Add mcp_server/README.md.


## Problem 4: Add the MCP server to vibe coder and test each tool

**Prompt:**
> Problem 4: Add the MCP server to vibe coder and test each tool:  in the vibe coder, add your MCP server to this project so the vibe coder can call the tools. Save the connection JSON text in .mcp.json at the project root ((or however your vibe coder saves local MCP server lists).

**Prompt (status check):**
> give me an update on where this assignment is and what has been done from an AI agent perspective: create a running log on lessons learned and tasks to acheive to make sure I can do this assignment without this website.  Create a checklist

**Prompt (second part):**
> with the vive coder connected, test each of your three MCP tools. Save the evidence in output/mcp_smoke.json

**Prompt (third part):**
> every tool will include: the prompt you asked the vibe coder, the tool name, the tool output (must match values in data/campus_customs_new.db)

**Prompt (vibe coder test session):**
> Read HW5_Checklist.md and output/harness.md first. Problem 4: with the campus-customs MCP server connected, call each of the three tools yourself: check_stock("CC-HOOD-NAVY","M") for ticket 103, check_stock("CC-TEE-WHITE","S") and get_invoice(501) for ticket 101, get_lease(1) for ticket 102. Add each call to output/mcp_smoke.json with the prompt, the tool name and the tool output, and confirm the values match data/campus_customs_new.db. Log my prompts word for word in AI_prompts.md. Only this problem.

**Follow-up prompt:**

**What was lacking after the first:**
I didn't know the goal was to prove each tool returns real database data, so I had to ask twice about the gaps and the intent.

**Stronger prompt:**
> Add .mcp.json so the vibe coder can call my server. Test each tool and save output/mcp_smoke.json with my prompt, the tool name, the output and whether it matches the database.


## Problem 5: Build the agent team and grow the MCP tools

**Prompt:**
> Problem 5:  Build the agent team and grow the MCP tools:

**Follow-up prompt:**
> now build the agentic team for Campus Customs using Pydantic AI: Boss, Inventory, Accounting, Facilities and Customer Service. Include prompts, models, and agent loops so they can delegate work to each other with full connectivity. this will be done by putting the agent prompts in backend/prompts/ one file per agent.  put data types in backend/models.py and the agent files unde backend/. the layout can vary as long as the five rols are clear. use the PORTKEY_API_KEY and only gpt-6-luna for every agent.

**Prompt (third part):**
> each prompt needs to be written by me with the shop rules the agent needs.  but show me some examples in the begginning so i can then give more detailed prompts later

**Prompt (fourth part):**
> add any tools the agents need to the MCP server so they can work on the open tickets. shop facts come from the MCP server over data/campus_customs_.new.db - do not invent a second shop tools layer that bypasses MCP.

**Prompt (fifth part):**
> wire the agents so they append to output/audit_trail.json as they run:  for each agent - loop step, record enough to audit later. append to this file - do not wipe it each run.

**Prompt (sixth part):**
> in the output/harness.md, list each agent and each MCP tool along with which table the tool uses. also add a short safety section: the gaurdrails a real business would want when the agents touch the real customers and real money, plus limits that keep token use in check. update the mcp_server/README.md so the tool list matches what i have now

**Prompt (seventh part):**
> guide me thru rewriting the prompts:  separate by problem and focus on what is missing

**Prompt (eighth part):**
> ok this is still not mking sense, just tell me exactly what you need to accomplsih the mission

**Shop rule answers (my words, for the agent prompts):**
> pay mandatory bills first but what bill makes more logical sense?  rent probably but why

> i love discounts... bggest dicount are end of year holiday blowouts to get rid of stock so go 50%

> make a fun military sale then,

> student discounts 10%

> ID pick up rule works

> Lock and Load Sale; discounts can not combine, partial ordersonly if financially responsible, regular short, agent asks a team mate when no decision can be made, always reply in a fun but professional manner

**Prompt (ninth part):**
> this still does not seem sufficient, give me more gaps to fill or opportunities to tack advantageof and make more money

**Prompt (tenth part):**
> fix and recommend the best outcome for the above

**Prompt (eleventh part):**
> what other gaps to fill?

**Prompt (twelfth part):**
> Yes, fix them

**Prompt (thirteenth part):**
> what else can be done

**Prompt (fourteenth part):**
> make sure one thru 6 works

**Prompt (fifteenth part):**
> follow thru with your recs

**Prompt (sixteenth part):**
> Yes, add it

**Prompt (seventeenth part):**
> review suspicious tickets

**What was lacking after the first:**
My shop rules came in many small messages, and I asked for examples instead of giving my rules once ("just tell me exactly what you need").

**Stronger prompt:**
> Build Boss, Inventory, Accounting, Facilities and Customer Service with Pydantic AI, gpt-6-luna through PORTKEY_API_KEY only. My rules: [bill order, discounts, ID pickup, partial orders, voice]. Ask me any owner decision. Append every step to output/audit_trail.json.


## Problem 6: Plan the three tickets

**Prompt:**
> Problem 6: Plan the three tickets

**Follow-up prompt:**
> Before the backend is wired, write down what you expect the tram to do on each open ticket. Build output/desk_tickets.html. this page you can double click with one tab per ticket (101, 102, and 103). Also add empty Cash and Reflection tabs for later problems. leave them. on each ticket tab, fillan Expected section only (leave room for an Actual section wuou will fill after you run agents

**Prompt (second part):**
> For each ticket's Expected section make sure you know wo the Boss should call first and why.  All the agent delegations you expect - not "Boss calls everyone" and which MCP tools you expect that run to use.   plans that send every sepcialisy on every ticket score low. You will cmpare this plan to what actuallyhappens when your agent resolve the three tickets.

**What was lacking after the first:**
I added "don't send every specialist on every ticket" in a second message, so the first plan wasn't testable.

**Stronger prompt:**
> For tickets 101-103 in output/desk_tickets.html, write who the Boss calls first and why, each hand-off, who is not called, and the exact MCP tools.


## Problem 7: Backend Routes

**Prompt:**
> problem 7: Backend Routes

**Follow-up prompt:**
> Your React frntend dashboard (the next problem)) needs a backend it can call. In backed/main.py, use FastAPI and add routes that do the following: retuen the three tickets and whether each is open or resovolved, take a ticket id and run your agent on that tikct, return recent agent events - what each agent said and    which tools they used-so the board can refresh,

**Prompt (third part):**
> approve a payment or purchase after human clicks approve (agents only prepare the pay; this route is what actually chanes cash); return the current checking balance from cash_accounts; reset the database to the original values when you want to try a fesh rn

**Prompt (fourth part, sent as a screenshot of the assignment's run command):**
> (screenshot) From the backend/ folder, start the server with: `uvicorn main:app --reload --port 8000`. This turns on your backend at http://localhost:8000 so the frontend dashboard can call those routes.

**Prompt (fifth part):**
> list each route in one line in the output/harness.md and what it does/url

**Prompt (sixth part):**
> give me an update on what this problem did

**Prompt (seventh part):**
> execute the above

**Prompt (eighth part):**
> explain in basic terms what this problemdid, what opportunities happened andwhat red flags remain

**Prompt (ninth part):**
> Done, start it

**Prompt (tenth part):**
> Yes, end them

**Prompt (eleventh part):**
> give me in baisc terms what happened in this problem

**Prompt (twelfth part):**
> with this entire problem create a studyguide on what was done, how and why for future taskers.  update the checklist created and give me better prompt ideas and why

**Prompt (thirteenth part):**
> what were the biggest lessons learned

**Prompt (fourteenth part):**
> how was this takeaway enforced in code on this assignment: give me all examples of the safety rules

**Prompt (fifteenth part):**
> include this in study guide

**Prompt (sixteenth part):**
> update my prompt sheet accordingly, from my questions help mme build better AI prompts

**Prompt (seventeenth part):**
> ensure all the above is imlemented in this assignment

**What was lacking after the first:**
I sent it in five pieces, and the port (8000) and run command came last, after the server was built on another port.

**Stronger prompt:**
> Build backend/main.py with FastAPI on port 8000 (uvicorn main:app --reload --port 8000): list tickets, run a ticket, show events, approve a payment only after a human clicks approve, return checking, reset the database. Done means: approve invoice 501 and checking drops $840.


## Problem 8: Agent Dashboard

**Prompt:**
> Problem 8: Agent Dashboard

**Prompt (second part):**
> dont do anything with problem 8 until i tell you

**Prompt (third part):**
> why would it matter?

**Prompt (fourth part):**
> lets stop and then bring back when warranted

**Follow-up prompt:**
> Build the frontend dashboard in frontend/ with React and Vite and TypeScript. call the routes built in problem 7. at min the board should:

**Follow-up prompt (the list):**
> list all 3 tickets, lets one ticket be picked adn start the agent team on it, show each agetn and what they are saying / doing while the ticket runs, mark a ticket resolved when the run finishes, show a short summary of what each agent did on that ticket, let a human approve a pay or purchase when asked, show the checking balance should drop after an approved pay

**Prompt (look and feel):**
> lets have a boutique feel with high end aesthetiques

**Prompt (connection rules):**
> front end must talk to backend at htto://localhost:8000.  on the back end allow the Vite page origin (usually http://localhost:5173 so the browser is allowed to call those routes.

**Prompt (run command, sent with a screenshot):**
> Start the board with
> (screenshot) npm run dev

**Prompt (sent as a screenshot of the assignment text):**
> (screenshot) Write output/design.md with what you chose for the dashboard look (layout, how agents read differently, how resolved tickets and cash show up) and why, including the creative choices that make it feel special and something humans would actually enjoy using.

**Prompt (asking for help understanding it):**
> i need further understanding of what is being asked before I can write my own prompt. help please

**Prompt (my own words for the design):**
> the user is a military student and they care most about ease and cost. i wanted it to feel high end and warm and inviting.

**Prompt (research):**
> what are other inputs that can used to augment this product? Also search for outside boutique businesses that have high revenue based off their brand and use accordingly.

**Prompt (my choice of ideas):**
> Brand voice + club

**Prompt:**
> do it in a classy way

**My answer when asked which part (voice, the open ideas, both, or the dashboard):** Both

**Prompt (asked whether to keep the three proposed names):**
> The Atelier

**Prompt (dashboard colors):**
> use wamer blue and grey tones

**Prompt (answering whether to keep The Crest Society and Seasonal Editions):**
> yes

**Prompt:**
> reset then run all three tickets on the board.

**Prompt:**
> open output/desk_tickets.html

**Prompt (Problem 6 follow-up):**
> from problem 6. on each ticket tab, fill the  Actual section from this run ;; which agents worked, what they delegated, and which tools they used. keep your Expected section so you can copare the two

**Prompt (sent with screenshots of the assignment text):**
> itimize the money:
> (screenshots) On the Cash tab of the same output/desk_tickets.html: starting checking balance (after the reset); for each ticket, how cash changed when that ticket resolved, and why (which pay or purchase, dollar amount); ending checking balance, which must match cash_accounts in the working database. Also save output/resolved_tickets.json (for each ticket: id, final status, short outcome, what each agent contributed, and any human approvals) and output/resolved_board.html (a page you can double-click with a screenshot of the React board for each resolved ticket). Append real runs to output/audit_trail.json. Finish output/harness.md so it covers tables, MCP tools, the five agents, API routes, the dashboard, and safety rules.

**Prompt:**
> ok again, lets figure out the

**Prompt:**
> explain in detail what this prompt is asking and how it works?

**Prompt:**
> in checklist form, how would a basic new student write these prompts?

**Prompt:**
> Exact file: output/desk_tickets.html

**Prompt:**
> what goes in it: starting ba;ance, change per ticket, ending balance

**Prompt:**
> check it by making sure it must match cash_accounts

**Prompt:**
> always explain things simply

**Prompt:**
> give me an update

**Prompt:**
> approve on the board yourself

**Prompt:**
> high end boutique look but include aviation

**What was lacking after the first:**
I pasted screenshots instead of typing the steps, and I said who the board is for (a military student who cares about ease and cost) after it was built.

**Stronger prompt:**
> Build the board in frontend/ (React + Vite + TS, npm run dev, :5173) calling :8000. User: a military student who wants ease and low cost. Feel: high end, warm blue and grey, aviation. Then reset, run 101-103, approve, and itemize cash so the end matches cash_accounts.


## Problem 10: Reflection

**Prompt:**
> Problem 10: Reflection

**Follow-up prompt:**
> lest build a department that is constantly learning, updating, providing data based feedback to improve

**My answer when asked what the learning department should be:** A sixth agent

**Prompt:**
> need a continuous updated report

**Prompt:**
> evaluate the performance of the agents per ticket and tell mewhy; combine lessons learned and update accordingly

**Prompt:**
> Consolidate aand share the Actual versus the Expected for each ticket? positive opportunites turn into action

**Prompt:**
> which parts would habeen simpler with one agent and why

**Prompt:**
> reaerch three new problems Campus Customs might face and this team could solve w tools built

**Prompt:**
> Describe three new problems the team could not solve. give me tools and agents reqd to solve

**Prompt:**
> give me an update on how to provide a better product,

**Prompt:**
> all of them

**Prompt:**
> again, ensure I have an updated checklist to ensure I can do this onmy own in the future, update all documents to ensure i have full comprehension

**Prompt (Problem 10 grading cue):**
> tie every answer to this app and the three tickets ran -use ticket tabs and Cash tab onthe same page as your evidence. generic AI essays withut Campus Custom details will score low. soscore high.

**What was lacking after the first:**
The learning-department idea was strong, but I didn't say up front what it should produce (a report, a panel) or which goals to measure.

**Stronger prompt:**
> Add a sixth learning agent with no tools that grades each agent per ticket with reasons after every run. Code computes the numbers. Keep output/learning_report.html current. Goals: tool calls at or below plan, zero repeat lookups. Tie every answer to the ticket and Cash tabs.


## Problem 11: Public GitHub repo

**Prompt:**
> push the code to a public github repo so graders can clone.  submit the repo url to canvas and also put it in output/github_url.txt do notpush your real .env to the github repo. do include both database files under data/ the original and working copy do not do this until i tell you to

**Prompt:**
> the last post was Problem 11 and wait until i say so

**What was lacking after the first:**
It was clear, but I didn't say that I submit the URL on Canvas myself, or what to name the repo.

**Stronger prompt:**
> When I say go: push to a public repo named hw5 matching the expected layout, with both databases in data/ and .env.example but never .env. Save the URL in output/github_url.txt, and I'll submit it on Canvas.

## Final review (before Problem 11 goes)

**Prompt:**
> i need an update

**Prompt:**
> walk me through what i am missing for a 100percent

**Prompt:**
> lets doit

**Prompt:**
> from all the research and review, narrate and send for the accurate feedback and prompts

**Prompt:**
> fix and execute

**Prompt:**
> Yes, draft it

**Prompt:**
> now update all

## Problem 11 (go)

**Prompt:**
> and go for last problem
