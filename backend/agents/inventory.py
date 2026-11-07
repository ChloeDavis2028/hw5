"""Inventory: stock by SKU and size, shortfalls, which vendor can restock.

Prompt: backend/prompts/inventory.md   Answer type: models.AgentReport
"""
from models import AgentReport
from team import build_agent

agent = build_agent("inventory", AgentReport)
