from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any


IR_VERSION = "ir-v1"


@dataclass(frozen=True)
class IRNode:
    kind: str
    children: tuple["IRNode", ...] = ()
    value: str | None = None
    line: int | None = None


def canonical_node(node: IRNode) -> dict[str, Any]:
    data: dict[str, Any] = {"kind": node.kind, "children": [canonical_node(c) for c in node.children]}
    if node.value is not None:
        data["value"] = node.value
    return data


def canonical_hash(root: IRNode) -> str:
    payload = json.dumps({"version": IR_VERSION, "root": canonical_node(root)}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def node_count(root: IRNode) -> int:
    return 1 + sum(node_count(child) for child in root.children)


def preorder_kinds(root: IRNode) -> tuple[str, ...]:
    return (root.kind,) + tuple(kind for child in root.children for kind in preorder_kinds(child))


@dataclass(frozen=True)
class IRComparison:
    status: str
    score: float | None
    distance: int | None
    operations: int
    left_nodes: int
    right_nodes: int


def compare_ir(left: IRNode, right: IRNode, max_operations: int = 100_000) -> IRComparison:
    """Compare normalized preorder sequences with bounded unit-cost edit distance."""
    a, b = preorder_kinds(left), preorder_kinds(right)
    operations = len(a) * len(b)
    if operations > max_operations:
        return IRComparison("analysis_limit", None, None, operations, len(a), len(b))
    previous = list(range(len(b) + 1))
    for row, left_kind in enumerate(a, start=1):
        current = [row]
        for column, right_kind in enumerate(b, start=1):
            current.append(min(
                current[-1] + 1,
                previous[column] + 1,
                previous[column - 1] + (left_kind != right_kind),
            ))
        previous = current
    distance = previous[-1]
    score = 100.0 * max(0.0, 1.0 - distance / max(len(a), len(b), 1))
    return IRComparison("complete", score, distance, operations, len(a), len(b))
