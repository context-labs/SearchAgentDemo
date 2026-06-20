from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tavily import TavilyClient

from search_agent_example.models import SearchResult


class SearchClient(Protocol):
    def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = False,
        topic: str = "general",
    ) -> dict: ...

    def extract(self, url: str, query: str | None = None, max_chars: int = 6000) -> dict: ...


@dataclass
class TavilySearchClient:
    api_key: str
    session_id: str | None = None
    human_id: str | None = None

    def __post_init__(self) -> None:
        self._client = TavilyClient(
            api_key=self.api_key,
            session_id=self.session_id,
            human_id=self.human_id,
        )

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = False,
        topic: str = "general",
    ) -> dict:
        response = self._client.search(
            query=query,
            max_results=max(1, min(max_results, 8)),
            include_answer=include_answer,
            search_depth="basic",
            topic=topic,
        )
        return normalize_search_response(response)

    def extract(self, url: str, query: str | None = None, max_chars: int = 6000) -> dict:
        response = self._client.extract(
            urls=url,
            extract_depth="basic",
            format="markdown",
            query=query,
        )
        results = response.get("results", [])
        if not results:
            return {"url": url, "raw_content": "", "truncated": False}
        raw_content = str(results[0].get("raw_content") or "")
        truncated = len(raw_content) > max_chars
        return {
            "url": results[0].get("url", url),
            "raw_content": raw_content[:max_chars],
            "truncated": truncated,
        }


class MockSearchClient:
    def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = False,
        topic: str = "general",
    ) -> dict:
        results = [
            SearchResult(
                title="Example government source",
                url="https://example.gov/report",
                content=(
                    "A public agency report says the query needs current source "
                    f"checking and careful date handling: {query}."
                ),
                score=0.91,
                published_date="2026-02-12",
            ),
            SearchResult(
                title="Example analyst note",
                url="https://example.org/analysis",
                content=(
                    "An analyst note gives context, but it is not a primary source "
                    "and may need corroboration."
                ),
                score=0.74,
                published_date="2025-11-01",
            ),
            SearchResult(
                title="Example vendor blog",
                url="https://example.com/blog",
                content=(
                    "A vendor blog frames the topic optimistically and should be "
                    "treated as lower confidence evidence."
                ),
                score=0.62,
                published_date=None,
            ),
        ][: max(1, min(max_results, 8))]
        return {
            "query": query,
            "answer": "Mock answer generated without calling Tavily." if include_answer else None,
            "results": [result.to_dict() for result in results],
        }

    def extract(self, url: str, query: str | None = None, max_chars: int = 6000) -> dict:
        content = (
            f"# Mock extracted page\n\nURL: {url}\n\n"
            "This deterministic page content is used for tests and local demos. "
            "It intentionally includes enough text for the agent to summarize while "
            "avoiding network usage."
        )
        return {"url": url, "raw_content": content[:max_chars], "truncated": False}


def normalize_search_response(response: dict) -> dict:
    normalized: list[dict] = []
    for item in response.get("results", []):
        normalized.append(
            SearchResult(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                content=str(item.get("content", "")),
                score=item.get("score"),
                published_date=item.get("published_date"),
            ).to_dict()
        )
    return {
        "query": response.get("query"),
        "answer": response.get("answer"),
        "results": normalized,
    }
