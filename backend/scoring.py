from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from math import isfinite


WEIGHTS = {"structure": 0.20, "syntax": 0.40, "tests": 0.20, "originality": 0.20}
SUPPORTED_POLICIES = {"core-v1": WEIGHTS}


def classify(score: float) -> str:
    if score >= 75:
        return "Good"
    if score >= 50:
        return "Average"
    return "Poor"


def legacy_structure_score(teacher_features: dict[str, int], student_features: dict[str, int]) -> float:
    scores = []
    for key, expected in teacher_features.items():
        actual = student_features.get(key, 0)
        if expected == 0:
            scores.append(100.0 if actual == 0 else 0.0)
        else:
            scores.append(max(0.0, min(100.0, (1 - abs(expected - actual) / expected) * 100)))
    return sum(scores) / len(scores) if scores else 0.0


def legacy_originality_score(reference: str, source: str) -> float:
    return (1 - SequenceMatcher(None, reference, source).ratio()) * 100


def weighted_test_score(passed_weights: float, total_weight: float) -> float:
    if total_weight <= 0:
        return 0.0
    return passed_weights / total_weight * 100


@dataclass(frozen=True)
class CoreScore:
    structure: float
    syntax: float
    tests: float
    originality: float

    def __post_init__(self) -> None:
        for value in (self.structure, self.syntax, self.tests, self.originality):
            if not isfinite(value) or not 0 <= value <= 100:
                raise ValueError("component scores must be finite values in [0, 100]")

    @property
    def total(self) -> float:
        return sum(getattr(self, name) * weight for name, weight in WEIGHTS.items())

    @property
    def category(self) -> str:
        return classify(self.total)


def validate_weights(weights: dict[str, float]) -> dict[str, float]:
    if set(weights) != set(WEIGHTS):
        raise ValueError("rubric must define structure, syntax, tests and originality")
    normalized = {name: float(value) for name, value in weights.items()}
    if any(not isfinite(value) or value < 0 for value in normalized.values()):
        raise ValueError("rubric weights must be finite and nonnegative")
    if abs(sum(normalized.values()) - 1.0) > 1e-9:
        raise ValueError("rubric weights must sum to 1")
    return normalized


def resolve_weights(policy_version: str, overrides: dict[str, float] | None = None) -> dict[str, float]:
    if policy_version not in SUPPORTED_POLICIES:
        raise ValueError(f"unsupported policy version: {policy_version}")
    return validate_weights(overrides or SUPPORTED_POLICIES[policy_version])


def compose_total(components: dict[str, float], weights: dict[str, float]) -> tuple[float, str]:
    checked = CoreScore(**components)
    total = sum(getattr(checked, name) * weight for name, weight in validate_weights(weights).items())
    return total, classify(total)
