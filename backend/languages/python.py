from __future__ import annotations

import ast
from dataclasses import dataclass
import sys

from backend.ir import IRNode


class PythonAnalysisError(ValueError):
    pass


@dataclass(frozen=True)
class PythonAnalysis:
    syntax_ok: bool
    diagnostics: tuple[str, ...]
    ir: IRNode | None
    support_status: str = "supported"


def _node(node: ast.AST) -> IRNode:
    children = tuple(_node(child) for child in ast.iter_child_nodes(node))
    kind = type(node).__name__.lower()
    value = None
    if isinstance(node, ast.Name):
        value = "identifier"
    elif isinstance(node, ast.Constant):
        value = type(node.value).__name__
    elif isinstance(node, ast.operator):
        value = kind
    return IRNode(kind=kind, children=children, value=value, line=getattr(node, "lineno", None))


def analyze(source: str, max_nodes: int = 10_000) -> PythonAnalysis:
    try:
        tree = ast.parse(source, mode="exec")
    except (SyntaxError, ValueError, TypeError) as exc:
        location = f" line {exc.lineno}" if isinstance(exc, SyntaxError) and exc.lineno else ""
        return PythonAnalysis(False, (f"syntax error{location}: {exc.msg if isinstance(exc, SyntaxError) else exc}",), None)
    root = _node(tree)
    count = sum(1 for _ in ast.walk(tree))
    if count > max_nodes:
        return PythonAnalysis(False, ("analysis_limit: AST node limit exceeded",), None)
    unsupported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module.split(".", 1)[0]] if node.module else ["relative-import"]
        else:
            continue
        unsupported.extend(module for module in modules if module not in sys.stdlib_module_names)
    if unsupported:
        names = ", ".join(sorted(set(unsupported)))
        return PythonAnalysis(True, (f"unsupported_dependency: {names}",), root, "unsupported")
    return PythonAnalysis(True, (), root)
