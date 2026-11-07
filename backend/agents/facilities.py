"""Facilities: the shop space - leases and rent.

Prompt: backend/prompts/facilities.md   Answer type: models.AgentReport
"""
from models import AgentReport
from team import build_agent

agent = build_agent("facilities", AgentReport)
