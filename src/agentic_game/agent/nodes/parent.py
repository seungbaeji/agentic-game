from __future__ import annotations

from agentic_game.agent.decisions import ParentDecision
from agentic_game.agent.models import SUBGRAPH_REGISTRY, ParentNode
from agentic_game.agent.prompts import (
    build_capability_response_prompt,
    build_cli_startup_prompt,
    build_parent_decision_prompt,
    build_parent_response_prompt,
)
from agentic_game.agent.state import ParentState
from agentic_game.agent.types import AvailableSubgraphs, ResponseText
from agentic_game.application.ports import LLMPort
from agentic_game.errors import AgenticGameError
from agentic_game.scenarios.intent import detect_parent_subgraph, is_capability_question


def make_parent_decision_node(llm: LLMPort):
    """Create a LangGraph node that chooses the target subgraph."""

    def parent_decision_node(state: ParentState) -> ParentState:
        """Decide the target subgraph from deterministic intent or LLM output."""
        user_input = state.get("user_input", "")
        detected_subgraph = detect_parent_subgraph(user_input)
        if detected_subgraph is not None:
            return {
                "target_subgraph": detected_subgraph,
                "reason": "user_input에서 명시적인 업무 의도를 감지했습니다.",
                "next_node": SUBGRAPH_REGISTRY[detected_subgraph].node,
            }

        if is_capability_question(user_input):
            return {
                "reason": "사용자가 가능한 업무를 물었습니다.",
                "next_node": ParentNode.ASK_USER,
            }

        current_subgraph = state.get("current_subgraph")
        if current_subgraph is not None:
            return {
                "target_subgraph": current_subgraph,
                "reason": "현재 scenario session을 이어갑니다.",
                "next_node": SUBGRAPH_REGISTRY[current_subgraph].node,
            }

        decision = llm.structured_output(
            ParentDecision,
            build_parent_decision_prompt(
                available_subgraphs=available_work_items(),
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


def available_work_items() -> AvailableSubgraphs:
    """Return user-facing workflow descriptions for prompts."""
    return [
        {
            "name": entry.name.value,
            "label": entry.label,
            "description": entry.description,
        }
        for entry in SUBGRAPH_REGISTRY.values()
    ]


def describe_available_work(*, include_exit_hint: bool = False) -> ResponseText:
    """Return the deterministic fallback capability message."""
    descriptions = "\n".join(
        f"- {entry.label}: {entry.description}" for entry in SUBGRAPH_REGISTRY.values()
    )
    exit_hint = "\n\n종료하려면 `exit`, `quit`, `q`, `종료` 중 하나를 입력하세요." if include_exit_hint else ""
    return (
        "안녕하세요. 지금은 이런 일을 할 수 있어요.\n"
        f"{descriptions}\n\n"
        "예: `몬스터를 공격할게`, `포션을 제작할게`, `NPC와 대화할게`\n\n"
        f"무엇부터 해볼까요?{exit_hint}"
    )


def generate_cli_startup_message(
    llm: LLMPort,
    *,
    exit_commands: tuple[str, ...],
) -> ResponseText:
    """Generate the first CLI message, falling back to deterministic text."""
    try:
        response = llm.respond(
            build_cli_startup_prompt(
                available_subgraphs=available_work_items(),
                exit_commands=exit_commands,
            )
        ).strip()
    except AgenticGameError:
        response = ""

    return response or describe_available_work(include_exit_hint=True)


def make_parent_ask_user_node(llm: LLMPort):
    """Create a node that explains available workflows with LLM fallback."""

    def parent_ask_user_node(state: ParentState) -> ParentState:
        user_input = state.get("user_input", "")
        try:
            response = llm.respond(
                build_capability_response_prompt(
                    available_subgraphs=available_work_items(),
                    user_input=user_input,
                )
            ).strip()
        except AgenticGameError:
            response = ""

        return {
            "current_subgraph": state.get("current_subgraph"),
            "response": response or describe_available_work(),
        }

    return parent_ask_user_node


def parent_route(state: ParentState) -> str:
    """Read the next parent node selected by the previous node."""
    return state["next_node"]
