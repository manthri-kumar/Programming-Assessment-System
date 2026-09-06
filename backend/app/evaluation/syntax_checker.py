"""
Syntax Checker.

Language-specific syntax checking:
    - Python: ast.parse
    - C: gcc (if available on PATH)
    - Java: javac (if available on PATH)

Gracefully degrades if gcc/javac are not installed — never crashes
the API (Section 21, 37).
"""

import ast
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def check_python_syntax(code: str) -> dict[str, Any]:
    """Check Python syntax using ast.parse."""
    try:
        ast.parse(code)
        return {"valid": True, "errors": [], "warnings": []}
    except SyntaxError as e:
        return {
            "valid": False,
            "errors": [f"Line {e.lineno}: {e.msg}"],
            "warnings": [],
        }


def check_c_syntax(code: str) -> dict[str, Any]:
    """Check C syntax using gcc, if available."""
    if shutil.which("gcc") is None:
        return {
            "valid": None,
            "errors": [],
            "warnings": ["gcc not found on PATH; syntax check skipped."],
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        source_path = Path(tmp_dir) / "submission.c"
        source_path.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                ["gcc", "-fsyntax-only", str(source_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "errors": ["gcc timed out while checking syntax."],
                "warnings": [],
            }

        if result.returncode == 0:
            return {"valid": True, "errors": [], "warnings": []}

        errors = [
            line.strip()
            for line in result.stderr.splitlines()
            if "error" in line.lower()
        ]
        return {"valid": False, "errors": errors or [result.stderr.strip()], "warnings": []}


def check_java_syntax(code: str, class_name: str = "Submission") -> dict[str, Any]:
    """Check Java syntax using javac, if available."""
    if shutil.which("javac") is None:
        return {
            "valid": None,
            "errors": [],
            "warnings": ["javac not found on PATH; syntax check skipped."],
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        source_path = Path(tmp_dir) / f"{class_name}.java"
        source_path.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                ["javac", str(source_path)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=tmp_dir,
            )
        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "errors": ["javac timed out while checking syntax."],
                "warnings": [],
            }

        if result.returncode == 0:
            return {"valid": True, "errors": [], "warnings": []}

        errors = [
            line.strip()
            for line in result.stderr.splitlines()
            if "error" in line.lower()
        ]
        return {"valid": False, "errors": errors or [result.stderr.strip()], "warnings": []}


def check_syntax(language: str, code: str) -> dict[str, Any]:
    """Dispatch to the correct language-specific syntax checker."""
    checkers = {
        "python": check_python_syntax,
        "c": check_c_syntax,
        "java": check_java_syntax,
    }
    checker = checkers.get(language)
    if checker is None:
        raise ValueError(f"Unsupported language for syntax checking: {language}")
    return checker(code)