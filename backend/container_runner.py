from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
import re
import uuid
from typing import Protocol, Sequence

from backend.runner import ExecutionLimits, RunnerUnavailable, RunStatus, TestRun


DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_CONTROL_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class ContainerPolicy:
    image: str
    image_digest: str
    memory_bytes: int = 256 * 1024 * 1024
    java_memory_bytes: int = 512 * 1024 * 1024
    cpu_count: float = 1.0
    limits: ExecutionLimits = ExecutionLimits()

    def validate(self) -> None:
        if not self.image or not DIGEST_PATTERN.fullmatch(self.image_digest):
            raise ValueError("a pinned sha256 worker image digest is required")
        if self.memory_bytes <= 0 or self.java_memory_bytes <= 0 or self.cpu_count <= 0:
            raise ValueError("container resource limits must be positive")
        if any(value <= 0 for value in (
            self.limits.compile_seconds, self.limits.test_seconds,
            self.limits.job_seconds, self.limits.output_bytes,
            self.limits.scratch_bytes, self.limits.process_count,
        )):
            raise ValueError("execution limits must be positive")

    @property
    def image_reference(self) -> str:
        self.validate()
        return f"{self.image}@{self.image_digest}"

    def isolation_arguments(self, language: str, job_id: str) -> tuple[str, ...]:
        self.validate()
        memory = self.java_memory_bytes if language == "java" else self.memory_bytes
        return (
            "--name", f"assessment-{job_id}",
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--pids-limit", str(self.limits.process_count),
            "--memory", str(memory),
            "--cpus", str(self.cpu_count),
            "--tmpfs", f"/work:rw,nosuid,nodev,size={self.limits.scratch_bytes},mode=1770,uid=65532,gid=65532",
            "--init",
            "--user", "65532:65532",
        )


@dataclass(frozen=True)
class ContainerJob:
    id: str
    language: str
    source: str
    reference_source: str
    tests: tuple[object, ...]


class IsolatedEngine(Protocol):
    def ready(self, image_reference: str) -> bool: ...
    def execute(self, job: ContainerJob, policy: ContainerPolicy) -> tuple[TestRun, ...]: ...
    def cleanup(self, job_id: str) -> None: ...


def _case_value(case: object, key: str, default: object = None) -> object:
    return case.get(key, default) if isinstance(case, dict) else getattr(case, key, default)


def serialize_worker_job(job: ContainerJob) -> bytes:
    """Serialize the allowlisted worker protocol without host paths or commands."""
    tests = []
    for case in job.tests:
        tests.append({
            "id": _case_value(case, "id"),
            "input": _case_value(case, "input", ""),
            "expected_output": _case_value(case, "expected_output", ""),
            "weight": _case_value(case, "weight"),
        })
    payload = {"id": job.id, "language": job.language, "source": job.source, "tests": tests}
    try:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RunnerUnavailable("worker request is not serializable") from exc
    if len(encoded) > MAX_CONTROL_BYTES:
        raise RunnerUnavailable("worker request exceeds control-channel limit")
    return encoded


def parse_worker_response(data: bytes, job: ContainerJob, policy: ContainerPolicy) -> tuple[TestRun, ...]:
    """Validate a worker response before it becomes assessment evidence."""
    if len(data) > MAX_CONTROL_BYTES:
        raise RunnerUnavailable("worker response exceeds control-channel limit")
    try:
        payload = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerUnavailable("worker returned malformed JSON") from exc
    if not isinstance(payload, dict):
        raise RunnerUnavailable("worker returned an invalid response")
    if "error" in payload:
        error = payload["error"] if isinstance(payload["error"], dict) else {}
        code = error.get("code", "worker_failure")
        raise RunnerUnavailable(f"isolated worker failed: {code}")
    if payload.get("job_id") != job.id or not isinstance(payload.get("outcomes"), list):
        raise RunnerUnavailable("worker response does not match the job")
    expected = {_case_value(case, "id"): case for case in job.tests}
    if len(expected) != len(job.tests):
        raise RunnerUnavailable("worker job contains duplicate test ids")
    outcomes: list[TestRun] = []
    seen: set[str] = set()
    for item in payload["outcomes"]:
        if not isinstance(item, dict):
            raise RunnerUnavailable("worker outcome is invalid")
        case_id = item.get("case_id")
        if case_id not in expected or case_id in seen:
            raise RunnerUnavailable("worker outcome ids do not match the job")
        try:
            status = RunStatus(item.get("status"))
        except ValueError as exc:
            raise RunnerUnavailable("worker returned an unknown outcome status") from exc
        stdout, stderr = item.get("stdout", ""), item.get("stderr", "")
        if not isinstance(stdout, str) or not isinstance(stderr, str):
            raise RunnerUnavailable("worker streams must be text")
        if len(stdout.encode("utf-8")) > policy.limits.output_bytes or len(stderr.encode("utf-8")) > policy.limits.output_bytes:
            raise RunnerUnavailable("worker returned an oversized stream")
        expected_weight = float(_case_value(expected[case_id], "weight"))
        weight = item.get("weight")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or not isfinite(float(weight)) or float(weight) != expected_weight:
            raise RunnerUnavailable("worker outcome weight does not match the job")
        exit_code = item.get("exit_code")
        if exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
            raise RunnerUnavailable("worker exit code is invalid")
        if status in {RunStatus.PASSED, RunStatus.WRONG_OUTPUT} and exit_code != 0:
            raise RunnerUnavailable("worker success outcome requires a zero exit code")
        seen.add(case_id)
        outcomes.append(TestRun(case_id, status, stdout, stderr, exit_code, expected_weight))
    if seen != set(expected):
        raise RunnerUnavailable("worker response omitted test outcomes")
    return tuple(outcomes)


class ContainerRunner:
    """Control-plane adapter for an external isolated engine.

    The adapter never invokes a host compiler or submission process. The engine
    must provide the protected container/VM control channel and enforce policy.
    """

    def __init__(self, engine: IsolatedEngine, policy: ContainerPolicy) -> None:
        self.engine = engine
        self.policy = policy

    def ready(self) -> bool:
        try:
            return self.engine.ready(self.policy.image_reference)
        except Exception:
            return False

    def run(self, language: str, source: str, reference_source: str, tests: Sequence[object]) -> tuple[TestRun, ...]:
        if language not in {"python", "c", "java"}:
            raise RunnerUnavailable("unsupported language")
        if not self.ready():
            raise RunnerUnavailable("pinned isolated worker is unavailable")
        job = ContainerJob(uuid.uuid4().hex, language, source, reference_source, tuple(tests))
        try:
            try:
                return self.engine.execute(job, self.policy)
            except RunnerUnavailable:
                raise
            except Exception as exc:
                raise RunnerUnavailable("isolated worker execution failed") from exc
        finally:
            try:
                self.engine.cleanup(job.id)
            except Exception as exc:
                raise RunnerUnavailable("isolated worker cleanup failed") from exc
