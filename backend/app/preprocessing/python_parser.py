"""
Python source code parser.

Extracts programming constructs from Python source code into the
project's Common Representation schema, using the standard `ast` module.
"""

import ast
from typing import Any


def parse_python(code: str) -> dict[str, Any]:
    """
    Parse Python source code into the Common Representation schema.

    Raises:
        SyntaxError: if the code cannot be parsed.
    """
    tree = ast.parse(code)
    visitor = _ConstructVisitor()
    visitor.visit(tree)

    concepts: list[str] = []
    if visitor.functions:
        concepts.append("function")
    if visitor.arrays:
        concepts.append("array")
    if visitor.loops:
        concepts.append("loop")
    if visitor.conditions:
        concepts.append("condition")
    if visitor.returns:
        concepts.append("return")
    if visitor.classes:
        concepts.append("class")
    if visitor.imports:
        concepts.append("import")

    return {
        "language": "python",
        "functions": visitor.functions,
        "variables": sorted(visitor.variables),
        "loops": visitor.loops,
        "conditions": visitor.conditions,
        "arrays": visitor.arrays,
        "returns": visitor.returns,
        "classes": visitor.classes,
        "imports": visitor.imports,
        "concepts": concepts,
    }


class _ConstructVisitor(ast.NodeVisitor):
    """Walks a Python AST and collects programming constructs."""

    def __init__(self) -> None:
        self.functions: list[str] = []
        self.variables: set[str] = set()
        self.loops: list[str] = []
        self.conditions: list[str] = []
        self.arrays: list[str] = []
        self.returns: list[str] = []
        self.classes: list[str] = []
        self.imports: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._collect_variable_names(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._collect_variable_names(node.target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._collect_variable_names(node.target)
        self.generic_visit(node)

    def _collect_variable_names(self, target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            self.variables.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._collect_variable_names(element)

    def visit_For(self, node: ast.For) -> None:
        self.loops.append("for")
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.loops.append("while")
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.conditions.append("if")
        self.generic_visit(node)

    def visit_List(self, node: ast.List) -> None:
        self.arrays.append("list")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.arrays.append("index_access")
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        self.returns.append("return")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}" if module else alias.name)
        self.generic_visit(node)