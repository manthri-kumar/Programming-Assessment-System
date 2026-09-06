"""
Comparison Module.

Performs concept-based comparison between a reference (teacher) and
student Common Representation, per Section 20 of the project spec.
"""

from typing import Any


def compare_representations(
    reference: dict[str, Any],
    student: dict[str, Any],
) -> dict[str, Any]:
    """
    Compare reference and student Common Representations.

    Comparison is concept-based (using the `concepts` list each parser
    produces), not raw source-code string comparison.

    Returns:
        {
            "matched": [...],
            "missing": [...],
            "incorrect": [...],
            "structural_issues": [...]
        }
    """
    reference_concepts = set(reference.get("concepts", []))
    student_concepts = set(student.get("concepts", []))

    matched = sorted(reference_concepts & student_concepts)
    missing = sorted(reference_concepts - student_concepts)

    # "incorrect" concepts (present but structurally inconsistent with the
    # reference) require deeper structural analysis than the MVP concept-set
    # comparison supports. Reserved for future extension once the Knowledge
    # Graph layer is integrated (Section 34).
    incorrect: list[str] = []

    structural_issues: list[str] = []

    # Lightweight structural signal: flag large discrepancies in loop count
    # (e.g. reference has nested loops but student has only a single loop).
    ref_loop_count = len(reference.get("loops", []))
    stu_loop_count = len(student.get("loops", []))
    if ref_loop_count > 1 and stu_loop_count < ref_loop_count:
        structural_issues.append(
            f"Reference uses {ref_loop_count} loop(s); "
            f"student uses {stu_loop_count}. Possible missing nested logic."
        )

    return {
        "matched": matched,
        "missing": missing,
        "incorrect": incorrect,
        "structural_issues": structural_issues,
    }