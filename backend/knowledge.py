from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


class GraphError(ValueError):
    pass


@dataclass(frozen=True)
class Concept:
    id: str
    label: str
    guidance: str


@dataclass(frozen=True)
class ConceptGraph:
    version: str
    concepts: dict[str, Concept]
    requires: dict[str, tuple[str, ...]]

    def validate(self) -> None:
        for concept, prerequisites in self.requires.items():
            if concept not in self.concepts:
                raise GraphError(f"unknown concept: {concept}")
            for prerequisite in prerequisites:
                if prerequisite not in self.concepts:
                    raise GraphError(f"unknown prerequisite: {prerequisite}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise GraphError(f"prerequisite cycle at {node}")
            if node in visited:
                return
            visiting.add(node)
            for prerequisite in self.requires.get(node, ()):
                visit(prerequisite)
            visiting.remove(node)
            visited.add(node)

        for concept in self.concepts:
            visit(concept)

    def prerequisite_order(self, weak: set[str], satisfied: set[str] | None = None) -> tuple[str, ...]:
        self.validate()
        satisfied = satisfied or set()
        result: set[str] = set()

        def add(node: str) -> None:
            for prerequisite in sorted(self.requires.get(node, ())):
                if prerequisite not in satisfied:
                    add(prerequisite)
            if node not in satisfied:
                result.add(node)

        for node in sorted(weak):
            if node in self.concepts:
                add(node)
        return tuple(sorted(result, key=lambda item: (self._depth(item), item)))

    def _depth(self, node: str) -> int:
        return max((self._depth(parent) + 1 for parent in self.requires.get(node, ())), default=0)

    def prerequisite_path(self, prerequisite: str, target: str) -> tuple[str, ...] | None:
        """Return a deterministic prerequisite-to-target path when one exists."""
        if prerequisite == target:
            return (target,)
        candidates: list[tuple[str, ...]] = []
        for parent in sorted(self.requires.get(target, ())):
            path = self.prerequisite_path(prerequisite, parent)
            if path:
                candidates.append(path + (target,))
        return min(candidates, key=lambda item: (len(item), item)) if candidates else None


def load_graph(path: str | Path) -> ConceptGraph:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    concepts_list = data.get("concepts")
    if not isinstance(concepts_list, list):
        raise GraphError("concepts must be a list")
    concepts: dict[str, Concept] = {}
    for item in concepts_list:
        concept = Concept(item["id"], item["label"], item["guidance"])
        if concept.id in concepts:
            raise GraphError(f"duplicate concept: {concept.id}")
        concepts[concept.id] = concept
    graph = ConceptGraph(data.get("version", ""), concepts, {key: tuple(value) for key, value in data.get("requires", {}).items()})
    if not graph.version:
        raise GraphError("graph version is required")
    graph.validate()
    return graph
