"""Run the agent team from the command line.

From My Work:
  .venv/Scripts/python backend/run_ticket.py 101            # one ticket
  .venv/Scripts/python backend/run_ticket.py --board        # every open ticket, one payment plan
  .venv/Scripts/python backend/run_ticket.py --board --reset  # reset the database first

Every loop step is appended to output/audit_trail.json, and every run's tokens
and dollar cost to output/usage_log.json. Payments are only proposed; nothing is paid.
"""

import argparse
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

import team  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticket_id", type=int, nargs="?")
    parser.add_argument("--board", action="store_true", help="work every open ticket at once")
    parser.add_argument("--reset", action="store_true", help="reset the database to the original first")
    parser.add_argument("--max-depth", type=int, default=3, help="how many hand-offs deep the team may go")
    parser.add_argument("--token-limit", type=int, default=None, help="hard token stop for this run")
    args = parser.parse_args()
    if not args.board and args.ticket_id is None:
        parser.error("give a ticket id, or --board")

    if args.reset:
        from reset_db import reset
        reset()

    if args.board:
        plan, checks, cost = asyncio.run(team.run_board(args.max_depth, args.token_limit or team.BOARD_TOKEN_LIMIT))
        print(plan.model_dump_json(indent=2))
        print(f"\nCode checks: {'PASSED' if checks['passed'] else 'FAILED'} {checks['problems']}")
        print(f"Saved output/board_plan.json")
    else:
        decision, deps, usage, cost = asyncio.run(
            team.run_ticket(args.ticket_id, args.max_depth, args.token_limit or team.TICKET_TOKEN_LIMIT))
        print(decision.model_dump_json(indent=2))
        print(f"\nDelegations: {len(deps.delegations)}  |  run_id: {deps.run_id}")
    limit = args.token_limit or (team.BOARD_TOKEN_LIMIT if args.board else team.TICKET_TOKEN_LIMIT)
    print(f"Model calls: {cost['requests']}  |  tokens: {cost['total_tokens']:,} (limit {limit:,})  |  "
          f"cost: ${cost['cost_usd']:.4f}  |  model: {cost['model']}")


if __name__ == "__main__":
    main()
