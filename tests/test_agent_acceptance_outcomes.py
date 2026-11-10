import json
from pathlib import Path

from backend.agents import AgentContext, AssessmentOrchestrator
from backend.knowledge import load_graph
from backend.runner import FailClosedRunner, FakeRunner, RunStatus, TestRun


ROOT = Path(__file__).parents[1]


def expected():
    return json.loads((ROOT / "data" / "benchmarks" / "agent-expected-outcomes-v1.json").read_text(encoding="utf-8"))


def context(tests):
    graph = load_graph(ROOT / "data" / "concepts" / "concept-v1.json")
    return AgentContext("python", "print(1)", "print(1)", graph, tests=tests)


def test_candidate_labels_are_complete_but_not_claimed_as_independently_approved():
    data = expected()
    assert data["label_status"] == "pending-independent-review"
    assert data["reviewer"] is None
    scenarios = {item["scenario"] for item in data["cases"]}
    assert scenarios == {
        "correct_program", "incorrect_program", "partially_correct_program", "syntax_error",
        "missing_concept", "alternative_valid_algorithm", "incorrect_structure",
        "unsupported_complexity_case", "graph_prerequisite_recommendation",
        "contradictory_agent_evidence", "execution_unavailable",
    }


def test_correct_incorrect_and_partial_expected_functional_outcomes():
    tests = ({"id": "a", "concept_ids": []}, {"id": "b", "concept_ids": []})
    correct = AssessmentOrchestrator(FakeRunner((TestRun("a", RunStatus.PASSED, weight=1), TestRun("b", RunStatus.PASSED, weight=1)))).run(context(tests))
    incorrect = AssessmentOrchestrator(FakeRunner((TestRun("a", RunStatus.WRONG_OUTPUT, weight=1), TestRun("b", RunStatus.WRONG_OUTPUT, weight=1)))).run(context(tests))
    partial = AssessmentOrchestrator(FakeRunner((TestRun("a", RunStatus.PASSED, weight=1), TestRun("b", RunStatus.WRONG_OUTPUT, weight=1)))).run(context(tests))
    assert correct["evaluation"].payload["components"]["tests"] == 100.0
    assert incorrect["evaluation"].payload["components"]["tests"] == 0.0
    assert partial["evaluation"].payload["components"]["tests"] == 50.0


def test_execution_unavailable_is_explicit_and_report_has_no_functional_claim():
    result = AssessmentOrchestrator(FailClosedRunner()).run(context(({"id": "a", "concept_ids": []},)))
    assert result["evaluation"].status == "incomplete"
    assert result["evaluation"].payload["total"] is None
    assert result["stages"]["test-execution"].status == "unavailable"
    assert "runner:unavailable" in result["report"].payload["report"]["evidence_lineage"]


def test_missing_concept_and_graph_prerequisites_produce_traceable_recommendations():
    graph = load_graph(ROOT / "data" / "concepts" / "concept-v1.json")
    assessment = AgentContext(
        "python", "print(1)", "print(1)", graph,
        tests=({"id": "zero", "concept_ids": ["zero-division-guard"]},),
    )
    result = AssessmentOrchestrator(FakeRunner((TestRun("zero", RunStatus.WRONG_OUTPUT, weight=1),))).run(assessment)
    concept = result["stages"]["concept-analysis"].payload["findings"]
    assert concept["zero-division-guard"] == "absent"
    assert result["knowledge_graph"].payload["ordered_prerequisites"] == ["input", "arithmetic", "conditionals", "zero-division-guard"]
    assert [item["concept_id"] for item in result["recommendations"].payload["recommendations"]] == ["input", "arithmetic", "conditionals", "zero-division-guard"]
    assert result["recommendations"].payload["recommendations"][-1]["triggering_evidence"] == ["test:zero:wrong_output", "concept:zero-division-guard:absent"]


def test_alternative_valid_algorithm_keeps_behavior_and_structure_separate():
    graph = load_graph(ROOT / "data" / "concepts" / "concept-v1.json")
    assessment = AgentContext(
        "python",
        "total = 0\nfor value in range(4):\n    total += value\nprint(total)\n",
        "print(sum([0, 1, 2, 3]))\n",
        graph,
        tests=({"id": "sum", "concept_ids": ["loops"]},),
    )
    result = AssessmentOrchestrator(FakeRunner((TestRun("sum", RunStatus.PASSED, weight=1),))).run(assessment)
    assert result["evaluation"].status == "complete"
    assert result["evaluation"].payload["components"]["tests"] == 100.0
    assert result["stages"]["structural-comparison"].payload["relation"] == "different"
    assert result["stages"]["structural-comparison"].payload["score"] < 100.0


def test_isolated_compile_failure_is_invalid_submission_not_a_scored_test_failure():
    tests = ({"id": "compile", "concept_ids": [], "weight": 1},)
    result = AssessmentOrchestrator(FakeRunner((
        TestRun("compile", RunStatus.COMPILE_ERROR, stderr="compiler diagnostic without keyword", exit_code=1, weight=1),
    ))).run(context(tests))
    evaluation = result["evaluation"]
    assert evaluation.status == "invalid_submission"
    assert evaluation.payload["total"] is None and evaluation.payload["category"] is None
    assert evaluation.payload["components"] == {"syntax": 0.0}
    assert evaluation.payload["compiler_status"] == "failed-isolated-compilation"
    assert result["feedback"].payload["items"][0]["code"] == "fix-syntax"


def test_runtime_timeout_and_resource_outcomes_remain_distinct_and_deterministic():
    tests = tuple({"id": name, "concept_ids": [], "weight": 1} for name in ("runtime", "timeout", "resource"))
    outcomes = (
        TestRun("runtime", RunStatus.RUNTIME_ERROR, stderr="exit", exit_code=2, weight=1),
        TestRun("timeout", RunStatus.TIMEOUT, stderr="deadline", weight=1),
        TestRun("resource", RunStatus.RESOURCE_LIMIT, stderr="limit", weight=1),
    )
    first = AssessmentOrchestrator(FakeRunner(outcomes)).run(context(tests))
    second = AssessmentOrchestrator(FakeRunner(outcomes)).run(context(tests))
    assert first["evaluation"].status == "complete"
    assert first["evaluation"].payload["components"]["tests"] == 0.0
    assert [item["status"] for item in first["evaluation"].payload["test_outcomes"]] == ["runtime_error", "timeout", "resource_limit"]
    assert first["report"].payload == second["report"].payload


def test_mixed_compile_and_execution_outcomes_are_rejected_as_invalid_evidence():
    tests = ({"id": "a", "concept_ids": [], "weight": 1}, {"id": "b", "concept_ids": [], "weight": 1})
    result = AssessmentOrchestrator(FakeRunner((
        TestRun("a", RunStatus.COMPILE_ERROR, weight=1),
        TestRun("b", RunStatus.PASSED, weight=1),
    ))).run(context(tests))
    assert result["evaluation"].status == "invalid_evidence"
    assert result["evaluation"].payload["total"] is None
