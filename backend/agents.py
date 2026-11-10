from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field, replace
import hashlib
import re
from time import perf_counter
from types import MappingProxyType
from typing import Any, Literal, Mapping, Protocol, runtime_checkable

from backend.agent_models import (
    AgentPayload, AgentStatus, OperationalTiming, SourceLocation,
    StageDiagnostic, StageMetadata,
)
from backend.ir import IR_VERSION, IRNode, canonical_hash, compare_ir, node_count
from backend.knowledge import ConceptGraph, GraphError
from backend.languages.python import analyze as analyze_python
from backend.languages.c import analyze as analyze_c
from backend.languages.java import analyze as analyze_java
from backend.observability import AuditEvent, AuditLogger
from backend.runner import FailClosedRunner, RunnerUnavailable, SubmissionRunner
from backend.scoring import compose_total, legacy_originality_score, resolve_weights, weighted_test_score


@dataclass(frozen=True)
class AgentContext:
    language: str
    source: str
    reference_source: str
    graph: ConceptGraph | None = None
    required_concepts: tuple[str, ...] = ()
    rubric: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    tests: tuple[Any, ...] = ()
    policy_version: str = "core-v1"
    cancelled: bool = False
    correlation_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "rubric", MappingProxyType(dict(self.rubric)))
        object.__setattr__(self, "required_concepts", tuple(self.required_concepts))
        object.__setattr__(self, "tests", tuple(self.tests))


@dataclass(frozen=True)
class ServiceResult:
    service: str
    status: AgentStatus
    evidence: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    ir: IRNode | None = None
    payload: AgentPayload = field(default_factory=dict)
    service_version: str = "1"
    lineage: tuple[str, ...] = ()
    metadata: StageMetadata | None = None

    def __post_init__(self) -> None:
        if len(self.evidence) > 128 or any(not item or len(item) > 256 for item in self.evidence):
            raise ValueError("service evidence is invalid or unbounded")
        if len(self.diagnostics) > 64 or any(not item or len(item) > 4096 for item in self.diagnostics):
            raise ValueError("service diagnostics are invalid or unbounded")
        if self.metadata is None:
            object.__setattr__(self, "metadata", _metadata_for(self.status, self.diagnostics, self.evidence))


@dataclass(frozen=True)
class ImplementationEvaluationResult:
    agent: Literal["implementation-evaluation"]
    status: AgentStatus
    evaluation: ServiceResult
    stages: Mapping[str, ServiceResult]
    evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    agent_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "stages", MappingProxyType(dict(self.stages)))


@dataclass(frozen=True)
class FeedbackResult:
    agent: Literal["feedback"]
    status: AgentStatus
    evaluation: ImplementationEvaluationResult
    graph_reasoning: ServiceResult
    feedback: ServiceResult
    recommendations: ServiceResult
    report: ServiceResult
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    agent_version: str = "1"


@runtime_checkable
class BaseAgent(Protocol):
    name: str
    version: str
    role: Literal["main-agent"]

    def run(self, context: AgentContext, *args: Any, **kwargs: Any) -> ImplementationEvaluationResult | FeedbackResult: ...


def _analyze_language(language: str, source: str):
    analyzer = {"python": analyze_python, "c": analyze_c, "java": analyze_java}.get(language)
    return analyzer(source) if analyzer else None


def _evidence_id(kind: str, value: str) -> str:
    return f"{kind}:{hashlib.sha256(value.encode('utf-8')).hexdigest()[:20]}"


def _classification(status: AgentStatus) -> str:
    return {
        "complete": "verified", "invalid_submission": "learner-error",
        "unsupported": "unsupported", "analysis_limit": "analysis-limit",
        "unavailable": "infrastructure-unavailable", "incomplete": "infrastructure-unavailable",
        "invalid_evidence": "contradictory", "cancelled": "cancelled", "skipped": "skipped",
        "undetermined": "analysis-limit",
    }[status]


def _location(message: str) -> SourceLocation | None:
    match = re.search(r"line\s+(\d+)(?:,\s*column\s+(\d+))?", message, re.IGNORECASE)
    return SourceLocation(int(match.group(1)), int(match.group(2) or 1)) if match else None


def _metadata_for(status: AgentStatus, diagnostics: tuple[str, ...], evidence: tuple[str, ...]) -> StageMetadata:
    classification = _classification(status)
    items = tuple(StageDiagnostic(
        code=f"{classification}-{index + 1}", classification=classification,
        message=message, severity="error" if status in {"invalid_submission", "invalid_evidence"} else "warning",
        evidence_refs=evidence[:16], location=_location(message),
    ) for index, message in enumerate(diagnostics))
    limitations = diagnostics if status in {"unsupported", "analysis_limit", "unavailable", "incomplete", "undetermined"} else ()
    confidence = 1.0 if status == "complete" else 0.0 if status in {"unavailable", "skipped"} else 0.8
    return StageMetadata(classification=classification, diagnostics=items, limitations=limitations, confidence=confidence)


def _timed(result: ServiceResult, started: float) -> ServiceResult:
    metadata = result.metadata or _metadata_for(result.status, result.diagnostics, result.evidence)
    return replace(result, metadata=replace(metadata, timing=OperationalTiming(round((perf_counter() - started) * 1000, 3))))


def _unique(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _skipped(service: str, reason: str, evidence: tuple[str, ...] = ()) -> ServiceResult:
    return ServiceResult(service, "skipped", evidence=evidence, diagnostics=(reason,), payload={"reason": reason})


def _test_value(case: Any, key: str, default: Any = None) -> Any:
    return case.get(key, default) if isinstance(case, dict) else getattr(case, key, default)


class CodePreprocessingService:
    name = "code-preprocessing"
    version = "2"

    def run(self, context: AgentContext) -> ServiceResult:
        result = _analyze_language(context.language, context.source)
        if result is None:
            return ServiceResult(self.name, "unavailable", diagnostics=("language adapter unavailable",), service_version=self.version)
        if getattr(result, "support_status", "supported") == "unsupported":
            return ServiceResult(self.name, "unsupported", diagnostics=result.diagnostics, ir=result.ir, service_version=self.version)
        if not result.syntax_ok or result.ir is None:
            return ServiceResult(self.name, "invalid_submission", diagnostics=result.diagnostics, service_version=self.version)
        evidence = (canonical_hash(result.ir),)
        return ServiceResult(self.name, "complete", evidence, ir=result.ir, payload={"node_count": node_count(result.ir), "ir_version": IR_VERSION}, service_version=self.version)


class SyntaxAnalysisService:
    name = "syntax-analysis"
    version = "2"

    def run(self, context: AgentContext) -> ServiceResult:
        result = _analyze_language(context.language, context.source)
        if result is None:
            return ServiceResult(self.name, "unavailable", diagnostics=("language adapter unavailable",), service_version=self.version)
        if getattr(result, "support_status", "supported") == "unsupported":
            return ServiceResult(self.name, "unsupported", diagnostics=result.diagnostics, ir=result.ir, service_version=self.version)
        evidence = (canonical_hash(result.ir),) if result.ir else ()
        if not result.syntax_ok:
            evidence = evidence or (_evidence_id("syntax", context.source + "\n" + "\n".join(result.diagnostics)),)
        authority = "verified" if context.language == "python" else "pending-isolated-worker"
        parser = {"python": "cpython-ast", "c": "tree-sitter-c", "java": "tree-sitter-java"}.get(context.language, "unavailable")
        return ServiceResult(self.name, "complete" if result.syntax_ok else "invalid_submission", evidence, result.diagnostics, result.ir, {"parser": parser, "compiler_authority": authority}, self.version)


class ConceptAnalysisService:
    name = "concept-analysis"
    version = "2"

    def run(self, context: AgentContext) -> ServiceResult:
        if context.graph is None:
            return ServiceResult(self.name, "unavailable", diagnostics=("concept graph unavailable",), service_version=self.version)
        try:
            context.graph.validate()
        except GraphError as exc:
            return ServiceResult(self.name, "unavailable", diagnostics=(str(exc),), service_version=self.version)
        analysis = _analyze_language(context.language, context.source)
        if analysis is None:
            return ServiceResult(self.name, "unavailable", diagnostics=("language adapter unavailable",), service_version=self.version)
        if not analysis.syntax_ok or analysis.ir is None:
            return ServiceResult(self.name, "invalid_submission", diagnostics=analysis.diagnostics, service_version=self.version)
        present: set[str] = set()
        mapping = {
            "for": "loops", "while": "loops", "for_statement": "loops", "while_statement": "loops", "enhanced_for_statement": "loops",
            "if": "conditionals", "if_statement": "conditionals", "conditional_expression": "conditionals",
            "functiondef": "functions", "asyncfunctiondef": "functions", "function_definition": "functions", "method_declaration": "functions",
            "binop": "arithmetic", "augassign": "arithmetic", "binary_expression": "arithmetic", "assignment_expression": "arithmetic",
        }

        def walk(node: IRNode) -> None:
            if node.kind in mapping:
                present.add(mapping[node.kind])
            for child in node.children:
                walk(child)

        walk(analysis.ir)
        if context.language == "python":
            tree = ast.parse(context.source)
            if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input" for node in ast.walk(tree)):
                present.add("input")
            divisions = [node for node in ast.walk(tree) if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod))]
            guarded_names = {
                side.id for node in ast.walk(tree) if isinstance(node, ast.Compare)
                for side in (node.left, *node.comparators)
                if isinstance(side, ast.Name) and any(isinstance(other, ast.Constant) and other.value == 0 for other in (node.left, *node.comparators))
            }
            if divisions and any(isinstance(item.right, ast.Name) and item.right.id in guarded_names for item in divisions):
                present.add("zero-division-guard")
        required = tuple(dict.fromkeys(context.required_concepts + tuple(concept for case in context.tests for concept in _test_value(case, "concept_ids", ()))))
        findings = {concept: "unmapped" if concept not in context.graph.concepts else "present" if concept in present else "absent" for concept in required}
        evidence = (f"graph:{context.graph.version}",) + tuple(f"concept:{key}:{value}" for key, value in sorted(findings.items()))
        return ServiceResult(self.name, "complete", evidence=evidence, payload={"findings": findings, "detected": sorted(present & set(context.graph.concepts)), "detector_version": "concept-static-v2"}, service_version=self.version)


class StructuralComparisonService:
    name = "structural-comparison"
    version = "1"

    def run(self, context: AgentContext) -> ServiceResult:
        student = _analyze_language(context.language, context.source)
        reference = _analyze_language(context.language, context.reference_source)
        if not student or not reference:
            return ServiceResult(self.name, "unavailable", diagnostics=("language adapter unavailable",))
        if not student.ir or not reference.ir:
            return ServiceResult(self.name, "unavailable", diagnostics=("normalized IR unavailable",))
        comparison = compare_ir(student.ir, reference.ir)
        evidence = (canonical_hash(student.ir), canonical_hash(reference.ir))
        if comparison.status != "complete":
            return ServiceResult(self.name, "analysis_limit", evidence=evidence, diagnostics=("structural comparison operation limit exceeded",), payload={"operations": comparison.operations})
        return ServiceResult(self.name, "complete", evidence=evidence, payload={
            "score": comparison.score, "distance": comparison.distance,
            "relation": "equivalent" if comparison.distance == 0 else "different",
            "student_nodes": comparison.left_nodes, "reference_nodes": comparison.right_nodes,
            "operations": comparison.operations, "metric_version": "ir-edit-v1",
        })


class ComplexityAnalysisService:
    name = "complexity-analysis"
    version = "2"

    def run(self, context: AgentContext) -> ServiceResult:
        analysis = _analyze_language(context.language, context.source)
        if not analysis or not analysis.ir:
            return ServiceResult(self.name, "undetermined", diagnostics=("normalized IR unavailable",), service_version=self.version)
        max_depth = 0
        loop_locations: list[int] = []

        def walk(node: IRNode, depth: int = 0) -> None:
            nonlocal max_depth
            if node.kind in {"for", "while", "for_statement", "while_statement", "enhanced_for_statement"}:
                depth += 1
                max_depth = max(max_depth, depth)
                if node.line is not None:
                    loop_locations.append(node.line)
            for child in node.children:
                walk(child, depth)

        walk(analysis.ir)
        recursion: bool | None = None
        unsupported: list[str] = []
        if context.language == "python":
            tree = ast.parse(context.source)
            definitions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
            recursion = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in definitions for node in ast.walk(tree))
        else:
            unsupported.append("recursion")
        estimate = "constant" if max_depth == 0 else "linear" if max_depth == 1 else f"polynomial-upper-bound-n^{max_depth}"
        return ServiceResult(self.name, "complete", evidence=(canonical_hash(analysis.ir),), payload={
            "estimate": estimate, "loop_nesting": max_depth, "loop_locations": sorted(set(loop_locations)),
            "recursion": recursion, "unsupported_indicators": unsupported, "ir_nodes": node_count(analysis.ir),
            "metric_version": "complexity-static-v2", "limitation": "static structural estimate; data-dependent bounds are not inferred",
        }, service_version=self.version)


class SecureTestExecutionService:
    name = "test-execution"
    version = "1"

    def __init__(self, runner: SubmissionRunner):
        self.runner = runner

    def run(self, context: AgentContext) -> ServiceResult:
        if not self.runner.ready():
            return ServiceResult(self.name, "unavailable", evidence=("runner:unavailable",), diagnostics=("isolated execution worker unavailable",))
        try:
            outcomes = self.runner.run(context.language, context.source, context.reference_source, context.tests)
        except RunnerUnavailable as exc:
            return ServiceResult(self.name, "unavailable", evidence=("runner:unavailable",), diagnostics=(str(exc),))
        serialized = tuple({
            "case_id": outcome.case_id, "status": outcome.status.value, "stdout": outcome.stdout,
            "stderr": outcome.stderr, "exit_code": outcome.exit_code, "weight": outcome.weight,
        } for outcome in outcomes)
        return ServiceResult(self.name, "complete", evidence=tuple(f"test:{item['case_id']}:{item['status']}" for item in serialized), payload={"outcomes": serialized, "isolation": "approved-runner"})


class RubricEvaluationService:
    name = "rubric-evaluation"
    version = "2"
    stage_order = ("code-preprocessing", "syntax-analysis", "concept-analysis", "structural-comparison", "complexity-analysis", "test-execution")

    @staticmethod
    def _criteria(stages: Mapping[str, ServiceResult], source: str = "", reference_source: str = "") -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        evidence = {
            "structure": list(stages.get("structural-comparison", ServiceResult("structural-comparison", "unavailable")).evidence),
            "syntax": list(stages.get("syntax-analysis", ServiceResult("syntax-analysis", "unavailable")).evidence),
            "tests": list(stages.get("test-execution", ServiceResult("test-execution", "unavailable")).evidence),
            "originality": [_evidence_id("similarity-input", reference_source + "\n---\n" + source)] if source or reference_source else [],
        }
        limitations = {
            "structure": ["Normalized structural similarity is not behavioral equivalence."],
            "syntax": ["Static parser acceptance is not isolated compiler acceptance."] if stages.get("syntax-analysis") and stages["syntax-analysis"].payload.get("compiler_authority") != "verified" else [],
            "tests": list(stages.get("test-execution", ServiceResult("test-execution", "unavailable")).diagnostics),
            "originality": ["Text similarity is a rubric heuristic and is not a plagiarism or misconduct verdict."],
        }
        return evidence, limitations

    def run(self, context: AgentContext, stages: Mapping[str, ServiceResult]) -> ServiceResult:
        if context.cancelled:
            return ServiceResult(self.name, "cancelled", evidence=("orchestration:cancelled",), diagnostics=("assessment cancelled before execution",), payload={"total": None, "category": None, "stages": [], "stage_statuses": {}}, service_version=self.version)
        try:
            weights = resolve_weights(context.policy_version, dict(context.rubric) or None)
        except ValueError as exc:
            return ServiceResult(self.name, "unsupported", evidence=("policy:invalid",), diagnostics=(str(exc),), payload={"total": None, "category": None, "stages": ["validation"], "stage_statuses": {}}, service_version=self.version)
        syntax, preprocessing = stages["syntax-analysis"], stages["code-preprocessing"]
        structure, complexity = stages["structural-comparison"], stages["complexity-analysis"]
        execution, concept = stages["test-execution"], stages["concept-analysis"]
        statuses = {name: stages[name].status for name in self.stage_order}
        lineage = _unique(tuple(item for name in self.stage_order for item in stages[name].evidence))
        criterion_evidence, criterion_limitations = self._criteria(stages, context.source, context.reference_source)
        if (preprocessing.status == "complete") != (syntax.status == "complete") or (syntax.status != "complete" and execution.status == "complete"):
            return ServiceResult(self.name, "invalid_evidence", lineage, diagnostics=("contradictory service evidence prevents scoring",), payload={"total": None, "category": None, "stages": list(self.stage_order), "stage_statuses": statuses, "criterion_evidence": criterion_evidence, "criterion_limitations": criterion_limitations}, lineage=lineage, service_version=self.version)
        if syntax.status != "complete":
            return ServiceResult(self.name, syntax.status, lineage, syntax.diagnostics, payload={"total": None, "category": None, "components": {"syntax": 0.0}, "stages": list(self.stage_order), "stage_statuses": statuses, "policy_version": context.policy_version, "criterion_evidence": criterion_evidence, "criterion_limitations": criterion_limitations}, lineage=lineage, service_version=self.version)
        if execution.status != "complete":
            return ServiceResult(self.name, "incomplete", lineage, execution.diagnostics, payload={"total": None, "category": None, "stages": list(self.stage_order), "stage_statuses": statuses, "policy_version": context.policy_version, "criterion_evidence": criterion_evidence, "criterion_limitations": criterion_limitations}, lineage=lineage, service_version=self.version)
        outcomes = tuple(execution.payload.get("outcomes", ()))
        compile_failures = tuple(item for item in outcomes if item.get("status") == "compile_error")
        if compile_failures and len(compile_failures) != len(outcomes):
            return ServiceResult(
                self.name, "invalid_evidence", lineage,
                diagnostics=("worker returned contradictory compile and execution outcomes",),
                payload={
                    "total": None, "category": None, "test_outcomes": outcomes,
                    "stages": list(self.stage_order), "stage_statuses": statuses,
                    "policy_version": context.policy_version, "compiler_status": "contradictory",
                    "criterion_evidence": criterion_evidence, "criterion_limitations": criterion_limitations,
                },
                lineage=lineage, service_version=self.version,
            )
        if compile_failures:
            diagnostics = tuple(dict.fromkeys(
                item.get("stderr", "compiler rejected the submission") or "compiler rejected the submission"
                for item in compile_failures
            ))
            return ServiceResult(
                self.name, "invalid_submission", lineage, diagnostics=diagnostics,
                payload={
                    "total": None, "category": None, "components": {"syntax": 0.0},
                    "test_outcomes": outcomes, "stages": list(self.stage_order),
                    "stage_statuses": statuses, "policy_version": context.policy_version,
                    "compiler_status": "failed-isolated-compilation",
                    "criterion_evidence": criterion_evidence, "criterion_limitations": criterion_limitations,
                },
                lineage=lineage, service_version=self.version,
            )
        total_weight = sum(float(item["weight"]) for item in outcomes)
        passed_weight = sum(float(item["weight"]) for item in outcomes if item["status"] == "passed")
        if not outcomes or total_weight <= 0 or structure.status != "complete":
            return ServiceResult(self.name, "incomplete", lineage, diagnostics=("required scoring evidence unavailable",), payload={"total": None, "category": None, "stages": list(self.stage_order), "stage_statuses": statuses, "policy_version": context.policy_version, "criterion_evidence": criterion_evidence, "criterion_limitations": criterion_limitations}, lineage=lineage, service_version=self.version)
        components = {
            "structure": float(structure.payload["score"]), "syntax": 100.0,
            "tests": weighted_test_score(passed_weight, total_weight),
            "originality": legacy_originality_score(context.reference_source, context.source),
        }
        total, category = compose_total(components, weights)
        diagnostics = tuple(message for result in (complexity, concept) if result.status not in {"complete", "skipped"} for message in result.diagnostics)
        return ServiceResult(self.name, "complete", lineage, diagnostics=diagnostics, payload={
            "total": round(total, 2), "category": category, "components": components, "weights": weights,
            "test_outcomes": outcomes, "stages": list(self.stage_order) + [self.name], "stage_statuses": statuses,
            "policy_version": context.policy_version, "compiler_status": "passed-isolated-compilation",
            "criterion_evidence": criterion_evidence, "criterion_limitations": criterion_limitations,
        }, lineage=lineage, service_version=self.version)


def _concept_evidence(context: AgentContext, outcomes: tuple[dict[str, Any], ...], passed: bool) -> dict[str, tuple[str, ...]]:
    tests_by_id = {_test_value(case, "id"): case for case in context.tests if _test_value(case, "id")}
    findings: dict[str, set[str]] = {}
    for outcome in outcomes:
        if (outcome.get("status") == "passed") != passed:
            continue
        case = tests_by_id.get(outcome.get("case_id"))
        if case is None:
            continue
        for concept in _test_value(case, "concept_ids", ()):
            if context.graph and concept in context.graph.concepts:
                findings.setdefault(concept, set()).add(f"test:{outcome['case_id']}:{outcome['status']}")
    return {concept: tuple(sorted(items)) for concept, items in sorted(findings.items())}


def failed_concept_evidence(context: AgentContext, outcomes: tuple[dict[str, Any], ...]) -> dict[str, tuple[str, ...]]:
    return _concept_evidence(context, outcomes, False)


class KnowledgeGraphReasoningService:
    name = "knowledge-graph-reasoning"
    version = "1"

    def run(self, context: AgentContext, evaluation: ImplementationEvaluationResult) -> ServiceResult:
        if context.graph is None:
            return ServiceResult(self.name, "unavailable", diagnostics=("concept graph unavailable",))
        try:
            context.graph.validate()
        except GraphError as exc:
            return ServiceResult(self.name, "unavailable", diagnostics=(str(exc),))
        concept = evaluation.stages.get("concept-analysis")
        execution = evaluation.stages.get("test-execution")
        outcomes = tuple(execution.payload.get("outcomes", ())) if execution and execution.status == "complete" else ()
        weak_evidence = failed_concept_evidence(context, outcomes)
        satisfied_evidence = _concept_evidence(context, outcomes, True)
        weak, satisfied = set(weak_evidence), set(satisfied_evidence) - set(weak_evidence)
        contradictions = set(weak_evidence) & set(satisfied_evidence)
        required = set(context.required_concepts) | {item for case in context.tests for item in _test_value(case, "concept_ids", ()) if item in context.graph.concepts}
        if concept and concept.status == "complete":
            for concept_id, finding in concept.payload.get("findings", {}).items():
                if finding == "absent" and concept_id in context.graph.concepts:
                    weak.add(concept_id)
                    static = f"concept:{concept_id}:absent"
                    prior = weak_evidence.get(concept_id, ())
                    weak_evidence[concept_id] = prior if static in prior else prior + (static,)
                elif finding == "present" and concept_id not in weak:
                    satisfied.add(concept_id)
                    satisfied_evidence.setdefault(concept_id, (f"concept:{concept_id}:present",))
        unknown = required - weak - satisfied
        ordered = context.graph.prerequisite_order(weak, satisfied)
        paths: dict[str, list[str]] = {}
        for prerequisite in ordered:
            candidates = [context.graph.prerequisite_path(prerequisite, target) for target in sorted(weak)]
            paths[prerequisite] = list(min((path for path in candidates if path), key=lambda value: (len(value), value), default=(prerequisite,)))
        evidence = _unique((f"graph:{context.graph.version}",) + tuple(item for values in weak_evidence.values() for item in values) + tuple(item for values in satisfied_evidence.values() for item in values))
        return ServiceResult(self.name, "complete", evidence=evidence, payload={
            "graph_version": context.graph.version, "weak": sorted(weak), "satisfied": sorted(satisfied),
            "unknown": sorted(unknown), "contradictions": sorted(contradictions), "ordered_prerequisites": list(ordered),
            "weak_evidence": {key: list(value) for key, value in sorted(weak_evidence.items())},
            "satisfied_evidence": {key: list(value) for key, value in sorted(satisfied_evidence.items())},
            "paths": paths, "scope": "current-assessment",
        })


class FeedbackCompositionService:
    name = "feedback-composition"
    version = "3"

    def run(self, context: AgentContext, evaluation: ImplementationEvaluationResult, graph: ServiceResult) -> ServiceResult:
        scored = evaluation.evaluation
        evidence = scored.evidence or ("evidence:unavailable",)
        items: list[dict[str, Any]] = []

        def add(code: str, message: str, evidence_id: str | None = None, *, category: str = "assessment", severity: str = "info", concept_ids: tuple[str, ...] = (), guidance: tuple[str, ...] = (), confidence: float | None = 1.0, limitations: tuple[str, ...] = (), location: SourceLocation | None = None, root_cause: str | None = None) -> None:
            reference = evidence_id or evidence[0]
            items.append({
                "code": code, "message": message, "evidence_id": reference,
                "template_version": "feedback-v3", "category": category, "severity": severity,
                "explanation": message, "root_cause": root_cause or message, "evidence_refs": [reference], "concept_ids": list(concept_ids),
                "source_location": asdict(location) if location else None, "guidance": list(guidance), "confidence": confidence,
                "limitations": list(limitations),
            })

        if scored.status == "invalid_submission":
            message = scored.diagnostics[0] if scored.diagnostics else "The parser rejected this submission before functional evaluation."
            syntax = evaluation.stages.get("syntax-analysis")
            location = syntax.metadata.diagnostics[0].location if syntax and syntax.metadata and syntax.metadata.diagnostics else None
            add("fix-syntax", message, category="syntax", severity="error", guidance=("Correct the reported syntax location and submit again.",), location=location)
        elif scored.status in {"incomplete", "cancelled", "unsupported", "invalid_evidence"}:
            detail = scored.diagnostics[0] if scored.diagnostics else "Required assessment evidence is unavailable."
            add("evaluation-unavailable", f"{detail} No total score was produced.", category="availability", severity="warning", confidence=None, limitations=tuple(scored.diagnostics))
        else:
            components = scored.payload.get("components", {})
            for outcome in scored.payload.get("test_outcomes", ()):
                if outcome["status"] != "passed":
                    case_id = outcome['case_id']
                    add("failed-test", f"The submitted program did not satisfy test case {case_id}.", f"test:{case_id}:{outcome['status']}", category="functional", severity="error", guidance=("Trace the input-to-output path for this case and correct the first divergent branch.",))
            if components.get("structure", 100) < 60:
                add("review-structure", "Normalized structure evidence is below the supported similarity threshold.", category="structure", severity="warning", guidance=("Compare control flow and decomposition with the stated task requirements.",))
            complexity = evaluation.stages.get("complexity-analysis")
            if complexity and complexity.status == "complete" and int(complexity.payload.get("loop_nesting", 0)) >= 2:
                add("review-complexity", f"Static analysis found loop nesting depth {complexity.payload['loop_nesting']}.", complexity.evidence[0] if complexity.evidence else None, category="complexity", severity="warning", guidance=("Check whether repeated work can be removed or indexed.",), limitations=(str(complexity.payload.get("limitation", "Static complexity is an estimate.")),))
            elif complexity and complexity.payload.get("unsupported_indicators"):
                add("complexity-unknown", "Some complexity indicators are unsupported for this language and remain unknown.", complexity.evidence[0] if complexity.evidence else None, category="complexity", severity="warning", confidence=None, limitations=tuple(complexity.payload["unsupported_indicators"]))
            if components.get("originality", 100) < 50:
                add("similarity-heuristic", "The text-dissimilarity heuristic is low; this measure is not a plagiarism or misconduct verdict.", category="originality", severity="warning", limitations=("Text similarity is only a rubric heuristic.",))
            if not items:
                add("verified-evidence", "All available scored criteria are supported by the recorded evidence.", category="strength", severity="info")
        if graph.status == "complete":
            weak_evidence = graph.payload.get("weak_evidence", {})
            for concept_id in graph.payload.get("ordered_prerequisites", ()):
                target = graph.payload.get("paths", {}).get(concept_id, [concept_id])[-1]
                triggers = weak_evidence.get(target, [f"concept:{target}:absent"])
                guidance = context.graph.concepts[concept_id].guidance if context.graph and concept_id in context.graph.concepts else "Review this prerequisite."
                add("learning-recommendation", f"Practice {concept_id}: {guidance}", triggers[0], category="concept", severity="warning", concept_ids=(concept_id,), guidance=(guidance,))
            if graph.payload.get("contradictions"):
                add("contradictory-evidence", "Concept evidence conflicts; failed evidence is retained for current-assessment recommendations and confidence is limited.", graph.evidence[0], category="concept", severity="warning", confidence=0.5, limitations=("Conflicting concept evidence requires teacher review.",))
        overall = "The assessment is provisional because required evidence is unavailable." if scored.status != "complete" else "The explanation is derived from recorded rubric, test, structure, and concept evidence."
        return ServiceResult(self.name, "complete", evidence, payload={"items": items, "overall_explanation": overall, "teacher_explanation": {"summary": overall, "evidence_refs": list(scored.evidence)}, "evaluation_status": scored.status, "template_version": "feedback-v3"}, lineage=scored.evidence, service_version=self.version)


class LearningRecommendationService:
    name = "learning-recommendation"
    version = "2"

    def run(self, context: AgentContext, graph: ServiceResult) -> ServiceResult:
        if not context.graph or graph.status != "complete":
            return ServiceResult(self.name, "unavailable", diagnostics=("knowledge graph reasoning unavailable",), service_version=self.version)
        targets = sorted(graph.payload.get("weak", ()))
        evidence_map = graph.payload.get("weak_evidence", {})
        recommendations = []
        for concept in graph.payload.get("ordered_prerequisites", ()):
            path = graph.payload.get("paths", {}).get(concept, [concept])
            target = path[-1]
            recommendations.append({
                "concept_id": concept, "guidance": context.graph.concepts[concept].guidance,
                "graph_version": context.graph.version, "path": list(path),
                "triggering_evidence": list(evidence_map.get(target, (f"weak:{target}",))),
                "mastery_status": "weak" if concept in targets else "unknown", "scope": "current-assessment",
                "selection_rationale": f"Selected as prerequisite on the evidence path to {target}." if concept != target else f"Selected because current-assessment evidence marks {target} weak.",
            })
        return ServiceResult(self.name, "complete", tuple(f"concept:{item}" for item in graph.payload.get("ordered_prerequisites", ())), payload={"recommendations": recommendations}, service_version=self.version)


def _serialize_service(result: ServiceResult) -> dict[str, Any]:
    metadata = asdict(result.metadata) if result.metadata else None
    # Operational timing belongs to observability, not the immutable academic
    # report. Excluding it keeps identical inputs byte-for-byte deterministic.
    if metadata:
        metadata.pop("timing", None)
    return {
        "service": result.service, "agent": result.service, "kind": "internal-service",
        "service_version": result.service_version, "agent_version": result.service_version,
        "status": result.status, "evidence": list(result.evidence), "diagnostics": list(result.diagnostics),
        "payload": result.payload, "lineage": list(result.lineage),
        "metadata": metadata,
    }


class ReportCompositionService:
    name = "report-composition"
    version = "3"

    def run(self, context: AgentContext, evaluation: ImplementationEvaluationResult, graph: ServiceResult, feedback: ServiceResult, recommendations: ServiceResult, strengths: tuple[str, ...], weaknesses: tuple[str, ...]) -> ServiceResult:
        internal = list(evaluation.stages.values()) + [evaluation.evaluation, graph, feedback, recommendations]
        stage_results = [_serialize_service(result) for result in internal]
        versions = {item["service"]: item["service_version"] for item in stage_results}
        versions.update({"implementation-evaluation": evaluation.agent_version, "feedback": "1", self.name: self.version})
        limitations = tuple(message for item in stage_results if item["status"] not in {"complete", "skipped"} for message in item["diagnostics"])
        report = {
            "report_version": "assessment-report-v3", "compatible_versions": ["assessment-report-v2"], "language": context.language,
            "status": evaluation.status, "policy_version": context.policy_version,
            "graph_version": context.graph.version if context.graph else None, "versions": versions,
            "stages": stage_results, "evaluation": evaluation.evaluation.payload,
            "feedback": feedback.payload.get("items", []), "recommendations": recommendations.payload.get("recommendations", []),
            "knowledge_graph": graph.payload, "strengths": list(strengths), "weaknesses": list(weaknesses),
            "evidence_lineage": list(evaluation.evidence), "limitations": list(_unique(evaluation.limitations + limitations)),
            "trace": ["implementation-evaluation", "feedback"],
            "internal_trace": [item["service"] for item in stage_results] + [self.name],
            "overview": {
                "verified_status": evaluation.status,
                "total": evaluation.evaluation.payload.get("total"),
                "category": evaluation.evaluation.payload.get("category"),
                "overall_explanation": feedback.payload.get("overall_explanation"),
                "execution_available": evaluation.stages.get("test-execution", ServiceResult("test-execution", "unavailable")).status == "complete",
            },
            "issues": [item for item in feedback.payload.get("items", []) if item.get("severity") in {"warning", "error"}],
            "actions": [step for item in feedback.payload.get("items", []) for step in item.get("guidance", [])],
            "teacher_explanation": feedback.payload.get("teacher_explanation"),
        }
        evidence = _unique(evaluation.evidence + graph.evidence + feedback.evidence + recommendations.evidence)
        return ServiceResult(self.name, "complete", evidence, payload={"report": report}, lineage=evaluation.evidence, service_version=self.version)


class ImplementationEvaluationAgent:
    name = "implementation-evaluation"
    version = "1"
    role: Literal["main-agent"] = "main-agent"

    def __init__(self, runner: SubmissionRunner):
        self.runner = runner

    def run(self, context: AgentContext) -> ImplementationEvaluationResult:
        if context.cancelled:
            evaluation = RubricEvaluationService().run(context, {})
            return ImplementationEvaluationResult(self.name, evaluation.status, evaluation, {}, evaluation.evidence, evaluation.diagnostics, self.version)
        try:
            resolve_weights(context.policy_version, dict(context.rubric) or None)
        except ValueError:
            evaluation = RubricEvaluationService().run(context, {})
            return ImplementationEvaluationResult(self.name, evaluation.status, evaluation, {}, evaluation.evidence, evaluation.diagnostics, self.version)
        stages: dict[str, ServiceResult] = {}
        for service in (CodePreprocessingService(), SyntaxAnalysisService()):
            started = perf_counter()
            stages[service.name] = _timed(service.run(context), started)
        if all(stages[name].status == "complete" for name in ("code-preprocessing", "syntax-analysis")):
            for service in (ConceptAnalysisService(), StructuralComparisonService(), ComplexityAnalysisService(), SecureTestExecutionService(self.runner)):
                started = perf_counter()
                stages[service.name] = _timed(service.run(context), started)
        else:
            reason = "preprocessing or syntax analysis did not complete"
            evidence = _unique(stages["code-preprocessing"].evidence + stages["syntax-analysis"].evidence)
            for name in ("concept-analysis", "structural-comparison", "complexity-analysis", "test-execution"):
                stages[name] = _skipped(name, reason, evidence)
        evaluation = RubricEvaluationService().run(context, stages)
        limitations = _unique(evaluation.diagnostics + tuple(message for result in stages.values() if result.status not in {"complete", "skipped"} for message in result.diagnostics))
        return ImplementationEvaluationResult(self.name, evaluation.status, evaluation, stages, evaluation.evidence, limitations, self.version)


class FeedbackAgent:
    name = "feedback"
    version = "1"
    role: Literal["main-agent"] = "main-agent"

    def run(self, context: AgentContext, evaluation: ImplementationEvaluationResult) -> FeedbackResult:
        if not isinstance(evaluation, ImplementationEvaluationResult):
            raise TypeError("FeedbackAgent requires an ImplementationEvaluationResult")
        started = perf_counter(); graph = _timed(KnowledgeGraphReasoningService().run(context, evaluation), started)
        started = perf_counter(); feedback = _timed(FeedbackCompositionService().run(context, evaluation, graph), started)
        started = perf_counter(); recommendations = _timed(LearningRecommendationService().run(context, graph), started)
        components = evaluation.evaluation.payload.get("components", {})
        strengths = tuple(sorted(name for name, score in components.items() if float(score) >= 75.0))
        weaknesses_set = {name for name, score in components.items() if float(score) < 60.0}
        weaknesses_set.update(graph.payload.get("weak", ()) if graph.status == "complete" else ())
        weaknesses = tuple(sorted(weaknesses_set))
        report = ReportCompositionService().run(context, evaluation, graph, feedback, recommendations, strengths, weaknesses)
        limitations = _unique(evaluation.limitations + graph.diagnostics + recommendations.diagnostics)
        evidence = _unique(evaluation.evidence + graph.evidence + feedback.evidence + recommendations.evidence)
        return FeedbackResult(self.name, "complete", evaluation, graph, feedback, recommendations, report, strengths, weaknesses, evidence, limitations, self.version)


def registered_agents(runner: SubmissionRunner) -> tuple[BaseAgent, BaseAgent]:
    return ImplementationEvaluationAgent(runner), FeedbackAgent()


class AssessmentOrchestrator:
    name = "assessment-orchestrator"
    version = "3"

    def __init__(self, runner: SubmissionRunner, audit_logger: AuditLogger | None = None):
        self.runner = runner
        self.audit_logger = audit_logger or AuditLogger()

    def _emit_agent(self, context: AgentContext, agent: str, version: str, status: str, evidence: tuple[str, ...], duration_ms: float) -> None:
        self.audit_logger.emit(AuditEvent(context.correlation_id or "local", "agent_complete", status, agent, version, duration_ms, evidence, {"policy_version": context.policy_version}))

    def _trace_service(self, context: AgentContext, result: ServiceResult) -> None:
        self.audit_logger.emit(AuditEvent(context.correlation_id or "local", "stage_trace", result.status, result.service, result.service_version, evidence_ids=result.evidence))

    def run(self, context: AgentContext) -> dict[str, Any]:
        agent_one = ImplementationEvaluationAgent(self.runner)
        started = perf_counter()
        evaluation = agent_one.run(context)
        self._emit_agent(context, agent_one.name, agent_one.version, evaluation.status, evaluation.evidence, (perf_counter() - started) * 1000)
        for stage in evaluation.stages.values():
            self._trace_service(context, stage)
        self._trace_service(context, evaluation.evaluation)

        agent_two = FeedbackAgent()
        started = perf_counter()
        feedback_result = agent_two.run(context, evaluation)
        self._emit_agent(context, agent_two.name, agent_two.version, feedback_result.status, feedback_result.evidence, (perf_counter() - started) * 1000)
        for stage in (feedback_result.graph_reasoning, feedback_result.feedback, feedback_result.recommendations, feedback_result.report):
            self._trace_service(context, stage)

        stages = dict(evaluation.stages)
        stages[feedback_result.graph_reasoning.service] = feedback_result.graph_reasoning
        return {
            "orchestrator_version": self.version,
            "implementation_evaluation": evaluation,
            "feedback_agent": feedback_result,
            "stages": stages,
            "evaluation": evaluation.evaluation,
            "knowledge_graph": feedback_result.graph_reasoning,
            "feedback": feedback_result.feedback,
            "recommendations": feedback_result.recommendations,
            "report": feedback_result.report,
        }
