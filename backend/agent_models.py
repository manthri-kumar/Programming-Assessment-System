from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict, TypeAlias


AgentStatus: TypeAlias = Literal[
    "complete", "invalid_submission", "invalid_evidence", "incomplete",
    "unavailable", "unsupported", "undetermined", "analysis_limit",
    "cancelled", "skipped",
]

EvidenceClassification: TypeAlias = Literal[
    "verified", "learner-error", "unsupported", "analysis-limit",
    "infrastructure-unavailable", "contradictory", "cancelled", "skipped",
]


@dataclass(frozen=True, slots=True)
class SourceLocation:
    line: int
    column: int = 1
    end_line: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        if self.line < 1 or self.column < 1:
            raise ValueError("source locations are one-based")
        if self.end_line is not None and self.end_line < self.line:
            raise ValueError("source location end precedes start")
        if self.end_column is not None and self.end_column < 1:
            raise ValueError("source location end column must be positive")


@dataclass(frozen=True, slots=True)
class StageDiagnostic:
    code: str
    classification: EvidenceClassification
    message: str
    severity: Literal["info", "warning", "error"]
    evidence_refs: tuple[str, ...] = ()
    location: SourceLocation | None = None

    def __post_init__(self) -> None:
        if not self.code or len(self.code) > 80:
            raise ValueError("diagnostic code must contain at most 80 characters")
        if not self.message or len(self.message) > 4096:
            raise ValueError("diagnostic message must contain at most 4096 characters")
        if len(self.evidence_refs) > 64 or any(not value or len(value) > 256 for value in self.evidence_refs):
            raise ValueError("diagnostic evidence references are invalid or unbounded")


@dataclass(frozen=True, slots=True)
class OperationalTiming:
    duration_ms: float

    def __post_init__(self) -> None:
        if self.duration_ms < 0 or self.duration_ms > 3_600_000:
            raise ValueError("stage duration is outside the supported bound")


@dataclass(frozen=True, slots=True)
class StageMetadata:
    schema_version: Literal["stage-evidence-v1"] = "stage-evidence-v1"
    classification: EvidenceClassification = "verified"
    diagnostics: tuple[StageDiagnostic, ...] = ()
    limitations: tuple[str, ...] = ()
    confidence: float | None = None
    timing: OperationalTiming | None = None

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between zero and one")
        if len(self.diagnostics) > 64:
            raise ValueError("stage diagnostic count exceeds 64")
        if len(self.limitations) > 32 or any(not item or len(item) > 1000 for item in self.limitations):
            raise ValueError("stage limitations are invalid or unbounded")


class PreprocessingPayload(TypedDict):
    node_count: int
    ir_version: str


class SyntaxPayload(TypedDict):
    parser: str
    compiler_authority: Literal["verified", "pending-isolated-worker"]


class ConceptPayload(TypedDict):
    findings: dict[str, Literal["present", "absent", "unmapped"]]
    detected: list[str]
    detector_version: str


class StructuralPayload(TypedDict):
    score: float
    distance: int
    relation: Literal["equivalent", "different"]
    student_nodes: int
    reference_nodes: int
    operations: int
    metric_version: str


class ComplexityPayload(TypedDict):
    estimate: str
    loop_nesting: int
    loop_locations: list[int]
    recursion: bool | None
    unsupported_indicators: list[str]
    ir_nodes: int
    metric_version: str
    limitation: str


class TestOutcomePayload(TypedDict):
    case_id: str
    status: str
    stdout: str
    stderr: str
    exit_code: int | None
    weight: float


class ExecutionPayload(TypedDict):
    outcomes: tuple[TestOutcomePayload, ...]
    isolation: Literal["approved-runner"]


class KnowledgeGraphPayload(TypedDict):
    graph_version: str
    weak: list[str]
    satisfied: list[str]
    unknown: list[str]
    contradictions: list[str]
    ordered_prerequisites: list[str]
    weak_evidence: dict[str, list[str]]
    satisfied_evidence: dict[str, list[str]]
    paths: dict[str, list[str]]
    scope: Literal["current-assessment"]


class EvaluationPayload(TypedDict):
    total: float | None
    category: str | None
    components: NotRequired[dict[str, float]]
    weights: NotRequired[dict[str, float]]
    test_outcomes: NotRequired[tuple[TestOutcomePayload, ...]]
    stages: list[str]
    stage_statuses: NotRequired[dict[str, str]]
    policy_version: NotRequired[str]


class FeedbackItem(TypedDict):
    code: str
    message: str
    evidence_id: str
    template_version: str
    category: NotRequired[str]
    severity: NotRequired[str]
    explanation: NotRequired[str]
    root_cause: NotRequired[str]
    evidence_refs: NotRequired[list[str]]
    concept_ids: NotRequired[list[str]]
    source_location: NotRequired[dict[str, int] | None]
    guidance: NotRequired[list[str]]
    confidence: NotRequired[float | None]
    limitations: NotRequired[list[str]]


class FeedbackPayload(TypedDict):
    items: list[FeedbackItem]
    evaluation_status: str
    template_version: str


class RecommendationPayload(TypedDict):
    recommendations: list[dict[str, Any]]


class ReportPayload(TypedDict):
    report: dict[str, Any]


class SkippedPayload(TypedDict):
    reason: str


AgentPayload: TypeAlias = (
    PreprocessingPayload | SyntaxPayload | ConceptPayload | StructuralPayload |
    ComplexityPayload | ExecutionPayload | KnowledgeGraphPayload |
    EvaluationPayload | FeedbackPayload | RecommendationPayload |
    ReportPayload | SkippedPayload | dict[str, Any]
)
