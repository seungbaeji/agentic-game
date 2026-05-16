from __future__ import annotations

from agentic_game.bootstrap import build_agent_graph, build_container
from agentic_game.config.settings import Settings
from agentic_game.outbound.llm.testing import TestingLLMAdapter
from tests.fakes import FixedRandom


def test_agent_graph_hydrates_flat_tools_for_battle_flow() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[18], damage=[10]),
    )
    graph = build_agent_graph(container)

    result = graph.invoke(
        {
            "user_input": "몬스터를 공격할게",
            "store_refs": {},
        }
    )

    assert result["response"] == "전투 행동 'attack' 결과는 critical_hit입니다."
    assert "battle_state" in result["store_refs"]

    saved_state = container.store.get(namespace=("battle", "state"), key="latest")
    assert saved_state["response"] == "전투 행동 'attack' 결과는 critical_hit입니다."
    assert saved_state["latest_refs"]["resolve.raw"] == "store://battle/resolve/raw/latest"
    assert "next_node" not in saved_state


def test_agent_graph_describes_capabilities_without_internal_reason() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    result = graph.invoke(
        {
            "user_input": "어떤걸 할 수 있어?",
            "store_refs": {},
        }
    )

    assert "전투" in result["response"]
    assert "제작" in result["response"]
    assert "reason=" not in result["response"]
    assert "The user asked" not in result["response"]


def test_agent_graph_asks_recipe_when_craft_intent_is_vague() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    result = graph.invoke(
        {
            "user_input": "제작하고 싶어",
            "store_refs": {},
        }
    )

    assert result["response"] == "제작할 아이템을 선택해 주세요. 가능한 선택: 포션 / 검"


def test_agent_graph_keeps_craft_context_for_recipe_and_followup() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[19]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "제작하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "포션",
            "store_refs": first["store_refs"],
        }
    )
    third = graph.invoke(
        {
            "user_input": "어떤 포션이야?",
            "store_refs": second["store_refs"],
        }
    )

    assert first["response"] == "제작할 아이템을 선택해 주세요. 가능한 선택: 포션 / 검"
    assert second["response"] == "potion 제작 성공"
    assert third["response"] == "방금 제작한 potion은 healing_potion입니다."


def test_agent_graph_continues_craft_after_recipe_selection() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[19]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "제작하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "포션",
            "store_refs": first["store_refs"],
        }
    )

    assert first["response"] == "제작할 아이템을 선택해 주세요. 가능한 선택: 포션 / 검"
    assert second["response"] == "potion 제작 성공"

    saved_state = container.store.get(namespace=("craft", "state"), key="latest")
    assert saved_state["latest_refs"]["result.raw"] == "store://craft/result/raw/latest"
    assert "next_node" not in saved_state


def test_agent_graph_routes_exploration_and_keeps_context() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "탐험하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "숲길로 갈래",
            "store_refs": first["store_refs"],
        }
    )

    assert first["response"] == "탐험 행동을 선택해 주세요. 가능한 선택: 숲길 / 유적 / 조사 / 후퇴"
    assert second["response"] == "숲길에서 낯선 흔적을 발견했습니다. 조사하거나 후퇴할 수 있습니다."
    assert "exploration_state" in second["store_refs"]

    saved_state = container.store.get(namespace=("exploration", "state"), key="latest")
    assert saved_state["phase"] == "encounter"
    assert saved_state["event"] == "take_forest"
    assert "next_node" not in saved_state
