"""Run a Flight Instructor debrief from the command line and rebuild the continuous report.

From My Work:  .venv/Scripts/python scripts/learning_review.py
Appends to output/learning_feedback.json and rebuilds output/learning_report.html.
(The backend also runs a debrief automatically after every ticket run.)
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
import team  # noqa: E402

entry = asyncio.run(team.run_learning_review(trigger="manual review (scripts/learning_review.py)"))
r = entry["report"]
print("HEADLINE:", r["headline"])
for t in r["ticket_reviews"]:
    print(f"  Ticket {t['ticket_id']}: {t['grade']}  {t['why']}")
    for a in t["agents"]:
        print(f"     {a['role']:16} {a['grade']:10} {a['why']}")
print("LESSONS:")
for l in r["lessons"]:
    print(f"  [{l['status']}] {l['lesson']}  ({l['evidence']})")
print("OPPORTUNITIES -> ACTIONS:")
for o in r.get("opportunities", []):
    print(f"  {o['opportunity']} -> {o['action']} [{o['owner']}; measure: {o['measure']}]")
print("PROMPT UPDATES:")
for u in r["prompt_updates"]:
    print(f"  {'OWNER' if u['owner_decision'] else 'safe '} {u['agent']}: {u['change']}")
print("NEXT:", r["next_experiment"])
print(f"cost ${entry['cost']['cost_usd']:.4f} | report: output/learning_report.html")
