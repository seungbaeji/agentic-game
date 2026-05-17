# Tool Calling Architecture Comparison

이 문서는 현재 `agentic-game`의 tool 실행 방식이 일반적인 MCP/tool-calling 패턴과 어떻게 다른지, 그리고 state-changing workflow 도메인에서 어떤 절충이 적절한지 정리합니다.

게임은 이 프로젝트의 샘플 도메인입니다. 최종 목표는 게임 전용 framework가 아니라, LangChain/LangGraph 위에서 사용할 수 있는 도메인 독립 phase/event workflow runtime을 추출하는 것입니다.

## 결론

현재 프로젝트는 완전한 autonomous tool-calling agent가 아닙니다.

현재 구조는 다음에 가깝습니다.

```text
LLM-assisted event workflow
phase/event driven workflow runtime
governed tool execution
```

즉 LLM이 직접 tool과 args를 모두 결정하기보다, LLM은 사용자의 의도를 event로 해석하고 runtime이 flow와 `ToolBinding`을 통해 실행을 통제합니다.

이 방향은 MCP나 LangGraph의 일반적인 agent loop와 다르지만, 상태 변경이 중요한 workflow 도메인에서는 합리적인 선택입니다. 승인 상태, 문서 처리 단계, 티켓 escalation, 환불 처리, inventory 변경 같은 side effect는 LLM이 자유롭게 만들기보다 deterministic rule과 runtime guard가 관리해야 하기 때문입니다.

## 일반적인 MCP / Tool Calling 패턴

일반적인 MCP 또는 LangGraph tool-calling agent는 보통 다음 흐름을 가집니다.

```text
LLM
  -> available tools를 본다
  -> 필요한 tool을 고른다
  -> tool args를 직접 만든다
  -> tool runtime이 실행한다
  -> tool result를 보고 다음 응답이나 다음 tool call을 결정한다
```

LangGraph의 `ToolNode` / `tools_condition` 예제는 이 패턴에 가깝습니다.

```text
LLM node
  -> tool call이 있으면 ToolNode
  -> tool result
  -> 다시 LLM node
  -> 최종 응답 또는 추가 tool call
```

이 방식은 다음에 적합합니다.

- 검색, 질의, 문서 조회
- 계산, 요약, 변환
- 외부 API 호출
- 목표가 열려 있고 해결 경로가 예측하기 어려운 작업

하지만 상태 변경이 중요한 도메인에서는 위험도 있습니다.

- LLM이 잘못된 tool을 고를 수 있다.
- tool args를 hallucinate할 수 있다.
- 실제 시스템 상태와 LLM의 mental model이 달라질 수 있다.
- 부분 실패, 재시도, 중복 실행, 권한 확인이 어려워진다.

## MCP는 Protocol이지 Runtime Policy가 아니다

MCP는 tool, resource, prompt를 표준 방식으로 노출하는 protocol입니다.

MCP가 제공하는 큰 축은 다음과 같습니다.

- `Tools`: AI model이 실행할 수 있는 함수
- `Resources`: 사용자나 model이 참고할 수 있는 context/data
- `Prompts`: 재사용 가능한 prompt/workflow template
- `Sampling`: server가 client에게 LLM 생성을 요청하는 기능
- `Roots`: client가 server에 작업 가능한 filesystem boundary를 알려주는 기능
- `Elicitation`: server가 사용자에게 추가 입력을 요청하는 기능

중요한 점은 MCP 자체가 “모든 tool을 LLM이 자유롭게 실행해야 한다”고 강제하지 않는다는 것입니다. 오히려 MCP specification은 tool safety, user consent, data privacy를 별도 원칙으로 둡니다.

따라서 MCP를 쓴다고 해서 반드시 다음처럼 만들어야 하는 것은 아닙니다.

```text
LLM decides everything
```

MCP를 쓰더라도 product runtime은 다음을 둘 수 있습니다.

```text
permission
phase guard
schema validation
approval
audit
state persistence
```

## 현재 프로젝트의 패턴

현재 `agentic-game`은 다음 흐름을 사용합니다.

```text
사용자 입력
  -> parent/scenario decision
  -> Event 선택
  -> flow transition 검증
  -> ScenarioSpec.phase_to_node
  -> ScenarioNode.EXECUTE
  -> ToolBinding lookup
  -> hydrated tool invoke
  -> raw/llm/ui payload 저장
  -> domain state 저장
```

LLM이 직접 고르는 것은 주로 event입니다. 게임 샘플에서는 다음처럼 보입니다.

```text
"몬스터를 공격할게"
  -> BattleEvent.ATTACK
```

runtime이 통제하는 것은 실행입니다.

```text
BattleEvent.ATTACK
  -> BATTLE_TOOL_BINDINGS
  -> resolve_battle_tool(action="attack")
  -> resolve_battle_action_and_store_player
  -> game/player/latest
```

다른 도메인에서는 같은 구조가 다음처럼 바뀝니다.

```text
ApprovalEvent.APPROVE
  -> APPROVAL_TOOL_BINDINGS
  -> approve_request_tool(request_id="...")
  -> approve_request
  -> approval/request/latest
```

이 구조에서 `ActionCard`와 `ToolBinding`은 역할이 다릅니다.

```text
ActionCard
  LLM에게 보여주는 행동 후보
  event, label, description, tool metadata

ToolBinding
  runtime이 실행에 쓰는 계약
  event, tool_name, tool_input, state_effect, risk
```

`ActionCard`는 tool을 실행하지 않습니다. tool-backed action의 metadata는 `ToolBinding`에서 파생되고, 최종 실행은 flow 검증 이후 runtime이 수행합니다.

## 유사 프로젝트 비교

| 프로젝트 / 패턴 | 핵심 방식 | 현재 프로젝트와의 관계 |
| --- | --- | --- |
| LangGraph agent loop | LLM이 tool call을 만들고 `ToolNode`가 실행한다. | 더 autonomous하다. 우리 구조보다 LLM 자유도가 높다. |
| LangGraph workflow | `StateGraph` node/edge가 흐름을 통제한다. | 현재 구조와 가깝다. |
| MCP 일반 구조 | server가 tools/resources/prompts를 노출한다. | protocol layer로 참고 가능하지만 runtime 정책은 별도 설계가 필요하다. |
| MCP Sampling | server가 client LLM에게 tool-enabled sampling을 요청할 수 있다. | 향후 LLM-assisted input builder에 참고할 수 있다. |
| `llmstatemachine` | state마다 허용 action을 제한한다. | phase별 action 제한이라는 점에서 유사하다. |
| Stately agent | state machine으로 agent decision을 guide한다. | state transition과 observation 중심이라는 점에서 유사하다. |
| Loop Engine | FSM, guard, audit trail로 AI 실행을 통제한다. | state-changing action을 runtime guard로 통제하는 관점이 유사하다. |
| Voyager | LLM이 Minecraft에서 code skill을 만들고 축적한다. | 훨씬 자유도가 높은 game agent다. 샘플 도메인 관점에서는 참고 사례지만, 이 프로젝트의 목표인 governed workflow runtime과는 다르다. |
| econagents | game server event 기반으로 state를 관리한다. | event-driven state management 관점에서 현재 구조와 가깝다. |

## State-Changing Workflow에서의 판단

이 프로젝트가 다루려는 핵심 문제는 게임에만 있지 않습니다. 여러 업무 도메인에는 LLM이 자유롭게 바꾸면 안 되는 상태가 있습니다.

| 도메인 | 통제해야 하는 상태 |
| --- | --- |
| Game sample | HP, EXP, gold, inventory, quest progress |
| Document processing | upload status, classification, extraction result, review status |
| Approval workflow | draft, reviewer assignment, approve/reject decision, audit record |
| Customer support | ticket status, escalation state, response history |
| Operational change | change request status, approval gate, rollout state |
| Accounting workflow | document category, validation result, posting status |

이 값들은 LLM이 자유롭게 결정하면 안 됩니다.

게임 샘플에서는 다음이 위험합니다.

```text
LLM -> exchange_item_tool(item_id="legendary_sword", price=1)
```

또는:

```text
LLM -> add_inventory(item_id="potion", quantity=999)
```

다른 도메인에서도 같은 문제가 생깁니다.

```text
LLM -> approve_request_tool(request_id="wrong-request")
LLM -> refund_customer_tool(amount=999999)
LLM -> mark_document_complete_tool(extraction_confidence="made-up")
```

따라서 workflow runtime에서는 다음 구분이 필요합니다.

| 영역 | LLM 자유도 | 이유 |
| --- | --- | --- |
| intent/event 선택 | 중간 | 자연어 입력 해석은 LLM이 잘한다. |
| narration/flavor | 높음 | 상태 변경이 없고 다양성이 중요하다. |
| read/query tool | 높음 | 조회는 side effect가 작다. |
| state-changing tool | 낮음 | 업무 규칙, 권한, 감사 가능성이 중요하다. |
| persistence | 낮음 | source of truth는 runtime이어야 한다. |
| phase transition | 낮음 | 허용되지 않은 진행을 막아야 한다. |

## 추천 Hybrid 구조

현재 방향을 완전히 MCP식 autonomous tool loop로 바꾸기보다, hybrid 구조로 가는 것이 좋습니다.

```text
LLM
  -> event 제안
  -> 필요하면 tool args 초안 제안

Runtime
  -> phase guard
  -> allowed event 검증
  -> ToolBinding 선택
  -> input builder 실행
  -> schema/domain validation
  -> tool 실행
  -> state persistence
  -> audit/payload 저장
```

즉 다음처럼 확장합니다.

```python
ToolBinding(
    event=TradeEvent.ACCEPT_PRICE,
    tool_name="exchange_item_tool",
    build_input=build_trade_input,
    validate_input=validate_trade_input,
    risk="state_change",
)
```

여기서 `build_input`은 여러 source를 사용할 수 있습니다.

```text
current phase
current event
user_input
stored domain state
latest tool payload
optional LLM extraction
```

하지만 최종 tool input은 반드시 runtime validation을 통과해야 합니다.

## Tool 종류별 권장 정책

| Tool 종류 | 예시 | 권장 실행 방식 |
| --- | --- | --- |
| read/query tool | inventory 조회, 문서 조회, 티켓 조회 | LLM 직접 호출 허용 가능 |
| deterministic mutation tool | 승인 처리, 거래 실행, 문서 상태 확정 | `ToolBinding` + runtime validation 필수 |
| content generation tool | 결과 설명, 응답 문장, 요약 | LLM 자유도 높게 허용 |
| planning tool | 다음 단계 추천, 후보 action 생성 | LLM 사용 가능, 실행은 별도 검증 |
| admin/debug tool | store reset, state override | 일반 agent에게 노출하지 않음 |

## 현재 프로젝트에 적용할 다음 단계

현재는 게임 샘플 중 battle/craft/trade가 `ToolBinding` 기반 tool-backed scenario입니다. 이들은 라이브러리 추출을 위한 reference implementation입니다.

다음 단계는 `ToolBinding`을 더 유연하게 만드는 것입니다.

1. `ToolBinding.tool_input`을 고정 dict만 받지 않게 한다.
2. `build_input(state, store, user_input)` 같은 callable을 허용한다.
3. read-only tool과 state-changing tool을 구분한다.
4. state-changing tool은 phase/event validation을 통과한 뒤에만 실행한다.
5. LLM이 제안한 args는 그대로 믿지 않고 domain validator를 통과시킨다.
6. tool result는 raw/llm/ui payload와 domain state를 분리해서 저장한다.
7. 향후 MCP를 붙이더라도 MCP server는 tool transport이고, workflow runtime policy는 이 프로젝트 안에 둔다.

## 선택 기준

앞으로 새 기능을 추가할 때는 다음 기준을 사용합니다.

LLM에게 맡겨도 되는가?

- 실패해도 상태가 망가지지 않는다.
- 결과가 표현이나 추천에 가깝다.
- 여러 답이 가능하다.
- 자연어 해석이 핵심이다.

runtime이 통제해야 하는가?

- domain state가 바뀐다.
- 승인, 결재, 환불, 게시, 완료 처리처럼 side effect가 있다.
- 중복 실행이 문제가 된다.
- 권한이나 phase guard가 필요하다.
- 테스트에서 deterministic하게 검증해야 한다.

이 기준을 따르면 프로젝트는 MCP/tool-calling 생태계와 어긋나지 않으면서도, 상태 변경 workflow에 필요한 규칙성, 감사 가능성, 재현성을 유지할 수 있습니다.

## References

- LangGraph Workflows and Agents: https://docs.langchain.com/oss/python/langgraph/workflows-agents
- LangChain Tools and ToolNode: https://docs.langchain.com/oss/python/langchain/tools
- Model Context Protocol Specification: https://modelcontextprotocol.io/specification/2025-11-25
- MCP Sampling: https://modelcontextprotocol.io/specification/draft/client/sampling
- robocorp/llmstatemachine: https://github.com/robocorp/llmstatemachine
- Stately Agent: https://github.com/statelyai/agent
- Loop Engine: https://www.loopengine.io/
- Voyager: https://arxiv.org/abs/2305.16291
- econagents: https://econagents.readthedocs.io/en/latest/
