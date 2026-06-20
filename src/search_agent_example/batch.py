from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from search_agent_example.agent import build_agent
from search_agent_example.config import load_settings
from search_agent_example.search_clients import MockSearchClient
from search_agent_example.tracing import setup_tracing

app = typer.Typer(help="Run dataset queries through the traced search agent.")
console = Console()
DATASET_OPTION = typer.Option(
    Path("data/queries.jsonl"),
    exists=True,
    readable=True,
    help="JSONL dataset of queries.",
)


@app.command()
def run(
    dataset: Path = DATASET_OPTION,
    limit: int = typer.Option(3, min=1, help="Number of dataset rows to execute."),
    start: int = typer.Option(0, min=0, help="Zero-based dataset offset."),
    user_id: str = typer.Option("demo-batch-user", help="User ID stored on traces."),
    max_turns: int = typer.Option(10, min=2, max=20, help="Maximum OpenAI Agents loop turns."),
    mock_search: bool = typer.Option(
        False,
        help="Use deterministic local search results instead of Tavily.",
    ),
) -> None:
    from agents import Runner
    from inference_catalyst_tracing import agent_span

    settings = load_settings()
    rows = load_dataset(dataset)[start : start + limit]
    tracing = setup_tracing()

    try:
        for row in rows:
            session_id = f"dataset-{row['id']}"
            search_client = MockSearchClient() if mock_search else None
            agent, _scratchpad = build_agent(
                settings=settings,
                search_client=search_client,
                tracing=tracing,
                session_id=session_id,
                user_id=user_id,
            )
            with agent_span(
                tracing.tracer,
                agent_id="traceable-search-agent",
                agent_name="Traceable Search Agent",
                span_name="traceable-search-agent.dataset_run",
                session_id=session_id,
                user_id=user_id,
                agent_role="search",
                system="openai",
            ) as span:
                span.set_input(row["query"])
                span.set_attribute("demo.dataset", "queries.jsonl")
                span.set_attribute("demo.query_id", row["id"])
                span.set_attribute("demo.category", row["category"])
                span.set_attribute("search.mock", mock_search)
                result = Runner.run_sync(agent, row["query"], max_turns=max_turns)
                span.set_output(str(result.final_output))

            console.rule(row["id"])
            console.print(result.final_output)
    finally:
        tracing.shutdown()


def load_dataset(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not {"id", "category", "query"} <= row.keys():
            raise ValueError(f"Invalid dataset row at line {line_number}: {row}")
        rows.append(row)
    return rows


if __name__ == "__main__":
    app()
