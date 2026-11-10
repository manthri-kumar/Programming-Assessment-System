"""Export the FastAPI contract without opening a network listener."""

from __future__ import annotations

import json
from pathlib import Path

from backend.api import create_app
from backend.auth import TokenManager
from backend.knowledge import load_graph
from backend.persistence import SQLiteRepository
from backend.runner import FailClosedRunner
from backend.service import AssessmentService


ROOT = Path(__file__).parents[1]


def main() -> None:
    graph = load_graph(ROOT / "data" / "concepts" / "concept-v1.json")
    app = create_app(
        SQLiteRepository(":memory:"),
        AssessmentService(FailClosedRunner(), graph),
        TokenManager(b"openapi-export-only"),
    )
    destination = ROOT / "docs" / "backend" / "openapi.json"
    destination.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
