# agentic-game

`agentic-game`은 LangGraph와 LangChain 위에서 사용할 phase/event 기반 agent workflow runtime을 게임 샘플로 검증하는 프로젝트입니다.

게임은 최종 목적이 아니라 샘플 도메인입니다. 이 문서는 코드 구조를 빠르게 파악하고, business flow가 공통 scenario graph를 어떻게 이끄는지, 그리고 이 패턴을 다른 업무 도메인으로 어떻게 추출할 수 있는지 이해하기 위한 가이드입니다.

## 먼저 읽을 순서

처음 보는 사람은 아래 순서로 읽는 것이 가장 덜 헷갈립니다.

1. [LLM, Tool, Flow 입문 가이드](llm-tool-flow-guide.md)
   LLM에게 맡기는 일과 runtime이 통제하는 일을 먼저 구분합니다.

2. [Glossary](glossary.md)
   scenario, phase, event, flow, ToolBinding 같은 용어를 짧게 확인합니다.

3. [State Model](state-model.md)
   pure/stateless/stateful, command/query, state scope 같은 상태 경계를 먼저 잡습니다.

4. [Flow-Centered Scenario Execution](node-flow.md)
   사용자 입력이 parent graph와 scenario graph를 거쳐 어떻게 실행되는지 봅니다.

5. [Architecture](architecture.md)
   폴더별 책임과 의존성 방향을 봅니다.

6. [Scenario Details](scenario-details.md)
   battle, craft, dialogue 같은 게임 샘플이 공통 구조를 어떻게 쓰는지 봅니다.

7. [Tool Calling Architecture Comparison](tool-calling-comparison.md)
   일반 tool-calling agent와 이 프로젝트의 guarded workflow 방식 차이를 봅니다.

## 문서별 책임

| 문서 | 책임 |
| --- | --- |
| [LLM, Tool, Flow 입문 가이드](llm-tool-flow-guide.md) | 처음 읽는 사람을 위한 배경과 mental model |
| [Glossary](glossary.md) | 용어 사전 |
| [State Model](state-model.md) | pure/stateless/stateful, state scope, command/query 경계 |
| [Flow-Centered Scenario Execution](node-flow.md) | runtime 실행 순서 |
| [Architecture](architecture.md) | 패키지 경계, 의존성 방향, 확장 규칙 |
| [Scenario Details](scenario-details.md) | 현재 게임 scenario별 동작 |
| [Tool Calling Architecture Comparison](tool-calling-comparison.md) | tool-calling 방식과 현재 hybrid 방식 비교 |

## 코드 지도

```text
src/agentic_game/
  domain/       # 순수 비즈니스 데이터와 규칙
  flow/         # 업무 phase/event transition
  scenarios/    # ScenarioSpec, intent 감지, scenario 등록
  engine/       # subgraph 실행과 tool runner
  application/  # usecase와 port
  agent/        # LangGraph graph/node 조립
  tools/        # LLM tool layer
  inbound/      # CLI, REST API, UI 같은 interface
  outbound/     # LLM, store, random adapter
  config/       # pydantic-settings 기반 설정
  errors/       # application-level custom exception
```

## 현재 범위

7개 게임 샘플 시나리오가 공통 scenario graph shape를 사용합니다.

| Scenario | 실행 방식 |
| --- | --- |
| battle | LangChain tool + usecase + player 저장 |
| craft | LangChain tool + usecase + inventory 저장 |
| exploration | deterministic execute node + world 저장 |
| quest | deterministic execute/response node + quest/player 저장 |
| trade | LangChain tool + usecase + player/inventory 저장 |
| dialogue | deterministic response 중심 + npc 저장 |
| skill_training | deterministic execute node + skill 저장 |

현재 실제 `@tool` 계층과 raw/llm/ui payload 저장은 battle/craft/trade에 있습니다. 이 시나리오들은 `ToolBinding`으로 event와 tool input을 연결합니다. 샘플에서는 player, inventory, quest, world 같은 game state를 저장하지만, 라이브러리로 추출할 때는 문서 처리 상태, 승인 상태, 고객지원 티켓, 운영 변경 요청 같은 도메인 상태로 바뀔 수 있습니다.

LLM 활용은 battle/craft/dialogue에 적용되어 있습니다. 상태 변경은 usecase와 flow가 확정하고, LLM은 의도 분류, 상세 계획, 후속 질문, 응답 문장 생성에 사용됩니다. 이는 state-changing workflow에서 LLM 자유도와 deterministic runtime control을 분리하기 위한 예시입니다.

## 실행

```bash
uv sync
uv run agentic-game
```

문서 서버는 다음 명령으로 실행합니다.

```bash
uv run --group docs agentic-game-docs serve
```
