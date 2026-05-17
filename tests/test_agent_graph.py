from __future__ import annotations

from agentic_game.agent.decisions import CraftDecision, DialogueDecision
from agentic_game.agent.nodes.parent import (
    describe_available_work,
    generate_cli_startup_message,
)
from agentic_game.application.content_generation import BattleNarration, CraftNarration
from agentic_game.bootstrap import build_agent_graph, build_container
from agentic_game.config.settings import Settings
from agentic_game.flow.models import SubgraphName
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

    player = container.store.get(namespace=("game", "player"), key="latest")
    assert player.hp == 100
    assert player.exp == 20


def test_agent_graph_uses_llm_battle_narration_without_changing_state() -> None:
    llm = TestingLLMAdapter(
        structured_outputs={
            BattleNarration: [
                {"response": "검격이 정확히 들어가며 적이 크게 휘청였습니다."}
            ],
        }
    )
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

    assert result["response"] == "검격이 정확히 들어가며 적이 크게 휘청였습니다."

    player = container.store.get(namespace=("game", "player"), key="latest")
    battle_raw = container.store.get(namespace=("battle", "resolve", "raw"), key="latest")
    assert player.hp == 100
    assert player.exp == 20
    assert battle_raw["outcome"] == "critical_hit"
    assert battle_raw["player_delta"] == {
        "hp_change": 0,
        "exp_gain": 20,
    }


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


def test_agent_graph_uses_llm_for_capability_response() -> None:
    llm = TestingLLMAdapter(responses=["무엇을 해볼까요? 전투나 제작부터 시작할 수 있어요."])
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    result = graph.invoke(
        {
            "user_input": "뭘 할 수 있어?",
            "store_refs": {},
        }
    )

    assert result["response"] == "무엇을 해볼까요? 전투나 제작부터 시작할 수 있어요."


def test_cli_startup_message_uses_llm_when_available() -> None:
    llm = TestingLLMAdapter(responses=["어서 오세요. 무엇부터 해볼까요?"])

    assert (
        generate_cli_startup_message(llm, exit_commands=("exit", "quit", "q", "종료"))
        == "어서 오세요. 무엇부터 해볼까요?"
    )


def test_cli_startup_message_falls_back_when_llm_is_empty() -> None:
    llm = TestingLLMAdapter()

    message = generate_cli_startup_message(
        llm,
        exit_commands=("exit", "quit", "q", "종료"),
    )

    assert message == describe_available_work(include_exit_hint=True)
    assert "무엇부터 해볼까요?" in message


def test_agent_graph_asks_item_details_when_craft_intent_is_vague() -> None:
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

    assert result["response"] == (
        "제작할 아이템을 알려 주세요. 범주: 소모품 / 무기 / 방어구 / 장신구 / 도구 / 재료. "
        "예: 회복 포션, 불꽃 단검, 튼튼한 방패, 유적 열쇠"
    )


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

    assert first["response"] == (
        "제작할 아이템을 알려 주세요. 범주: 소모품 / 무기 / 방어구 / 장신구 / 도구 / 재료. "
        "예: 회복 포션, 불꽃 단검, 튼튼한 방패, 유적 열쇠"
    )
    assert second["response"] == "회복 포션 제작 성공"
    assert third["response"] == "방금 제작한 회복 포션은 소모품 범주의 아이템이고, 의도한 효과는 healing입니다."


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

    assert first["response"] == (
        "제작할 아이템을 알려 주세요. 범주: 소모품 / 무기 / 방어구 / 장신구 / 도구 / 재료. "
        "예: 회복 포션, 불꽃 단검, 튼튼한 방패, 유적 열쇠"
    )
    assert second["response"] == "회복 포션 제작 성공"

    saved_state = container.store.get(namespace=("craft", "state"), key="latest")
    assert saved_state["latest_refs"]["result.raw"] == "store://craft/result/raw/latest"
    assert "next_node" not in saved_state

    inventory = container.store.get(namespace=("game", "inventory"), key="latest")
    assert inventory.items[0].item_id == "healing_potion"
    assert inventory.items[0].quantity == 1


def test_agent_graph_uses_llm_craft_plan_for_custom_item() -> None:
    llm = TestingLLMAdapter(
        structured_outputs={
            CraftDecision: [
                {
                    "intent": "action",
                    "event": "craft_weapon",
                    "craft_plan": {
                        "category": "weapon",
                        "item_name": "flame_dagger",
                        "display_name": "불꽃 단검",
                        "requested_effect": "burn",
                    },
                    "reason": "사용자가 불꽃 단검 제작을 요청했습니다.",
                }
            ]
        }
    )
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[13]),
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
            "user_input": "불꽃 단검을 만들래",
            "store_refs": first["store_refs"],
        }
    )

    assert second["response"] == "불꽃 단검 제작 성공"

    saved_state = container.store.get(namespace=("craft", "state"), key="latest")
    assert saved_state["event"] == "craft_weapon"
    assert saved_state["craft_plan"] == {
        "category": "weapon",
        "item_name": "flame_dagger",
        "display_name": "불꽃 단검",
        "requested_effect": "burn",
    }

    craft_raw = container.store.get(namespace=("craft", "result", "raw"), key="latest")
    assert craft_raw["category"] == "weapon"
    assert craft_raw["item_name"] == "flame_dagger"
    assert craft_raw["display_name"] == "불꽃 단검"
    assert craft_raw["requested_effect"] == "burn"


def test_agent_graph_uses_llm_craft_narration_without_changing_state() -> None:
    llm = TestingLLMAdapter(
        structured_outputs={
            CraftNarration: [
                {"response": "연금대 위에서 healing_potion이 맑게 빛나며 완성됐습니다."}
            ],
        }
    )
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

    assert second["response"] == "연금대 위에서 healing_potion이 맑게 빛나며 완성됐습니다."

    inventory = container.store.get(namespace=("game", "inventory"), key="latest")
    craft_raw = container.store.get(namespace=("craft", "result", "raw"), key="latest")
    assert inventory.items[0].item_id == "healing_potion"
    assert inventory.items[0].quantity == 1
    assert craft_raw["item_name"] == "healing_potion"
    assert craft_raw["inventory_delta"] == {
        "item_id": "healing_potion",
        "quantity": 1,
    }


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

    world = container.store.get(namespace=("game", "world"), key="latest")
    assert world.current_location == "forest_path"
    assert world.discovered_locations == ("forest_path",)


def test_agent_graph_routes_trade_and_keeps_context_until_exchange() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "상인과 거래하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "가격을 제안할게",
            "store_refs": first["store_refs"],
        }
    )
    third = graph.invoke(
        {
            "user_input": "수락할게",
            "store_refs": second["store_refs"],
        }
    )

    assert first["response"] == "거래 행동을 선택해 주세요. 가능한 선택: 가격 제안 / 수락 / 거절 / 취소"
    assert second["response"] == "제안한 가격을 확인해 주세요. 수락하거나 거절할 수 있습니다."
    assert third["response"] == "거래가 성사되었습니다. travel_ration을 구매하고 15 gold를 지불했습니다."
    assert "trade_state" in third["store_refs"]

    saved_state = container.store.get(namespace=("trade", "state"), key="latest")
    assert saved_state["phase"] == "exchange"
    assert saved_state["event"] == "accept_price"
    assert saved_state["latest_refs"]["exchange.raw"] == "store://trade/exchange/raw/latest"
    assert "next_node" not in saved_state

    trade_raw = container.store.get(namespace=("trade", "exchange", "raw"), key="latest")
    player = container.store.get(namespace=("game", "player"), key="latest")
    inventory = container.store.get(namespace=("game", "inventory"), key="latest")
    assert trade_raw["item_id"] == "travel_ration"
    assert trade_raw["price"] == 15
    assert player.gold == 85
    assert inventory.items[0].item_id == "travel_ration"
    assert inventory.items[0].quantity == 1


def test_agent_graph_routes_quest_and_keeps_context_until_turn_in() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "퀘스트를 수락하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "퀘스트를 시작할게",
            "store_refs": first["store_refs"],
        }
    )
    third = graph.invoke(
        {
            "user_input": "목표를 달성했어",
            "store_refs": second["store_refs"],
        }
    )

    assert first["response"] == "퀘스트 행동을 선택해 주세요. 가능한 선택: 시작 / 진행 / 완료 / 포기"
    assert second["response"] == "퀘스트를 계속 진행합니다."
    assert third["response"] == "퀘스트 목표를 달성했습니다. 보고하고 보상을 받을 수 있습니다."
    assert "quest_state" in third["store_refs"]

    saved_state = container.store.get(namespace=("quest", "state"), key="latest")
    assert saved_state["phase"] == "turn_in"
    assert saved_state["event"] == "progress"
    assert "next_node" not in saved_state

    quest_log = container.store.get(namespace=("game", "quests"), key="latest")
    assert quest_log.quests[0].quest_id == "old_ruins"
    assert quest_log.quests[0].status == "ready_to_turn_in"
    assert quest_log.quests[0].progress == 100


def test_agent_graph_routes_dialogue_and_keeps_context_until_reward() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "NPC와 대화하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "소문을 물어볼게",
            "store_refs": first["store_refs"],
        }
    )
    third = graph.invoke(
        {
            "user_input": "고마워",
            "store_refs": second["store_refs"],
        }
    )

    assert first["response"] == "대화 선택지를 골라 주세요. 가능한 선택: 소문 묻기 / 거래 묻기 / 감사 / 보상 / 떠나기"
    assert second["response"] == (
        "NPC는 북쪽의 오래된 유적에서 밤마다 푸른 빛이 새어 나오고, "
        "가끔 낮은 종소리가 들린다는 소문을 들려줬습니다."
    )
    assert third["response"] == "NPC가 감사의 표시로 작은 보상을 준비했습니다."
    assert "dialogue_state" in third["store_refs"]

    saved_state = container.store.get(namespace=("dialogue", "state"), key="latest")
    assert saved_state["phase"] == "reward"
    assert saved_state["event"] == "thank"
    assert "next_node" not in saved_state

    npc_memory = container.store.get(namespace=("game", "npcs"), key="latest")
    assert npc_memory.npcs[0].npc_id == "village_elder"
    assert npc_memory.npcs[0].relation == 1
    assert npc_memory.npcs[0].memories == (
        "old_ruins_rumor",
        "received_thanks",
    )


def test_agent_graph_answers_dialogue_followup_without_advancing_flow() -> None:
    llm = TestingLLMAdapter(
        structured_outputs={
            DialogueDecision: [
                {
                    "intent": "question",
                    "response": "북쪽 유적에서 밤마다 푸른 빛과 낮은 종소리가 난다는 소문입니다.",
                    "reason": "사용자가 직전 소문에 대한 후속 질문을 했습니다.",
                }
            ],
        }
    )
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "NPC와 대화하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "소문을 물어볼게",
            "store_refs": first["store_refs"],
        }
    )
    third = graph.invoke(
        {
            "user_input": "어떤 소문인데?",
            "store_refs": second["store_refs"],
        }
    )

    assert third["response"] == "북쪽 유적에서 밤마다 푸른 빛과 낮은 종소리가 난다는 소문입니다."

    saved_state = container.store.get(namespace=("dialogue", "state"), key="latest")
    assert saved_state["phase"] == "react"
    assert saved_state["event"] == "ask_rumor"
    assert saved_state["input_intent"] == "question"


def test_agent_graph_continues_active_dialogue_for_ambiguous_input() -> None:
    llm = TestingLLMAdapter(
        structured_outputs={
            DialogueDecision: [
                {
                    "intent": "question",
                    "response": "그 소문은 북쪽 유적의 푸른 빛과 종소리에 관한 이야기입니다.",
                    "reason": "현재 대화 맥락의 후속 질문입니다.",
                }
            ],
        }
    )
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "대화하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "소문을 묻자",
            "store_refs": first["store_refs"],
            "current_subgraph": first["current_subgraph"],
        }
    )
    third = graph.invoke(
        {
            "user_input": "자세히 말해줘",
            "store_refs": second["store_refs"],
            "current_subgraph": second["current_subgraph"],
        }
    )

    assert second["current_subgraph"] == SubgraphName.DIALOGUE
    assert third["current_subgraph"] == SubgraphName.DIALOGUE
    assert third["response"] == "그 소문은 북쪽 유적의 푸른 빛과 종소리에 관한 이야기입니다."


def test_agent_graph_clears_current_subgraph_when_dialogue_ends() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "대화하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "소문을 묻자",
            "store_refs": first["store_refs"],
            "current_subgraph": first["current_subgraph"],
        }
    )
    third = graph.invoke(
        {
            "user_input": "떠나기",
            "store_refs": second["store_refs"],
            "current_subgraph": second["current_subgraph"],
        }
    )

    assert third["response"] == "NPC와의 대화를 마쳤습니다."
    assert third["current_subgraph"] is None


def test_agent_graph_preserves_active_scenario_during_help_pause() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "대화하고 싶어",
            "store_refs": {},
        }
    )
    help_result = graph.invoke(
        {
            "user_input": "메뉴 보여줘",
            "store_refs": first["store_refs"],
            "current_subgraph": first["current_subgraph"],
        }
    )
    resumed = graph.invoke(
        {
            "user_input": "소문을 묻자",
            "store_refs": help_result["store_refs"],
            "current_subgraph": help_result["current_subgraph"],
        }
    )

    assert help_result["current_subgraph"] == SubgraphName.DIALOGUE
    assert "전투" in help_result["response"]
    assert resumed["current_subgraph"] == SubgraphName.DIALOGUE
    assert resumed["response"] == (
        "NPC는 북쪽의 오래된 유적에서 밤마다 푸른 빛이 새어 나오고, "
        "가끔 낮은 종소리가 들린다는 소문을 들려줬습니다."
    )


def test_agent_graph_switches_from_active_scenario_on_explicit_new_scenario() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "대화하고 싶어",
            "store_refs": {},
        }
    )
    switched = graph.invoke(
        {
            "user_input": "그만하고 탐험할래",
            "store_refs": first["store_refs"],
            "current_subgraph": first["current_subgraph"],
        }
    )

    assert switched["current_subgraph"] == SubgraphName.EXPLORATION
    assert switched["response"] == "탐험 행동을 선택해 주세요. 가능한 선택: 숲길 / 유적 / 조사 / 후퇴"
    assert "exploration_state" in switched["store_refs"]


def test_agent_graph_routes_skill_training_and_keeps_context_until_level_up() -> None:
    llm = TestingLLMAdapter()
    container = build_container(
        settings=Settings(_env_file=None),
        llm=llm,
        random=FixedRandom(d20=[]),
    )
    graph = build_agent_graph(container)

    first = graph.invoke(
        {
            "user_input": "검술을 훈련하고 싶어",
            "store_refs": {},
        }
    )
    second = graph.invoke(
        {
            "user_input": "훈련할게",
            "store_refs": first["store_refs"],
        }
    )
    third = graph.invoke(
        {
            "user_input": "레벨 올릴게",
            "store_refs": second["store_refs"],
        }
    )

    assert first["response"] == "스킬이 선택되었습니다. 이제 훈련을 실행할 수 있습니다."
    assert second["response"] == "훈련 성과를 확인했습니다. 레벨 상승을 선택할 수 있습니다."
    assert third["response"] == "스킬 레벨이 상승했습니다."
    assert "skill_training_state" in third["store_refs"]

    saved_state = container.store.get(namespace=("skill_training", "state"), key="latest")
    assert saved_state["phase"] == "level_up"
    assert saved_state["event"] == "level_up"
    assert saved_state["selected_skill"] == "swordsmanship"
    assert "next_node" not in saved_state

    skill_book = container.store.get(namespace=("game", "skills"), key="latest")
    assert skill_book.skills[0].skill_id == "swordsmanship"
    assert skill_book.skills[0].level == 2
    assert skill_book.skills[0].exp == 0
