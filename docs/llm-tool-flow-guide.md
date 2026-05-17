# LLM, Tool, Flow 입문 가이드

이 문서는 `agentic-game`의 구조가 낯선 사람을 위한 첫 번째 읽기 문서입니다.

이 프로젝트는 단순히 LLM에게 모든 일을 맡기는 agent도 아니고, LangGraph node를 도메인마다 직접 설계하는 샘플도 아닙니다. 목표는 LLM, tool, flow의 책임을 나눠서 상태 변경이 있는 agent workflow를 예측 가능하게 만드는 것입니다.

## LLM 이전의 배경 개념

이 프로젝트에서 다루는 문제는 LLM 때문에 완전히 새로 생긴 문제가 아닙니다. 오래전부터 CS와 소프트웨어 설계에서 다루던 workflow, state, command 처리 문제 위에 LLM을 얹는 것에 가깝습니다.

여기서 말하는 stateless runtime은 "같은 입력이면 항상 같은 출력"이라는 뜻이 아닙니다. domain rule은 가능한 한 pure/deterministic하게 두고, agent runtime은 process memory에 session state를 들고 있지 않게 하며, domain state와 scenario 진행 상태는 scope가 있는 store에 저장하는 모델입니다. 자세한 구분은 [State Model](state-model.md)을 참고하세요.

### Finite State Machine

현재 상태와 입력 event를 보고 다음 상태를 결정하는 모델입니다.

```text
현재 phase + event -> 다음 phase
```

예를 들면 다음과 같습니다.

```text
BattlePhase.PREPARE + BattleEvent.ATTACK -> BattlePhase.RESOLVE
CraftPhase.CRAFT + CraftEvent.CRAFT_WEAPON -> CraftPhase.RESULT
```

이 프로젝트의 `flow/`가 이 역할을 합니다. LLM이 다음 phase를 마음대로 정하지 않고, flow가 가능한 전이를 검증합니다.

### Event-Driven Workflow

사용자 입력이나 시스템 사건을 event로 보고 workflow를 움직이는 방식입니다.

```text
사용자 입력
  -> Event
  -> Transition
  -> Handler
  -> State Update
```

여기서 event는 자연어 그 자체가 아니라 내부 시스템이 이해하는 명령형 값입니다. 예를 들어 `"몬스터를 공격할게"`는 내부에서 `BattleEvent.ATTACK`으로 해석됩니다.

### Workflow Orchestration

여러 실행 단계를 어떤 순서로 호출할지 조율하는 개념입니다.

이 프로젝트에서 LangGraph는 orchestration engine에 가깝습니다. 단, 업무 규칙을 LangGraph edge에 모두 넣지는 않습니다. 업무 규칙은 `flow/`에 두고, LangGraph는 `DECISION -> FLOW -> EXECUTE -> RESPONSE` 같은 실행 순서를 조립합니다.

### Command Query Separation

상태를 바꾸는 요청과 상태를 읽는 요청을 나누는 개념입니다.

```text
Command: 상태를 바꾸는 요청
Query: 상태를 읽는 요청
```

예를 들면 다음처럼 구분합니다.

```text
포션을 만들자       -> command/action
내 아이템 뭐야?     -> query
무슨 단서야?        -> question/query
```

이 경계가 흐려지면 “내 아이템 뭐야?” 같은 조회 입력이 제작 action으로 오인됩니다. 지금 이 프로젝트에서 다음으로 정리해야 할 중요한 지점도 이 부분입니다.

### Domain-Driven Design

도메인 규칙, usecase, adapter, runtime 조립을 분리하는 설계 관점입니다.

이 프로젝트에서는 대략 다음처럼 나눕니다.

```text
domain       순수 규칙과 데이터
flow         업무 전이 규칙
application  usecase
tools        LLM/tool adapter
agent        LangGraph와 LLM 조립
engine       공통 실행기
```

이렇게 나누면 게임이 아닌 승인, 문서 처리, 고객지원 같은 도메인으로 옮길 때도 같은 실행 패턴을 재사용할 수 있습니다.

### Semantic Parsing

사용자의 자연어를 내부 명령과 구조화된 값으로 바꾸는 개념입니다.

```text
"불꽃 단검을 만들고 싶어"
  -> event = CraftEvent.CRAFT_WEAPON
  -> item_name = "flame_dagger"
  -> display_name = "불꽃 단검"
  -> requested_effect = "fire"
```

LLM은 이 부분에 강합니다. 하지만 구조화된 값이 나왔다고 바로 실행하지 않고, flow와 tool 계층에서 다시 검증하고 실행합니다.

### Guarded Execution

LLM의 해석을 그대로 믿고 실행하지 않고, deterministic rule로 한 번 더 통제하는 방식입니다.

```text
LLM: 사용자는 공격하려는 것 같습니다.
Flow: 지금 phase에서 공격 event가 가능한가?
Tool: 가능하면 usecase를 실행한다.
```

이 프로젝트의 핵심 안전장치는 이 구조입니다.

## 왜 세 가지로 나누나

LLM은 자연어를 잘 이해하고, 설명을 자연스럽게 만들고, 사용자가 애매하게 말한 의도를 추정하는 데 강합니다. 하지만 LLM이 상태 변경까지 자유롭게 결정하면 실행 결과가 흔들릴 수 있습니다.

tool은 실제 일을 수행합니다. 전투 결과 계산, 아이템 제작, 거래 처리처럼 시스템 상태를 바꾸는 usecase를 호출합니다. 다른 업무 도메인이라면 문서 분류, 승인 처리, 티켓 상태 변경 같은 일이 됩니다.

flow는 가능한 상태 전이를 검증합니다. 지금 phase에서 이 event가 가능한지, 다음 phase가 무엇인지 판단합니다. 예를 들어 전투 준비 단계에서는 `공격`이 가능하지만, 이미 결과가 나온 단계에서 다시 `공격`이 가능한지는 flow가 결정합니다.

그래서 이 프로젝트의 기본 원칙은 다음과 같습니다.

```text
LLM은 이해와 표현을 맡는다.
Flow는 가능한 전이를 검증한다.
Tool은 실제 일을 실행한다.
```

## 여기서 LLM이 맡는 역할

LLM은 자연어 interface와 해석층에 가깝습니다. 기존 workflow 구조의 뼈대를 대체하지 않고, 사람이 편하게 말할 수 있게 해석하고 표현하는 역할을 맡습니다.

### Intent Classification

사용자 입력이 action인지, question인지, query인지, clarify인지 분류합니다.

```text
"포션을 만들자" -> action
"내 아이템 뭐야?" -> query
"무슨 단서야?" -> question
```

현재는 일부 deterministic keyword rule이 이 역할을 먼저 수행합니다. 다만 질문과 action의 경계가 섞이는 문제가 있어, 이 부분은 더 명확한 공통 intent gate로 개선할 예정입니다.

### Slot Filling

사용자가 자연어로 말한 세부 정보를 구조화합니다.

```text
"불꽃 단검을 만들고 싶어"
  -> category = WEAPON
  -> item_name = flame_dagger
  -> display_name = 불꽃 단검
  -> requested_effect = fire
```

flow는 `WEAPON` 같은 범주를 보고 전이를 판단하고, tool은 구조화된 값을 받아 usecase를 실행합니다.

### Natural Response

tool/usecase가 만든 결과를 사용자가 읽기 좋은 문장으로 바꿉니다.

```text
raw result: success=True, display_name="회복 포션", quantity=1
response: "회복 포션 1개를 성공적으로 제작했습니다."
```

단, LLM이 결과 값을 새로 만들어내면 안 됩니다. 성공 여부, 수량, HP, gold 같은 authoritative value는 usecase 결과를 따라야 합니다.

### Contextual Answer

이전 결과나 현재 scenario 맥락에 대한 후속 질문에 답합니다.

```text
"방금 만든 포션 효과가 뭐야?"
"무슨 단서야?"
"NPC가 뭐라고 했지?"
```

이런 입력은 action이 아니라 state나 최근 결과를 읽는 질문입니다. flow transition을 만들지 않고, 저장된 state나 latest result를 바탕으로 답해야 합니다.

## LLM에게 맡기지 않는 역할

LLM이 강력하더라도 아래 역할은 맡기지 않는 것이 좋습니다.

```text
상태 변경 확정
가능한 phase/event 전이 판정
inventory, hp, gold 같은 authoritative state 변경
tool 실행 여부 최종 결정
```

예를 들어 LLM이 “전투에서 승리했다”고 말하더라도, 실제 승리 여부는 battle usecase 결과가 정합니다. LLM은 그 결과를 설명할 수 있지만, 결과 자체를 바꾸면 안 됩니다.

한 줄로 정리하면 다음과 같습니다.

```text
기존 CS 구조가 뼈대고, LLM은 자연어 interface와 해석층이다.
```

## 한 문장으로 보는 실행 모델

사용자의 말은 먼저 의도로 해석되고, action일 때만 flow를 통과하며, 실제 상태 변경은 tool/usecase가 수행합니다.

```text
사용자 입력
  -> LLM 또는 keyword rule이 의도를 해석
  -> action이면 event 선택
  -> flow가 phase/event 전이를 검증
  -> tool 또는 usecase 실행
  -> LLM 또는 deterministic response가 사용자 응답 생성
```

중요한 점은 LLM이 바로 tool을 마음대로 호출하지 않는다는 것입니다. LLM은 “이 사용자가 어떤 event를 말하는 것 같다”는 결정을 도와주고, runtime이 flow로 검증한 다음 실행합니다.

## 게임 예시로 보기

전투에서 사용자가 이렇게 말합니다.

```text
몬스터를 공격할게
```

이 입력은 다음처럼 처리됩니다.

```text
1. parent graph
   전투 scenario로 보낸다.

2. decision
   사용자 입력을 BattleEvent.ATTACK으로 해석한다.

3. flow
   BattlePhase.PREPARE + BattleEvent.ATTACK이 가능한 전이인지 확인한다.

4. scenario node
   다음 phase가 실행 단계인지, 사용자 확인 단계인지, 응답 단계인지 고른다.

5. tool
   resolve_battle_tool이 usecase를 호출해 전투 결과를 계산한다.

6. response
   계산된 결과를 사용자에게 보여준다.
```

제작에서는 조금 다릅니다.

```text
불꽃 단검을 만들고 싶어
```

이때 flow는 “무기 제작”이라는 범주 전이를 다룹니다. `불꽃 단검`이라는 구체적인 이름과 `불꽃` 효과 힌트는 LLM이 `CraftPlan`으로 추출합니다.

```text
LLM: "불꽃 단검"은 무기 범주이며, 효과 힌트는 burn/fire다.
Flow: 지금 phase에서 무기 제작 event가 가능한지 확인한다.
Tool: craft_item_tool이 제작 결과와 inventory 저장을 처리한다.
```

즉 상세 묘사는 LLM에게 맡기되, 상태 변경은 flow와 tool이 통제합니다.

## 질문은 action이 아니다

다음 입력은 action이 아닙니다.

```text
무슨 단서야?
내가 가진 아이템이 뭐지?
방금 만든 포션 효과가 뭐야?
```

이런 입력은 phase/event transition을 만들면 안 됩니다. 현재 또는 최근 state를 읽어서 답해야 합니다.

현재 이 부분은 개선 대상입니다. 질문, 조회, 후속 설명, scenario 전환, action의 경계를 더 분명히 나누는 작업은 이슈 #3에서 다룹니다.

## 주요 개념

### Scenario

하나의 업무 흐름입니다.

게임 샘플에서는 battle, craft, exploration, trade, quest, dialogue, skill_training이 scenario입니다.

업무 도메인으로 바꾸면 document processing, approval workflow, customer support 같은 단위가 될 수 있습니다.

### Phase

scenario 안의 현재 업무 상태입니다.

예를 들어 craft에는 아이템을 고르는 phase, 제작을 실행하는 phase, 결과를 보여주는 phase가 있습니다.

### Event

사용자가 일으킨 업무 행동입니다.

예를 들어 battle의 `ATTACK`, craft의 `CRAFT_WEAPON`, dialogue의 `ASK_RUMOR`가 event입니다.

### Flow

`현재 phase + event -> 다음 phase`를 결정하는 규칙입니다.

flow는 LangGraph를 몰라야 합니다. 업무 전이만 알고 있어야 합니다.

### ScenarioNode

LangGraph가 실행하는 공통 단계입니다.

도메인마다 `BattleNode`, `CraftNode`를 늘리는 대신, 대부분의 scenario가 다음 공통 node를 사용합니다.

```text
DECISION
FLOW
HITL
EXECUTE
RESPONSE
ASK_USER
```

### ToolBinding

event와 tool 실행을 연결하는 설정입니다.

예를 들어 `CraftEvent.CRAFT_WEAPON`이 들어오면 어떤 tool을 어떤 input으로 호출할지 연결합니다.

### ActionCard

LLM decision prompt에 전달되는 행동 후보입니다.

LLM에게 “지금 가능한 행동은 이것들이다”라고 알려주기 위한 구조입니다. LLM은 이 후보 안에서 event를 고르고, flow가 다시 검증합니다.

## 어디에 무엇이 있나

```text
domain/
  phase, event, outcome, 순수 규칙

flow/
  phase/event transition

scenarios/
  ScenarioSpec, scenario 등록, intent 감지

agent/
  LangGraph graph/node 조립, LLM decision prompt

engine/
  subgraph 실행, state 저장, tool runner

tools/
  LangChain @tool과 결과 payload 변환

application/
  실제 usecase
```

처음 코드를 읽을 때는 아래 순서가 좋습니다.

```text
1. docs/glossary.md
2. docs/node-flow.md
3. src/agentic_game/scenarios/spec.py
4. src/agentic_game/scenarios/definitions.py
5. src/agentic_game/flow/craft.py
6. src/agentic_game/agent/nodes/craft.py
7. src/agentic_game/engine/tool_runner.py
```

## 구현할 때의 판단 기준

새 기능을 만들 때는 먼저 이 질문을 던집니다.

```text
이 코드는 사용자의 말을 이해하는가?
-> agent/decision 또는 prompt 쪽이다.

이 코드는 가능한 업무 전이를 판단하는가?
-> flow 쪽이다.

이 코드는 실제 상태를 바꾸는가?
-> application usecase 또는 tool 쪽이다.

이 코드는 scenario를 LangGraph 실행 단계와 연결하는가?
-> scenarios 또는 engine 쪽이다.

이 코드는 LangGraph node/edge를 조립하는가?
-> agent/graph 또는 agent/nodes 쪽이다.
```

헷갈릴 때는 LLM에게 더 맡기는 방향보다, 상태 변경 경계를 먼저 고정하는 방향이 안전합니다. LLM은 넓게 이해하고 말할 수 있지만, 상태 변경은 작고 명확한 함수가 담당해야 나중에 디버깅할 수 있습니다.

## 다음에 읽을 문서

- [Glossary](glossary.md): 용어를 짧게 확인합니다.
- [Flow-Centered Scenario Execution](node-flow.md): 실제 실행 흐름을 봅니다.
- [Scenario Details](scenario-details.md): 각 게임 scenario가 같은 구조를 어떻게 쓰는지 봅니다.
- [Tool Calling Architecture Comparison](tool-calling-comparison.md): 순수 tool-calling 방식과 현재 hybrid 방식의 차이를 봅니다.
