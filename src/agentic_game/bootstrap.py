from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from langgraph.store.memory import InMemoryStore

from agentic_game.agent.graph.parent import build_parent_graph
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.application.usecases import craft_item, resolve_battle_action
from agentic_game.config import Settings, get_settings
from agentic_game.outbound.llm import GeminiLLMAdapter
from agentic_game.outbound.random import RandomAdapter
from agentic_game.outbound.store import LangGraphStoreAdapter
from agentic_game.tools import craft_item_tool, resolve_battle_tool


@dataclass(frozen=True)
class AppContainer:
    settings: Settings
    store: StorePort
    llm: LLMPort
    random: RandomPort


def build_container(
    settings: Settings | None = None,
    *,
    llm: LLMPort | None = None,
    random: RandomPort | None = None,
    store: StorePort | None = None,
) -> AppContainer:
    """Build the runtime dependency container with default outbound adapters."""
    resolved_settings = settings or get_settings()

    return AppContainer(
        settings=resolved_settings,
        store=store or LangGraphStoreAdapter(InMemoryStore()),
        llm=llm or GeminiLLMAdapter(resolved_settings),
        random=random or RandomAdapter(),
    )


@lru_cache
def get_container() -> AppContainer:
    """Return the process-wide cached application container."""
    return build_container()


def build_agent_graph(container: AppContainer):
    """Compose the parent agent graph from the hydrated application container."""
    return build_parent_graph(
        container.store,
        container.llm,
        resolve_battle_tool,
        craft_item_tool,
        resolve_battle_action,
        craft_item,
        container.random,
    )
