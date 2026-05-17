# agentic-game

LangGraph 기반 게임 시나리오 에이전트입니다.

이 프로젝트는 phase/event 기반 게임 시나리오를 LangGraph로 실행하는 구조를 검증합니다. 도메인 규칙, 업무 flow, 시나리오 정의, 실행 engine, LangGraph agent 조립, inbound/outbound adapter를 분리해서 새 게임 도메인을 추가해도 runtime 구조를 크게 바꾸지 않도록 만드는 것이 목표입니다.

## 문서

- [아키텍처](docs/architecture.md): 폴더 구조, 역할/책임/경계, 의존성 방향, 확장 지점
- [Flow 중심 Scenario 실행](docs/node-flow.md): parent graph, scenario flow, 공통 graph 실행 방식

MkDocs로 문서를 볼 수 있습니다.

```bash
uv run --group docs agentic-game-docs serve
```

## 구조 요약

```text
src/agentic_game/
  domain/       # 게임 데이터, phase/event enum, 순수 도메인 규칙
  flow/         # phase/event transition과 flow helper
  scenarios/    # ScenarioSpec 정의, scenario intent, parent routing, graph 등록
  engine/       # subgraph 실행, persistence wrapper, tool runner
  application/  # usecase와 port
  agent/        # LangGraph graph/node 조립, prompt, routing
  tools/        # LLM이 호출할 @tool 계층
  inbound/      # CLI, 향후 REST API/UI 같은 interface
  outbound/     # LLM, store, random 등 외부 adapter
  config/       # pydantic-settings 기반 설정
  errors/       # application-level custom exception
```

## 현재 Scenario와 Tool 지원 상태

현재 7개 게임 시나리오가 같은 `ScenarioNode` graph shape를 사용합니다.

| Scenario | 실행 방식 | 실제 LangChain tool |
| --- | --- | --- |
| battle | usecase-backed tool 실행 | `resolve_battle_tool(action)` |
| craft | usecase-backed tool 실행 + inventory 저장 | `craft_item_tool(recipe)` |
| exploration | deterministic execute node | 없음 |
| quest | deterministic execute node | 없음 |
| trade | deterministic execute node | 없음 |
| dialogue | deterministic response 중심 | 없음 |
| skill_training | deterministic execute node | 없음 |

즉 일반화된 부분은 `phase/event -> flow -> ScenarioNode -> 공통 LangGraph shape`입니다. 아직 모든 시나리오가 tool/usecase까지 일반화된 것은 아닙니다. 현재 실제 LangChain `@tool`과 payload persistence는 battle/craft에만 있습니다. craft는 성공 시 `game/inventory/latest`에 제작 아이템도 저장합니다.

## Flow 중심 실행 요약

이 프로젝트는 “업무 흐름”을 중심에 두고, LangGraph는 그 흐름을 실행하는 공통 껍데기로 둡니다.

전투를 예로 들면, `공격한다`는 업무 event이고 `전투 결과를 계산해야 한다`는 다음 업무 phase입니다. graph는 scenario마다 새로 설계하지 않고, `ScenarioNode`라는 공통 실행 단계를 사용합니다.

```text
사용자 입력
  -> decision node
       사용자의 의도를 event로 결정합니다.
       예: "몬스터를 공격할게" -> BattleEvent.ATTACK

  -> flow
       현재 phase와 event를 보고 다음 업무 phase를 계산합니다.
       예: BattlePhase.PREPARE + BattleEvent.ATTACK -> BattlePhase.RESOLVE

  -> scenario node
       ScenarioSpec.phase_to_node가 phase를 공통 실행 단계로 바꿉니다.
       예: BattlePhase.RESOLVE -> ScenarioNode.EXECUTE

  -> generic graph
       모든 scenario가 같은 node shape를 사용합니다.
       예: FLOW -> EXECUTE -> RESPONSE
```

각 파일의 책임은 다음과 같습니다.

- `flow/`: 업무 규칙을 정의합니다. `PREPARE + ATTACK -> RESOLVE`처럼 phase/event 전이를 다루며 LangGraph node를 모릅니다.
- `scenarios/`: 어떤 게임 시나리오가 있는지, 사용자 입력을 scenario/event로 어떻게 해석하는지, parent graph에 어떤 scenario를 등록하는지 설명합니다.
- `engine/`: subgraph 실행, state persistence, tool 실행처럼 scenario를 실제로 돌리는 공통 실행기를 둡니다.
- `agent/transitions.py`: parent graph edge table입니다. scenario subgraph의 node shape는 `agent/graph/scenario_graph.py`의 공통 graph를 사용합니다.
- `agent/graph/`: `StateGraph`를 만들고 node와 edge table을 조립합니다. node 내부 로직은 알지 않습니다.
- `agent/nodes/`: LangGraph가 호출하는 얇은 실행 단위입니다. state를 읽고 decision/flow/engine에 위임한 뒤 다음 state update를 반환합니다.

`scenarios/` 내부 경계는 다음과 같습니다.

```text
scenarios/
  spec.py          # 공통 ScenarioSpec / ScenarioNode
  definitions.py   # 각 게임 시나리오의 ScenarioSpec 정의
  registry.py      # parent graph에 concrete scenario 연결
  router.py        # parent-level intent routing
  battle.py        # battle 내부 event intent
  craft.py         # craft 내부 event intent
  exploration.py   # exploration 내부 event intent
  quest.py
  trade.py
  dialogue.py
  skill_training.py
```

예를 들어 전투에서 `몬스터를 공격할게`를 입력하면 다음처럼 흐릅니다.

```text
1. parent decision
   입력이 전투 의도라고 판단하고 battle subgraph로 보냅니다.

2. battle decision
   입력에서 공격 의도를 찾아 BattleEvent.ATTACK을 선택합니다.

3. battle flow
   현재 phase가 PREPARE이고 event가 ATTACK이므로 다음 phase를 RESOLVE로 바꿉니다.

4. scenario node 선택
   RESOLVE phase는 실제 전투 결과를 계산해야 하므로 ScenarioNode.EXECUTE로 보냅니다.

5. execute tool
   battle은 tool runner를 통해 usecase를 실행하고 raw/llm/ui 결과를 store에 저장합니다.

6. response
   저장된 실행 결과를 사용자에게 보여줄 응답으로 반환합니다.
```

자세한 내용은 [Flow 중심 Scenario 실행](docs/node-flow.md)를 참고하세요.

## 실행

```bash
uv sync
export LLM__API_KEY="..."
uv run agentic-game
```

CLI에서 메시지를 입력하면 에이전트가 응답합니다. `exit`, `quit`, `q`, `종료`를 입력하면 종료됩니다.

`.env` 파일로도 설정할 수 있습니다.

```dotenv
LLM__PROVIDER=google
LLM__API_KEY=...
LLM__MODEL=gemini-2.5-flash
LLM__TEMPERATURE=0
LLM__TIMEOUT_SECONDS=30
LLM__MAX_RETRIES=2
UI__APP_NAME=agentic-game
```

OpenAI를 사용할 때는 provider와 model을 바꿉니다.

```dotenv
LLM__PROVIDER=openai
LLM__API_KEY=...
LLM__MODEL=gpt-4.1-mini
```

## 개발 검증

```bash
uv run ruff check src tests
uv run pytest
```
