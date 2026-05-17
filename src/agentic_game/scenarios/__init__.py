"""Scenario package.

This package describes which game scenarios exist and how user intent maps into
them. It does not execute graphs directly; execution belongs to engine, and
LangGraph assembly belongs to agent.
"""

from agentic_game.scenarios.spec import ScenarioNode, ScenarioSpec

__all__ = ["ScenarioNode", "ScenarioSpec"]
