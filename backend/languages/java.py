from __future__ import annotations

import tree_sitter_java

from backend.languages.treesitter import TreeSitterAnalysis, parse


def analyze(source: str, max_nodes: int = 10_000) -> TreeSitterAnalysis:
    result = parse(source, tree_sitter_java.language(), max_nodes)
    if result.syntax_ok and _has_unsupported_layout(source):
        return TreeSitterAnalysis(False, ("unsupported layout: one Main.java using java.* standard-library imports is required",), None)
    if result.syntax_ok and not _has_main_class(source):
        return TreeSitterAnalysis(False, ("unsupported layout: class Main is required",), None)
    return result


def _has_main_class(source: str) -> bool:
    # Layout validation is separate from syntax parsing and intentionally strict.
    tokens = source.replace("{", " ").replace("\n", " ").split()
    return any(tokens[index] == "class" and index + 1 < len(tokens) and tokens[index + 1] == "Main" for index in range(len(tokens)))


def _has_unsupported_layout(source: str) -> bool:
    import re
    if re.search(r"^\s*package\s+", source, re.MULTILINE):
        return True
    imports = re.findall(r"^\s*import\s+(?:static\s+)?([\w.]+)", source, re.MULTILINE)
    if any(not name.startswith("java.") for name in imports):
        return True
    public_types = re.findall(r"\bpublic\s+(?:class|interface|enum|record)\s+(\w+)", source)
    return any(name != "Main" for name in public_types) or len(public_types) > 1
