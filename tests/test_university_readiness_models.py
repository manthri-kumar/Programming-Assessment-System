from dataclasses import asdict

import pytest

from backend.agent_models import OperationalTiming, SourceLocation, StageDiagnostic, StageMetadata
from backend.agents import AgentContext, AssessmentOrchestrator, ServiceResult
from backend.knowledge import Concept, ConceptGraph
from backend.runner import FakeRunner, RunStatus, TestRun


def test_versioned_stage_models_are_typed_serializable_and_bounded():
    location = SourceLocation(2, 4)
    diagnostic = StageDiagnostic(
        code="syntax-error", classification="learner-error", message="syntax error at line 2, column 4",
        severity="error", evidence_refs=("syntax:one",), location=location,
    )
    metadata = StageMetadata(
        classification="learner-error", diagnostics=(diagnostic,), limitations=("functional tests skipped",),
        confidence=0.9, timing=OperationalTiming(1.5),
    )
    serialized = asdict(metadata)
    assert serialized["schema_version"] == "stage-evidence-v1"
    assert serialized["diagnostics"][0]["location"] == {"line": 2, "column": 4, "end_line": None, "end_column": None}
    with pytest.raises(ValueError):
        SourceLocation(0)
    with pytest.raises(ValueError):
        StageMetadata(confidence=1.1)
    with pytest.raises(ValueError):
        StageDiagnostic("x", "verified", "m", "info", tuple("e" for _ in range(65)))
    with pytest.raises(ValueError):
        ServiceResult("unsafe", "complete", evidence=tuple(f"e:{index}" for index in range(129)))


def test_report_v3_and_feedback_v3_are_evidence_linked_and_deterministic():
    graph = ConceptGraph("graph-v1", {"loops": Concept("loops", "Loops", "Practice bounded loops")}, {})
    context = AgentContext(
        "python", "for value in range(2):\n print(value)", "for value in range(2):\n print(value)", graph,
        required_concepts=("loops",), tests=({"id": "visible-id", "concept_ids": ["loops"]},),
    )
    runner = FakeRunner((TestRun("visible-id", RunStatus.WRONG_OUTPUT, weight=1),))
    first = AssessmentOrchestrator(runner).run(context)["feedback_agent"]
    second = AssessmentOrchestrator(runner).run(context)["feedback_agent"]
    assert first.report.payload == second.report.payload
    report = first.report.payload["report"]
    assert report["report_version"] == "assessment-report-v3"
    assert report["compatible_versions"] == ["assessment-report-v2"]
    assert report["trace"] == ["implementation-evaluation", "feedback"]
    assert report["feedback"]
    assert all(item["template_version"] == "feedback-v3" for item in report["feedback"])
    assert all(item["evidence_refs"] for item in report["feedback"])
    assert report["overview"]["total"] == 60.0
    criteria = first.evaluation.evaluation.payload["criterion_evidence"]
    assert set(criteria) == {"structure", "syntax", "tests", "originality"}
    assert all(criteria[name] for name in criteria)
    assert "plagiarism" in first.evaluation.evaluation.payload["criterion_limitations"]["originality"][0]


def test_feedback_v3_covers_complexity_and_provisional_unavailable_evidence():
    graph = ConceptGraph("graph-v1", {"loops": Concept("loops", "Loops", "Practice loops")}, {})
    nested = AgentContext(
        "python", "for x in range(2):\n for y in range(2):\n  print(x, y)",
        "for x in range(2):\n for y in range(2):\n  print(x, y)", graph,
        required_concepts=("loops",), tests=({"id": "case", "concept_ids": ["loops"]},),
    )
    complete = AssessmentOrchestrator(FakeRunner((TestRun("case", RunStatus.PASSED, weight=1),))).run(nested)
    assert any(item["code"] == "review-complexity" for item in complete["feedback"].payload["items"])
    assert complete["recommendations"].payload["recommendations"] == []

    unavailable = AssessmentOrchestrator(FakeRunner((), available=False)).run(nested)
    item = unavailable["feedback"].payload["items"][0]
    assert item["code"] == "evaluation-unavailable"
    assert item["confidence"] is None
    assert unavailable["report"].payload["report"]["overview"]["execution_available"] is False


@pytest.mark.parametrize(
    ("language", "source"),
    [
        ("python", "if True print('x')"),
        ("c", "int main( { return 0; }"),
        ("java", "class Main { public static void main(String[] args) {"),
    ],
)
def test_language_syntax_diagnostics_include_typed_source_locations(language, source):
    result = AssessmentOrchestrator(FakeRunner(())).run(AgentContext(language, source, source))["implementation_evaluation"]
    syntax = result.stages["syntax-analysis"]
    assert syntax.status == "invalid_submission"
    assert syntax.metadata is not None
    assert syntax.metadata.classification == "learner-error"
    assert syntax.metadata.diagnostics
    assert syntax.metadata.diagnostics[0].location is not None
