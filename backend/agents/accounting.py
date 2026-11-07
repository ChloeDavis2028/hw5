"""Accounting: cash, invoices, margins; prepares payments and purchase orders for human approval.

Prompt: backend/prompts/accounting.md   Answer type: models.AgentReport
"""
from models import AgentReport
from team import build_agent

agent = build_agent("accounting", AgentReport)
