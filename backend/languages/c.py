from __future__ import annotations

import tree_sitter_c

from backend.languages.treesitter import TreeSitterAnalysis, parse


def analyze(source: str, max_nodes: int = 10_000) -> TreeSitterAnalysis:
    return parse(source, tree_sitter_c.language(), max_nodes)
