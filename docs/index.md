# agentic-game

`agentic-game`은 LangGraph와 LangChain 위에서 사용할 phase/event 기반 agent workflow runtime을 게임 샘플로 검증하는 프로젝트입니다.

게임은 최종 목적이 아니라 샘플 도메인입니다. 이 문서는 코드 구조를 빠르게 파악하고, business flow가 공통 scenario graph를 어떻게 이끄는지, 그리고 이 패턴을 다른 업무 도메인으로 어떻게 추출할 수 있는지 이해하기 위한 가이드입니다.

## 문서 구성

- [Architecture](architecture.md): 폴더 구조, 역할/책임/경계, 의존성 방향, 확장 지점
- [Flow-Centered Scenario Execution](node-flow.md): parent graph, scenario flow, 공통 graph 실행 방식
- [Tool Calling Architecture Comparison](tool-calling-comparison.md): MCP/tool-calling 패턴과 현재 hybrid runtime 비교

## 핵심 구조

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

LLM 다양성은 battle/craft에 적용되어 있습니다. 상태 변경은 usecase가 확정하고, LLM은 확정된 결과의 응답 문장만 변주합니다. 이는 state-changing workflow에서 LLM 자유도와 deterministic runtime control을 분리하기 위한 예시입니다.

## 실행

```bash
uv sync
uv run agentic-game
```

문서 서버는 다음 명령으로 실행합니다.

```bash
uv run --group docs agentic-game-docs serve
```
