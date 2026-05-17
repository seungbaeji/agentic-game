# Flow-Centered Scenario Execution

이 문서는 공통 실행 흐름만 설명합니다.

용어가 낯설다면 [Glossary](glossary.md)를 먼저 봐도 됩니다. 구체 scenario별 동작은 [Scenario Details](scenario-details.md)를 참고하세요. 폴더 구조와 계층 책임은 [Architecture](architecture.md)를 참고하세요.

## 핵심 원칙

이 프로젝트는 LangGraph node/edge 자체보다 `phase/event` 업무 흐름을 중심에 둡니다.

```text
사용자 입력
  -> intent fast-path / LLM decision
  -> event 선택
  -> flow transition
  -> ScenarioNode 선택
  -> execute / response / ask user
  -> state persistence
```

LangGraph는 이 흐름을 실행하는 조립 계층입니다. 업무 전이는 `flow/`가 결정하고, 실행은 `engine/`과 `agent/nodes/`가 담당합니다.

## LLM Decision Boundary

LLM을 많이 활용하더라도 flow 자체를 LLM에게 맡기지 않습니다.

입력 처리 우선순위는 다음과 같습니다.

1. deterministic fast-path
   명시적인 행동 입력은 키워드 기반 감지로 바로 event를 고릅니다.

2. LLM scenario decision
   명시적인 행동이 아니면 LLM이 입력을 `action`, `question`, `clarify`, `smalltalk` 같은 의도로 분류합니다.

3. flow transition
   `action`만 `flow/`의 phase/event transition table을 통과합니다.

4. direct response
   `question`, `clarify`, `smalltalk`은 phase를 움직이지 않고 현재 scenario state를 바탕으로 응답합니다.

## Parent Graph

Parent graph는 최상위 router입니다.

```text
ParentNode.DECISION
ParentNode.<SCENARIO>
ParentNode.RESPONSE
ParentNode.ASK_USER
```

처리 순서:

1. `detect_parent_subgraph(user_input)`로 명시적인 scenario 의도를 먼저 찾습니다.
2. capability question이면 가능한 scenario를 안내합니다.
3. 그래도 모호하면 LLM `ParentDecision`으로 target scenario를 고릅니다.
4. scenario wrapper가 subgraph를 실행합니다.
5. parent response가 subgraph response를 사용자에게 돌려줍니다.

시작 안내와 capability 응답은 LLM이 생성할 수 있고, LLM 응답이 비어 있거나 실패하면 deterministic fallback을 사용합니다.

## Scenario Graph Shape

현재 scenario는 공통 `ScenarioNode` graph shape를 공유합니다.

```text
DECISION -> FLOW | RESPONSE | ASK_USER
FLOW -> HITL | EXECUTE | RESPONSE | ASK_USER
HITL -> DECISION | ASK_USER
EXECUTE -> RESPONSE
RESPONSE -> END
ASK_USER -> END
```

각 node의 책임은 작게 유지합니다.

| Node | 책임 |
| --- | --- |
| DECISION | 입력을 event/action/question 등으로 분류 |
| FLOW | phase/event transition 검증 |
| HITL | 사용자 입력이 더 필요한지 확인 |
| EXECUTE | tool 또는 deterministic usecase 실행 |
| RESPONSE | 사용자 응답 생성 |
| ASK_USER | 다음 입력 요청 |

## Flow와 ScenarioNode를 나누는 이유

`flow/`는 업무 상태 전이를 설명합니다.

```text
BattlePhase.PREPARE + BattleEvent.ATTACK -> BattlePhase.RESOLVE
```

`ScenarioNode`는 LangGraph 실행 단계를 설명합니다.

```text
BattlePhase.RESOLVE -> ScenarioNode.EXECUTE
```

둘을 합치면 업무 규칙과 graph 실행 구조가 섞입니다. 분리하면 같은 graph shape를 유지하면서 scenario별 phase/event만 바꿀 수 있습니다.

## Tool Execution

tool-backed scenario는 다음 순서로 실행됩니다.

```text
event
  -> ToolBinding
  -> tool input
  -> LangChain @tool
  -> application usecase
  -> domain result
  -> raw/llm/ui projection
  -> store persistence
```

`ActionCard`는 LLM에게 보여주는 행동 후보입니다. tool-backed action의 `tool_name`, `state_effect`, `risk` metadata는 `ToolBinding`에서 파생됩니다.

LLM은 action metadata를 참고해 event를 고를 수 있지만 tool을 직접 실행하지 않습니다. runtime이 flow 전이를 검증한 뒤 `ToolBinding`으로 tool input을 만들고 실행합니다.

## State Persistence

subgraph wrapper는 scenario state를 store에 저장합니다.

```text
<scenario> / state / latest
```

tool result는 payload 종류별로 저장합니다.

```text
<scenario> / <phase> / raw / latest
<scenario> / <phase> / llm / latest
<scenario> / <phase> / ui / latest
<scenario> / <phase> / raw / history / 1
...
```

graph state에는 latest/history ref만 남깁니다.

```python
{
    "latest_refs": {
        "result.raw": "store://craft/result/raw/latest"
    },
    "history_refs": {
        "result.raw": ["store://craft/result/raw/history/1"]
    },
}
```

## Runtime-Only Keys

`next_node`는 LangGraph routing을 위한 runtime-only key입니다.

state를 저장하기 전에 `remove_runtime_routing()`이 `next_node`를 제거합니다. 저장된 state는 다음 입력을 이어가기 위한 업무 상태만 포함해야 합니다.

## Error Handling

LLM provider 예외는 outbound adapter에서 application-level error로 변환됩니다.

```text
provider exception
  -> LLMError or LLMQuotaExceededError
  -> CLI-safe message
```

CLI는 provider-specific exception을 알 필요가 없습니다.

## Testing Focus

테스트는 다음을 검증합니다.

- domain: 순수 도메인 판정
- flow: phase/event transition table
- scenarios: intent 감지와 ScenarioSpec
- agent graph: parent/scenario graph invoke
- usecases/tools: usecase와 tool projection
- settings/llm testing: 설정, fake LLM, LLM factory

graph 테스트는 `TestingLLMAdapter`와 `FixedRandom`을 사용해 외부 provider를 호출하지 않습니다.
