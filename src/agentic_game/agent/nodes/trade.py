from __future__ import annotations

from agentic_game.agent.nodes.scenario_nodes import (
    make_ask_user_node,
    make_decision_node,
    make_flow_node,
    make_hitl_node,
)
from agentic_game.agent.state import TradeState
from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.trade import serialize_trade_actions
from agentic_game.scenarios.catalog import TRADE_SCENARIO
from agentic_game.scenarios.spec import ScenarioNode
from agentic_game.scenarios.trade import infer_trade_event

trade_decision_node = make_decision_node(
    default_phase=TradePhase.BROWSE,
    serialize_actions=serialize_trade_actions,
    infer_event=infer_trade_event,
    inferred_reason="user_input에서 명시적인 거래 행동을 감지했습니다.",
    fallback_reason="거래 행동 선택이 필요합니다.",
    default_events={
        TradePhase.BROWSE: (
            TradeEvent.SELECT_ITEM,
            "거래할 아이템 선택 단계로 이동합니다.",
        ),
    },
)


trade_flow_node = make_flow_node(
    spec=TRADE_SCENARIO,
    node_for=lambda node: node,
    invalid_event_message="현재 거래 phase에서 허용되지 않은 event입니다.",
)

trade_hitl_node = make_hitl_node(
    default_phase=TradePhase.NEGOTIATE,
    infer_event=infer_trade_event,
    prompt="거래 행동을 선택해 주세요. 가능한 선택: 가격 제안 / 수락 / 거절 / 취소",
)


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


trade_ask_user_node = make_ask_user_node(
    "거래 행동을 선택해 주세요. 가능한 선택: 가격 제안 / 수락 / 거절 / 취소"
)
