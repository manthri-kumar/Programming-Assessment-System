import pytest

from backend.container_runner import (
    ContainerJob, ContainerPolicy, ContainerRunner,
    parse_worker_response, serialize_worker_job,
)
from backend.runner import RunStatus, RunnerUnavailable, TestRun


DIGEST = "sha256:" + "a" * 64


class RecordingEngine:
    def __init__(self, available=True):
        self.available = available
        self.jobs = []
        self.cleaned = []

    def ready(self, image_reference):
        self.image_reference = image_reference
        return self.available

    def execute(self, job, policy):
        self.jobs.append(job)
        return (TestRun("case", RunStatus.PASSED, weight=1),)

    def cleanup(self, job_id):
        self.cleaned.append(job_id)


class FailingEngine(RecordingEngine):
    def __init__(self, *, fail_execute=False, fail_cleanup=False):
        super().__init__()
        self.fail_execute = fail_execute
        self.fail_cleanup = fail_cleanup

    def execute(self, job, policy):
        self.jobs.append(job)
        if self.fail_execute:
            raise RuntimeError("engine detail must not escape")
        return super().execute(job, policy)

    def cleanup(self, job_id):
        self.cleaned.append(job_id)
        if self.fail_cleanup:
            raise RuntimeError("cleanup detail must not escape")


def test_policy_requires_digest_and_contains_required_isolation_flags():
    policy = ContainerPolicy("example/worker", DIGEST)
    args = policy.isolation_arguments("c", "job")
    joined = " ".join(args)
    assert policy.image_reference == f"example/worker@{DIGEST}"
    for expected in ("--network none", "--read-only", "--cap-drop ALL", "no-new-privileges:true", "--pids-limit 64", "--user 65532:65532", "--init"):
        assert expected in joined
    assert "nosuid,nodev" in joined and "noexec" not in joined
    assert "--volume" not in args and "--mount" not in args
    with pytest.raises(ValueError):
        ContainerPolicy("example/worker", "latest").validate()


def test_runner_uses_unique_jobs_and_always_requests_cleanup():
    engine = RecordingEngine()
    runner = ContainerRunner(engine, ContainerPolicy("example/worker", DIGEST))
    runner.run("python", "print(1)", "print(1)", ())
    runner.run("python", "print(2)", "print(2)", ())
    assert len({job.id for job in engine.jobs}) == 2
    assert engine.cleaned == [job.id for job in engine.jobs]


def test_runner_fails_closed_when_engine_or_digest_is_unavailable():
    unavailable = ContainerRunner(RecordingEngine(False), ContainerPolicy("example/worker", DIGEST))
    with pytest.raises(RunnerUnavailable):
        unavailable.run("c", "int main(){}", "int main(){}", ())
    invalid = ContainerRunner(RecordingEngine(), ContainerPolicy("example/worker", ""))
    assert invalid.ready() is False
    with pytest.raises(RunnerUnavailable):
        invalid.run("java", "class Main {}", "class Main {}", ())


def test_runner_wraps_engine_failures_and_always_attempts_cleanup():
    execute_failure = FailingEngine(fail_execute=True)
    runner = ContainerRunner(execute_failure, ContainerPolicy("example/worker", DIGEST))
    with pytest.raises(RunnerUnavailable, match="execution failed"):
        runner.run("python", "print(1)", "print(1)", ())
    assert len(execute_failure.cleaned) == 1

    cleanup_failure = FailingEngine(fail_cleanup=True)
    runner = ContainerRunner(cleanup_failure, ContainerPolicy("example/worker", DIGEST))
    with pytest.raises(RunnerUnavailable, match="cleanup failed"):
        runner.run("python", "print(1)", "print(1)", ())


def test_worker_protocol_round_trip_and_rejects_untrusted_response_fields():
    tests = ({"id": "case", "input": "", "expected_output": "1", "weight": 1.0},)
    job = ContainerJob("a" * 32, "python", "print(1)", "print(1)", tests)
    encoded = serialize_worker_job(job)
    assert b"reference_source" not in encoded and b"print(1)" in encoded
    response = b'{"job_id":"' + b"a" * 32 + b'","outcomes":[{"case_id":"case","status":"passed","stdout":"1\\n","stderr":"","exit_code":0,"weight":1.0}]}'
    outcomes = parse_worker_response(response, job, ContainerPolicy("example/worker", DIGEST))
    assert outcomes == (TestRun("case", RunStatus.PASSED, "1\n", "", 0, 1.0),)

    wrong_id = response.replace(b'"case"', b'"other"')
    with pytest.raises(RunnerUnavailable, match="ids"):
        parse_worker_response(wrong_id, job, ContainerPolicy("example/worker", DIGEST))
    oversized = b'{"job_id":"' + b"a" * 32 + b'","outcomes":[{"case_id":"case","status":"passed","stdout":"' + b"x" * (64 * 1024 + 1) + b'","stderr":"","exit_code":0,"weight":1.0}]}'
    with pytest.raises(RunnerUnavailable, match="oversized"):
        parse_worker_response(oversized, job, ContainerPolicy("example/worker", DIGEST))


def test_policy_rejects_nonpositive_server_limits():
    from backend.runner import ExecutionLimits
    with pytest.raises(ValueError, match="execution limits"):
        ContainerPolicy("example/worker", DIGEST, limits=ExecutionLimits(test_seconds=0)).validate()
