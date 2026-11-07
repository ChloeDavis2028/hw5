"""Boss: reads each ticket, picks who works on it, makes the final call.

Prompt: backend/prompts/boss.md   Answer type: models.TicketDecision
"""
from models import TicketDecision
from team import build_agent

agent = build_agent("boss", TicketDecision)
