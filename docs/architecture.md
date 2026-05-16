# Architecture

`agentic-game`은 LangGraph 기반 에이전트 샘플이지만, LangGraph를 프로젝트 전체의 중심 계층으로 두지는 않습니다. LangGraph는 agent runtime으로 제한하고, 순수 도메인 규칙과 시스템 usecase는 별도 계층에 둡니다. 이렇게 해야 CLI, REST API, UI, LLM tool이 같은 업무 기능을 재사용할 수 있습니다.

## 설계 목표

- 도메인 모델은 LangGraph, LangChain, 외부 API를 모른다.
- application usecase는 domain과 port를 조합해 시스템이 제공하는 기능을 만든다.
- tool은 usecase를 LLM이 호출할 수 있는 형태로 노출하는 상위 계층이다.
- agent는 LangGraph runtime 구성, node 실행, routing, prompt, state orchestration을 담당한다.
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
```

여기에는 다음이 들어갑니다.

- 전투/제작 phase, event, outcome 같은 enum
- usecase 결과 dataclass
- 순수 판정 함수

여기에는 다음이 들어가면 안 됩니다.

- LangGraph state
- node routing
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
  intent.py
  models.py
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
- 입력 문장에서 명시적 intent 추론
- 이전 결과에 대한 간단한 follow-up 응답

`flow`는 LangGraph node를 모릅니다. `BattleNode`, `CraftNode` 같은 agent runtime 개념을 import하지 않습니다.

### application

`application/`은 시스템 usecase와 port를 둡니다.

```text
application/
  ports.py
  usecases/
    battle.py
    craft.py
```

usecase는 함수로 유지합니다.

- `resolve_battle_action`
- `craft_item`

이 함수들은 domain 규칙과 port dependency를 조합합니다. CLI, REST API, tool, agent 모두 같은 usecase를 호출할 수 있습니다.

`ports.py`는 application이 필요로 하는 추상화입니다.

- `LLMPort`
- `StorePort`
- `RandomPort`

application은 outbound 구현체를 import하지 않습니다. 구현체는 bootstrap에서 주입됩니다.

### tools

`tools/`는 LLM이 usecase를 호출할 수 있게 만드는 계층입니다.

```text
tools/
  battle.py
  craft.py
  projections.py
  types.py
```

tool은 outbound가 아닙니다. 외부 시스템으로 나가는 adapter가 아니라, application usecase를 LLM runtime이 사용할 수 있는 형태로 감싸는 상위 계층입니다.

현재 tool은 LangChain `@tool`로 정의됩니다.

- `resolve_battle_tool`
- `craft_item_tool`

tool의 입력에는 usecase와 random adapter가 injected argument로 들어갑니다. tool은 usecase 결과를 LLM/UI/raw 용 payload로 projection하고 `ToolResult`를 반환합니다.

### agent

`agent/`는 LangGraph runtime 관련 코드만 둡니다.

```text
agent/
  graph/
  nodes/
  runtime/
  decisions.py
  models.py
  prompts.py
  routing.py
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
```

node는 다음 일을 합니다.

- state에서 필요한 값을 읽는다.
- flow/application/runtime 함수에 위임한다.
- 다음 state update를 반환한다.

node 안에 길고 복잡한 business logic, prompt 문자열, store orchestration이 오래 머물면 읽기 어려워지므로 별도 모듈로 뺍니다.

#### runtime

`runtime/`은 LangGraph 실행 환경에 가까운 일을 담당합니다.

```text
runtime/
  subgraph.py
  tools.py
```

`subgraph.py`는 parent graph 안에서 battle/craft subgraph를 실행합니다.

- 이전 subgraph state를 store에서 읽는다.
- 초기 state를 만든다.
- subgraph를 invoke한다.
- runtime routing key를 제거한다.
- 최신 state를 store에 저장한다.
- parent state update를 반환한다.

`tools.py`는 tool 실행과 payload 저장을 담당합니다.

- event를 tool input으로 변환한다.
- hydrated tool을 invoke한다.
- raw/llm/ui payload를 store에 저장한다.
- graph state update를 반환한다.

#### transitions.py

`transitions.py`는 LangGraph edge table입니다.

여기에는 `add_conditional_edges`에 들어갈 mapping과 직접 edge 목록만 둡니다. node 함수 안에 흩어져 있던 LangGraph-level 전이를 모아 한눈에 볼 수 있게 합니다.

#### routing.py

`routing.py`는 flow phase를 LangGraph node로 바꿉니다.

예를 들어 battle flow가 `BattlePhase.RESOLVE`로 이동하면 agent runtime은 `BattleNode.EXECUTE`로 이동해야 합니다. 이 매핑은 domain flow 규칙도, LangGraph edge table도 아니므로 `routing.py`에 둡니다.

#### prompts.py

`prompts.py`는 LLM prompt 문자열 생성만 담당합니다.

node 파일에서 긴 prompt 문자열이 사라지면 node는 “무슨 일을 하는지”가 더 잘 보입니다.

#### decisions.py

`decisions.py`는 LLM structured output DTO입니다.

- `ParentDecision`
- `BattleDecision`
- `CraftDecision`

이 객체들은 외부 LLM 응답과 내부 agent runtime 사이의 경계 객체입니다. 그래서 Pydantic `BaseModel`을 사용합니다.

#### state.py

`state.py`는 LangGraph state shape입니다.

- `ParentState`
- `BattleState`
- `CraftState`

LangGraph state는 dict 기반으로 merge/update되기 때문에 `TypedDict`를 사용합니다. state 안에서 반복되는 primitive dict는 `agent/types.py`의 alias를 사용해 의미를 드러냅니다.

#### models.py

`models.py`는 agent runtime model입니다.

- `ParentNode`
- `BattleNode`
- `CraftNode`
- `SubgraphEntry`
- `SUBGRAPH_REGISTRY`

node enum은 LangGraph node id로 쓰입니다. `SUBGRAPH_REGISTRY`는 parent graph가 사용 가능한 subgraph 목록을 알 수 있게 합니다.

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
- `application`은 domain과 port를 의존한다.
- `tools`는 application usecase를 LLM tool로 노출한다.
- `agent`는 LangGraph runtime이며 flow, tools, application port를 조합한다.
- `outbound`는 application port를 구현한다.
- `inbound`는 bootstrap으로 조립된 graph만 사용한다.

## 경계 객체 원칙

프로젝트는 객체 성격에 따라 타입 표현을 다르게 씁니다.

- 순수 내부 데이터: `dataclass`
- 외부 시스템/LLM 경계 DTO: Pydantic `BaseModel`
- LangGraph state: `TypedDict`
- 반복되는 primitive: `type alias`

예를 들어 `ParentDecision`, `BattleDecision`, `CraftDecision`은 LLM structured output이므로 Pydantic 모델입니다. 반면 battle/craft 결과는 내부 usecase 결과이므로 dataclass입니다. LangGraph state는 dict merge semantics가 중요하므로 `TypedDict`를 사용합니다.

## 확장 방법

새 업무 subgraph를 추가할 때는 보통 다음 순서로 추가합니다.

1. `domain/`에 순수 데이터와 규칙을 추가한다.
2. `flow/`에 phase/event transition을 추가한다.
3. `application/usecases/`에 usecase 함수를 추가한다.
4. `tools/`에 LLM tool을 추가한다.
5. `agent/models.py`에 node enum과 `SUBGRAPH_REGISTRY` entry를 추가한다.
6. `agent/state.py`에 subgraph state를 추가한다.
7. `agent/nodes/`에 node wrapper를 추가한다.
8. `agent/graph/`에 subgraph builder를 추가한다.
9. `agent/runtime/subgraph.py`에서 parent wrapper를 추가한다.
10. `agent/transitions.py`와 `agent/routing.py`에 runtime 전이를 추가한다.
11. `bootstrap.py`에서 usecase/tool dependency를 graph에 주입한다.

새 LLM provider를 추가할 때는 다음만 건드리는 것이 이상적입니다.

1. `outbound/llm/<provider>.py`에 `LLMPort` 구현체를 추가한다.
2. `outbound/llm/factory.py`에 provider mapping을 추가한다.
3. 설정 예시와 테스트를 추가한다.

agent, application, domain은 provider-specific 코드를 몰라야 합니다.
