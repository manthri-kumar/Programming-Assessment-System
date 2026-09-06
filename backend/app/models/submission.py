"""
Request model for a submission evaluation.
"""

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    input: str
    expected_output: str


class EvaluationRequest(BaseModel):
    reference_code: str
    student_code: str
    language: str  # "python" | "c" | "java"
    rubric: dict[str, int] | None = None
    test_cases: list[TestCase] = Field(default_factory=list)