from __future__ import annotations

from dataclasses import dataclass
from tree_sitter import Language, Parser, Node

from backend.ir import IRNode, node_count


@dataclass(frozen=True)
class TreeSitterAnalysis:
    syntax_ok: bool
    diagnostics: tuple[str, ...]
    ir: IRNode | None


NORMALIZED_VALUES = {
    "identifier": "identifier", "type_identifier": "type", "field_identifier": "identifier",
    "decimal_integer_literal": "integer", "number_literal": "number", "string_literal": "string",
    "character_literal": "character", "true": "boolean", "false": "boolean", "null_literal": "null",
}


def parse(source: str, language_capsule, max_nodes: int = 10_000) -> TreeSitterAnalysis:
    raw = source.encode("utf-8")
    parser = Parser(Language(language_capsule))
    tree = parser.parse(raw)
    diagnostics: list[str] = []

    def convert(node: Node) -> IRNode:
        if node.type == "ERROR" or node.is_missing:
            diagnostics.append(f"syntax error at line {node.start_point.row + 1}, column {node.start_point.column + 1}")
        value = NORMALIZED_VALUES.get(node.type)
        return IRNode(node.type, tuple(convert(child) for child in node.named_children), value, node.start_point.row + 1)

    root = convert(tree.root_node)
    if node_count(root) > max_nodes:
        return TreeSitterAnalysis(False, ("analysis_limit: AST node limit exceeded",), None)
    if tree.root_node.has_error:
        return TreeSitterAnalysis(False, tuple(diagnostics or ["syntax error at line 1, column 1"]), None)
    return TreeSitterAnalysis(True, (), root)
