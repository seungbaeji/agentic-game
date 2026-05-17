# Glossary

이 문서는 `agentic-game`에서 반복해서 등장하는 용어를 짧게 설명합니다.

처음 읽을 때는 모든 용어를 외울 필요가 없습니다. `scenario`, `phase`, `event`, `flow`, `ScenarioNode`만 먼저 잡으면 나머지는 실행 흐름을 읽으며 따라올 수 있습니다.

## Core Workflow Terms

### Scenario

하나의 독립된 업무 흐름입니다.

예:

- battle
- craft
- exploration
- dialogue

Scenario는 LangGraph graph 자체가 아닙니다. Scenario는 phase, event, transition, 실행 node mapping을 가진 업무 단위입니다.

### Phase

업무가 지금 어디까지 진행됐는지 나타내는 단계입니다.

예:

```text
CraftPhase.CRAFT
DialoguePhase.CHOICE
ExplorationPhase.ENCOUNTER
```

Phase는 “현재 상태”에 가깝지만, 저장된 모든 도메인 상태를 뜻하지는 않습니다. 플레이어 HP나 inventory는 domain state이고, `phase`는 workflow 진행 위치입니다.

### Event

phase를 다음 phase로 움직이는 업무 사건입니다.

예:

```text
CraftEvent.CRAFT_WEAPON
DialogueEvent.ASK_RUMOR
ExplorationEvent.INSPECT
```

사용자 입력 문장 자체가 event는 아닙니다. 사용자 입력을 해석해서 event를 고릅니다.

### Flow

`phase + event -> next phase` 규칙입니다.

예:

```text
CraftPhase.CRAFT + CraftEvent.CRAFT_WEAPON -> CraftPhase.RESULT
```

Flow는 LangGraph edge가 아닙니다. Flow는 업무 규칙이고, LangGraph는 그 규칙을 실행하는 조립 계층입니다.

### TransitionRule

하나의 flow 규칙을 표현하는 데이터입니다.

```text
from_phase
on_event
to_phase
label
description
```

도메인별 flow 파일은 여러 `TransitionRule`을 모아 scenario의 업무 흐름을 정의합니다.

### ScenarioSpec

scenario를 실행하는 데 필요한 설정 묶음입니다.

현재 핵심 필드는 다음과 같습니다.

```text
name
initial_phase
transitions
phase_to_node
```

`ScenarioSpec`은 “이 scenario는 어떤 phase/event flow를 가지고 있고, 각 phase가 어떤 실행 단계로 이어지는가”를 설명합니다.

## Graph Runtime Terms

### Parent Graph

사용자 입력을 보고 어떤 scenario subgraph로 보낼지 결정하는 최상위 graph입니다.

예:

```text
"포션 만들래" -> craft
"NPC와 대화하고 싶어" -> dialogue
```

### Scenario Subgraph

하나의 scenario를 실행하는 LangGraph subgraph입니다.

예:

```text
craft subgraph
dialogue subgraph
battle subgraph
```

Scenario subgraph는 공통 `ScenarioNode` shape를 사용합니다.

### ScenarioNode

scenario subgraph 안에서 사용하는 공통 실행 단계 이름입니다.

```text
DECISION
FLOW
HITL
EXECUTE
RESPONSE
ASK_USER
```

주의할 점은 `ScenarioNode`가 business phase가 아니라는 것입니다.

예:

```text
CraftPhase.RESULT -> ScenarioNode.EXECUTE
```

`RESULT`는 업무 phase이고, `EXECUTE`는 graph 실행 단계입니다.

### Node

LangGraph가 호출하는 함수 단위입니다.

예:

```text
craft_decision_node
craft_flow_node
craft_execute_tool_node
```

Node는 state를 입력받고 state update를 반환합니다.

### Edge

LangGraph node 사이의 연결입니다.

예:

```text
DECISION -> FLOW
FLOW -> EXECUTE
RESPONSE -> END
```

Edge는 graph 실행 경로이고, flow transition은 업무 phase 전이입니다. 둘은 비슷해 보이지만 책임이 다릅니다.

### Wrapper

parent graph와 scenario subgraph 사이의 adapter입니다.

Wrapper의 책임은 다음과 같습니다.

- 이전 scenario state load
- subgraph invoke
- runtime-only key 제거
- scenario state persistence
- parent state update 반환

Wrapper는 업무 규칙을 판단하지 않아야 합니다.

### Runtime-Only Key

실행 중 routing에만 필요하고 저장하면 안 되는 state key입니다.

대표 예:

```text
next_node
```

`next_node`는 LangGraph routing을 위해 필요하지만, 다음 사용자 입력까지 보존할 업무 상태는 아닙니다.

## LLM Terms

### Decision

사용자 입력을 어떻게 처리할지 정하는 LLM structured output입니다.

예:

```text
ParentDecision
CraftDecision
DialogueDecision
```

Decision은 상태 변경을 직접 수행하지 않습니다. event 후보나 intent를 고를 뿐입니다.

### Intent

사용자 입력의 처리 유형입니다.

예:

```text
action
question
clarify
smalltalk
```

`action`만 flow transition을 통과합니다. `question`, `clarify`, `smalltalk`은 보통 phase를 움직이지 않고 응답합니다.

### CraftPlan

LLM이 만든 제작 상세 계획입니다.

예:

```json
{
  "category": "weapon",
  "item_name": "flame_dagger",
  "display_name": "불꽃 단검",
  "requested_effect": "burn"
}
```

Craft flow는 `item_name`을 보지 않습니다. Flow는 `category`에 대응하는 event만 검증합니다.

### ActionCard

LLM에게 보여주는 가능한 행동 후보입니다.

ActionCard에는 event, label, description이 들어가고, tool-backed action이면 tool metadata도 붙을 수 있습니다.

LLM은 ActionCard를 참고해 event를 고르지만, tool을 직접 실행하지 않습니다.

## Tool And Persistence Terms

### ToolBinding

event와 실제 tool input을 연결하는 계약입니다.

예:

```text
CraftEvent.CRAFT_WEAPON
  -> craft_item_tool(category="weapon", ...)
```

LLM이 event를 고른 뒤에도 runtime은 `ToolBinding`을 통해 실행 가능한 tool input을 만듭니다.

### ToolResult

tool 실행 결과를 여러 소비자 관점으로 나눈 객체입니다.

```text
raw
llm
ui
metadata
```

### Projection

usecase/domain result를 `ToolResult` 같은 외부 경계 payload로 변환하는 작업입니다.

예:

```text
CraftItemResult -> raw/llm/ui payload
```

### raw / llm / ui Payload

tool 결과를 목적별로 나눈 데이터입니다.

- `raw`: 감사 가능하고 재처리 가능한 원본에 가까운 결과
- `llm`: LLM 응답 생성에 필요한 요약 데이터
- `ui`: 화면이나 CLI에 보여주기 좋은 형태

### StoreRef

store에 저장된 payload를 가리키는 참조 문자열입니다.

예:

```text
store://craft/result/raw/latest
```

Graph state에 큰 payload 전체를 넣지 않고 ref만 보관하기 위해 사용합니다.

### latest_refs / history_refs

최근 payload와 과거 payload 목록을 가리키는 ref 모음입니다.

```python
{
    "latest_refs": {
        "result.raw": "store://craft/result/raw/latest"
    },
    "history_refs": {
        "result.raw": ["store://craft/result/raw/history/1"]
    }
}
```

이렇게 하면 graph state는 작게 유지하고, 필요한 상세 결과는 store에서 다시 읽을 수 있습니다.

## Layer Terms

### domain

순수 도메인 데이터와 규칙입니다.

LangGraph, LLM, store, tool을 알지 않아야 합니다.

### flow

phase/event transition과 action 직렬화 규칙입니다.

LangGraph node를 알지 않아야 합니다.

### scenarios

scenario 정의, scenario 등록, intent 감지 규칙을 둡니다.

### engine

subgraph 실행, persistence, tool runner 같은 공통 실행기를 둡니다.

### agent

LangGraph graph/node 조립과 LLM prompt/decision DTO를 둡니다.

### application

usecase와 port를 둡니다.

### tools

application usecase를 LLM/tool runtime이 호출할 수 있는 형태로 감쌉니다.

### outbound

LLM provider, store, random source 같은 외부 adapter를 둡니다.
