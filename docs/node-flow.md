# Node Flow And Transitions

이 문서는 LangGraph node 전이와 business flow가 어떻게 함께 적용되는지 설명합니다.

프로젝트에는 두 종류의 전이가 있습니다.

- business flow transition: 업무 phase/event가 어떻게 바뀌는지 정의한다.
- LangGraph node transition: graph runtime이 다음에 어떤 node를 실행할지 정의한다.

이 둘은 비슷해 보이지만 같은 책임이 아닙니다. `BattlePhase.ACTION`으로 이동한다는 것은 업무 상태가 행동 선택 단계가 됐다는 뜻입니다. 하지만 LangGraph 입장에서는 그 다음에 `BattleNode.HITL`을 실행해야 합니다. 이 연결이 `routing.py`의 역할입니다.

## 전체 실행 흐름

CLI 기준 전체 흐름은 다음과 같습니다.

```text
inbound/cli/main.py
  -> get_container()
  -> build_agent_graph(container)
  -> graph.invoke(parent_state)

parent graph
  -> parent decision
  -> battle subgraph or craft subgraph
  -> parent response
```

사용자 입력 하나는 항상 parent graph로 들어갑니다.

```python
{
    "user_input": "...",
    "store_refs": {...},
}
```

parent graph는 입력 intent를 보고 battle 또는 craft subgraph로 위임합니다. subgraph가 끝나면 parent graph는 subgraph response를 최종 response로 돌려줍니다.

## Parent Graph

Parent graph는 최상위 router입니다.

### Nodes

```text
ParentNode.DECISION
ParentNode.BATTLE
ParentNode.CRAFT
ParentNode.RESPONSE
ParentNode.ASK_USER
```

### Graph Builder

`agent/graph/parent.py`는 다음 일을 합니다.

```text
StateGraph(ParentState)
  add_node(parent_decision)
  add_node(battle_subgraph wrapper)
  add_node(craft_subgraph wrapper)
  add_node(parent_response)
  add_node(parent_ask_user)
  set_entry_point(parent_decision)
  add_conditional_edges(parent_decision, parent_route, PARENT_DECISION_EDGES)
  add direct edges from PARENT_DIRECT_EDGES
```

graph builder는 node 내부 로직을 모릅니다. node와 edge table을 연결할 뿐입니다.

### Decision Node

`agent/nodes/parent.py`의 `make_parent_decision_node`는 target subgraph를 고릅니다.

우선순위는 다음과 같습니다.

1. deterministic intent inference
2. capability question detection
3. LLM structured output

#### 1. deterministic intent inference

`flow/intent.py`의 `infer_parent_subgraph(user_input)`를 호출합니다.

예를 들어 다음 입력은 battle로 바로 갑니다.

```text
몬스터를 공격할게
```

반환 state update:

```python
{
    "target_subgraph": SubgraphName.BATTLE,
    "reason": "...",
    "next_node": ParentNode.BATTLE,
}
```

#### 2. capability question detection

사용자가 “뭘 할 수 있어?”처럼 기능을 물으면 subgraph를 호출하지 않습니다.

반환 state update:

```python
{
    "reason": "...",
    "next_node": ParentNode.ASK_USER,
}
```

#### 3. LLM structured output

명시적 intent가 없으면 LLM에게 `ParentDecision`을 요청합니다.

```text
ParentDecision
  target_subgraph: SubgraphName | None
  reason: str
```

LLM prompt는 `agent/prompts.py`에서 생성합니다.

### Parent Conditional Edge

`ParentNode.DECISION` 다음 전이는 `parent_route(state)`가 `state["next_node"]`를 읽어 결정합니다.

`agent/transitions.py`:

```python
PARENT_DECISION_EDGES = {
    ParentNode.BATTLE: ParentNode.BATTLE,
    ParentNode.CRAFT: ParentNode.CRAFT,
    ParentNode.ASK_USER: ParentNode.ASK_USER,
}
```

즉 decision node는 `next_node`를 쓰고, LangGraph는 그 값을 edge table에서 찾습니다.

### Parent Direct Edges

```python
PARENT_DIRECT_EDGES = [
    (ParentNode.BATTLE, ParentNode.RESPONSE),
    (ParentNode.CRAFT, ParentNode.RESPONSE),
    (ParentNode.RESPONSE, END),
    (ParentNode.ASK_USER, END),
]
```

battle/craft wrapper는 subgraph를 실행한 뒤 parent response로 갑니다. ask user는 바로 종료됩니다.

## Battle Subgraph

Battle subgraph는 전투 업무 흐름을 실행합니다.

### Business Phases

`domain/battle.py`의 `BattlePhase`가 업무 상태를 표현합니다.

```text
PREPARE
ACTION
RESOLVE
COMPLETE
```

### Business Events

`BattleEvent`는 사용자가 선택하거나 LLM이 결정한 업무 event입니다.

```text
CONTINUE
ATTACK
DEFEND
FLEE
RETRY
COMPLETE
```

### Business Flow Transition

`flow/battle.py`의 `BATTLE_TRANSITIONS`가 phase/event transition table입니다.

```text
PREPARE --CONTINUE--> ACTION
PREPARE --ATTACK--> RESOLVE
PREPARE --DEFEND--> RESOLVE
PREPARE --FLEE--> RESOLVE
ACTION --ATTACK--> RESOLVE
ACTION --DEFEND--> RESOLVE
ACTION --FLEE--> RESOLVE
RESOLVE --RETRY--> ACTION
RESOLVE --COMPLETE--> COMPLETE
```

이 table은 LangGraph node를 모릅니다. 업무 phase만 다룹니다.

### Battle Nodes

```text
BattleNode.DECISION
BattleNode.FLOW
BattleNode.HITL
BattleNode.EXECUTE
BattleNode.RESPONSE
BattleNode.ASK_USER
```

### Battle Graph Shape

`agent/graph/battle.py`:

```text
DECISION -> FLOW
FLOW -> HITL | EXECUTE | RESPONSE | ASK_USER
HITL -> DECISION | RESPONSE
EXECUTE -> RESPONSE
RESPONSE -> END
ASK_USER -> END
```

### Battle Decision Node

`make_battle_decision_node`는 battle event를 결정합니다.

입력 state에서 읽는 값:

```text
phase
human_input
user_input
```

처리 순서:

1. 현재 phase의 available actions를 만든다.
2. 사용자 입력에서 명시적 event를 추론한다.
3. 추론되면 LLM을 호출하지 않고 event를 확정한다.
4. 추론되지 않으면 LLM structured output으로 `BattleDecision`을 받는다.
5. `next_node = BattleNode.FLOW`를 반환한다.

반환 예시:

```python
{
    "phase": BattlePhase.PREPARE,
    "event": BattleEvent.ATTACK,
    "available_actions": [...],
    "reason": "...",
    "next_node": BattleNode.FLOW,
}
```

### Battle Flow Node

`battle_flow_node`는 business flow transition을 적용합니다.

처리 순서:

1. `state["phase"]`와 `state["event"]`를 읽는다.
2. `resolve_battle_transition(phase, event)`로 flow rule을 찾는다.
3. rule이 없으면 `BattleNode.ASK_USER`로 보낸다.
4. rule이 있으면 `next_phase = rule.to_phase`를 얻는다.
5. `routing.battle_node_after_phase(next_phase)`로 LangGraph next node를 결정한다.

중요한 점은 flow node가 두 단계를 연결한다는 것입니다.

```text
business event -> business phase -> LangGraph node
```

예:

```text
PREPARE + ATTACK
  -> flow transition: RESOLVE
  -> routing: BattleNode.EXECUTE
```

반환 state update:

```python
{
    "phase": BattlePhase.RESOLVE,
    "available_actions": serialize_battle_actions(BattlePhase.RESOLVE),
    "next_node": BattleNode.EXECUTE,
}
```

### Battle Routing

`agent/routing.py`:

```python
def battle_node_after_phase(phase: BattlePhase) -> BattleNode:
    if phase == BattlePhase.ACTION:
        return BattleNode.HITL
    if phase == BattlePhase.RESOLVE:
        return BattleNode.EXECUTE
    return BattleNode.RESPONSE
```

이 규칙은 flow transition table과 분리되어 있습니다. flow는 업무 phase만 알고, routing은 graph runtime node만 압니다.

### Battle HITL Node

`battle_hitl_node`는 human input이 필요한 상황을 처리합니다.

human input이 없으면 response를 만들고 종료 방향으로 보냅니다.

```python
{
    "response": "HITL 필요: ...",
    "next_node": BattleNode.RESPONSE,
}
```

human input이 있으면 다시 decision으로 보냅니다.

```python
{
    "next_node": BattleNode.DECISION,
}
```

### Battle Execute Node

`battle_execute_tool_node`는 직접 tool 실행 로직을 들고 있지 않습니다. `agent/runtime/tools.py`의 `execute_battle_tool`에 위임합니다.

runtime 처리 순서:

1. `BattleEvent`를 tool action 문자열로 변환한다.
2. hydrated `resolve_battle_tool`을 invoke한다.
3. tool이 application usecase `resolve_battle_action`을 호출한다.
4. tool result를 raw/llm/ui payload로 projection한다.
5. store에 payload를 저장한다.
6. `latest_refs`, `history_refs`, `response`, `next_node`를 반환한다.

store 저장 형태:

```text
battle / resolve / raw / latest
battle / resolve / llm / latest
battle / resolve / ui / latest
battle / resolve / raw / history / 1
...
```

graph state에는 store ref만 남깁니다.

```python
{
    "latest_refs": {
        "resolve.raw": "store://battle/resolve/raw/latest",
        "resolve.llm": "store://battle/resolve/llm/latest",
        "resolve.ui": "store://battle/resolve/ui/latest",
    },
    "history_refs": {
        "resolve.raw": ["store://battle/resolve/raw/history/1"],
        ...
    },
    "response": "...",
    "next_node": BattleNode.RESPONSE,
}
```

### Battle Response Node

response가 이미 있으면 그대로 반환합니다. tool 실행 결과처럼 concrete response가 있을 때 LLM이 불필요하게 다시 요약하지 않도록 하기 위함입니다.

response가 없으면 `build_battle_response_prompt(state)`를 사용해 LLM response를 생성합니다.

## Craft Subgraph

Craft subgraph는 제작 업무 흐름을 실행합니다.

### Business Phases

```text
SELECT_RECIPE
CRAFT
RESULT
COMPLETE
```

### Business Events

```text
CONTINUE
CRAFT_POTION
CRAFT_SWORD
RETRY
COMPLETE
```

### Business Flow Transition

`flow/craft.py`의 `CRAFT_TRANSITIONS`:

```text
SELECT_RECIPE --CONTINUE--> CRAFT
SELECT_RECIPE --CRAFT_POTION--> RESULT
SELECT_RECIPE --CRAFT_SWORD--> RESULT
CRAFT --CRAFT_POTION--> RESULT
CRAFT --CRAFT_SWORD--> RESULT
RESULT --RETRY--> CRAFT
RESULT --COMPLETE--> COMPLETE
```

### Craft Nodes

```text
CraftNode.DECISION
CraftNode.FLOW
CraftNode.HITL
CraftNode.EXECUTE
CraftNode.RESPONSE
CraftNode.ASK_USER
```

### Craft Graph Shape

```text
DECISION -> FLOW | ASK_USER
FLOW -> HITL | EXECUTE | RESPONSE | ASK_USER
HITL -> DECISION | RESPONSE | ASK_USER
EXECUTE -> RESPONSE
RESPONSE -> END
ASK_USER -> END
```

Battle과 다른 점은 `DECISION`에서 바로 `ASK_USER`로 갈 수 있다는 점입니다. “제작하고 싶어”처럼 recipe가 없는 입력은 제작할 아이템을 물어야 합니다.

### Craft Decision Node

처리 순서:

1. 현재 phase의 available actions를 만든다.
2. 명시적 recipe intent를 추론한다.
3. recipe가 있으면 `CraftNode.FLOW`로 보낸다.
4. `SELECT_RECIPE` phase에서 recipe가 없으면 `CONTINUE` event로 `FLOW`에 보낸다.
5. `CRAFT` phase에서 recipe가 없으면 `ASK_USER`로 보낸다.
6. 그 외에는 LLM structured output으로 `CraftDecision`을 받는다.

이 로직 때문에 다음 UX가 가능합니다.

```text
> 제작하고 싶어
제작할 아이템을 선택해 주세요. 가능한 선택: 포션 / 검
> 포션
potion 제작 성공
```

### Craft Flow Node

`craft_flow_node`는 `resolve_craft_transition(phase, event)`로 business flow rule을 찾고, `craft_node_after_phase(next_phase)`로 LangGraph next node를 고릅니다.

`agent/routing.py`:

```python
def craft_node_after_phase(phase: CraftPhase) -> CraftNode:
    if phase == CraftPhase.CRAFT:
        return CraftNode.HITL
    if phase == CraftPhase.RESULT:
        return CraftNode.EXECUTE
    return CraftNode.RESPONSE
```

예:

```text
SELECT_RECIPE + CONTINUE
  -> flow transition: CRAFT
  -> routing: CraftNode.HITL
```

```text
CRAFT + CRAFT_POTION
  -> flow transition: RESULT
  -> routing: CraftNode.EXECUTE
```

### Craft HITL Node

`craft_hitl_node`는 recipe 선택이 필요한지 확인합니다.

recipe가 없으면:

```python
{
    "response": "HITL 필요: 제작할 아이템을 선택하세요. ...",
    "next_node": CraftNode.ASK_USER,
}
```

recipe가 있으면:

```python
{
    "next_node": CraftNode.DECISION,
}
```

### Craft Execute Node

`craft_execute_tool_node`는 `execute_craft_tool`에 위임합니다.

runtime 처리 순서:

1. `CraftEvent`를 recipe 문자열로 변환한다.
2. hydrated `craft_item_tool`을 invoke한다.
3. tool이 application usecase `craft_item`을 호출한다.
4. tool result를 raw/llm/ui payload로 projection한다.
5. store에 payload를 저장한다.
6. response와 refs를 반환한다.

저장 namespace:

```text
craft / result / raw / latest
craft / result / llm / latest
craft / result / ui / latest
craft / result / raw / history / 1
...
```

### Craft Follow-up Handling

Craft wrapper는 subgraph를 실행하기 전에 이전 craft result에 대한 follow-up 질문인지 확인합니다.

위치는 `agent/runtime/subgraph.py`입니다.

```text
parent graph
  -> craft wrapper
    -> load saved craft state
    -> load latest craft result ui payload
    -> answer_craft_result_question(...)
```

예:

```text
> 포션
potion 제작 성공
> 어떤 포션이야?
방금 제작한 potion은 healing_potion입니다.
```

이 응답은 LLM이나 tool을 다시 호출하지 않고 `flow/craft.py`의 간단한 flow 함수로 처리됩니다.

## State Persistence

Parent graph는 각 subgraph state를 store에 저장합니다.

```text
battle state -> namespace=("battle", "state"), key="latest"
craft state -> namespace=("craft", "state"), key="latest"
```

Parent state에는 직접 전체 subgraph state를 넣지 않고 store ref만 넣습니다.

```python
{
    "store_refs": {
        "battle_state": "store://battle/state/latest",
        "craft_state": "store://craft/state/latest",
    }
}
```

이렇게 하면 parent graph state가 커지는 것을 막고, tool payload history도 store에서 관리할 수 있습니다.

## Runtime-only Keys

`next_node`는 LangGraph routing을 위한 runtime-only key입니다. 저장할 필요가 없습니다.

그래서 subgraph state를 저장하기 전에 `remove_runtime_routing`이 `next_node`를 제거합니다.

```python
def remove_runtime_routing(state):
    persisted_state = dict(state)
    persisted_state.pop("next_node", None)
    return persisted_state
```

테스트에서도 persisted state에 `next_node`가 없는지 확인합니다.

## 왜 transitions.py와 routing.py가 분리되어 있는가

`transitions.py`는 LangGraph edge table입니다.

```text
어떤 node에서 어떤 node로 갈 수 있는가?
```

`routing.py`는 phase-to-node mapping입니다.

```text
업무 phase가 결정된 뒤 LangGraph runtime은 어떤 node를 실행해야 하는가?
```

`flow/*.py`는 business transition입니다.

```text
현재 phase와 event가 주어졌을 때 다음 업무 phase는 무엇인가?
```

세 계층을 합치면 다음 순서가 됩니다.

```text
user input
  -> decision node
  -> event
  -> flow transition
  -> next business phase
  -> routing
  -> next graph node
  -> transitions edge table
  -> actual LangGraph transition
```

이 분리 덕분에 업무 흐름을 바꾸는 작업과 LangGraph node 구조를 바꾸는 작업이 서로 덜 얽힙니다.

## Error Handling

LLM provider 예외는 outbound adapter에서 application-level error로 변환됩니다.

```text
Gemini/OpenAI provider error
  -> LLMError or LLMQuotaExceededError
  -> inbound/cli/main.py
  -> user-facing message
```

CLI는 provider-specific exception을 알 필요가 없습니다.

## Testing Focus

테스트는 계층별로 나뉩니다.

- domain: 순수 battle/craft 판정
- flow: transition table과 intent inference
- agent transitions: LangGraph edge table
- agent graph: 실제 graph invoke와 store refs
- usecases/tools: usecase와 tool projection
- settings/llm testing: 설정, fake LLM, LLM factory

graph 테스트는 `TestingLLMAdapter`와 `FixedRandom`을 사용해 외부 provider를 호출하지 않습니다.
