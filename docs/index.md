# agentic-game

`agentic-game`은 LangGraph 기반 게임 시나리오 에이전트입니다.

이 문서는 코드 구조를 빠르게 파악하고, business flow가 공통 scenario graph를 어떻게 이끄는지 이해하기 위한 가이드입니다.

## 문서 구성

- [Architecture](architecture.md): 폴더 구조, 역할/책임/경계, 의존성 방향, 확장 지점
- [Flow-Centered Scenario Execution](node-flow.md): parent graph, scenario flow, 공통 graph 실행 방식

## 핵심 구조

```text
src/agentic_game/
  domain/       # 순수 비즈니스 데이터와 규칙
  flow/         # 업무 phase/event transition
  scenarios/    # ScenarioSpec, intent, parent routing, scenario 등록
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

7개 게임 시나리오가 공통 scenario graph shape를 사용합니다.

| Scenario | 실행 방식 |
| --- | --- |
| battle | LangChain tool + usecase |
| craft | LangChain tool + usecase + inventory 저장 |
| exploration | deterministic execute node |
| quest | deterministic execute node |
| trade | deterministic execute node |
| dialogue | deterministic response 중심 |
| skill_training | deterministic execute node + skill 저장 |

현재 실제 `@tool` 계층과 raw/llm/ui payload 저장은 battle/craft에만 있습니다. craft는 성공한 제작 결과를 `game/inventory/latest`에도 반영하고, skill_training은 `game/skills/latest`에 스킬 성장 상태를 반영합니다. 나머지 시나리오는 flow 일반화와 graph shape 검증을 위한 lightweight 구현입니다.

## 실행

```bash
uv sync
uv run agentic-game
```

문서 서버는 다음 명령으로 실행합니다.

```bash
uv run --group docs agentic-game-docs serve
```
