# agentic-game

LangGraph와 LangChain 위에서 사용할 phase/event 기반 agent workflow runtime을 실험하는 프로젝트입니다.

게임은 최종 목적이 아니라 샘플 도메인입니다. battle, craft, trade 같은 게임 시나리오를 통해 여러 업무 도메인에 추출 가능한 패턴을 찾고, 장기적으로는 LangChain/LangGraph와 함께 쓰는 재사용 가능한 workflow 라이브러리로 분리하는 것이 목표입니다.

해결하려는 문제는 LLM agent를 순수 tool-calling loop로 만들면 너무 자유롭고, LangGraph를 직접 쓰면 node, edge, wrapper, persistence, HITL, tool 실행 코드가 도메인마다 반복된다는 점입니다. 이 프로젝트는 그 사이에 있는 spec-driven runtime 계층을 검증합니다.

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

## 문서

- [LLM, Tool, Flow 입문 가이드](docs/llm-tool-flow-guide.md): tool 기반 개발과 LLM 위임 구조가 낯선 사람을 위한 첫 문서
- [용어 사전](docs/glossary.md): scenario, phase, event, flow, ToolBinding 같은 용어 정리
- [State Model](docs/state-model.md): pure/stateless/stateful, state scope, command/query 경계
- [Flow 중심 Scenario 실행](docs/node-flow.md): parent graph, scenario graph, LLM/flow/runtime 경계
- [아키텍처](docs/architecture.md): 폴더 구조, 역할/책임/경계, 의존성 방향, 확장 지점
- [Scenario 상세](docs/scenario-details.md): battle/craft/dialogue 등 현재 게임 샘플별 동작
- [Tool Calling 비교](docs/tool-calling-comparison.md): MCP/tool-calling 패턴과 현재 hybrid runtime 비교

MkDocs로 문서를 볼 수 있습니다.

```bash
uv run --group docs agentic-game-docs serve
```

## 현재 Scenario와 Tool 지원 상태

현재 7개 게임 샘플 시나리오가 같은 `ScenarioNode` graph shape를 사용합니다.

| Scenario | 실행 방식 | 실제 LangChain tool |
| --- | --- | --- |
| battle | usecase-backed tool 실행 + player 저장 | `resolve_battle_tool(action)` |
| craft | category 기반 usecase-backed tool 실행 + inventory 저장 | `craft_item_tool(category, item_name, display_name, requested_effect)` |
| exploration | deterministic execute node + world 저장 | 없음 |
| quest | deterministic execute/response node + quest/player 저장 | 없음 |
| trade | usecase-backed tool 실행 + player/inventory 저장 | `exchange_item_tool(item_id, price)` |
| dialogue | deterministic response 중심 + npc 저장 | 없음 |
| skill_training | deterministic execute node + skill 저장 | 없음 |

즉 일반화된 부분은 `phase/event -> flow -> ScenarioNode -> 공통 LangGraph shape`입니다. battle, craft, trade는 `ToolBinding`을 통해 event와 LangChain tool input을 연결하고 raw/llm/ui payload를 store에 저장합니다. 샘플에서는 battle이 `game/player/latest`에 HP/EXP를 저장하고, craft가 `game/inventory/latest`에 제작 아이템을 저장하며, trade가 player gold와 inventory를 갱신합니다. 다른 업무 도메인에서는 이 위치가 승인 상태, 문서 처리 결과, 티켓 상태, 고객 응대 기록 같은 도메인 상태가 됩니다.

`ActionCard`는 decision prompt에 전달되는 행동 후보입니다. tool-backed action의 `tool_name`, `state_effect`, `risk` metadata는 `ToolBinding`에서 파생됩니다. LLM은 이 정보를 참고해 event를 고르지만 tool을 직접 실행하지 않습니다. runtime이 flow 전이를 검증한 뒤 `ToolBinding`으로 tool input을 만들고 실행합니다.

battle과 craft는 LLM narration도 지원합니다. craft는 `소모품`, `무기`, `방어구`, `장신구`, `도구`, `재료` 같은 일반 제작 범주로 flow를 결정하고, `불꽃 단검` 같은 상세 아이템 이름과 효과 힌트는 LLM `CraftPlan`이 채웁니다. dialogue는 후속 질문을 LLM decision으로 분류해 flow를 움직이지 않고 답할 수 있습니다. 상태 변경은 deterministic usecase와 flow가 확정하고, LLM은 자연어 이해, 후속 질문 응답, 표현/요약/설명을 맡습니다. 이는 다른 도메인에서 “상태 변경은 runtime이 통제하고, 입력 이해와 표현은 LLM이 맡는” 패턴을 검증하기 위한 예시입니다.

## Flow 중심 실행 요약

이 프로젝트는 “업무 흐름”을 중심에 두고, LangGraph는 그 흐름을 실행하는 공통 껍데기로 둡니다.

전투를 예로 들면, `공격한다`는 업무 event이고 `전투 결과를 계산해야 한다`는 다음 업무 phase입니다. 문서 처리 도메인이라면 `업로드한다 -> 분류해야 한다`, 승인 도메인이라면 `제출한다 -> 리뷰해야 한다`로 바뀔 수 있습니다. graph는 scenario마다 새로 설계하지 않고, `ScenarioNode`라는 공통 실행 단계를 사용합니다.

```text
사용자 입력
  -> intent fast-path / LLM decision
       명시적 행동은 빠르게 감지하고, 후속 질문이나 애매한 입력은 LLM이 분류합니다.

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

LLM이 `question`, `clarify`, `smalltalk`으로 분류한 입력은 flow 전이를 만들지 않고 현재 scenario 맥락에서 바로 응답합니다. `action`으로 분류된 입력만 `flow/`의 phase/event transition을 통과합니다.

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
   tool-backed scenario는 tool runner를 통해 usecase를 실행하고 raw/llm/ui 결과를 store에 저장합니다.

6. response
   저장된 실행 결과를 사용자에게 보여줄 응답으로 반환합니다.
```

공통 실행 흐름은 [Flow 중심 Scenario 실행](docs/node-flow.md)를, scenario별 예시는 [Scenario 상세](docs/scenario-details.md)를 참고하세요.

## 구조 요약

```text
src/agentic_game/
  domain/       # 샘플 도메인 데이터, phase/event enum, 순수 도메인 규칙
  flow/         # phase/event transition과 flow helper
  scenarios/    # ScenarioSpec 정의, intent 감지, graph 등록
  engine/       # subgraph 실행, persistence wrapper, tool runner
  application/  # usecase와 port
  agent/        # LangGraph graph/node 조립, prompt, routing
  tools/        # LLM이 호출할 @tool 계층
  inbound/      # CLI, 향후 REST API/UI 같은 interface
  outbound/     # LLM, store, random 등 외부 adapter
  config/       # pydantic-settings 기반 설정
  errors/       # application-level custom exception
```

각 파일의 책임은 다음과 같습니다.

- `flow/`: 업무 규칙을 정의합니다. `PREPARE + ATTACK -> RESOLVE`처럼 phase/event 전이를 다루며 LangGraph node를 모릅니다.
- `scenarios/`: 어떤 도메인 scenario가 있는지, 사용자 입력을 scenario/event로 어떻게 해석하는지, parent graph에 어떤 scenario를 등록하는지 설명합니다.
- `engine/`: subgraph 실행, state persistence, tool 실행처럼 scenario를 실제로 돌리는 공통 실행기를 둡니다.
- `agent/transitions.py`: parent graph edge table입니다. scenario subgraph의 node shape는 `agent/graph/scenario_graph.py`의 공통 graph를 사용합니다.
- `agent/graph/`: `StateGraph`를 만들고 node와 edge table을 조립합니다. node 내부 로직은 알지 않습니다.
- `agent/nodes/`: LangGraph가 호출하는 얇은 실행 단위입니다. state를 읽고 decision/flow/engine에 위임한 뒤 다음 state update를 반환합니다.

`scenarios/` 내부 경계는 다음과 같습니다.

```text
scenarios/
  spec.py          # 공통 ScenarioSpec / ScenarioNode
  definitions.py   # 각 샘플 시나리오의 ScenarioSpec 정의
  registry.py      # parent graph에 concrete scenario 연결
  intent.py        # parent scenario와 scenario event 감지 규칙
```

## 개발 검증

```bash
uv run ruff check src tests
uv run pytest
```
