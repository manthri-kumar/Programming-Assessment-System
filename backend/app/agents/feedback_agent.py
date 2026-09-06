"""
Feedback Agent (Agent 2).

Consumes the Evaluation Agent's structured output and produces
personalized, concept-specific feedback: strengths, weaknesses,
recommendations, and practice questions (Section 25).

Rule-based/deterministic for the MVP — no external LLM dependency.
"""

from typing import Any

from app.agents.base_agent import BaseAgent


# Concept -> (recommendation, practice question) knowledge base.
# Kept simple and rule-based per Section 25; can be swapped for an
# LLM-backed generator later without changing the agent's interface.
_CONCEPT_GUIDANCE: dict[str, dict[str, str]] = {
    "function": {
        "strength": "Correct function structure",
        "recommendation": "Review function decomposition and parameter usage",
        "practice_question": "How would you split this logic into smaller helper functions?",
    },
    "array": {
        "strength": "Correct use of arrays/lists",
        "recommendation": "Practice array traversal and boundary handling",
        "practice_question": "What happens if the array is empty?",
    },
    "loop": {
        "strength": "Correct loop implementation",
        "recommendation": "Review loop termination conditions and edge cases",
        "practice_question": "What happens if the loop needs to run zero times?",
    },
    "condition": {
        "strength": "Correct conditional logic",
        "recommendation": "Review conditional statements and boundary conditions",
        "practice_question": "What happens if the condition is never true?",
    },
    "return": {
        "strength": "Correct return statement usage",
        "recommendation": "Ensure all code paths return a value",
        "practice_question": "What does your function return if no match is found?",
    },
}


class FeedbackAgent(BaseAgent):
    name = "FeedbackAgent"

    def run(
        self,
        evaluation: dict[str, Any],
        structural_issues: list[str] | None = None,
    ) -> dict[str, Any]:
        self.log_header(5, "FEEDBACK AGENT")
        self.log("Reading evaluation...")

        matched = evaluation.get("matched_concepts", [])
        missing = evaluation.get("missing_concepts", [])
        incorrect = evaluation.get("incorrect_concepts", [])
        structural_issues = structural_issues or []

        self.log("Identifying strengths...")
        strengths = [
            _CONCEPT_GUIDANCE[c]["strength"]
            for c in matched
            if c in _CONCEPT_GUIDANCE
        ]

        self.log("Identifying weak concepts...")
        weaknesses = []
        for c in missing:
            weaknesses.append(f"{c.capitalize()} logic is missing")
        for c in incorrect:
            weaknesses.append(f"{c.capitalize()} logic is incomplete or incorrect")
        weaknesses.extend(structural_issues)

        self.log("Generating recommendations...")
        recommendations = [
            _CONCEPT_GUIDANCE[c]["recommendation"]
            for c in (missing + incorrect)
            if c in _CONCEPT_GUIDANCE
        ]
        if structural_issues:
            recommendations.append(
                "Review whether every function you define is actually used — "
                "unused or unreachable logic often signals an incomplete implementation."
            )

        practice_questions = [
            _CONCEPT_GUIDANCE[c]["practice_question"]
            for c in (missing + incorrect)
            if c in _CONCEPT_GUIDANCE
        ]

        summary = _build_feedback_summary(evaluation.get("status", ""), strengths, weaknesses)

        self.log("✓ Personalized feedback generated")

        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "practice_questions": practice_questions,
        }


def _build_feedback_summary(status: str, strengths: list[str], weaknesses: list[str]) -> str:
    if not weaknesses:
        return "Excellent work — your solution correctly demonstrates all expected concepts."

    strength_part = (
        f"Your solution correctly implements {len(strengths)} concept(s)."
        if strengths
        else "Your solution needs foundational work."
    )
    weakness_part = f" However, {len(weaknesses)} area(s) need improvement."

    return strength_part + weakness_part