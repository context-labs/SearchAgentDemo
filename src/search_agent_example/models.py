from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Scratchpad:
    notes: list[dict[str, str]] = field(default_factory=list)

    def write(self, note: str, label: str = "note") -> dict[str, str]:
        entry = {
            "label": label[:40],
            "note": note[:1200],
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.notes.append(entry)
        return entry

    def read(self, limit: int = 10) -> list[dict[str, str]]:
        return self.notes[-max(1, min(limit, 25)) :]


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    content: str
    score: float | None = None
    published_date: str | None = None

    def to_dict(self) -> dict[str, str | float | None]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score,
            "published_date": self.published_date,
        }
