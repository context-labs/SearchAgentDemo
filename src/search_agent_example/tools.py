from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from agents import function_tool

from search_agent_example.models import Scratchpad
from search_agent_example.search_clients import SearchClient
from search_agent_example.tracing import maybe_manual_span


def build_tools(
    search_client: SearchClient,
    scratchpad: Scratchpad,
    tracing: Any | None,
    max_tool_results: int = 5,
    max_extract_chars: int = 6000,
) -> list:
    @function_tool
    def scratchpad_write(note: str, label: str = "note") -> str:
        """Store a short planning note, source observation, or uncertainty for this run."""
        entry = scratchpad.write(note=note, label=label)
        return json.dumps({"ok": True, "entry": entry, "total_notes": len(scratchpad.notes)})

    @function_tool
    def scratchpad_read(limit: int = 10) -> str:
        """Read recent notes written to the scratchpad during this run."""
        return json.dumps({"notes": scratchpad.read(limit)})

    @function_tool
    def web_search(
        query: str,
        max_results: int = 5,
        include_answer: bool = False,
        topic: str = "general",
    ) -> str:
        """Search the web for sources. Use sparingly and prefer focused queries."""
        capped_results = min(max(1, max_results), max_tool_results)
        with maybe_manual_span(
            tracing,
            name="tavily.search",
            span_kind_name="RETRIEVER",
            input_payload={
                "query": query,
                "max_results": capped_results,
                "include_answer": include_answer,
                "topic": topic,
            },
        ) as span:
            response = search_client.search(
                query=query,
                max_results=capped_results,
                include_answer=include_answer,
                topic=topic,
            )
            if span:
                span.set_output(
                    {
                        "result_count": len(response.get("results", [])),
                        "urls": [item.get("url") for item in response.get("results", [])],
                    }
                )
        return json.dumps(response)

    @function_tool
    def extract_page(url: str, query: str | None = None) -> str:
        """Extract readable content from a URL returned by search."""
        with maybe_manual_span(
            tracing,
            name="tavily.extract",
            span_kind_name="RETRIEVER",
            input_payload={"url": url, "query": query, "max_chars": max_extract_chars},
        ) as span:
            response = search_client.extract(url=url, query=query, max_chars=max_extract_chars)
            if span:
                span.set_output(
                    {
                        "url": response.get("url"),
                        "content_chars": len(str(response.get("raw_content", ""))),
                        "truncated": response.get("truncated"),
                    }
                )
        return json.dumps(response)

    @function_tool
    def assess_source(url: str, title: str = "", snippet: str = "") -> str:
        """Apply a simple source-quality heuristic to a result."""
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        score = 0.45
        reasons: list[str] = []

        if host.endswith(".gov") or ".gov." in host:
            score += 0.35
            reasons.append("government domain")
        if host.endswith(".edu") or ".edu." in host:
            score += 0.25
            reasons.append("education domain")
        if any(token in host for token in ["nature.com", "science.org", "who.int", "oecd.org"]):
            score += 0.25
            reasons.append("recognized institutional source")
        if any(token in host for token in ["blog", "medium.com", "substack.com"]):
            score -= 0.15
            reasons.append("commentary or blog-like source")
        if "sponsored" in snippet.lower() or "press release" in snippet.lower():
            score -= 0.15
            reasons.append("possible promotional framing")

        score = round(max(0.0, min(score, 1.0)), 2)
        return json.dumps(
            {
                "url": url,
                "title": title,
                "quality_score": score,
                "reasons": reasons or ["generic domain heuristic only"],
            }
        )

    @function_tool
    def compare_claims(claim_a: str, claim_b: str) -> str:
        """Compare two short claims and classify their relationship."""
        a = claim_a.lower().strip()
        b = claim_b.lower().strip()
        overlap = sorted(set(a.split()) & set(b.split()))
        if a == b:
            relationship = "same"
        elif len(overlap) >= max(3, min(len(set(a.split())), len(set(b.split()))) // 2):
            relationship = "related"
        else:
            relationship = "unclear"
        return json.dumps(
            {
                "relationship": relationship,
                "shared_terms": overlap[:12],
                "warning": "Lexical comparison only. This can miss semantic agreement or conflict.",
            }
        )

    return [
        scratchpad_write,
        scratchpad_read,
        web_search,
        extract_page,
        assess_source,
        compare_claims,
    ]
