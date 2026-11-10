import hashlib
import json
import sys
from pathlib import Path

import pytest

from backend.benchmark import calculate_metrics, calculate_repeatability, load_benchmark, main
from backend.ablations import ABLATIONS, ablation_manifest
from backend.corpus import CorpusError, load


ROOT = Path(__file__).parents[1]


def test_corrected_corpus_hash_and_review_provenance_validate():
    corpus = load(ROOT / "data" / "benchmarks" / "corpus-v1.json")
    assert corpus["corrections"][0]["new_expected_output"] == "5\n5\n0\nError\n"
    assert corpus["label_review"]["status"] == "pending-independent-review"


def test_candidate_split_is_disjoint_but_metrics_require_independent_approval():
    path = ROOT / "data" / "benchmarks" / "corpus-candidate-v2.json"
    candidate = load_benchmark(path, require_approved=False)
    assert {case["language"] for case in candidate["cases"]} == {"python", "c", "java"}
    with pytest.raises(CorpusError, match="independent label approval"):
        load_benchmark(path, require_approved=True)


def test_expanded_candidate_has_cross_language_functional_and_boundary_cases_but_remains_unapproved():
    path = ROOT / "data" / "benchmarks" / "corpus-candidate-v3.json"
    candidate = load_benchmark(path, require_approved=False)
    assert len(candidate["cases"]) == 12
    assert {case["language"] for case in candidate["cases"]} == {"python", "c", "java"}
    expected_kinds = {"correct", "partially-correct", "incorrect", "boundary-correct"}
    for language in ("python", "c", "java"):
        assert {case["case_kind"] for case in candidate["cases"] if case["language"] == language} == expected_kinds
    assert candidate["label_review"]["status"] == "pending-independent-review"
    with pytest.raises(CorpusError, match="independent label approval"):
        load_benchmark(path, require_approved=True)


def test_supplemental_execution_candidate_covers_syntax_and_runtime_per_language_but_remains_unapproved():
    path = ROOT / "data" / "benchmarks" / "corpus-execution-candidate-v1.json"
    candidate = load_benchmark(path, require_approved=False)
    assert len(candidate["cases"]) == 6
    for language in ("python", "c", "java"):
        assert {case["case_kind"] for case in candidate["cases"] if case["language"] == language} == {"syntax-error", "runtime-error"}
    assert candidate["label_review"]["status"] == "pending-independent-review"
    with pytest.raises(CorpusError, match="independent label approval"):
        load_benchmark(path, require_approved=True)


def test_benchmark_rejects_hash_mismatch(tmp_path):
    data = json.loads((ROOT / "data" / "benchmarks" / "corpus-candidate-v2.json").read_text(encoding="utf-8"))
    data["cases"][0]["source_text"] = "changed"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CorpusError, match="source hash mismatch"):
        load_benchmark(path, require_approved=False)


def test_corpus_rejects_inconsistent_correction_and_review_metadata(tmp_path):
    original = json.loads((ROOT / "data" / "benchmarks" / "corpus-v1.json").read_text(encoding="utf-8"))
    source = ROOT / original["cases"][0]["source"]
    original["cases"][0]["source"] = str(source)
    original["corrections"][0]["new_expected_output"] = "mismatch\n"
    path = tmp_path / "bad-correction.json"
    path.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(CorpusError, match="correction output"):
        load(path)

    original["corrections"][0]["new_expected_output"] = original["cases"][0]["expected_output"]
    original["label_review"] = {"status": "approved", "reviewers": []}
    path.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(CorpusError, match="independent reviewer"):
        load(path)


def test_metric_calculations_are_hand_computable():
    corpus = {
        "corpus_version": "calculation-fixture",
        "cases": [
            {"id": "a", "language": "python", "labels": {"syntax_ok": True, "functional_verdict": "correct", "test_outcomes": {"t": "passed"}, "score": 80, "category": "Good", "concepts": ["loops"], "recommendations": ["loops"], "feedback_codes": ["ok"], "feedback_grounded": True}},
            {"id": "b", "language": "python", "labels": {"syntax_ok": False, "functional_verdict": "invalid", "test_outcomes": {"t": "compile_error"}, "score": 20, "category": "Poor", "concepts": ["input"], "recommendations": ["input"], "feedback_codes": ["syntax"], "feedback_grounded": True}},
        ],
    }
    predictions = {
        "a": {"syntax_ok": True, "functional_verdict": "correct", "test_outcomes": {"t": "passed"}, "score": 70, "category": "Average", "concepts": ["loops", "input"], "recommendations": ["loops", "input"], "feedback_codes": ["ok"], "feedback_grounded": True, "duration_ms": 100},
        "b": {"syntax_ok": True, "functional_verdict": "incorrect", "test_outcomes": {"t": "compile_error"}, "score": 20, "category": "Poor", "concepts": [], "recommendations": [], "feedback_codes": ["other"], "feedback_grounded": False, "duration_ms": 300},
    }
    metrics = calculate_metrics(corpus, predictions)
    assert metrics["per_language"]["python"]["syntax"] == {"tp": 1, "tn": 0, "fp": 1, "fn": 0, "precision": 0.5, "recall": 1.0, "f1": pytest.approx(2 / 3)}
    assert metrics["test_outcome_agreement"] == 1.0
    assert metrics["score_mae"] == 5.0
    assert metrics["category_agreement"] == 0.5
    assert metrics["recommendation_precision"] == 0.5
    assert metrics["recommendation_recall"] == 0.5
    assert metrics["functional_verdict_accuracy"] == 0.5
    assert metrics["concept_precision"] == 0.5
    assert metrics["concept_recall"] == 0.5
    assert metrics["concept_f1"] == 0.5
    assert metrics["feedback_agreement"] == 0.5
    assert metrics["rubric_within_0_01"] == 0.5
    assert metrics["per_language"]["python"]["test_outcome_agreement"] == 1.0
    assert metrics["feedback_grounding_agreement"] == 0.5
    assert metrics["latency_ms_mean"] == 200.0
    assert metrics["latency_ms_p95"] == 300.0
    assert metrics["sequential_throughput_cases_per_second"] == 5.0


def test_fixed_ablation_manifests_are_hash_stable_and_share_the_same_corpus():
    corpus_hash = "a" * 64
    manifests = [ablation_manifest(name, corpus_hash) for name in sorted(ABLATIONS)]
    assert {item["corpus_sha256"] for item in manifests} == {corpus_hash}
    assert len({item["configuration_sha256"] for item in manifests}) == len(manifests)
    assert manifests == [ablation_manifest(name, corpus_hash) for name in sorted(ABLATIONS)]
    with pytest.raises(ValueError):
        ablation_manifest("unknown", corpus_hash)


def test_benchmark_cli_writes_machine_readable_report(tmp_path, monkeypatch):
    source = "print(1)\n"
    corpus = {
        "schema_version": "benchmark-schema-v1",
        "corpus_version": "approved-test-fixture",
        "label_review": {"status": "approved", "reviewers": ["independent-reviewer-test"]},
        "cases": [{"id": "case", "split": "held-out", "language": "python", "source_text": source, "source_sha256": hashlib.sha256(source.encode()).hexdigest(), "labels": {"syntax_ok": True}}],
    }
    predictions = {"predictions": [{"id": "case", "syntax_ok": True}]}
    corpus_path, predictions_path, output_path = tmp_path / "corpus.json", tmp_path / "predictions.json", tmp_path / "report.json"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
    predictions_path.write_text(json.dumps(predictions), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["benchmark", "--corpus", str(corpus_path), "--predictions", str(predictions_path), "--output", str(output_path)])
    assert main() == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["case_count"] == 1
    assert report["per_language"]["python"]["syntax"]["f1"] == 1.0
    assert len(report["corpus_sha256"]) == 64
    assert len(report["predictions_sha256"]) == 64


def test_repeatability_reports_decision_mismatches():
    first = {"a": {"syntax_ok": True, "score": 80}, "b": {"syntax_ok": False, "score": None}}
    same = {"a": {"syntax_ok": True, "score": 80}, "b": {"syntax_ok": False, "score": None}}
    assert calculate_repeatability(first, same)["agreement"] == 1.0
    changed = {**same, "b": {"syntax_ok": True, "score": None}}
    result = calculate_repeatability(first, changed)
    assert result["agreement"] == 0.5 and result["mismatched_case_ids"] == ["b"]
    with pytest.raises(CorpusError, match="identical case ids"):
        calculate_repeatability(first, {"a": same["a"]})
