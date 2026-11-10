"""Safe compatibility CLI for the automated assessment backend."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.knowledge import load_graph
from backend.runner import FailClosedRunner
from backend.service import AssessmentService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess source without unsafe host execution")
    parser.add_argument("--language", choices=("python", "c", "java"), default="c")
    parser.add_argument("--student", type=Path, default=Path("student_submissions/student1.c"))
    parser.add_argument("--reference", type=Path, default=Path("teacher_solution/teacher.c"))
    parser.add_argument("--plot", action="store_true", help="show component scores after a complete assessment")
    return parser


def run(language: str, student: Path, reference: Path) -> dict:
    graph = load_graph(Path("data/concepts/concept-v1.json"))
    service = AssessmentService(FailClosedRunner(), graph)
    return service.assess(language, student.read_text(encoding="utf-8"), reference.read_text(encoding="utf-8"))


def plot_result(result: dict, plotter=None) -> None:
    components = result.get("components")
    if result.get("status") != "complete" or not components:
        raise ValueError("plotting requires a complete assessment with component scores")
    if plotter is None:
        from results.plot import plot_scores
        plotter = plot_scores
    plotter(components)


def main() -> int:
    args = build_parser().parse_args()
    result = run(args.language, args.student, args.reference)
    print(json.dumps(result, indent=2, default=str))
    if args.plot:
        plot_result(result)
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
