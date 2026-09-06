"""
Response model for the Feedback Agent's output.
"""

from pydantic import BaseModel


class FeedbackResult(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    practice_questions: list[str]