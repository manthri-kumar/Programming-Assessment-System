"""
Response model for the Evaluation Agent's output.
"""

from pydantic import BaseModel


class EvaluationResult(BaseModel):
    score: float
    status: str
    concept_scores: dict[str, int]
    matched_concepts: list[str]
    missing_concepts: list[str]
    incorrect_concepts: list[str]
    syntax_score: int
    test_score: float | None
    summary: str