from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence


class RunnerUnavailable(RuntimeError):
    """Raised when the approved isolation backend is not ready."""


class RunStatus(str, Enum):
    PASSED = "passed"
    WRONG_OUTPUT = "wrong_output"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
    COMPILE_ERROR = "compile_error"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ExecutionLimits:
    compile_seconds: float = 10.0
    test_seconds: float = 2.0
    job_seconds: float = 120.0
    output_bytes: int = 64 * 1024
    scratch_bytes: int = 16 * 1024 * 1024
    process_count: int = 64


@dataclass(frozen=True)
class TestRun:
    __test__ = False
    case_id: str
    status: RunStatus
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    weight: float = 0.0


class SubmissionRunner(Protocol):
    def ready(self) -> bool: ...

    def run(self, language: str, source: str, reference_source: str, tests: Sequence[object]) -> tuple[TestRun, ...]: ...


class FailClosedRunner:
    """Production placeholder until the isolated Linux worker is configured.

    It deliberately has no host subprocess fallback. Calling ``run`` is always
    an explicit infrastructure failure, which prevents accidental unsafe use.
    """

    def __init__(self, reason: str = "isolated execution worker is unavailable", limits: ExecutionLimits | None = None) -> None:
        self.reason = reason
        self.limits = limits or ExecutionLimits()

    def ready(self) -> bool:
        return False

    def run(self, language: str, source: str, reference_source: str, tests: Sequence[object]) -> tuple[TestRun, ...]:
        raise RunnerUnavailable(self.reason)


class FakeRunner:
    """Deterministic runner for domain tests; it never executes source text."""

    def __init__(self, outcomes: Sequence[TestRun], available: bool = True) -> None:
        self.outcomes = tuple(outcomes)
        self.available = available

    def ready(self) -> bool:
        return self.available

    def run(self, language: str, source: str, reference_source: str, tests: Sequence[object]) -> tuple[TestRun, ...]:
        if not self.available:
            raise RunnerUnavailable("fake runner configured unavailable")
        return self.outcomes
