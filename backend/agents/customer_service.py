"""Customer Service: writes replies as drafts that stay on the board; never sends.

Prompt: backend/prompts/customer_service.md   Answer type: models.AgentReport
"""
from models import AgentReport
from team import build_agent

agent = build_agent("customer_service", AgentReport)
