"""
Complexity Analysis.

A simple static heuristic estimate of time complexity based on loop
nesting depth, per Section 23. This is explicitly an MVP heuristic,
not a rigorous static analysis.
"""

import re
from typing import Any


def _estimate_from_max_nesting(max_nesting: int) -> str:
    """Map a maximum loop-nesting depth to an approximate Big-O label."""
    if max_nesting == 0:
        return "O(1)"
    if max_nesting == 1:
        return "O(n)"
    if max_nesting == 2:
        return "O(n^2)"
    if max_nesting == 3:
        return "O(n^3)"
    return f"O(n^{max_nesting})"


def _max_loop_nesting_from_braces(code: str, loop_keyword_pattern: str) -> int:
    """
    Estimate maximum loop nesting depth using brace/indentation tracking.

    This is a heuristic, not a real parser: it tracks '{' / '}' depth
    for C/Java, and indentation depth for Python-style loop keywords.
    """
    loop_starts = [m.start() for m in re.finditer(loop_keyword_pattern, code)]
    if not loop_starts:
        return 0

    # Track nesting by counting how many *other* loop starts occur
    # before each loop's matching closing point. Simplified approach:
    # count loop keywords appearing within the brace-delimited or
    # indentation-delimited body of each other loop.
    max_depth = 0
    for i, start in enumerate(loop_starts):
        depth = 1
        for j, other_start in enumerate(loop_starts):
            if i == j:
                continue
            if other_start < start:
                # Check if `start` occurs within the same nested block as
                # `other_start` by a naive brace-count heuristic.
                segment = code[other_start:start]
                if segment.count("{") > segment.count("}"):
                    depth += 1
        max_depth = max(max_depth, depth)

    return max_depth


def analyze_complexity(representation: dict[str, Any], code: str) -> dict[str, Any]:
    """
    Estimate static complexity from a Common Representation and raw code.

    Returns:
        {
            "loop_count": int,
            "function_count": int,
            "max_nesting_depth": int,
            "estimated_complexity": str
        }
    """
    language = representation.get("language", "")
    loop_count = len(representation.get("loops", []))
    function_count = len(representation.get("functions", []))

    if language == "python":
        # Python: nesting depth estimated via indentation of loop lines.
        max_nesting = _max_nesting_python(code)
    else:
        # C / Java: nesting depth estimated via brace tracking.
        max_nesting = _max_loop_nesting_from_braces(code, r"\b(for|while)\s*\(")

    return {
        "loop_count": loop_count,
        "function_count": function_count,
        "max_nesting_depth": max_nesting,
        "estimated_complexity": _estimate_from_max_nesting(max_nesting),
    }


def _max_nesting_python(code: str) -> int:
    """Estimate max loop nesting depth in Python via indentation levels."""
    loop_pattern = re.compile(r"^(\s*)(for|while)\b")
    indents_of_loops = []

    for line in code.splitlines():
        match = loop_pattern.match(line)
        if match:
            indent_level = len(match.group(1).expandtabs(4))
            indents_of_loops.append(indent_level)

    if not indents_of_loops:
        return 0

    indents_of_loops.sort()
    max_depth = 0
    depth = 0
    seen_indents: list[int] = []

    for indent in sorted(set(indents_of_loops)):
        # Count how many earlier (smaller) indents precede this one —
        # a reasonable proxy for nesting depth.
        depth = sum(1 for i in seen_indents if i < indent) + 1
        seen_indents.append(indent)
        max_depth = max(max_depth, depth)

    return max_depth