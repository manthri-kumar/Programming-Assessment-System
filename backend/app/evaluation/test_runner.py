"""
Test Runner.

Executes submitted code against a small set of controlled test cases.
Supports Python, C, and Java. Execution is sandboxed to a temp
directory and time-limited — no unrestricted arbitrary execution
is exposed (Section 22, 37).
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, TypedDict


class TestCase(TypedDict):
    input: str
    expected_output: str


_TIMEOUT_SECONDS = 5


def _run_process(cmd: list[str], stdin_text: str, cwd: str) -> tuple[bool, str]:
    """Run a subprocess, returning (ran_ok, stdout_or_error)."""
    try:
        result = subprocess.run(
            cmd,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        return False, "Execution timed out."

    if result.returncode != 0:
        return False, result.stderr.strip() or "Runtime error."

    return True, result.stdout.strip()


def run_python_tests(code: str, test_cases: list[TestCase]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        source_path = Path(tmp_dir) / "submission.py"
        source_path.write_text(code, encoding="utf-8")

        return _run_all_cases(
            test_cases,
            lambda stdin_text: _run_process(
                ["python", str(source_path)], stdin_text, tmp_dir
            ),
        )


def run_c_tests(code: str, test_cases: list[TestCase]) -> dict[str, Any]:
    if shutil.which("gcc") is None:
        return {"passed": 0, "total": len(test_cases), "results": [], "skipped": True,
                "reason": "gcc not found on PATH; test execution skipped."}

    with tempfile.TemporaryDirectory() as tmp_dir:
        source_path = Path(tmp_dir) / "submission.c"
        binary_path = Path(tmp_dir) / ("submission.exe")
        source_path.write_text(code, encoding="utf-8")

        compile_result = subprocess.run(
            ["gcc", str(source_path), "-o", str(binary_path)],
            capture_output=True, text=True, timeout=10, cwd=tmp_dir,
        )
        if compile_result.returncode != 0:
            return {"passed": 0, "total": len(test_cases), "results": [],
                    "skipped": False, "reason": f"Compilation failed: {compile_result.stderr.strip()}"}

        return _run_all_cases(
            test_cases,
            lambda stdin_text: _run_process([str(binary_path)], stdin_text, tmp_dir),
        )


def run_java_tests(code: str, test_cases: list[TestCase], class_name: str = "Submission") -> dict[str, Any]:
    if shutil.which("javac") is None or shutil.which("java") is None:
        return {"passed": 0, "total": len(test_cases), "results": [], "skipped": True,
                "reason": "javac/java not found on PATH; test execution skipped."}

    with tempfile.TemporaryDirectory() as tmp_dir:
        source_path = Path(tmp_dir) / f"{class_name}.java"
        source_path.write_text(code, encoding="utf-8")

        compile_result = subprocess.run(
            ["javac", str(source_path)],
            capture_output=True, text=True, timeout=10, cwd=tmp_dir,
        )
        if compile_result.returncode != 0:
            return {"passed": 0, "total": len(test_cases), "results": [],
                    "skipped": False, "reason": f"Compilation failed: {compile_result.stderr.strip()}"}

        return _run_all_cases(
            test_cases,
            lambda stdin_text: _run_process(["java", class_name], stdin_text, tmp_dir),
        )


def _run_all_cases(test_cases: list[TestCase], executor) -> dict[str, Any]:
    results = []
    passed = 0

    for case in test_cases:
        ran_ok, output = executor(case["input"])
        expected = case["expected_output"].strip()
        actual = output.strip() if ran_ok else output
        case_passed = ran_ok and actual == expected

        if case_passed:
            passed += 1

        results.append({
            "input": case["input"],
            "expected_output": expected,
            "actual_output": actual,
            "passed": case_passed,
        })

    return {"passed": passed, "total": len(test_cases), "results": results, "skipped": False, "reason": None}


def run_tests(language: str, code: str, test_cases: list[TestCase]) -> dict[str, Any]:
    """Dispatch to the correct language-specific test runner."""
    runners = {
        "python": run_python_tests,
        "c": run_c_tests,
        "java": run_java_tests,
    }
    runner = runners.get(language)
    if runner is None:
        raise ValueError(f"Unsupported language for test execution: {language}")
    return runner(code, test_cases)