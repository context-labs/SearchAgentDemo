from __future__ import annotations

import asyncio
import json

from agents.tool_context import ToolContext

from search_agent_example.models import Scratchpad
from search_agent_example.search_clients import MockSearchClient
from search_agent_example.tools import build_tools


def _tool_by_name(tools: list, name: str):
    return next(tool for tool in tools if tool.name == name)


def _invoke(tool, payload: str) -> str:
    context = ToolContext(
        context=None,
        tool_name=tool.name,
        tool_call_id=f"call-{tool.name}",
        tool_arguments=payload,
    )
    return asyncio.run(tool.on_invoke_tool(context, payload))


def test_mock_search_client_is_deterministic() -> None:
    client = MockSearchClient()
    first = client.search("test query", max_results=2)
    second = client.search("test query", max_results=2)
    assert first == second
    assert len(first["results"]) == 2


def test_scratchpad_tool_writes_and_reads() -> None:
    scratchpad = Scratchpad()
    tools = build_tools(MockSearchClient(), scratchpad, tracing=None)
    write_tool = _tool_by_name(tools, "scratchpad_write")
    read_tool = _tool_by_name(tools, "scratchpad_read")

    write_result = json.loads(_invoke(write_tool, '{"note":"check dates","label":"plan"}'))
    read_result = json.loads(_invoke(read_tool, '{"limit":5}'))

    assert write_result["ok"] is True
    assert read_result["notes"][0]["note"] == "check dates"


def test_source_assessment_penalizes_blog() -> None:
    tools = build_tools(MockSearchClient(), Scratchpad(), tracing=None)
    assess_tool = _tool_by_name(tools, "assess_source")
    result = json.loads(
        _invoke(
            assess_tool,
            json.dumps(
                {
                    "url": "https://vendor.example.com/blog/post",
                    "title": "Vendor view",
                    "snippet": "A sponsored post",
                }
            ),
        )
    )
    assert result["quality_score"] < 0.45
