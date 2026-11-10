from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any


MAX_SOURCE_BYTES = 64 * 1024
MAX_TESTS = 50
MAX_TEXT_BYTES = 64 * 1024


class Language(str, Enum):
    PYTHON = "python"
    C = "c"
    JAVA = "java"


class AssessmentStatus(str, Enum):
    COMPLETE = "complete"
    INVALID_SUBMISSION = "invalid_submission"
    INCOMPLETE = "incomplete"


class ComponentStatus(str, Enum):
    COMPLETE = "complete"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"


class ValidationError(ValueError):
    pass


def _size(value: str, field_name: str, limit: int) -> None:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be text")
    if len(value.encode("utf-8")) > limit:
        raise ValidationError(f"{field_name} exceeds {limit} UTF-8 bytes")


@dataclass(frozen=True)
class TestCase:
    __test__ = False
    id: str
    input: str
    expected_output: str
    weight: float
    concept_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id or len(self.id) > 128:
            raise ValidationError("test id must be nonempty and at most 128 characters")
        _size(self.input, "test input", MAX_TEXT_BYTES)
        _size(self.expected_output, "expected output", MAX_TEXT_BYTES)
        if not isfinite(self.weight) or self.weight <= 0:
            raise ValidationError("test weight must be positive and finite")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ValidationError("concept ids must be unique per test")


@dataclass(frozen=True)
class AssessmentRequest:
    language: Language
    source: str
    reference_source: str
    tests: tuple[TestCase, ...]
    policy_version: str = "core-v1"

    def __post_init__(self) -> None:
        _size(self.source, "source", MAX_SOURCE_BYTES)
        _size(self.reference_source, "reference_source", MAX_SOURCE_BYTES)
        if not self.source.strip() or not self.reference_source.strip():
            raise ValidationError("source and reference_source must not be blank")
        if not self.tests or len(self.tests) > MAX_TESTS:
            raise ValidationError(f"tests must contain 1 to {MAX_TESTS} cases")
        ids = [case.id for case in self.tests]
        if len(ids) != len(set(ids)):
            raise ValidationError("test ids must be unique")
        if self.policy_version not in {"legacy-v1", "core-v1"}:
            raise ValidationError("unsupported policy version")


@dataclass(frozen=True)
class Evidence:
    id: str
    kind: str
    message: str
    concept_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentResult:
    name: str
    status: ComponentStatus
    score: float | None = None
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class AssessmentResult:
    status: AssessmentStatus
    policy_version: str
    components: tuple[ComponentResult, ...]
    total: float | None = None
    category: str | None = None
    diagnostics: tuple[Evidence, ...] = ()
    feedback: tuple[str, ...] = ()
    recommendations: tuple[dict[str, Any], ...] = ()
