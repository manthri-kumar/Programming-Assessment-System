from pathlib import Path

import pytest

from concurrent.futures import ThreadPoolExecutor

from worker.entrypoint import WorkerInputError, execute_job, language_commands, validate_job


def job(**overrides):
    value = {
        "id": "a" * 32,
        "language": "python",
        "source": "print(1)\n",
        "tests": [{"id": "case", "input": ""}],
    }
    value.update(overrides)
    return value


def test_worker_protocol_validates_bounds_and_duplicate_cases_without_execution():
    assert validate_job(job())["tests"][0] == {"id": "case", "input": ""}
    with pytest.raises(WorkerInputError, match="job id"):
        validate_job(job(id="../escape"))
    with pytest.raises(WorkerInputError, match="unique"):
        validate_job(job(tests=[job()["tests"][0], job()["tests"][0]]))
    with pytest.raises(WorkerInputError, match="source"):
        validate_job(job(source="x" * (64 * 1024 + 1)))
    with pytest.raises(WorkerInputError, match="hidden expectations"):
        validate_job(job(tests=[{"id": "case", "input": "", "expected_output": "secret"}]))


def test_worker_uses_fixed_language_commands_and_workspace_paths():
    workspace = Path("/work/job")
    py_name, py_compile, py_run = language_commands("python", workspace)
    assert py_name == "Main.py" and py_compile[:4] == ("python3.11", "-I", "-B", "-m") and py_run[-1] == "Main.py"
    c_name, c_compile, c_run = language_commands("c", workspace)
    assert c_name == "Main.c" and c_compile[0] == "clang-14" and "-std=c11" in c_compile and c_run == (str(workspace / "program"),)
    java_name, java_compile, java_run = language_commands("java", workspace)
    assert java_name == "Main.java" and java_compile[0] == "javac" and ("--release", "17") == java_compile[2:4] and "-Xmx256m" in java_run and java_run[-1] == "Main"


def test_worker_entrypoint_is_installed_but_never_called_by_host_tests():
    dockerfile = (Path(__file__).parents[1] / "worker" / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY --chown=65532:65532 worker/entrypoint.py /opt/assessment-worker/bin/worker" in dockerfile
    assert 'ENTRYPOINT ["/opt/assessment-worker/bin/worker"]' in dockerfile


def test_real_worker_verifier_covers_required_failure_and_cleanup_scenarios_without_running_them():
    verifier = (Path(__file__).parents[1] / "scripts" / "worker" / "verify-local-worker.py").read_text(encoding="utf-8")
    required = {
        "python-compile", "c-compile", "java-compile",
        "crash-after-output", "timeout-with-child", "output-limit", "memory-limit", "process-limit",
        "scratch-limit", "network-denied", "host-file-denied", "outer-whitespace", "internal-whitespace",
        "cancellation", "cleanup-repeat-1", "cleanup-repeat-2",
    }
    assert all(f'"{name}"' in verifier for name in required)
    assert all(f'("{language}",' in verifier for language in ("python", "c", "java"))


def completed(stdout="", stderr="", exit_code=0, status="completed"):
    return {"status": status, "stdout": stdout, "stderr": stderr, "exit_code": exit_code}


@pytest.mark.parametrize(
    ("run_result", "expected_status"),
    [
        (completed("1\n"), "completed"),
        (completed("2\n"), "completed"),
        (completed("1\n", exit_code=3), "runtime_error"),
        (completed(status="timeout", exit_code=None), "timeout"),
        (completed(status="resource_limit", exit_code=None), "resource_limit"),
    ],
)
def test_worker_classifies_bounded_runtime_outcomes_without_host_execution(tmp_path, run_result, expected_status):
    calls = []
    def executor(command, workspace, stdin, timeout, output_limit):
        calls.append((command, workspace, stdin, timeout, output_limit))
        return completed() if len(calls) == 1 else run_result
    result = execute_job(validate_job(job()), tmp_path, executor)
    assert result["outcomes"][0]["status"] == expected_status
    assert not calls[0][1].exists()


def test_worker_compile_error_worker_failure_and_cleanup_without_host_execution(tmp_path):
    workspaces = []
    def compile_error(command, workspace, stdin, timeout, output_limit):
        workspaces.append(workspace)
        return completed(stderr="diagnostic without keyword", exit_code=1)
    result = execute_job(validate_job(job(language="c", source="int main(void){return 0;}")), tmp_path, compile_error)
    assert result["outcomes"][0]["status"] == "compile_error"
    assert result["outcomes"][0]["stderr"] == "diagnostic without keyword"
    assert all(not workspace.exists() for workspace in workspaces)

    def broken(command, workspace, stdin, timeout, output_limit):
        workspaces.append(workspace)
        raise RuntimeError("simulated worker failure")
    with pytest.raises(RuntimeError, match="simulated worker failure"):
        execute_job(validate_job(job()), tmp_path, broken)
    assert all(not workspace.exists() for workspace in workspaces)


def test_overlapping_jobs_use_unique_workspaces_and_remove_them(tmp_path):
    observed = []
    def run_one(index):
        candidate = validate_job(job(id=f"{index:032x}", source=f"print({index})\n", tests=[{"id": "case", "input": ""}]))
        call_count = 0
        def executor(command, workspace, stdin, timeout, output_limit):
            nonlocal call_count
            call_count += 1
            observed.append(workspace)
            return completed() if call_count == 1 else completed(f"{index}\n")
        return execute_job(candidate, tmp_path, executor)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_one, range(1, 5)))
    assert all(result["outcomes"][0]["status"] == "completed" for result in results)
    assert len({str(path) for path in observed}) == 4
    assert all(not path.exists() for path in observed)
