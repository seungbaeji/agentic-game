from __future__ import annotations

from agentic_game.agent.nodes.scenario import make_flow_node
from agentic_game.agent.scenario import ScenarioNode
from agentic_game.agent.scenarios import TRADE_SCENARIO
from agentic_game.agent.state import TradeState
from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.intent import infer_trade_event
from agentic_game.flow.trade import serialize_trade_actions


def trade_decision_node(state: TradeState) -> TradeState:
    """Decide the next trade event from deterministic intent."""
    phase = state.get("phase", TradePhase.BROWSE)
    available_actions = serialize_trade_actions(phase)
    user_text = state.get("human_input") or state.get("user_input", "")
    inferred_event = infer_trade_event(phase, user_text)

    if inferred_event is not None:
        return {
            "phase": phase,
            "event": inferred_event,
            "available_actions": available_actions,
            "reason": "user_input에서 명시적인 거래 행동을 감지했습니다.",
            "next_node": ScenarioNode.FLOW,
        }

    if phase == TradePhase.BROWSE:
        return {
            "phase": phase,
            "event": TradeEvent.SELECT_ITEM,
            "available_actions": available_actions,
            "reason": "거래할 아이템 선택 단계로 이동합니다.",
            "next_node": ScenarioNode.FLOW,
        }

    return {
        "phase": phase,
        "available_actions": available_actions,
        "reason": "거래 행동 선택이 필요합니다.",
        "next_node": ScenarioNode.ASK_USER,
    }


trade_flow_node = make_flow_node(
    spec=TRADE_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 거래 phase에서 허용되지 않은 event입니다.",
)


def trade_hitl_node(state: TradeState) -> TradeState:
    """Ask for trade input when the graph cannot continue alone."""
    phase = state.get("phase", TradePhase.NEGOTIATE)
    human_input = state.get("human_input", "")

    if infer_trade_event(phase, human_input) is None:
        return {
            "response": "거래 행동을 선택해 주세요. 가능한 선택: 가격 제안 / 수락 / 거절 / 취소",
            "next_node": ScenarioNode.ASK_USER,
        }

    return {
        "next_node": ScenarioNode.DECISION,
    }


def trade_execute_node(state: TradeState) -> TradeState:
    """Resolve a lightweight item exchange."""
    return {
        "response": "거래가 성사되었습니다. 아이템과 재화를 교환했습니다.",
        "next_node": ScenarioNode.RESPONSE,
    }


def trade_response_node(state: TradeState) -> TradeState:
    """Return a deterministic trade response."""
    phase = state.get("phase")
    if phase == TradePhase.CONFIRM:
        return {
            "response": "제안한 가격을 확인해 주세요. 수락하거나 거절할 수 있습니다.",
        }
    if phase == TradePhase.CANCELLED:
        return {
            "response": "거래를 취소했습니다.",
        }
    if phase == TradePhase.COMPLETE:
        return {
            "response": "거래를 완료했습니다.",
        }

    existing_response = state.get("response")
    if existing_response:
        return {
            "response": existing_response,
        }

    return {
        "response": "거래를 계속 진행합니다.",
    }


def trade_ask_user_node(state: TradeState) -> TradeState:
    """Return a user-facing prompt for trade choices."""
    return {
        "response": "거래 행동을 선택해 주세요. 가능한 선택: 가격 제안 / 수락 / 거절 / 취소",
    }


def trade_route(state: TradeState) -> str:
    """Read the next trade node selected by the previous node."""
    return state["next_node"]


def trade_decision_route(state: TradeState) -> str:
    """Route after trade decision, defaulting to the flow node."""
    return state.get("next_node", ScenarioNode.FLOW)
