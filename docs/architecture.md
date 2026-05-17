# Architecture

`agentic-game`은 LangGraph 기반 게임 샘플을 통해 phase/event agent workflow runtime을 검증하는 프로젝트입니다. 게임은 최종 목적이 아니라 반복 가능한 workflow abstraction을 찾기 위한 샘플 도메인입니다. LangGraph를 프로젝트 전체의 중심 계층으로 두지 않고, phase/event flow가 scenario 실행을 이끌도록 둡니다. LangGraph는 agent 조립 계층으로 제한하고, 순수 도메인 규칙과 시스템 usecase는 별도 계층에 둡니다.

장기 목표는 이 구조를 LangChain/LangGraph와 함께 사용할 수 있는 도메인 독립 라이브러리로 추출하는 것입니다. 이 라이브러리는 LangGraph를 대체하지 않고, LangGraph 위에서 반복되는 graph/node/tool/persistence/HITL 패턴을 spec-driven runtime으로 줄이는 역할을 합니다.

## 설계 목표

- 게임 샘플에서 발견한 반복 구조를 도메인 독립 workflow runtime으로 추출한다.
- LangGraph를 대체하지 않고, LangGraph 위에서 반복되는 node/edge/wrapper/persistence/HITL/tool 실행 조립을 줄인다.
- LLM의 자연어 이해와 deterministic workflow control을 함께 사용한다.
- 도메인 모델은 LangGraph, LangChain, 외부 API를 모른다.
- application usecase는 domain과 port를 조합해 시스템이 제공하는 기능을 만든다.
- tool은 usecase를 LLM이 호출할 수 있는 형태로 노출하는 상위 계층이다.
- scenarios는 어떤 도메인 scenario가 있고 phase가 어떤 공통 실행 단계로 이어지는지 설명한다.
- engine은 subgraph 실행, state persistence, tool runner를 담당한다.
- agent는 LangGraph graph/node 조립, prompt, state orchestration을 담당한다.
- inbound는 사용자와 시스템 사이의 interface다. CLI, REST API, UI는 여기에 추가된다.
- outbound는 외부 시스템 adapter다. LLM provider, store, random source 등이 여기에 있다.
- bootstrap은 실제 adapter를 조립해 실행 가능한 container를 만든다.

## 폴더 구조

```text
src/agentic_game/
  bootstrap.py
  config/
  domain/
  flow/
  scenarios/
  engine/
  application/
  tools/
  agent/
  inbound/
  outbound/
  errors/
```

### bootstrap.py

`bootstrap.py`는 runtime dependency를 조립합니다.

- `Settings`를 읽는다.
- `StorePort`, `LLMPort`, `RandomPort` 구현체를 선택한다.
- application usecase와 tool을 parent graph에 주입한다.
- CLI나 API가 사용할 최종 agent graph를 만든다.

중요한 점은 container가 tool/usecase 자체를 소유하지 않는다는 것입니다. container는 낮은 수준의 dependency인 settings, store, llm, random만 제공합니다. 실제 graph composition은 `build_agent_graph(container)`에서 명시적으로 이뤄집니다.

### config

`config/`는 pydantic-settings 기반 설정 계층입니다.

```text
config/
  settings.py
```

`Settings`는 `.env`와 환경 변수를 읽습니다. 현재 핵심 설정은 다음과 같습니다.

- `LLM__PROVIDER`: `google`, `gemini`, `openai`
- `LLM__API_KEY`: LLM provider API key. `SecretStr`로 관리한다.
- `LLM__MODEL`: provider model name
- `LLM__TEMPERATURE`
- `LLM__TIMEOUT_SECONDS`
- `LLM__MAX_RETRIES`
- `UI__APP_NAME`

설정 객체는 provider-specific 이름을 피하고 `llm`이라는 일반 설정 그룹을 사용합니다. Google Gemini와 OpenAI 모두 같은 `LLMSettings`를 공유합니다.

### domain

`domain/`은 DDD 관점의 순수 비즈니스 데이터와 규칙을 담습니다.

```text
domain/
  battle.py
  craft.py
  exploration.py
  game_state.py
  quest.py
  trade.py
  dialogue.py
  skill_training.py
```

여기에는 다음이 들어갑니다.

- battle/craft/exploration 같은 샘플 시나리오의 phase, event, outcome enum
- player, inventory, skill book 같은 샘플 상태 모델과 순수 변경 규칙
- usecase 결과 dataclass
- 순수 판정 함수

여기에는 다음이 들어가면 안 됩니다.

- LangGraph state
- ScenarioNode 실행 단계
- LLM prompt
- store reference
- LangChain tool
- API/CLI 입출력 처리

domain은 프로젝트의 가장 안쪽 계층입니다. 다른 계층을 import하지 않아야 합니다.

### flow

`flow/`는 순수 도메인 모델만으로는 표현하기 어려운 업무 흐름 규칙을 둡니다.

```text
flow/
  battle.py
  craft.py
  exploration.py
  quest.py
  trade.py
  dialogue.py
  skill_training.py
  models.py
  transitions.py
```

예를 들어 battle에는 다음 흐름이 있습니다.

```text
PREPARE --continue--> ACTION
PREPARE --attack--> RESOLVE
ACTION --attack--> RESOLVE
RESOLVE --retry--> ACTION
RESOLVE --complete--> COMPLETE
```

이 규칙은 순수 battle 결과 계산과는 다릅니다. 그래서 `domain`이 아니라 `flow`에 둡니다.

`flow`의 책임은 다음과 같습니다.

- phase/event transition table 관리
- 현재 phase에서 가능한 action 직렬화
- 이전 결과에 대한 간단한 follow-up 응답

`flow`는 LangGraph node를 모릅니다. phase/event 전이만 다루고, graph 실행 단계 선택은 `ScenarioSpec.phase_to_node`가 담당합니다.

현재 action 직렬화 결과는 `ActionCard`입니다. `ActionCard`는 기존 `ActionSpec`을 대체한 개념이며, decision prompt에 전달되는 행동 후보입니다. 기본 필드는 `event`, `label`, `description`이고, battle/craft/trade처럼 tool-backed action은 `tool_name`, `state_effect`, `risk` 같은 optional metadata를 가질 수 있습니다.

```text
TransitionRule
  -> ActionCard
  -> LLM/event decision
  -> flow validation
  -> ToolBinding
  -> optional tool execution
```

중요한 점은 `ActionCard`가 tool을 직접 실행하지 않는다는 것입니다. `ToolBinding`이 event와 실제 tool input을 연결하고, `ActionCard`의 tool metadata도 이 binding에서 파생됩니다. LLM은 action metadata를 참고해 event를 고르고, runtime이 event를 검증한 뒤 binding으로 tool을 실행합니다.

### application

`application/`은 시스템 usecase와 port를 둡니다.

```text
application/
  game_state.py
  ports.py
  usecases/
    battle.py
    craft.py
    trade.py
```

usecase는 함수로 유지합니다.

- `resolve_battle_action`
- `craft_item`
- `craft_item_and_store_reward`
- `exchange_item`

이 함수들은 domain 규칙과 port dependency를 조합합니다. CLI, REST API, tool, agent 모두 같은 usecase를 호출할 수 있습니다.

`ports.py`는 application이 필요로 하는 추상화입니다.

- `LLMPort`
- `StorePort`
- `RandomPort`

application은 outbound 구현체를 import하지 않습니다. 구현체는 bootstrap에서 주입됩니다.

`game_state.py`는 `StorePort` 위에 놓인 작은 repository입니다. 현재는 battle 결과를 player state에 저장하고, craft 성공 결과를 player inventory에 저장하고, exploration 발견 상태를 world state에 저장하고, quest 진행 상태를 quest log에 저장하고, dialogue 결과를 NPC memory에 저장하고, skill_training 결과를 skill book에 저장합니다.

```text
game/player/latest    -> PlayerState
game/inventory/latest -> InventoryState
game/npcs/latest      -> NpcMemory
game/quests/latest    -> QuestLog
game/skills/latest    -> SkillBook
game/world/latest     -> WorldState
```

`StorePort`는 낮은 수준의 put/get만 제공하고, player, inventory, NPC memory, quest log, skill book, world state를 어떻게 읽고 갱신할지는 `GameStateRepository`가 담당합니다.

`content_generation.py`는 LLM을 이용한 표현 변주를 담당합니다. 현재는 battle/craft 결과 narration을 제공합니다.

```text
battle/craft deterministic result
  -> domain state 저장
  -> raw/llm/ui payload 저장
  -> optional LLM narration
  -> user response
```

LLM은 `BattleNarration`, `CraftNarration` structured output으로 응답 문장만 생성합니다. damage, item, success, quantity 같은 상태 변경 값은 이미 usecase에서 확정된 값을 사용하고 LLM 결과로 바꾸지 않습니다.

### tools

`tools/`는 LLM이 usecase를 호출할 수 있게 만드는 계층입니다.

```text
tools/
  battle.py
  craft.py
  trade.py
  projections.py
  types.py
```

tool은 outbound가 아닙니다. 외부 시스템으로 나가는 adapter가 아니라, application usecase를 LLM runtime이 사용할 수 있는 형태로 감싸는 상위 계층입니다.

현재 tool은 LangChain `@tool`로 정의됩니다.

- `resolve_battle_tool`
- `craft_item_tool`
- `exchange_item_tool`

tool의 입력에는 usecase, random adapter, 필요한 state repository가 injected argument로 들어갑니다. tool은 usecase 결과를 LLM/UI/raw 용 payload로 projection하고 `ToolResult`를 반환합니다.

현재 실제 tool-backed 시나리오는 battle, craft, trade입니다. battle은 `GameStateRepository`를 통해 player HP/EXP를 갱신하고, craft는 성공 시 inventory를 갱신하며, trade는 player gold와 inventory를 갱신합니다. exploration은 deterministic node에서 world state를 갱신하고, quest는 quest log와 player reward를 갱신하고, dialogue는 NPC memory를 갱신하고, skill_training은 deterministic node에서 skill book을 갱신합니다.

### scenarios

`scenarios/`는 어떤 도메인 scenario가 있고, 사용자 입력이 어떤 scenario/event로 해석되는지 설명합니다. 현재 repository에서는 게임 scenario를 샘플로 사용하지만, 같은 구조는 문서 처리, 승인 workflow, 고객지원, 운영 변경 같은 도메인으로 옮길 수 있어야 합니다.

```text
scenarios/
  spec.py
  definitions.py
  registry.py
  router.py
  battle.py
  craft.py
  exploration.py
  quest.py
  trade.py
  dialogue.py
  skill_training.py
```

`spec.py`는 `ScenarioSpec`, `ScenarioNode` 같은 공통 모델만 둡니다.
`definitions.py`는 각 시나리오의 `ScenarioSpec` 정의만 둡니다.
`router.py`는 parent-level intent routing만 둡니다.
`registry.py`는 concrete scenario를 parent graph에 연결합니다.
각 scenario 파일은 해당 scenario 내부 event intent만 둡니다.

### engine

`engine/`은 scenario를 실제로 실행하는 공통 실행기입니다.

```text
engine/
  subgraph.py
  tool_runner.py
```

`subgraph.py`는 parent graph 안에서 subgraph를 실행하고 state를 저장합니다.

- 이전 subgraph state를 store에서 읽는다.
- 초기 state를 만든다.
- subgraph를 invoke한다.
- runtime routing key를 제거한다.
- 최신 state를 store에 저장한다.
- parent state update를 반환한다.

`tool_runner.py`는 tool 실행과 payload 저장을 담당합니다.

- event에 연결된 `ToolBinding`을 찾는다.
- hydrated tool을 invoke한다.
- raw/llm/ui payload를 store에 저장한다.
- graph state update를 반환한다.

현재 `tool_runner.py`가 알고 있는 concrete tool binding은 battle/craft/trade입니다.

```text
BattleEvent -> action -> resolve_battle_tool
CraftEvent  -> recipe -> craft_item_tool
TradeEvent  -> item_id/price -> exchange_item_tool
```

battle tool 실행은 결과에 따라 `game/player/latest`를 갱신합니다.

```text
BattleEvent
  -> resolve_battle_tool
  -> resolve_battle_action_and_store_player
  -> GameStateRepository.apply_player_delta
  -> game/player/latest
```

craft tool 실행은 성공한 제작 결과를 `game/inventory/latest`에도 저장합니다.

```text
CraftEvent
  -> craft_item_tool
  -> craft_item_and_store_reward
  -> GameStateRepository.add_item
  -> game/inventory/latest
```

trade tool 실행은 거래 가격만큼 player gold를 줄이고 아이템을 inventory에 저장합니다.

```text
TradeEvent
  -> exchange_item_tool
  -> exchange_item
  -> GameStateRepository.apply_player_delta
  -> GameStateRepository.add_item
  -> game/player/latest + game/inventory/latest
```

exploration, quest, dialogue, skill_training은 아직 이 runner를 사용하지 않습니다. 이 경계는 의도적으로 좁게 유지되어 있습니다. scenario flow와 graph shape 일반화가 먼저이며, tool/usecase/state persistence 일반화는 필요한 시나리오부터 확장합니다.

### agent

`agent/`는 LangGraph와 LLM 조립 관련 코드만 둡니다.

```text
agent/
  graph/
  nodes/
  decisions.py
  models.py
  prompts.py
  state.py
  transitions.py
  types.py
```

#### graph

`graph/`는 LangGraph 조립만 담당합니다.

```text
graph/
  parent.py
  battle.py
  craft.py
  exploration.py
  quest.py
  trade.py
  dialogue.py
  skill_training.py
  scenario_graph.py
```

여기에서만 `StateGraph`, `add_node`, `add_edge`, `add_conditional_edges`, `compile`이 보이는 것이 이상적입니다.

graph 파일은 node 내부 로직을 알지 않습니다. node 함수와 edge table을 가져와 연결합니다.

#### nodes

`nodes/`는 LangGraph가 호출하는 node wrapper입니다.

```text
nodes/
  parent.py
  battle.py
  craft.py
  exploration.py
  quest.py
  trade.py
  dialogue.py
  skill_training.py
  scenario_nodes.py
```

node는 다음 일을 합니다.

- state에서 필요한 값을 읽는다.
- flow/application/engine 함수에 위임한다.
- 다음 state update를 반환한다.

node 안에 길고 복잡한 business logic, prompt 문자열, store orchestration이 오래 머물면 읽기 어려워지므로 별도 모듈로 뺍니다.

현재 execute node는 두 종류가 있습니다.

| 종류 | 대상 | 특징 |
| --- | --- | --- |
| tool-backed execute node | battle, craft, trade | `engine/tool_runner.py`를 통해 LangChain tool과 application usecase를 호출하고 payload를 store에 저장한다. battle은 player, craft는 inventory, trade는 player/inventory도 갱신한다. |
| deterministic execute/response node | exploration, quest, dialogue, skill_training | lightweight sample 로직으로 response를 만든다. exploration은 world, quest는 quest log/player reward, dialogue는 NPC memory, skill_training은 skill book 저장까지 수행한다. |

#### transitions.py

`transitions.py`는 parent graph edge table입니다.

scenario subgraph의 edge table은 도메인마다 따로 두지 않고, `agent/graph/scenario_graph.py`의 공통 graph shape를 사용합니다.

#### prompts.py

`prompts.py`는 LLM prompt 문자열 생성만 담당합니다.

node 파일에서 긴 prompt 문자열이 사라지면 node는 “무슨 일을 하는지”가 더 잘 보입니다.

#### decisions.py

`decisions.py`는 LLM structured output DTO입니다.

- `ParentDecision`
- `BattleDecision`
- `CraftDecision`

이 객체들은 외부 LLM 응답과 내부 agent 조립 계층 사이의 경계 객체입니다. 그래서 Pydantic `BaseModel`을 사용합니다.

#### state.py

`state.py`는 LangGraph state shape입니다.

- `ParentState`
- `BattleState`
- `CraftState`

LangGraph state는 dict 기반으로 merge/update되기 때문에 `TypedDict`를 사용합니다. state 안에서 반복되는 primitive dict는 `agent/types.py`의 alias를 사용해 의미를 드러냅니다.

#### models.py

`models.py`는 parent graph model입니다.

- `ParentNode`
- `SubgraphEntry`
- `SUBGRAPH_REGISTRY`

`ParentNode`는 parent graph node id로 쓰입니다. scenario 내부 node id는 `scenarios/spec.py`의 공통 `ScenarioNode`를 사용합니다. `SUBGRAPH_REGISTRY`는 parent graph가 사용 가능한 subgraph 목록을 알 수 있게 합니다.

### inbound

`inbound/`는 사용자 또는 외부 caller와 만나는 interface입니다.

```text
inbound/
  cli/
    main.py
```

현재는 CLI만 있습니다. CLI의 책임은 작아야 합니다.

- container를 가져온다.
- graph를 만든다.
- 사용자 입력 loop를 돈다.
- response를 출력한다.
- 종료 명령을 처리한다.
- application-level error를 사용자 메시지로 보여준다.

CLI 안에서 usecase 조립, tool hydration, graph 내부 node 실행을 직접 다루지 않습니다.

### outbound

`outbound/`는 외부 시스템 adapter입니다.

```text
outbound/
  llm/
  store/
  random.py
```

#### llm

`outbound/llm`은 `LLMPort` 구현체를 제공합니다.

- `GeminiLLMAdapter`
- `OpenAILLMAdapter`
- `TestingLLMAdapter`
- `create_llm_adapter`

`bootstrap`은 provider 이름을 보고 직접 분기하지 않고 `create_llm_adapter`에 위임합니다.

#### store

`outbound/store`는 `StorePort` 구현체를 제공합니다.

현재는 LangGraph `BaseStore`를 감싼 `LangGraphStoreAdapter`가 있습니다.

#### random

`outbound/random.py`는 `RandomPort` 구현체입니다.

테스트에서는 deterministic fake random을 사용하고, runtime에서는 `RandomAdapter`를 사용합니다.

### errors

`errors/`는 application-level custom exception입니다.

- `AgenticGameError`
- `ConfigurationError`
- `LLMError`
- `LLMQuotaExceededError`

외부 provider의 예외는 outbound adapter에서 이 예외들로 변환합니다. inbound는 provider-specific error를 몰라도 사용자에게 일관된 메시지를 보여줄 수 있습니다.

## 의존성 방향

의존성은 바깥에서 안쪽으로 흐릅니다.

```text
inbound
  -> bootstrap
    -> agent
      -> scenarios
      -> engine
      -> tools
      -> application
      -> flow
      -> domain

outbound -> application ports
bootstrap -> outbound implementations
```

중요한 규칙은 다음과 같습니다.

- `domain`은 아무 계층도 의존하지 않는다.
- `flow`는 domain을 의존하지만 agent를 의존하지 않는다.
- `scenarios`는 flow/domain의 정의를 읽고, agent/engine 조립 지점과 만난다.
- `engine`은 subgraph 실행과 tool runner를 담당하지만 concrete flow 전이를 직접 판단하지 않는다.
- `application`은 domain과 port를 의존한다.
- `tools`는 application usecase를 LLM tool로 노출한다.
- `agent`는 LangGraph 조립 계층이며 scenarios, engine, tools, application port를 조합한다.
- `outbound`는 application port를 구현한다.
- `inbound`는 bootstrap으로 조립된 graph만 사용한다.

## 경계 객체 원칙

프로젝트는 객체 성격에 따라 타입 표현을 다르게 씁니다.

- 순수 내부 데이터: `dataclass`
- 외부 시스템/LLM 경계 DTO: Pydantic `BaseModel`
- LangGraph state: `TypedDict`
- 반복되는 primitive: `type alias`

예를 들어 `ParentDecision`, `BattleDecision`, `CraftDecision`은 LLM structured output이므로 Pydantic 모델입니다. 반면 usecase 결과는 내부 결과이므로 dataclass입니다. LangGraph state는 dict merge semantics가 중요하므로 `TypedDict`를 사용합니다.

## 확장 방법

새 업무 subgraph를 추가할 때는 보통 다음 순서로 추가합니다.

1. `domain/`에 순수 데이터와 규칙을 추가한다.
2. `flow/`에 phase/event transition을 추가한다.
3. `scenarios/definitions.py`에 `ScenarioSpec`을 추가한다.
4. `scenarios/<scenario>.py`에 scenario 내부 event intent를 추가한다.
5. 필요하면 `application/usecases/`에 usecase 함수를 추가한다.
6. 필요하면 `tools/`에 LLM tool을 추가한다.
7. `agent/models.py`에 parent/subgraph enum과 registry entry를 추가한다.
8. `agent/state.py`에 subgraph state를 추가한다.
9. `agent/nodes/`에 node wrapper를 추가한다.
10. `agent/graph/`에 subgraph builder를 추가한다.
11. `scenarios/registry.py`에서 parent graph wrapper를 추가한다.
12. 필요하면 `agent/transitions.py`에 parent graph 전이를 추가한다.
13. `bootstrap.py`에서 usecase/tool dependency를 graph에 주입한다.

tool-backed 시나리오로 확장하려면 추가로 다음 작업이 필요합니다.

1. `application/usecases/`에 실제 시스템 기능을 추가한다.
2. `tools/<scenario>.py`에 LangChain `@tool` wrapper와 projection을 추가한다.
3. `flow/<scenario>.py`에 event별 `ToolBinding`을 추가한다.
4. `engine/tool_runner.py`에서 해당 binding과 hydrated tool을 연결한다.
5. scenario execute node가 직접 결과를 만들지 않고 tool runner에 위임하게 바꾼다.
6. `bootstrap.py`, `agent/graph/parent.py`, `scenarios/registry.py`에서 hydrated tool/usecase dependency를 주입한다.

반대로 flow 검증용 lightweight 시나리오라면 domain, flow, scenarios, agent graph/node만으로도 충분합니다.

새 LLM provider를 추가할 때는 다음만 건드리는 것이 이상적입니다.

1. `outbound/llm/<provider>.py`에 `LLMPort` 구현체를 추가한다.
2. `outbound/llm/factory.py`에 provider mapping을 추가한다.
3. 설정 예시와 테스트를 추가한다.

agent, application, domain은 provider-specific 코드를 몰라야 합니다.
