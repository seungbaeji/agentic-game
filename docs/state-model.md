# State Model

이 문서는 `agentic-game`에서 state를 어디까지 없애고, 어디부터 명시적으로 소유해야 하는지 정리합니다.

핵심 문장은 다음과 같습니다.

```text
Agent runtime은 프로세스 메모리 기준으로 stateless하게 유지한다.
단, 도메인 상태와 scenario 진행 상태는 본질적으로 stateful하며,
StorePort를 통해 scope 단위로 저장하고 복원한다.
```

## Pure, Stateless, Stateful

`stateless`는 "같은 입력이면 항상 같은 출력"과 같은 뜻이 아닙니다. 그 성질은 더 강한 조건인 pure/deterministic에 가깝습니다.

| 개념 | 의미 | 같은 입력이면 같은 출력인가 |
| --- | --- | --- |
| Pure / deterministic | 외부 IO, store, random, time, LLM을 보지 않는 순수 계산 | 예 |
| Stateless | 객체나 프로세스가 호출 사이의 상태를 자기 메모리에 보관하지 않음 | 외부 state를 읽으면 아닐 수 있음 |
| Stateful | 이전 호출의 상태가 다음 호출에 영향을 줌 | 보통 아님 |

예:

```python
apply_player_delta(PlayerState(hp=100), hp_change=-10)
```

이 함수는 pure/deterministic입니다. 같은 `PlayerState`와 delta를 넣으면 항상 같은 결과를 반환합니다.

반면 다음 함수는 내부 상태를 들고 있지 않으므로 stateless하지만, store의 현재 값에 따라 결과가 달라질 수 있습니다.

```python
def get_player_status(repo: GameStateRepository) -> PlayerState:
    return repo.load_player()
```

서버나 application service에서 말하는 stateless는 보통 "session state를 process memory에 들고 있지 않다"는 뜻입니다. DB, store, LLM, random을 읽는 순간 pure/deterministic은 아닙니다.

## State Categories

이 프로젝트에는 서로 다른 종류의 state가 있습니다.

| 종류 | 예 | 소유 경계 |
| --- | --- | --- |
| Workflow state | `phase`, `event`, `current_subgraph` | agent/engine이 전달하고 engine이 저장 |
| Domain state | player HP, inventory, quest log, NPC memory | application repository와 store |
| Runtime-only state | `next_node` | LangGraph 실행 중에만 사용 |
| Tool payload state | raw/llm/ui result, history | engine/tool runner와 store |
| Session scope | `session_id`, future `user_id`, `tenant_id` | inbound/API/CLI 경계 |

`phase`는 workflow 진행 위치입니다. `PlayerState.hp`나 `InventoryState.items` 같은 도메인 상태와 다릅니다.

`next_node`는 routing에만 필요합니다. 다음 입력까지 보존해야 하는 업무 상태가 아니므로 store에 저장하면 안 됩니다.

## Layer Ownership

레이어별 state 원칙은 다음과 같습니다.

| 레이어 | state 모델 |
| --- | --- |
| `domain/` | pure/deterministic. 외부 IO와 저장소를 알지 않음 |
| `flow/` | stateless transition definition. phase/event 규칙만 표현 |
| `scenarios/` | stateless metadata. scenario spec과 registry |
| `agent/` | stateless transformer. input state를 읽고 output update를 반환 |
| `engine/` | state orchestration. scenario state load/save, tool result persistence |
| `application/` | command/query usecase. repository port로 state read/write |
| `tools/` | application usecase를 tool interface로 노출 |
| `outbound/` | physical state adapter. store, LLM, random 구현 |
| `inbound/` | session boundary. CLI loop, future API request/session 처리 |

목표는 모든 것을 stateless로 만드는 것이 아닙니다. 상태가 필요한 부분을 `engine`, `application`, `outbound`, `inbound` 경계로 몰아넣고, 안쪽 규칙과 graph transformer는 가능한 한 작고 예측 가능하게 유지하는 것입니다.

## Usecase And CQRS

Usecase는 항상 pure해야 하는 것이 아닙니다.

더 정확한 규칙은 다음과 같습니다.

```text
Usecase object는 호출 사이의 mutable state를 보유하지 않는다.
Usecase execution은 repository/port를 통해 state를 읽거나 쓸 수 있다.
```

CQRS 관점에서는 command와 query를 나눕니다.

| 종류 | 책임 | 예 |
| --- | --- | --- |
| Command | 상태 변경 | battle 결과로 player HP/EXP 갱신 |
| Query | 상태 조회 | 현재 player status 조회 |

Command usecase는 stateful operation입니다. repository에서 현재 상태를 읽고, domain rule을 적용하고, 변경된 상태를 저장합니다. 하지만 command handler 자체가 세션 상태를 필드에 들고 있으면 안 됩니다.

Query usecase는 상태를 읽지만 변경하지 않습니다. store를 읽기 때문에 pure는 아니지만 side effect는 없어야 합니다.

현재 구조에서는 `application/usecases/` 아래에 command 성격의 함수가 섞여 있습니다. 규모가 커지면 다음처럼 나누는 것이 자연스럽습니다.

```text
application/
  commands/
    resolve_battle_action.py
    craft_item.py
    exchange_item.py
  queries/
    get_player_status.py
    get_latest_result.py
  repositories/
    game_state.py
```

처음부터 read model까지 분리할 필요는 없습니다. 다만 "상태를 바꾸는가, 읽기만 하는가"는 usecase 이름과 테스트에서 명확해야 합니다.

## Store Scope

stateful boundary에서 가장 중요한 개념은 scope입니다.

현재 샘플은 단일 CLI process를 기준으로 동작하므로 다음 namespace를 사용합니다.

```text
game / player / latest
craft / state / latest
battle / resolve / raw / latest
```

이 구조는 단일 세션에서는 단순하지만, API나 멀티 유저 환경에서는 session 간 state가 섞입니다. persistent/shared store를 쓰려면 namespace 앞에 scope가 있어야 합니다.

예:

```text
tenant / <tenant_id> / session / <session_id> / game / player / latest
tenant / <tenant_id> / session / <session_id> / craft / state / latest
```

`latest`는 전역 latest가 아니라 scope 안의 latest여야 합니다.

권장 방향은 `StoreScope`와 `ScopedStore`를 두는 것입니다.

```python
@dataclass(frozen=True)
class StoreScope:
    tenant_id: str
    session_id: str


class ScopedStore:
    def __init__(self, inner: StorePort, scope: StoreScope) -> None:
        self._inner = inner
        self._scope = scope

    def put(self, *, namespace, key, value):
        return self._inner.put(
            namespace=(
                "tenant",
                self._scope.tenant_id,
                "session",
                self._scope.session_id,
                *namespace,
            ),
            key=key,
            value=value,
        )
```

이렇게 하면 `GameStateRepository`와 engine wrapper는 기존 namespace를 유지하면서도, 실제 저장소에서는 session별로 격리됩니다.

## Runtime State Persistence

Scenario wrapper는 subgraph 실행 전후로 state를 load/save합니다.

```text
parent state
  -> load saved scenario state
  -> inject user_input / human_input
  -> subgraph invoke
  -> remove runtime-only keys
  -> save scenario state
  -> return parent update
```

tool-backed scenario는 tool result를 payload 종류별로 저장합니다.

```text
<scope> / <scenario> / <phase> / raw / latest
<scope> / <scenario> / <phase> / llm / latest
<scope> / <scenario> / <phase> / ui / latest
<scope> / <scenario> / <phase> / raw / history / <id>
```

Graph state에는 큰 payload를 넣지 않고 ref만 남깁니다.

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

이 ref는 graph state를 작게 유지하기 위한 pointer입니다. source of truth는 store에 있습니다.

## Idempotency And Concurrency

CLI 샘플에서는 동시 실행과 재시도 문제가 작습니다. API로 확장하면 command id와 동시성 제어가 필요해집니다.

### Idempotency

같은 command가 재시도되어도 상태 변경이 중복 적용되지 않아야 합니다.

예:

```text
같은 battle command가 네트워크 재시도로 두 번 들어옴
-> EXP가 두 번 오르면 안 됨
```

이 경우 inbound에서 `command_id`를 받고, command 처리 결과를 scope 안에 기록하는 방식이 필요합니다.

### Concurrency

동시에 여러 요청이 같은 domain state를 바꾸면 lost update가 생길 수 있습니다.

예:

```text
request A: player gold 100 읽음
request B: player gold 100 읽음
A가 -30 저장
B가 -50 저장
```

DB adapter를 붙일 때는 optimistic lock, transaction, compare-and-swap, append-only event log 같은 전략 중 하나를 선택해야 합니다.

현재 `history` key를 `len(history) + 1`로 만드는 방식은 concurrent write에 약합니다. API 환경에서는 store-generated id나 append-safe key를 쓰는 편이 낫습니다.

## Unit Of Work

하나의 command가 여러 state를 바꾸면 Unit of Work 경계가 필요해집니다.

예:

```text
trade command
  -> player gold 감소
  -> inventory item 증가
  -> tool raw/llm/ui history 저장
```

이 중 일부만 성공하면 state가 깨집니다. DB 기반 store로 갈 때는 command usecase나 engine 실행 경계에서 transaction을 묶어야 합니다.

처음에는 `StorePort`만으로 충분할 수 있지만, 여러 aggregate를 함께 갱신하는 command가 늘어나면 다음 형태를 고려합니다.

```text
with unit_of_work:
    player = repo.load_player()
    inventory = repo.load_inventory()
    repo.save_player(updated_player)
    repo.save_inventory(updated_inventory)
    unit_of_work.commit()
```

## Design Rule

이 프로젝트의 state 설계 규칙은 다음과 같습니다.

1. `domain/`은 pure하게 유지한다.
2. `flow/`는 phase/event transition만 표현한다.
3. `agent/` node는 input state를 받아 state update를 반환하는 transformer로 둔다.
4. scenario state load/save는 `engine/`으로 모은다.
5. domain state read/write는 `application` repository port로 모은다.
6. physical persistence는 `outbound/store` adapter가 맡는다.
7. inbound layer는 session scope를 결정한다.
8. `latest`는 반드시 scope 안의 latest여야 한다.
9. command는 idempotency와 transaction 경계를 고려한다.

즉, 목표는 "state를 없애는 것"이 아니라 "state가 어디에 있고 누구에게 속하는지 명확히 하는 것"입니다.
