# Scenario Details

이 문서는 현재 게임 샘플 scenario가 공통 runtime 위에서 어떻게 동작하는지 보여줍니다.

Architecture 문서는 폴더와 책임을 설명하고, Flow 문서는 공통 실행 순서를 설명합니다. 이 문서는 구체 scenario 예시만 다룹니다. 용어가 낯설다면 [Glossary](glossary.md)를 참고하세요.

## Scenario Matrix

| Scenario | Flow 기준 | 실행 방식 | LLM 사용 위치 |
| --- | --- | --- | --- |
| battle | 전투 행동 | tool + usecase + player 저장 | event 선택 fallback, 결과 narration |
| craft | 제작 category | tool + usecase + inventory 저장 | CraftPlan 생성, 결과 narration |
| exploration | 탐험 경로/행동 | deterministic execute + world 저장 | 아직 없음 |
| quest | 퀘스트 진행 | deterministic execute/response + quest/player 저장 | 아직 없음 |
| trade | 거래 단계 | tool + usecase + player/inventory 저장 | 아직 없음 |
| dialogue | 대화 선택/후속 질문 | deterministic response + npc 저장 | 후속 질문/clarify/smalltalk |
| skill_training | 스킬 선택/훈련 | deterministic execute + skill 저장 | 아직 없음 |

## Battle

Battle은 가장 단순한 state-changing tool scenario입니다.

```text
사용자 입력
  -> BattleEvent 선택
  -> battle flow transition
  -> resolve_battle_tool
  -> resolve_battle_action_and_store_player
  -> game/player/latest 갱신
  -> optional LLM narration
```

예:

```text
PREPARE + ATTACK -> RESOLVE -> EXECUTE -> RESPONSE
```

LLM narration은 응답 문장만 바꿉니다. `damage`, `outcome`, `player_delta` 같은 상태 변경 값은 usecase 결과를 그대로 사용합니다.

## Craft

Craft는 “flow는 category, detail은 LLM” 패턴을 검증합니다.

사용자가 `불꽃 단검을 만들래`라고 입력하면 LLM은 상세 계획을 만듭니다.

```json
{
  "intent": "action",
  "event": "craft_weapon",
  "craft_plan": {
    "category": "weapon",
    "item_name": "flame_dagger",
    "display_name": "불꽃 단검",
    "requested_effect": "burn"
  }
}
```

flow는 상세 아이템을 보지 않고 category event만 검증합니다.

```text
CRAFT + CRAFT_WEAPON -> RESULT -> EXECUTE
```

tool/usecase는 deterministic policy로 결과를 확정합니다.

```text
CraftCategory.WEAPON
  -> success_threshold=13
  -> craft_item_tool(category, item_name, display_name, requested_effect)
  -> craft_item_and_store_reward
  -> game/inventory/latest 갱신
```

지원하는 일반 제작 범주는 다음과 같습니다.

```text
consumable
weapon
armor
accessory
tool
material
```

이 구조 덕분에 `포션`, `불꽃 단검`, `튼튼한 방패`, `유적 열쇠` 같은 상세 아이템을 event enum에 계속 추가하지 않아도 됩니다.

## Craft Follow-Up

Craft wrapper는 subgraph 실행 전에 이전 craft 결과에 대한 후속 질문인지 확인합니다.

```text
parent graph
  -> craft wrapper
    -> load saved craft state
    -> load latest craft result ui payload
    -> answer_craft_result_question(...)
```

예:

```text
> 불꽃 단검을 만들래
불꽃 단검 제작 성공
> 어떤 단검이야?
방금 제작한 불꽃 단검은 무기 범주의 아이템이고, 의도한 효과는 burn입니다.
```

이 응답은 tool을 다시 실행하지 않습니다.

## Dialogue

Dialogue는 “action이 아닌 입력은 flow를 움직이지 않는다”는 패턴을 검증합니다.

```text
대화하고 싶어
  -> GREETING + CONTINUE -> CHOICE

소문 묻기
  -> CHOICE + ASK_RUMOR -> REACT

어떤 소문인데?
  -> LLM DialogueDecision(intent=question)
  -> phase 유지
  -> 현재 대화 맥락으로 응답
```

`question`, `clarify`, `smalltalk`은 phase/event transition을 만들지 않습니다. `action`만 flow를 통과합니다.

## Trade

Trade는 tool-backed scenario지만 현재는 fixed exchange sample입니다.

```text
BROWSE -> NEGOTIATE -> CONFIRM -> EXCHANGE -> COMPLETE
```

`ACCEPT_PRICE`가 `EXCHANGE` phase로 이동하면 `exchange_item_tool`이 실행되고 player gold와 inventory가 갱신됩니다.

## Lightweight Scenarios

Exploration, quest, skill_training은 현재 LangChain tool 없이 deterministic node와 usecase로 동작합니다.

이 scenario들은 flow와 graph shape 검증에 가깝습니다.

```text
event 선택
  -> flow transition
  -> deterministic execute/response
  -> game state 저장
```

이후 필요하면 dialogue의 LLM intent 분류나 craft의 category/detail 분리 패턴을 옮길 수 있습니다.
