"""Static analysis regressions; runner doubles verify contracts, not execution."""
from pathlib import Path

import pytest

from backend.agents import AgentContext, AssessmentOrchestrator, ComplexityAnalysisService
from backend.knowledge import load_graph
from backend.runner import FailClosedRunner, FakeRunner, RunStatus, TestRun
from backend.service import AssessmentService
from backend.languages.python import analyze as analyze_python
from backend.languages.c import analyze as analyze_c
from backend.languages.java import analyze as analyze_java


GRAPH = load_graph(Path(__file__).parents[1] / "data/concepts/concept-v1.json")


@pytest.mark.parametrize(("source", "recursive"), [
    ("def double(n):\n return n * 2\nprint(double(4))", False),
    ("def first(n):\n return second(n)\ndef second(n):\n return n + 1\nprint(first(2))", False),
    ("def factorial(n):\n return 1 if n < 2 else n * factorial(n - 1)", True),
    ("def even(n):\n return True if n == 0 else odd(n - 1)\ndef odd(n):\n return False if n == 0 else even(n - 1)", True),
    ("def first(n):\n def second(n):\n  return first(n)\n return n", False),
])
def test_recursion_requires_a_cycle_inside_function_calls(source, recursive):
    result = ComplexityAnalysisService().run(AgentContext("python", source, source))
    assert result.payload["recursion"] is recursive
    assert result.payload["metric_version"] == "complexity-static-v3"


def test_nested_and_method_recursion_remain_explicitly_unsupported():
    source = "def outer():\n def inner():\n  return inner()\n return inner()\nclass Example:\n def method(self):\n  return self.method()"
    result = ComplexityAnalysisService().run(AgentContext("python", source, source))
    assert result.payload["unsupported_indicators"] == ["method-recursion", "nested-function-recursion"]


def test_static_absence_and_passing_test_do_not_report_both_weak_and_satisfied():
    context = AgentContext("python", "print(1)", "print(1)", GRAPH,
                           tests=({"id": "case", "concept_ids": ["input"]},))
    result = AssessmentOrchestrator(FakeRunner((TestRun("case", RunStatus.PASSED, weight=1),))).run(context)
    graph = result["knowledge_graph"].payload
    assert graph["weak"] == ["input"]
    assert graph["satisfied"] == []
    assert graph["contradictions"] == ["input"]
    assert graph["satisfied_evidence"]["input"] == ["test:case:passed"]
    assert graph["weak_evidence"]["input"] == ["concept:input:absent"]
    assert result["recommendations"].payload["recommendations"][0]["concept_id"] == "input"
    assert any(item["code"] == "contradictory-evidence" for item in result["feedback"].payload["items"])


def test_worker_unavailable_keeps_specific_static_guidance_and_null_score():
    source = "for x in range(3):\n for y in range(3):\n  print(x, y)"
    result = AssessmentService(FailClosedRunner(), GRAPH).assess("python", source, "print(1)")
    assert result["total"] is None and result["test_outcomes"] == ()
    items = {item["code"]: item for item in result["feedback"]}
    assert {"evaluation-unavailable", "review-complexity", "review-structure"} <= set(items)
    assert "Provisional static feedback" in items["review-complexity"]["limitations"][0]
    assert items["review-complexity"]["evidence_id"] in result["analysis"]["complexity-analysis"]["evidence"]
    assert result["agent_trace"] == ["implementation-evaluation", "feedback"]


def test_assignment_required_concepts_reach_feedback_and_change_request_identity():
    service = AssessmentService(FailClosedRunner(), GRAPH)
    unconstrained = service.assess("python", "print(1)", "print(1)")
    constrained = service.assess("python", "print(1)", "print(1)", required_concepts=("loops",))
    assert constrained["request_hash"] != unconstrained["request_hash"]
    assert constrained["analysis"]["concept-analysis"]["payload"]["findings"] == {"loops": "absent"}
    assert constrained["recommendations"][-1]["concept_id"] == "loops"
    assert constrained == service.assess("python", "print(1)", "print(1)", required_concepts=("loops", "loops"))


@pytest.mark.parametrize(("status", "message"), [
    (RunStatus.WRONG_OUTPUT, "output that did not match"),
    (RunStatus.RUNTIME_ERROR, "runtime error"),
    (RunStatus.TIMEOUT, "time limit"),
    (RunStatus.RESOURCE_LIMIT, "resource limit"),
])
def test_functional_feedback_explains_outcome_without_disclosing_outputs(status, message):
    context = AgentContext("python", "print(1)", "print(1)", GRAPH,
                           tests=({"id": "case", "concept_ids": []},))
    result = AssessmentOrchestrator(FakeRunner((TestRun("case", status, stdout="private output", stderr="private diagnostic", weight=1),))).run(context)
    item = next(item for item in result["feedback"].payload["items"] if item["code"] == "failed-test")
    assert message in item["message"]
    assert item["root_cause"] == f"The isolated worker reported {status.value}."
    assert "private" not in str(item)
    assert item["guidance"]


@pytest.mark.parametrize(("language", "source", "analyzer"), [
    ("python", "value = " + "+".join(["1"] * 500), analyze_python),
    ("c", "int main(void) { return " + "+".join(["1"] * 500) + "; }", analyze_c),
    ("java", "class Main { int value() { return " + "+".join(["1"] * 500) + "; } }", analyze_java),
])
def test_deep_ast_is_bounded_before_ir_conversion_without_learner_penalty(language, source, analyzer):
    analysis = analyzer(source)
    assert analysis.ir is None
    assert analysis.diagnostics == ("analysis_limit: AST depth limit exceeded",)
    result = AssessmentService(FailClosedRunner(), GRAPH).assess(language, source, source)
    assert result["status"] == "analysis_limit"
    assert result["components"] == {}
    assert result["total"] is None
    assert result["feedback"][0]["code"] == "evaluation-unavailable"
    assert result["analysis"]["test-execution"]["status"] == "skipped"


def test_unsupported_dependency_is_not_a_zero_syntax_grade():
    result = AssessmentService(FailClosedRunner(), GRAPH).assess("python", "import unknown_assessment_package", "pass")
    assert result["status"] == "unsupported"
    assert result["components"] == {}
    assert result["total"] is None


def test_partial_worker_availability_never_becomes_a_learner_failure():
    context = AgentContext("python", "print(1)", "print(1)", GRAPH,
                           tests=({"id": "a", "concept_ids": ["loops"]}, {"id": "b", "concept_ids": ["loops"]}))
    result = AssessmentOrchestrator(FakeRunner((
        TestRun("a", RunStatus.PASSED, weight=1),
        TestRun("b", RunStatus.UNAVAILABLE, weight=1),
    ))).run(context)
    assert result["evaluation"].status == "incomplete"
    assert result["evaluation"].payload["total"] is None
    assert result["stages"]["test-execution"].status == "unavailable"
    assert "test:b:unavailable" not in str(result["knowledge_graph"].payload)
    assert not any(item["code"] == "failed-test" for item in result["feedback"].payload["items"])
