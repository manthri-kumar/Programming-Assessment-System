from __future__ import annotations

from copy import deepcopy
from typing import Any


SUPPORTED_REPORT_VERSIONS = frozenset({"assessment-report-v2", "assessment-report-v3"})


def replay_compatible_result(result: dict[str, Any]) -> dict[str, Any]:
    """Return a presentation-compatible copy without rewriting persisted history."""
    output = deepcopy(result)
    report = output.get("report")
    if not isinstance(report, dict):
        return output
    version = report.get("report_version")
    if version not in SUPPORTED_REPORT_VERSIONS:
        return output
    if version == "assessment-report-v2":
        evaluation = report.get("evaluation") if isinstance(report.get("evaluation"), dict) else {}
        report.setdefault("compatible_versions", ["assessment-report-v2"])
        report.setdefault("overview", {
            "verified_status": report.get("status", output.get("status")),
            "total": evaluation.get("total", output.get("total")),
            "category": evaluation.get("category", output.get("category")),
            "overall_explanation": "This historical report is displayed through the v2 compatibility adapter.",
            "execution_available": any(
                stage.get("service") == "test-execution" and stage.get("status") == "complete"
                for stage in report.get("stages", []) if isinstance(stage, dict)
            ),
        })
        report.setdefault("issues", report.get("feedback", []))
        report.setdefault("actions", [])
        report.setdefault("teacher_explanation", None)
    return output

