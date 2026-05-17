from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.graph.battle import build_battle_subgraph
from agentic_game.agent.graph.craft import build_craft_subgraph
from agentic_game.agent.graph.dialogue import build_dialogue_subgraph
from agentic_game.agent.graph.exploration import build_exploration_subgraph
from agentic_game.agent.graph.quest import build_quest_subgraph
from agentic_game.agent.graph.skill_training import build_skill_training_subgraph
from agentic_game.agent.graph.trade import build_trade_subgraph
from agentic_game.agent.models import ParentNode, SubgraphName
from agentic_game.agent.state import CraftState, ParentState
from agentic_game.agent.types import RuntimePayload, StoreRefs
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.battle import BattlePhase, BattleResult
from agentic_game.domain.craft import CraftPhase, CraftResult
from agentic_game.domain.dialogue import DialoguePhase
from agentic_game.domain.exploration import ExplorationPhase
from agentic_game.domain.quest import QuestPhase
from agentic_game.domain.skill_training import SkillTrainingPhase
from agentic_game.domain.trade import TradePhase
from agentic_game.engine.subgraph import make_simple_subgraph_wrapper, make_subgraph_wrapper
from agentic_game.engine.tool_runner import ToolInvoker
from agentic_game.flow.craft import answer_craft_result_question


def load_latest_craft_result(
    store: StorePort,
    saved_state: CraftState,
) -> RuntimePayload | None:
    """Load the latest persisted craft UI result when one is referenced."""
    latest_refs = saved_state.get("latest_refs", {})
    if "result.ui" not in latest_refs:
        return None

    try:
        latest_result = store.get(
            namespace=("craft", "result", "ui"),
            key="latest",
        )
    except KeyError:
        return None

    return latest_result


def make_battle_wrapper(
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleResult],
    random: RandomPort,
):
    """Create the parent node that invokes and persists the battle subgraph."""
    battle_graph = build_battle_subgraph(
        store,
        llm,
        resolve_battle_tool,
        resolve_battle_action,
        random,
    )

    return make_subgraph_wrapper(
        store=store,
        graph=battle_graph,
        subgraph=SubgraphName.BATTLE,
        state_ref_key="battle_state",
        state_namespace=("battle", "state"),
        initial_state={
            "phase": BattlePhase.PREPARE,
            "latest_refs": {},
            "history_refs": {},
        },
    )


def make_craft_wrapper(
    store: StorePort,
    llm: LLMPort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., CraftResult],
    random: RandomPort,
):
    """Create the parent node that invokes and persists the craft subgraph."""
    craft_graph = build_craft_subgraph(
        store,
        llm,
        craft_item_tool,
        craft_item,
        random,
    )

    def answer_followup(
        store: StorePort,
        saved_state: RuntimePayload,
        state: ParentState,
        refs: StoreRefs,
    ) -> ParentState | None:
        followup_response = answer_craft_result_question(
            phase=saved_state.get("phase", CraftPhase.SELECT_RECIPE),
            latest_result=load_latest_craft_result(store, saved_state),
            user_input=state.get("user_input", ""),
        )
        if followup_response is not None:
            return {
                "current_subgraph": SubgraphName.CRAFT,
                "store_refs": refs,
                "response": followup_response,
                "next_node": ParentNode.RESPONSE,
            }

        return None

    return make_subgraph_wrapper(
        store=store,
        graph=craft_graph,
        subgraph=SubgraphName.CRAFT,
        state_ref_key="craft_state",
        state_namespace=("craft", "state"),
        initial_state={
            "phase": CraftPhase.SELECT_RECIPE,
            "latest_refs": {},
            "history_refs": {},
        },
        before_invoke=answer_followup,
    )


def make_exploration_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the exploration subgraph."""
    return make_simple_subgraph_wrapper(
        store=store,
        graph=build_exploration_subgraph(),
        subgraph=SubgraphName.EXPLORATION,
        initial_phase=ExplorationPhase.START,
    )


def make_trade_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the trade subgraph."""
    return make_simple_subgraph_wrapper(
        store=store,
        graph=build_trade_subgraph(),
        subgraph=SubgraphName.TRADE,
        initial_phase=TradePhase.BROWSE,
    )


def make_quest_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the quest subgraph."""
    return make_simple_subgraph_wrapper(
        store=store,
        graph=build_quest_subgraph(),
        subgraph=SubgraphName.QUEST,
        initial_phase=QuestPhase.AVAILABLE,
    )


def make_dialogue_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the dialogue subgraph."""
    return make_simple_subgraph_wrapper(
        store=store,
        graph=build_dialogue_subgraph(),
        subgraph=SubgraphName.DIALOGUE,
        initial_phase=DialoguePhase.GREETING,
    )


def make_skill_training_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the skill training subgraph."""
    return make_simple_subgraph_wrapper(
        store=store,
        graph=build_skill_training_subgraph(),
        subgraph=SubgraphName.SKILL_TRAINING,
        initial_phase=SkillTrainingPhase.SELECT_SKILL,
    )
