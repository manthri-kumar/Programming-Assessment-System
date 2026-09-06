"""
C source code parser.

Extracts programming constructs from C source code using practical
regex/token analysis rather than a full compiler-grade parser, per
the project's MVP scope (Section 18).
"""

import re
from typing import Any


_TYPE_KEYWORDS = r"(?:void|int|float|double|char|long|short|unsigned|signed|size_t|bool)"

_INCLUDE_RE = re.compile(r'#include\s*[<"]([^">]+)[">]')
_STRUCT_RE = re.compile(r'\bstruct\s+(\w+)\s*\{')
_FUNCTION_RE = re.compile(
    rf'\b{_TYPE_KEYWORDS}[\w\s\*]*?\b(\w+)\s*\([^;{{}}]*\)\s*\{{'
)
_FOR_RE = re.compile(r'\bfor\s*\(')
_WHILE_RE = re.compile(r'\bwhile\s*\(')
_IF_RE = re.compile(r'\bif\s*\(')
_RETURN_RE = re.compile(r'\breturn\b')
_ARRAY_DECL_RE = re.compile(rf'\b{_TYPE_KEYWORDS}\s+\**\s*(\w+)\s*\[')
_ARRAY_INDEX_RE = re.compile(r'\b(\w+)\s*\[[^\]]*\]')
_VAR_DECL_RE = re.compile(
    rf'\b{_TYPE_KEYWORDS}\s+\**\s*(\w+)\s*(?:=[^;,]*)?\s*[;,]'
)


def parse_c(code: str) -> dict[str, Any]:
    """
    Parse C source code into the Common Representation schema.
    """
    functions = _FUNCTION_RE.findall(code)
    structs = _STRUCT_RE.findall(code)
    includes = _INCLUDE_RE.findall(code)

    loops: list[str] = []
    loops.extend(["for"] * len(_FOR_RE.findall(code)))
    loops.extend(["while"] * len(_WHILE_RE.findall(code)))

    conditions = ["if"] * len(_IF_RE.findall(code))
    returns = ["return"] * len(_RETURN_RE.findall(code))

    arrays: list[str] = []
    arrays.extend(_ARRAY_DECL_RE.findall(code))
    arrays.extend(f"{name}_index" for name in _ARRAY_INDEX_RE.findall(code))

    variables = sorted(set(_VAR_DECL_RE.findall(code)) - set(functions))

    concepts: list[str] = []
    if functions:
        concepts.append("function")
    if arrays:
        concepts.append("array")
    if loops:
        concepts.append("loop")
    if conditions:
        concepts.append("condition")
    if returns:
        concepts.append("return")
    if structs:
        concepts.append("struct")
    if includes:
        concepts.append("import")

    return {
        "language": "c",
        "functions": functions,
        "variables": variables,
        "loops": loops,
        "conditions": conditions,
        "arrays": arrays,
        "returns": returns,
        "classes": structs,
        "imports": includes,
        "concepts": concepts,
    }