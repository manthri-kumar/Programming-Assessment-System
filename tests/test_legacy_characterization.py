import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modules.feedback import generate_feedback
from modules.sbcam import count_features, structure_score
from modules.sedm import syntax_check
from modules.stcam import plagiarism_score, test_case_score as legacy_test_case_score

from backend.scoring import CoreScore, classify


ROOT = Path(__file__).parents[1]
GOLDENS = json.loads((ROOT / "data" / "benchmarks" / "legacy-v1-goldens.json").read_text(encoding="utf-8"))


def test_legacy_structure_and_zero_reference_goldens():
    assert count_features("int main(){ /* for if */ return 0; }")["loops"] == 1
    assert structure_score("", "") == GOLDENS["goldens"]["zero_reference_matching"]
    assert structure_score("", "int x;") == 75.0
    assert structure_score("int main(){}", "int main(){}") == 100.0


def test_legacy_syntax_counts_tokens_and_ignores_exit_code_without_host_execution():
    with patch("modules.sedm.subprocess.run", return_value=SimpleNamespace(stderr="error: one\nerror: two", returncode=1)) as run:
        assert syntax_check("never-compiled.c") == GOLDENS["goldens"]["two_error_tokens"]
        run.assert_called_once()
    with patch("modules.sedm.subprocess.run", return_value=SimpleNamespace(stderr="fatal diagnostic", returncode=1)):
        assert syntax_check("never-compiled.c") == GOLDENS["goldens"]["no_error_token_even_nonzero_exit"]


def test_legacy_weighted_stdout_and_exit_code_behavior_without_execution():
    outcomes = [
        SimpleNamespace(stdout="ok\n", returncode=0),
        SimpleNamespace(stdout="wrong\n", returncode=0),
        SimpleNamespace(stdout="still-ok\n", returncode=9),
    ]
    cases = [("a", "ok", 1), ("b", "expected", 1), ("c", "still-ok", 2)]
    with patch("modules.stcam.subprocess.run", side_effect=outcomes):
        assert legacy_test_case_score("never-run", cases) == 75.0


def test_legacy_feedback_boundaries_and_similarity_are_frozen():
    below = generate_feedback(59.999, 79.999, 69.999, 49.999, 49.999)
    at = generate_feedback(60, 80, 70, 50, 50)
    good = generate_feedback(60, 80, 70, 50, 75)
    assert below == [
        "Improve code structure and modularity (use functions properly).",
        "Fix syntax errors and ensure correct syntax usage.",
        "Your program is failing test cases. Check logic and edge cases.",
        "High similarity detected. Try to write original code.",
        "Poor performance. Focus on fundamentals.",
    ]
    assert at[-1] == "Average performance. Needs improvement in some areas."
    assert good[-1] == "Overall performance is excellent."
    assert plagiarism_score("same", "same") == 0.0


def test_core_policy_golden_and_category_boundaries():
    score = CoreScore(80, 100, 50, 40)
    assert score.total == GOLDENS["goldens"]["core_sample_total"]
    assert score.category == GOLDENS["goldens"]["core_sample_category"]
    assert [classify(value) for value in (49.999, 50, 74.999, 75)] == ["Poor", "Average", "Average", "Good"]
