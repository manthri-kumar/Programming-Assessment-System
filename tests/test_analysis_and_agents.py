import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.agents import (
    AgentContext, AssessmentOrchestrator, BaseAgent,
    CodePreprocessingService, ComplexityAnalysisService, ConceptAnalysisService,
    FeedbackAgent, ImplementationEvaluationAgent, KnowledgeGraphReasoningService,
    SecureTestExecutionService, ServiceResult, StructuralComparisonService,
    SyntaxAnalysisService, failed_concept_evidence, registered_agents,
)
from backend.corpus import load
from backend.ir import IRNode, canonical_hash, compare_ir
from backend.knowledge import Concept, ConceptGraph, GraphError, load_graph
from backend.languages.c import analyze as analyze_c
from backend.languages.java import analyze as analyze_java
from backend.languages.python import analyze
from backend.runner import FailClosedRunner, FakeRunner, RunStatus, TestRun


ROOT = Path(__file__).parents[1]


class AnalysisTests(unittest.TestCase):
    def test_reviewed_zero_division_fixture_uses_teacher_output(self):
        case = load(ROOT / "data" / "benchmarks" / "corpus-v1.json")["cases"][0]
        self.assertEqual(case["expected_output"], "5\n5\n0\nError\n")

    def test_python_analysis_is_safe_deterministic_and_identifier_normalized(self):
        source = "# for\ndef add(value):\n    return value + 1\n"
        first, second = analyze(source), analyze(source)
        self.assertTrue(first.syntax_ok)
        self.assertEqual(first.ir, second.ir)
        renamed = analyze("def renamed(other):\n    return other + 1\n")
        self.assertEqual(canonical_hash(first.ir), canonical_hash(renamed.ir))

    def test_python_syntax_limit_and_dependency_failures_are_explicit(self):
        self.assertFalse(analyze("def broken(:\n pass").syntax_ok)
        self.assertEqual(analyze("value = 1", max_nodes=1).diagnostics, ("analysis_limit: AST node limit exceeded",))
        external = analyze("import definitely_not_installed_assessment_package\nvalue = 1\n")
        self.assertEqual(external.support_status, "unsupported")
        result = SyntaxAnalysisService().run(AgentContext("python", "import definitely_not_installed_assessment_package", "pass"))
        self.assertEqual(result.status, "unsupported")

    def test_comments_and_strings_do_not_create_control_flow(self):
        result = analyze("# for while if\ntext = 'for while if'\n")
        kinds = []

        def walk(node):
            kinds.append(node.kind)
            for child in node.children:
                walk(child)

        walk(result.ir)
        self.assertNotIn("for", kinds)
        self.assertNotIn("while", kinds)
        self.assertNotIn("if", kinds)

    def test_c_and_java_use_language_aware_parsers(self):
        self.assertTrue(analyze_c("int main(void) { /* if for */ return 0; }").syntax_ok)
        self.assertFalse(analyze_c("int main( { return 0; }").syntax_ok)
        self.assertTrue(analyze_java("class Main { public static void main(String[] args) { if (true) return; } }").syntax_ok)
        self.assertFalse(analyze_java("class Helper { }").syntax_ok)
        self.assertFalse(analyze_java("import org.example.Tool; public class Main { }").syntax_ok)
        self.assertFalse(analyze_java("package demo; public class Main { }").syntax_ok)

    def test_bounded_ir_edit_comparison(self):
        left = IRNode("module", (IRNode("return"),))
        self.assertEqual(compare_ir(left, left).score, 100)
        self.assertEqual(compare_ir(left, IRNode("module", (IRNode("if"),))).distance, 1)
        self.assertEqual(compare_ir(left, left, max_operations=1).status, "analysis_limit")

    def test_cross_language_preprocessing_and_structure_services(self):
        for language, source in (("c", "int main(void) { return 0; }"), ("java", "class Main { int f() { return 0; } }")):
            context = AgentContext(language, source, source)
            self.assertEqual(CodePreprocessingService().run(context).status, "complete")
            self.assertEqual(StructuralComparisonService().run(context).payload["score"], 100)

    def test_graph_validation_and_versioned_paths(self):
        graph = load_graph(ROOT / "data" / "concepts" / "concept-v1.json")
        self.assertEqual(graph.prerequisite_order({"zero-division-guard"}), ("input", "arithmetic", "conditionals", "zero-division-guard"))
        cyclic = ConceptGraph("bad", graph.concepts, {"conditionals": ("zero-division-guard",), "zero-division-guard": ("conditionals",)})
        with self.assertRaises(GraphError):
            cyclic.validate()
        duplicate = {"version": "bad", "concepts": [{"id": "x", "label": "A", "guidance": "A"}, {"id": "x", "label": "B", "guidance": "B"}], "requires": {}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            path.write_text(json.dumps(duplicate), encoding="utf-8")
            with self.assertRaises(GraphError):
                load_graph(path)

    def test_importing_main_has_no_execution_side_effect(self):
        import main
        self.assertTrue(callable(importlib.reload(main).main))
        captured = []
        main.plot_result({"status": "complete", "components": {"syntax": 100}}, captured.append)
        self.assertEqual(captured, [{"syntax": 100}])


class TwoAgentTests(unittest.TestCase):
    def setUp(self):
        self.graph = load_graph(ROOT / "data" / "concepts" / "concept-v1.json")

    def test_registry_exposes_exactly_two_main_agents(self):
        agents = registered_agents(FailClosedRunner())
        self.assertEqual([agent.name for agent in agents], ["implementation-evaluation", "feedback"])
        self.assertEqual(len(agents), 2)
        self.assertTrue(all(isinstance(agent, BaseAgent) for agent in agents))
        self.assertFalse(isinstance(SyntaxAnalysisService(), BaseAgent))
        self.assertFalse(isinstance(KnowledgeGraphReasoningService(), BaseAgent))

    def test_typed_handoff_is_deterministic_and_uses_no_network(self):
        runner = FakeRunner((TestRun("case", RunStatus.PASSED, weight=1),))
        context = AgentContext("python", "print(1)", "print(1)", self.graph, tests=({"id": "case", "concept_ids": []},))
        with patch("socket.socket", side_effect=AssertionError("network access forbidden")):
            first_run = AssessmentOrchestrator(runner).run(context)
            second_run = AssessmentOrchestrator(runner).run(context)
        first = first_run["implementation_evaluation"]
        second = first_run["feedback_agent"]
        self.assertIs(second.evaluation, first)
        self.assertEqual(first.evaluation.payload, second_run["implementation_evaluation"].evaluation.payload)
        self.assertEqual(second.report.payload, second_run["feedback_agent"].report.payload)
        self.assertEqual(second.report.payload["report"]["trace"], ["implementation-evaluation", "feedback"])

    def test_only_two_agent_complete_events_are_emitted(self):
        class Recorder:
            def __init__(self): self.events = []
            def emit(self, event): self.events.append(event)

        recorder = Recorder()
        context = AgentContext("python", "print(1)", "print(1)", self.graph, tests=({"id": "case", "concept_ids": []},), correlation_id="two-agent")
        AssessmentOrchestrator(FakeRunner((TestRun("case", RunStatus.PASSED, weight=1),)), recorder).run(context)
        agents = [event.agent for event in recorder.events if event.event == "agent_complete"]
        self.assertEqual(agents, ["implementation-evaluation", "feedback"])
        services = [event.agent for event in recorder.events if event.event == "stage_trace"]
        self.assertIn("syntax-analysis", services)
        self.assertIn("knowledge-graph-reasoning", services)

    def test_agent_one_cancellation_and_unknown_policy_skip_runner(self):
        class CountingRunner(FakeRunner):
            calls = 0
            def run(self, *args, **kwargs):
                self.calls += 1
                return super().run(*args, **kwargs)

        runner = CountingRunner(())
        cancelled = ImplementationEvaluationAgent(runner).run(AgentContext("python", "pass", "pass", cancelled=True))
        unsupported = ImplementationEvaluationAgent(runner).run(AgentContext("python", "pass", "pass", policy_version="unknown"))
        self.assertEqual(cancelled.status, "cancelled")
        self.assertEqual(unsupported.status, "unsupported")
        self.assertEqual(runner.calls, 0)

    def test_syntax_failure_skips_execution_and_agent_two_reports_it(self):
        class CountingRunner(FakeRunner):
            calls = 0
            def run(self, *args, **kwargs):
                self.calls += 1
                return super().run(*args, **kwargs)

        runner = CountingRunner(())
        pipeline = AssessmentOrchestrator(runner).run(AgentContext("python", "def broken(:", "pass", self.graph))
        self.assertEqual(runner.calls, 0)
        self.assertEqual(pipeline["implementation_evaluation"].stages["test-execution"].status, "skipped")
        self.assertEqual(pipeline["report"].payload["report"]["status"], "invalid_submission")

    def test_agent_one_preserves_rubric_score_and_agent_two_adds_feedback(self):
        runner = FakeRunner((TestRun("case", RunStatus.WRONG_OUTPUT, weight=1),))
        context = AgentContext("python", "print(1)", "print(1)", self.graph, tests=({"id": "case", "concept_ids": ["input"]},))
        pipeline = AssessmentOrchestrator(runner).run(context)
        evaluation = pipeline["implementation_evaluation"].evaluation
        self.assertEqual(evaluation.payload["components"], {"structure": 100.0, "syntax": 100.0, "tests": 0.0, "originality": 0.0})
        self.assertEqual(evaluation.payload["total"], 60.0)
        self.assertIn("input", pipeline["feedback_agent"].weaknesses)
        self.assertTrue(any(item["code"] == "failed-test" for item in pipeline["feedback"].payload["items"]))

    def test_graph_reasoning_and_recommendations_are_internal_to_feedback_agent(self):
        runner = FakeRunner((TestRun("zero", RunStatus.WRONG_OUTPUT, weight=1),))
        context = AgentContext("python", "print(1)", "print(1)", self.graph, tests=({"id": "zero", "concept_ids": ["zero-division-guard"]},))
        first = ImplementationEvaluationAgent(runner).run(context)
        second = FeedbackAgent().run(context, first)
        self.assertEqual(second.graph_reasoning.payload["ordered_prerequisites"], ["input", "arithmetic", "conditionals", "zero-division-guard"])
        self.assertEqual([item["concept_id"] for item in second.recommendations.payload["recommendations"]], ["input", "arithmetic", "conditionals", "zero-division-guard"])

    def test_contradictory_graph_evidence_is_retained(self):
        context = AgentContext("python", "value = int(input())", "value = int(input())", self.graph, tests=(
            {"id": "pass", "concept_ids": ["input"]}, {"id": "fail", "concept_ids": ["input"]},
        ))
        first = ImplementationEvaluationAgent(FakeRunner((TestRun("pass", RunStatus.PASSED, weight=1), TestRun("fail", RunStatus.WRONG_OUTPUT, weight=1)))).run(context)
        graph = FeedbackAgent().run(context, first).graph_reasoning
        self.assertEqual(graph.payload["contradictions"], ["input"])
        self.assertEqual(graph.payload["weak"], ["input"])

    def test_services_handle_missing_graph_fail_closed_and_complexity_limits(self):
        context = AgentContext("python", "x = 1", "x = 1")
        self.assertEqual(ConceptAnalysisService().run(context).status, "unavailable")
        self.assertEqual(SecureTestExecutionService(FailClosedRunner()).run(context).status, "unavailable")
        source = "def recurse(n):\n    if n:\n        return recurse(n - 1)\n    for x in range(2):\n        for y in range(2):\n            print(x, y)\n"
        complexity = ComplexityAnalysisService().run(AgentContext("python", source, source))
        self.assertEqual(complexity.payload["loop_nesting"], 2)
        self.assertTrue(complexity.payload["recursion"])
        c_result = ComplexityAnalysisService().run(AgentContext("c", "int main(void){return 0;}", "int main(void){return 0;}"))
        self.assertIsNone(c_result.payload["recursion"])

    def test_unlabelled_failures_do_not_invent_concepts(self):
        context = AgentContext("c", "int main(void){return 0;}", "int main(void){return 0;}", self.graph, tests=(
            {"id": "zero", "concept_ids": ["zero-division-guard"]}, {"id": "unlabelled", "concept_ids": []},
        ))
        evidence = failed_concept_evidence(context, ({"case_id": "zero", "status": "wrong_output"}, {"case_id": "unlabelled", "status": "runtime_error"}))
        self.assertEqual(evidence, {"zero-division-guard": ("test:zero:wrong_output",)})

    def test_feedback_agent_requires_typed_agent_one_result(self):
        with self.assertRaisesRegex(TypeError, "ImplementationEvaluationResult"):
            FeedbackAgent().run(AgentContext("python", "pass", "pass"), ServiceResult("wrong", "complete"))


if __name__ == "__main__":
    unittest.main()
