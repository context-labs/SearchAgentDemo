from __future__ import annotations

import uuid

import typer
from rich.console import Console

from search_agent_example.agent import build_agent
from search_agent_example.config import load_settings
from search_agent_example.search_clients import MockSearchClient
from search_agent_example.tracing import setup_tracing

app = typer.Typer(help="Run the HALO search agent example.")
console = Console()


@app.command()
def run(
    query: str = typer.Argument(..., help="Question or task for the search agent."),
    session_id: str | None = typer.Option(None, help="Stable session ID for trace grouping."),
    user_id: str = typer.Option("demo-user", help="User ID stored on the agent span."),
    max_turns: int = typer.Option(10, min=2, max=20, help="Maximum OpenAI Agents loop turns."),
    mock_search: bool = typer.Option(
        False,
        help="Use deterministic local search results instead of Tavily.",
    ),
) -> None:
    from agents import Runner
    from inference_catalyst_tracing import agent_span

    settings = load_settings()
    tracing = setup_tracing()
    actual_session_id = session_id or f"search-demo-{uuid.uuid4()}"
    search_client = MockSearchClient() if mock_search else None

    try:
        agent, _scratchpad = build_agent(
            settings=settings,
            search_client=search_client,
            tracing=tracing,
            session_id=actual_session_id,
            user_id=user_id,
        )
        with agent_span(
            tracing.tracer,
            agent_id="traceable-search-agent",
            agent_name="Traceable Search Agent",
            span_name="traceable-search-agent.run",
            session_id=actual_session_id,
            user_id=user_id,
            agent_role="search",
            system="openai",
        ) as span:
            span.set_input(query)
            span.set_attribute("demo.dataset", "manual")
            span.set_attribute("search.mock", mock_search)
            result = Runner.run_sync(agent, query, max_turns=max_turns)
            span.set_output(str(result.final_output))

        console.print(result.final_output)
        console.print(f"\n[dim]session_id={actual_session_id}[/dim]")
    finally:
        tracing.shutdown()


if __name__ == "__main__":
    app()
