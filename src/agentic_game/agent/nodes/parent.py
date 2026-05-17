from __future__ import annotations

from agentic_game.agent.decisions import ParentDecision
from agentic_game.agent.models import SUBGRAPH_REGISTRY, ParentNode
from agentic_game.agent.prompts import (
    build_parent_decision_prompt,
    build_parent_response_prompt,
)
from agentic_game.agent.state import ParentState
from agentic_game.agent.types import AvailableSubgraphs, ResponseText
from agentic_game.application.ports import LLMPort
from agentic_game.scenarios.router import infer_parent_subgraph, is_capability_question


def make_parent_decision_node(llm: LLMPort):
    """Create a LangGraph node that chooses the target subgraph."""

    def parent_decision_node(state: ParentState) -> ParentState:
        """Decide the target subgraph from deterministic intent or LLM output."""
        user_input = state.get("user_input", "")
        inferred_subgraph = infer_parent_subgraph(user_input)
        if inferred_subgraph is not None:
            return {
                "target_subgraph": inferred_subgraph,
                "reason": "user_input에서 명시적인 업무 의도를 감지했습니다.",
                "next_node": SUBGRAPH_REGISTRY[inferred_subgraph].node,
            }

        if is_capability_question(user_input):
            return {
                "reason": "사용자가 가능한 업무를 물었습니다.",
                "next_node": ParentNode.ASK_USER,
            }

        available_subgraphs: AvailableSubgraphs = [
            {
                "name": entry.name.value,
                "label": entry.label,
                "description": entry.description,
            }
            for entry in SUBGRAPH_REGISTRY.values()
        ]

        decision = llm.structured_output(
            ParentDecision,
            build_parent_decision_prompt(
                available_subgraphs=available_subgraphs,
                user_input=user_input,
            ),
        )

        if decision.target_subgraph is None:
            return {
                "reason": decision.reason,
                "next_node": ParentNode.ASK_USER,
            }

        return {
            "target_subgraph": decision.target_subgraph,
            "reason": decision.reason,
            "next_node": SUBGRAPH_REGISTRY[decision.target_subgraph].node,
        }

    return parent_decision_node


def make_parent_response_node(llm: LLMPort):
    """Create a LangGraph node that produces the final parent response."""

    def parent_response_node(state: ParentState) -> ParentState:
        """Return a subgraph response or ask the LLM for a final response."""
        subgraph_response = state.get("response", "")
        if subgraph_response:
            return {
                "response": subgraph_response,
            }

        response = llm.respond(
            build_parent_response_prompt(
                subgraph_response=subgraph_response,
                store_refs=state.get("store_refs"),
            )
        )

        return {
            "response": response,
        }

    return parent_response_node


def describe_available_work() -> ResponseText:
    """Describe the currently registered user-facing workflows."""
    descriptions = "\n".join(
        f"- {entry.label}: {entry.description}" for entry in SUBGRAPH_REGISTRY.values()
    )
    return (
        "지금은 이런 일을 할 수 있어요.\n"
        f"{descriptions}\n\n"
        "예: `몬스터를 공격할게`, `포션을 제작할게`, `숲을 탐험할게`, `상인과 거래할게`, `퀘스트를 수락할게`, `NPC와 대화할게`, `검술을 훈련할게`"
    )


def parent_ask_user_node(state: ParentState) -> ParentState:
    """Return a capability message when no target subgraph is selected."""
    return {
        "response": describe_available_work(),
    }


def parent_route(state: ParentState) -> str:
    """Read the next parent node selected by the previous node."""
    return state["next_node"]
