"""
Evaluation Agent (Agent 1).

Converts comparison, syntax, test, and complexity results into a
structured, deterministic evaluation — score, status, concept-level
scoring, and a plain-language summary (Section 24).

Deterministic and explainable. Does NOT depend on an external LLM
API — fully offline/local, per Section 24.
"""

from typing import Any

from app.agents.base_agent import BaseAgent


DEFAULT_RUBRIC = {
    "function": 20,
    "array": 20,
    "loop": 20,
    "condition": 20,
    "return": 20,
}


class EvaluationAgent(BaseAgent):
    name = "EvaluationAgent"

    def run(
        self,
        comparison: dict[str, Any],
        syntax_result: dict[str, Any],
        test_result: dict[str, Any],
        complexity_result: dict[str, Any],
        rubric: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        rubric = rubric or DEFAULT_RUBRIC

        self.log_header(4, "EVALUATION AGENT")
        self.log("Receiving comparison...")
        self.log("Applying rubric...")
        self.log("Analyzing concept coverage...")

        matched = comparison.get("matched", [])
        missing = comparison.get("missing", [])
        incorrect = comparison.get("incorrect", [])

        concept_scores: dict[str, int] = {}
        for concept, weight in rubric.items():
            if concept in matched:
                concept_scores[concept] = weight
            elif concept in incorrect:
                concept_scores[concept] = weight // 2
            else:
                concept_scores[concept] = 0

        concept_total = sum(concept_scores.values())
        concept_max = sum(rubric.values()) or 1
        concept_score_pct = round((concept_total / concept_max) * 100, 2)

        syntax_valid = syntax_result.get("valid")
        syntax_score = 100 if syntax_valid else (0 if syntax_valid is False else 50)

        test_total = test_result.get("total", 0)
        test_passed = test_result.get("passed", 0)
        test_skipped = test_result.get("skipped", False)

        self.log("Calculating score...")

        if test_total > 0 and not test_skipped:
            test_score = round((test_passed / test_total) * 100, 2)
            concept_weight, test_weight, syntax_weight = 0.5, 0.3, 0.2
        else:
            # No usable test results: redistribute weight instead of
            # penalizing the submission for a missing/unavailable toolchain.
            test_score = None
            concept_weight, test_weight, syntax_weight = 0.7, 0.0, 0.3

        final_score = round(
            (concept_score_pct * concept_weight)
            + ((test_score or 0) * test_weight)
            + (syntax_score * syntax_weight),
            2,
        )

        if final_score >= 85:
            status = "Correct"
        elif final_score >= 50:
            status = "Partially Correct"
        else:
            status = "Incorrect"

        summary = _build_summary(matched, missing, incorrect)

        self.log("✓ Evaluation generated")
        self.log(f"Score: {final_score}/100")
        self.log(f"Status: {status}")

        return {
            "score": final_score,
            "status": status,
            "concept_scores": concept_scores,
            "matched_concepts": matched,
            "missing_concepts": missing,
            "incorrect_concepts": incorrect,
            "syntax_score": syntax_score,
            "test_score": test_score,
            "summary": summary,
        }


def _build_summary(matched: list[str], missing: list[str], incorrect: list[str]) -> str:
    if not missing and not incorrect:
        return "The solution correctly implements all expected concepts."

    parts = []
    if matched:
        parts.append(f"correctly implements {', '.join(matched)}")
    if missing:
        parts.append(f"does not implement {', '.join(missing)}")
    if incorrect:
        parts.append(f"implements {', '.join(incorrect)} incorrectly")

    return "The solution " + "; ".join(parts) + "."