from __future__ import annotations

import json
from pathlib import Path


def test_dataset_has_50_unique_queries() -> None:
    rows = [json.loads(line) for line in Path("data/queries.jsonl").read_text().splitlines()]
    assert len(rows) == 50
    assert len({row["id"] for row in rows}) == 50
    assert all(row["query"].endswith("?") for row in rows)
    assert all(row["category"] for row in rows)
