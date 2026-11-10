#!/usr/bin/env python3
"""Single-job worker process intended to run inside the locked container.

This module is never used as a host execution fallback. The container control
plane supplies one bounded JSON job on stdin and receives one JSON response.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable


MAX_CONTROL_BYTES = 8 * 1024 * 1024
MAX_SOURCE_BYTES = 64 * 1024
MAX_TESTS = 50
JOB_ID = re.compile(r"^[a-f0-9]{32}$")


class WorkerInputError(ValueError):
    pass


def validate_job(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkerInputError("job must be an object")
    job_id = value.get("id")
    language = value.get("language")
    source = value.get("source")
    tests = value.get("tests")
    if not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
        raise WorkerInputError("invalid job id")
    if language not in {"python", "c", "java"}:
        raise WorkerInputError("unsupported language")
    if not isinstance(source, str) or len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise WorkerInputError("invalid source")
    if not isinstance(tests, list) or not 1 <= len(tests) <= MAX_TESTS:
        raise WorkerInputError("tests must contain 1 to 50 cases")
    ids: set[str] = set()
    normalized = []
    for item in tests:
        if not isinstance(item, dict):
            raise WorkerInputError("test must be an object")
        case_id = item.get("id")
        stdin = item.get("input", "")
        if not isinstance(case_id, str) or not case_id or len(case_id) > 128 or case_id in ids:
            raise WorkerInputError("test ids must be unique bounded strings")
        if not isinstance(stdin, str) or len(stdin.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise WorkerInputError("invalid test input")
        if "expected_output" in item or "weight" in item:
            raise WorkerInputError("hidden expectations must not enter the job container")
        ids.add(case_id)
        normalized.append({"id": case_id, "input": stdin})
    return {"id": job_id, "language": language, "source": source, "tests": normalized}


def language_commands(language: str, workspace: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    if language == "python":
        return "Main.py", ("python3.11", "-I", "-B", "-m", "py_compile", "Main.py"), ("python3.11", "-I", "-B", "Main.py")
    if language == "c":
        return "Main.c", ("clang-14", "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror=implicit-function-declaration", "-o", "program", "Main.c"), (str(workspace / "program"),)
    if language == "java":
        return "Main.java", ("javac", "-J-Djava.io.tmpdir=/work", "--release", "17", "-encoding", "UTF-8", "Main.java"), ("java", "-Djava.io.tmpdir=/work", "-XX:-UsePerfData", "-Xms16m", "-Xmx256m", "-XX:ActiveProcessorCount=1", "-cp", ".", "Main")
    raise WorkerInputError("unsupported language")


def _terminate_group(process: subprocess.Popen[bytes]) -> None:
    # Descendants can outlive the group leader and keep its pipes/workspace open.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=1)


def capture_process(command: tuple[str, ...], workspace: Path, stdin: str, timeout: float, output_limit: int, *, environment: dict[str, str] | None = None) -> dict[str, Any]:
    process = subprocess.Popen(
        command,
        cwd=workspace,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment if environment is not None else {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "HOME": "/nonexistent", "TMPDIR": "/work"},
        start_new_session=True,
    )
    assert process.stdin and process.stdout and process.stderr
    selector = selectors.DefaultSelector()
    deadline = time.monotonic() + timeout
    try:
        pending_input = memoryview(stdin.encode("utf-8"))
        for stream in (process.stdin, process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
        if pending_input:
            selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
        else:
            process.stdin.close()
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        streams = {"stdout": bytearray(), "stderr": bytearray()}
        exceeded = False
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _terminate_group(process)
                return {"status": "timeout", "stdout": _decode(streams["stdout"]), "stderr": _decode(streams["stderr"]), "exit_code": None}
            events = selector.select(min(remaining, 0.1))
            for key, _ in events:
                if key.data == "stdin":
                    try:
                        written = os.write(key.fileobj.fileno(), pending_input[:8192])
                        pending_input = pending_input[written:]
                    except BrokenPipeError:
                        pending_input = pending_input[:0]
                    except BlockingIOError:
                        continue
                    if not pending_input:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    continue
                try:
                    chunk = os.read(key.fileobj.fileno(), 8192)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                target = streams[key.data]
                room = output_limit - len(target)
                target.extend(chunk[:max(0, room)])
                exceeded = exceeded or len(chunk) > room
            if exceeded:
                _terminate_group(process)
                return {"status": "resource_limit", "stdout": _decode(streams["stdout"]), "stderr": _decode(streams["stderr"]), "exit_code": None}
        try:
            exit_code = process.wait(timeout=max(0.001, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "stdout": _decode(streams["stdout"]), "stderr": _decode(streams["stderr"]), "exit_code": None}
        return {"status": "completed", "stdout": _decode(streams["stdout"]), "stderr": _decode(streams["stderr"]), "exit_code": exit_code}
    finally:
        try:
            _terminate_group(process)
        finally:
            selector.close()
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()


def _decode(value: bytearray) -> str:
    # Replacement characters must not expand the output beyond its byte budget.
    return bytes(value).decode("utf-8", errors="replace").encode("utf-8")[:len(value)].decode("utf-8", errors="ignore")


ProcessExecutor = Callable[[tuple[str, ...], Path, str, float, int], dict[str, Any]]


def execute_job(
    job: dict[str, Any],
    workspace_root: Path = Path("/work"),
    process_executor: ProcessExecutor = capture_process,
) -> dict[str, Any]:
    started = time.monotonic()
    workspace = Path(tempfile.mkdtemp(prefix=f"{job['id']}-", dir=workspace_root))
    try:
        filename, compile_command, run_command = language_commands(job["language"], workspace)
        (workspace / filename).write_text(job["source"], encoding="utf-8")
        compiled = process_executor(compile_command, workspace, "", 10.0, 64 * 1024)
        if compiled["status"] != "completed" or compiled["exit_code"] != 0:
            status = "compile_error" if compiled["status"] == "completed" else compiled["status"]
            return {"job_id": job["id"], "outcomes": [
                {"case_id": item["id"], "status": status, "stdout": compiled["stdout"], "stderr": compiled["stderr"], "exit_code": compiled["exit_code"]}
                for item in job["tests"]
            ]}
        outcomes = []
        for item in job["tests"]:
            remaining = 120.0 - (time.monotonic() - started)
            if remaining <= 0:
                outcome = {"status": "timeout", "stdout": "", "stderr": "aggregate job deadline exceeded", "exit_code": None}
            else:
                outcome = process_executor(run_command, workspace, item["input"], min(2.0, remaining), 64 * 1024)
            status = outcome["status"]
            if status == "completed":
                if outcome["exit_code"] != 0:
                    status = "runtime_error"
            outcomes.append({"case_id": item["id"], "status": status, "stdout": outcome["stdout"], "stderr": outcome["stderr"], "exit_code": outcome["exit_code"]})
        return {"job_id": job["id"], "outcomes": outcomes}
    finally:
        shutil.rmtree(workspace, ignore_errors=False)


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_CONTROL_BYTES + 1)
        if len(raw) > MAX_CONTROL_BYTES:
            raise WorkerInputError("control request too large")
        job = validate_job(json.loads(raw))
        response = execute_job(job)
    except (WorkerInputError, UnicodeError, json.JSONDecodeError) as exc:
        response = {"error": {"code": "invalid_job", "message": str(exc)}}
        print(json.dumps(response, separators=(",", ":"), sort_keys=True))
        return 2
    except Exception as exc:
        response = {"error": {"code": "worker_failure", "message": type(exc).__name__}}
        print(json.dumps(response, separators=(",", ":"), sort_keys=True))
        return 1
    print(json.dumps(response, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
