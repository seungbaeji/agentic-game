# Architecture

이 문서는 `agentic-game`의 패키지 경계와 의존성 방향을 설명합니다.

실행 순서를 보고 싶다면 [Flow-Centered Scenario Execution](node-flow.md)를, LLM/tool/flow의 배경을 먼저 잡고 싶다면 [LLM, Tool, Flow 입문 가이드](llm-tool-flow-guide.md)를, scenario별 예시는 [Scenario Details](scenario-details.md)를 참고하세요.

## 설계 목표

`agentic-game`은 게임 전용 framework가 아니라 phase/event 기반 agent workflow runtime을 게임 샘플로 검증하는 프로젝트입니다.

핵심 목표는 다음과 같습니다.

- LangGraph를 업무 규칙의 중심이 아니라 실행 조립 계층으로 제한한다.
- 업무 전이는 `flow/`가 phase/event 기준으로 결정한다.
- 상태 변경은 application usecase와 tool이 담당한다.
- LLM은 자연어 이해, 구조화, 응답 생성을 돕되 상태 변경의 최종 권한자가 되지 않는다.
- scenario가 늘어나도 graph shape, wrapper, persistence, tool 실행 코드가 과도하게 반복되지 않게 한다.

## 패키지 지도

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

## 계층별 책임

| 경로 | 책임 | 알면 안 되는 것 |
| --- | --- | --- |
| `domain/` | 순수 도메인 데이터, phase/event enum, 판정 함수 | LangGraph, LangChain, store, prompt |
| `flow/` | phase/event transition과 현재 phase의 action 후보 | LangGraph node, tool 실행, persistence |
| `scenarios/` | ScenarioSpec, scenario 등록, intent 감지 | concrete store 구현, provider-specific LLM |
| `engine/` | subgraph lifecycle, state persistence, tool runner | concrete flow 판단 |
| `application/` | usecase와 port | outbound 구현체, LangGraph state |
| `tools/` | LangChain `@tool` wrapper와 result projection | graph routing, CLI |
| `agent/` | LangGraph graph/node 조립, prompt, state shape | provider-specific LLM 구현 |
| `inbound/` | CLI/API/UI 같은 사용자 interface | usecase 세부 조립 |
| `outbound/` | LLM/store/random 같은 외부 adapter | agent graph 내부 구조 |
| `config/` | 환경 설정 | 업무 규칙 |
| `errors/` | application-level 예외 | provider-specific 예외 노출 |

## 핵심 의존성 방향

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

- `domain`은 다른 계층을 import하지 않습니다.
- `flow`는 domain을 의존하지만 agent나 engine을 의존하지 않습니다.
- `application`은 domain과 port를 조합합니다.
- `tools`는 application usecase를 LLM/tool runtime이 호출할 수 있는 형태로 감쌉니다.
- `scenarios`는 flow/domain 정의와 agent/engine 조립 지점을 연결합니다.
- `engine`은 실행과 저장을 담당하지만 concrete scenario 전이를 직접 판단하지 않습니다.
- `agent`는 LangGraph 조립 계층입니다.
- `outbound`는 application port를 구현합니다.
- `inbound`는 bootstrap으로 조립된 graph만 사용합니다.

## 각 패키지 설명

### `domain/`

순수한 도메인 모델과 규칙을 둡니다.

예:

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

여기에는 phase, event, outcome, result dataclass, 순수 판정 함수가 들어갑니다.

좋은 예:

```text
craft_result(category, dice, item_name, display_name, requested_effect)
```

나쁜 예:

```text
LangGraph state 읽기
LLM prompt 생성
store에 저장
LangChain tool 호출
```

### `flow/`

업무 흐름을 phase/event transition으로 표현합니다.

예:

```text
BattlePhase.PREPARE + BattleEvent.ATTACK -> BattlePhase.RESOLVE
CraftPhase.CRAFT + CraftEvent.CRAFT_WEAPON -> CraftPhase.RESULT
```

`flow/`는 다음을 담당합니다.

- transition table
- 현재 phase에서 가능한 action 직렬화
- 간단한 follow-up helper

`flow/`는 `ScenarioNode`나 LangGraph edge를 몰라야 합니다. 업무 전이와 실행 node 선택은 분리합니다.

### `scenarios/`

scenario를 공통 runtime에 등록하기 위한 정의를 둡니다.

```text
scenarios/
  spec.py          # ScenarioSpec, ScenarioNode, ToolBinding
  definitions.py   # 게임 샘플 scenario 정의
  registry.py      # parent graph에 scenario 연결
  intent.py        # parent/scenario intent fast-path
```

`ScenarioSpec`은 다음을 연결합니다.

```text
initial_phase
transitions
phase_to_node
tool_binding
terminal_phases
```

새 도메인을 추가할 때 가장 먼저 읽어야 하는 곳입니다.

### `engine/`

공통 실행기를 둡니다.

```text
engine/
  subgraph.py
  tool_runner.py
```

`subgraph.py`는 parent graph 안에서 scenario subgraph를 실행합니다.

```text
이전 state load
-> subgraph invoke
-> runtime key 제거
-> state persistence
-> parent update 반환
```

`tool_runner.py`는 tool-backed scenario 실행을 담당합니다.

```text
event
-> ToolBinding
-> hydrated tool invoke
-> raw/llm/ui payload 저장
-> graph state update
```

### `application/`

시스템 usecase와 port를 둡니다.

```text
application/
  game_state.py
  ports.py
  usecases/
```

usecase는 domain 규칙과 port dependency를 조합합니다.

예:

```text
resolve_battle_action_and_store_player
craft_item_and_store_reward
exchange_item
```

`ports.py`는 application이 필요로 하는 추상화입니다.

```text
LLMPort
StorePort
RandomPort
```

application은 outbound 구현체를 import하지 않습니다.

### `tools/`

LLM/tool runtime이 usecase를 호출할 수 있도록 감싸는 계층입니다.

```text
tools/
  battle.py
  craft.py
  trade.py
  result_projection.py
  types.py
```

tool은 outbound가 아닙니다. 외부 시스템 adapter가 아니라, application usecase를 tool interface로 노출하는 adapter입니다.

`ToolResult`는 tool 경계에서 raw/llm/ui payload를 분리합니다.

```text
raw: source of truth에 가까운 구조화 결과
llm: 응답 생성에 참고할 payload
ui: 화면 표현에 쓰기 쉬운 payload
metadata: system event, risk, trace 정보
```

### `agent/`

LangGraph와 LLM 조립 계층입니다.

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

`graph/`는 `StateGraph` 조립만 담당합니다.

`nodes/`는 LangGraph가 호출하는 얇은 wrapper입니다.

```text
state 읽기
-> decision/flow/engine에 위임
-> state update 반환
```

`prompts.py`는 prompt 문자열 생성, `decisions.py`는 LLM structured output DTO, `state.py`는 LangGraph state shape를 둡니다.

### `inbound/`

사용자 또는 외부 caller와 만나는 interface입니다.

현재는 CLI만 있습니다.

```text
inbound/
  cli/
    main.py
```

CLI는 input loop, response 출력, 종료 명령, 사용자에게 보여줄 error message만 다룹니다.

### `outbound/`

외부 시스템 adapter입니다.

```text
outbound/
  llm/
  store/
  random.py
```

LLM provider, LangGraph store adapter, random source가 여기에 있습니다.

## 경계 객체 원칙

객체의 성격에 따라 타입 표현을 나눕니다.

| 성격 | 표현 |
| --- | --- |
| 순수 내부 데이터 | `dataclass` |
| LLM/provider 경계 DTO | Pydantic `BaseModel` |
| LangGraph state | `TypedDict` |
| 반복 primitive | `type alias` |

예를 들어 `CraftDecision`은 LLM structured output이므로 Pydantic 모델입니다. 반면 `CraftResult`는 내부 usecase 결과이므로 dataclass입니다.

## 확장 규칙

새 scenario를 추가할 때는 보통 아래 순서로 진행합니다.

1. `domain/`에 phase/event/result를 추가한다.
2. `flow/`에 transition table과 action 직렬화를 추가한다.
3. `scenarios/definitions.py`에 `ScenarioSpec`을 추가한다.
4. `scenarios/intent.py`에 최소한의 intent fast-path를 추가한다.
5. 상태 변경이 필요하면 `application/usecases/`를 추가한다.
6. tool-backed scenario라면 `tools/`와 `ToolBinding`을 추가한다.
7. `agent/state.py`, `agent/models.py`, `agent/graph/`, `agent/nodes/`에 graph 연결을 추가한다.
8. `scenarios/registry.py`와 `bootstrap.py`에서 조립한다.
9. domain, flow, graph, tool/usecase 테스트를 추가한다.

확장할 때의 기본 판단 기준은 다음과 같습니다.

```text
업무 규칙인가?        -> domain 또는 flow
상태 변경 usecase인가? -> application
tool interface인가?   -> tools
graph 실행 구조인가?  -> agent 또는 engine
scenario 연결인가?    -> scenarios
외부 adapter인가?     -> outbound
```
