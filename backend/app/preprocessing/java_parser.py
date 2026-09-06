"""
Java source code parser.

Extracts programming constructs from Java source code using practical
regex/token analysis rather than a full compiler-grade parser, per
the project's MVP scope (Section 19).
"""

import re
from typing import Any


_TYPE_KEYWORDS = r"(?:void|int|float|double|char|long|short|boolean|byte|String|var)"

_IMPORT_RE = re.compile(r'\bimport\s+([\w.]+)\s*;')
_CLASS_RE = re.compile(r'\bclass\s+(\w+)')
_METHOD_RE = re.compile(
    rf'\b(?:public|private|protected|static|final|\s)*'
    rf'{_TYPE_KEYWORDS}(?:\[\])?\s+(\w+)\s*\([^;{{}}]*\)\s*\{{'
)
_FOR_RE = re.compile(r'\bfor\s*\(')
_WHILE_RE = re.compile(r'\bwhile\s*\(')
_IF_RE = re.compile(r'\bif\s*\(')
_RETURN_RE = re.compile(r'\breturn\b')
_ARRAY_DECL_RE = re.compile(rf'\b{_TYPE_KEYWORDS}\s*\[\]\s*(\w+)')
_ARRAY_INDEX_RE = re.compile(r'\b(\w+)\s*\[[^\]]*\]')
_VAR_DECL_RE = re.compile(
    rf'\b{_TYPE_KEYWORDS}\s+(\w+)\s*(?:=[^;,]*)?\s*[;,]'
)


def parse_java(code: str) -> dict[str, Any]:
    """
    Parse Java source code into the Common Representation schema.
    """
    classes = _CLASS_RE.findall(code)
    methods = _METHOD_RE.findall(code)
    imports = _IMPORT_RE.findall(code)

    loops: list[str] = []
    loops.extend(["for"] * len(_FOR_RE.findall(code)))
    loops.extend(["while"] * len(_WHILE_RE.findall(code)))

    conditions = ["if"] * len(_IF_RE.findall(code))
    returns = ["return"] * len(_RETURN_RE.findall(code))

    arrays: list[str] = []
    arrays.extend(_ARRAY_DECL_RE.findall(code))
    arrays.extend(f"{name}_index" for name in _ARRAY_INDEX_RE.findall(code))

    variables = sorted(set(_VAR_DECL_RE.findall(code)) - set(methods))

    concepts: list[str] = []
    if methods:
        concepts.append("function")
    if arrays:
        concepts.append("array")
    if loops:
        concepts.append("loop")
    if conditions:
        concepts.append("condition")
    if returns:
        concepts.append("return")
    if classes:
        concepts.append("class")
    if imports:
        concepts.append("import")

    return {
        "language": "java",
        "functions": methods,
        "variables": variables,
        "loops": loops,
        "conditions": conditions,
        "arrays": arrays,
        "returns": returns,
        "classes": classes,
        "imports": imports,
        "concepts": concepts,
    }