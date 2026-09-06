"""
/evaluate endpoint.

Orchestrates the full pipeline:
    Language Detection -> Parsing -> Comparison -> Syntax -> Tests
    -> Complexity -> Evaluation Agent -> Feedback Agent
"""

from fastapi import APIRouter, HTTPException

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.feedback_agent import FeedbackAgent
from app.evaluation.call_analysis import find_uncalled_functions
from app.evaluation.comparison import compare_representations
from app.evaluation.complexity import analyze_complexity
from app.evaluation.syntax_checker import check_syntax
from app.evaluation.test_runner import run_tests
from app.models.submission import EvaluationRequest
from app.preprocessing.c_parser import parse_c
from app.preprocessing.java_parser import parse_java
from app.preprocessing.python_parser import parse_python

router = APIRouter()

_PARSERS = {
    "python": parse_python,
    "c": parse_c,
    "java": parse_java,
}


@router.post("/evaluate")
def evaluate_submission(request: EvaluationRequest) -> dict:
    print("=" * 50)
    print("INTELLIGENT PROGRAMMING ASSESSMENT")
    print("=" * 50)

    language = request.language.lower()

    print(f"\n[1] LANGUAGE DETECTION")
    print(f"    Detected Language: {language.capitalize()}")

    parser = _PARSERS.get(language)
    if parser is None:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    print(f"\n[2] SOURCE PROCESSING")
    print(f"    Extracting programming constructs...")

    try:
        reference_representation = parser(request.reference_code)
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Reference code syntax error: {e}")

    try:
        student_representation = parser(request.student_code)
    except SyntaxError as e:
        # Student syntax errors are a valid, expected outcome — not a
        # server error. We still return a structured, low-score result.
        student_representation = {
            "language": language,
            "functions": [], "variables": [], "loops": [], "conditions": [],
            "arrays": [], "returns": [], "classes": [], "imports": [], "concepts": [],
        }

    for construct in ["Functions", "Variables", "Loops", "Conditions", "Return statements"]:
        print(f"    ✓ {construct}")

    print(f"\n[3] COMPARISON MODULE")
    print(f"    Comparing reference and student representations...")

    comparison = compare_representations(reference_representation, student_representation)
    print(f"\n    ✓ Matched concepts: {len(comparison['matched'])}")
    print(f"    ⚠ Missing concepts: {len(comparison['missing'])}")
    print(f"    ✗ Incorrect concepts: {len(comparison['incorrect'])}")

    reference_uncalled = find_uncalled_functions(
        reference_representation.get("functions", []), request.reference_code
    )
    student_uncalled = find_uncalled_functions(
        student_representation.get("functions", []), request.student_code
    )
    dropped_calls = [
        fn for fn in reference_representation.get("functions", [])
        if fn not in reference_uncalled
        and fn in student_representation.get("functions", [])
        and fn in student_uncalled
    ]
    if dropped_calls:
        comparison["structural_issues"].append(
            f"Function(s) defined but never used in the student solution: {', '.join(dropped_calls)}."
        )

    syntax_result = check_syntax(language, request.student_code)

    test_cases = [tc.model_dump() for tc in request.test_cases]
    test_result = run_tests(language, request.student_code, test_cases) if test_cases else {
        "passed": 0, "total": 0, "results": [], "skipped": True, "reason": "No test cases provided."
    }

    complexity_result = analyze_complexity(student_representation, request.student_code)

    evaluation_agent = EvaluationAgent()
    evaluation = evaluation_agent.run(
        comparison=comparison,
        syntax_result=syntax_result,
        test_result=test_result,
        complexity_result=complexity_result,
        rubric=request.rubric,
    )

    feedback_agent = FeedbackAgent()
    feedback = feedback_agent.run(evaluation, comparison.get("structural_issues"))

    print("\n" + "=" * 50)
    print("ASSESSMENT COMPLETE")
    print("=" * 50)

    return {
        "language": language,
        "reference_representation": reference_representation,
        "student_representation": student_representation,
        "comparison": comparison,
        "syntax": syntax_result,
        "tests": test_result,
        "complexity": complexity_result,
        "evaluation": evaluation,
        "feedback": feedback,
    }