from __future__ import annotations

from typing import Any

from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel

from search_agent_example.config import Settings
from search_agent_example.models import Scratchpad
from search_agent_example.search_clients import (
    MockSearchClient,
    SearchClient,
    TavilySearchClient,
)
from search_agent_example.tools import build_tools

AGENT_INSTRUCTIONS = """
You are TraceableSearchAgent, a compact web-search agent built for HALO trace analysis.

Operating loop:
1. Write a short plan to scratchpad_write before searching.
2. Use one or two focused web_search calls. Avoid broad repeated searches.
3. Assess one to three high-value sources with assess_source.
4. Extract one page when a snippet is not enough to support a claim.
5. Use scratchpad_read before the final answer if you wrote more than one note.
6. Prefer a useful final answer over exhausting the turn budget.

Final answer requirements:
- Give a concise answer first.
- Include a "Sources consulted" section with source titles or URLs.
- Include an "Uncertainties" section when evidence is thin, stale, or conflicting.
- Do not claim certainty from snippets alone.

Known rough edges for HALO:
- Source quality is heuristic and can be wrong.
- The scratchpad is unstructured and can accumulate stale notes.
- There is no enforced final response schema.
- Date handling is mostly delegated to the model.
""".strip()


def build_agent(
    settings: Settings,
    search_client: SearchClient | None = None,
    tracing: Any | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
) -> tuple[Agent, Scratchpad]:
    scratchpad = Scratchpad()
    if search_client is None:
        if not settings.tavily_api_key:
            search_client = MockSearchClient()
        else:
            search_client = TavilySearchClient(
                api_key=settings.tavily_api_key,
                session_id=session_id,
                human_id=user_id,
            )

    tools = build_tools(
        search_client=search_client,
        scratchpad=scratchpad,
        tracing=tracing,
        max_tool_results=settings.max_tool_results,
        max_extract_chars=settings.max_extract_chars,
    )

    agent = Agent(
        name="TraceableSearchAgent",
        instructions=AGENT_INSTRUCTIONS,
        model=LitellmModel(
            model=settings.litellm_model_id,
            api_key=settings.litellm_api_key,
            base_url=settings.litellm_base_url,
        ),
        tools=tools,
    )
    return agent, scratchpad


def run_agent_sync(
    query: str,
    settings: Settings,
    tracing: Any | None,
    search_client: SearchClient | None = None,
    max_turns: int = 10,
    session_id: str = "local-session",
    user_id: str = "demo-user",
) -> str:
    agent, _scratchpad = build_agent(
        settings=settings,
        search_client=search_client,
        tracing=tracing,
        session_id=session_id,
        user_id=user_id,
    )
    result = Runner.run_sync(agent, query, max_turns=max_turns)
    return str(result.final_output)
