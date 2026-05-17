from __future__ import annotations

from agentic_game.agent.models import SubgraphName
from agentic_game.agent.nodes.parent import generate_cli_startup_message
from agentic_game.bootstrap import build_agent_graph, get_container
from agentic_game.errors import AgenticGameError

EXIT_COMMANDS = {"exit", "quit", "q", "종료"}


def format_app_error(exc: AgenticGameError) -> str:
    """Convert an application exception into a CLI-safe message."""
    return exc.user_message


def main() -> None:
    """Run the interactive command-line interface."""
    try:
        container = get_container()
    except AgenticGameError as exc:
        raise SystemExit(format_app_error(exc)) from exc

    graph = build_agent_graph(container)
    store_refs: dict[str, str] = {}
    current_subgraph: SubgraphName | None = None

    print(
        generate_cli_startup_message(
            container.llm,
            exit_commands=tuple(sorted(EXIT_COMMANDS)),
        )
    )

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            return

        if not user_input:
            continue

        if user_input.lower() in EXIT_COMMANDS:
            print("종료합니다.")
            return

        try:
            result = graph.invoke(
                {
                    "user_input": user_input,
                    "store_refs": store_refs,
                    "current_subgraph": current_subgraph,
                }
            )
        except AgenticGameError as exc:
            print(format_app_error(exc))
            continue

        store_refs = result.get("store_refs", store_refs)
        current_subgraph = result.get("current_subgraph", current_subgraph)
        print(result.get("response", ""))
