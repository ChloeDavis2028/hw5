"""Flight Instructor: the learning department. It debriefs the crew after each run.

Prompt: backend/prompts/learning.md   Answer type: models.LearningReport
It gets no shop tools at all: it reads computed metrics and writes feedback.
"""
from models import LearningReport
from team import build_learning_agent

agent = build_learning_agent(LearningReport)
