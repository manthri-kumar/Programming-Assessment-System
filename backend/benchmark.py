from __future__ import annotations

import argparse
import hashlib
import json
from math import ceil
from pathlib import Path
from typing import Any

from backend.corpus import CorpusError


def load_benchmark(path: str | Path, require_approved: bool = True) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != "benchmark-schema-v1":
        raise CorpusError("unsupported benchmark schema")
    review = data.get("label_review", {})
    if require_approved and (review.get("status") != "approved" or len(review.get("reviewers", [])) < 1):
        raise CorpusError("independent label approval is required before benchmark reporting")
    cases = data.get("cases", [])
    if not cases:
        raise CorpusError("benchmark cases are required")
    ids, all_hashes, hashes = set(), set(), {"development": set(), "held-out": set()}
    for case in cases:
        case_id, split = case.get("id"), case.get("split")
        if not case_id or case_id in ids or split not in hashes:
            raise CorpusError("unique case ids and valid splits are required")
        if case.get("language") not in {"python", "c", "java"} or not isinstance(case.get("labels"), dict):
            raise CorpusError(f"language and labels are required: {case_id}")
        ids.add(case_id)
        source = case.get("source_text")
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest() if isinstance(source, str) else None
        if digest != case.get("source_sha256"):
            raise CorpusError(f"source hash mismatch: {case_id}")
        if digest in all_hashes:
            raise CorpusError(f"source hashes must be unique: {case_id}")
        all_hashes.add(digest)
        hashes[split].add(digest)
    if hashes["development"] & hashes["held-out"]:
        raise CorpusError("development and held-out source hashes must be disjoint")
    return data


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _classification_metrics(counts: dict[str, int]) -> dict[str, float | int | None]:
    precision = _safe_ratio(counts["tp"], counts["tp"] + counts["fp"])
    recall = _safe_ratio(counts["tp"], counts["tp"] + counts["fn"])
    return {
        **counts,
        "precision": precision,
        "recall": recall,
        "f1": (2 * precision * recall / (precision + recall)) if precision is not None and recall is not None and precision + recall else None,
    }


def _new_bucket() -> dict[str, Any]:
    return {
        "count": 0,
        "syntax": {"tp": 0, "tn": 0, "fp": 0, "fn": 0},
        "functional": {"matches": 0, "count": 0},
        "tests": {"matches": 0, "count": 0},
        "scores": {"absolute_error": 0.0, "count": 0, "within_0_01": 0},
        "categories": {"matches": 0, "count": 0},
        "concepts": {"tp": 0, "fp": 0, "fn": 0},
        "recommendations": {"tp": 0, "fp": 0, "fn": 0},
        "feedback": {"matches": 0, "count": 0},
        "feedback_grounding": {"matches": 0, "count": 0},
        "latency_ms": [],
    }


def _finalize_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    scores = bucket["scores"]
    concepts = _classification_metrics(bucket["concepts"])
    recommendations = _classification_metrics(bucket["recommendations"])
    latency = sorted(bucket["latency_ms"])
    p95_index = max(0, ceil(len(latency) * 0.95) - 1) if latency else 0
    return {
        "count": bucket["count"],
        "syntax": _classification_metrics(bucket["syntax"]),
        "functional_verdict_accuracy": _safe_ratio(bucket["functional"]["matches"], bucket["functional"]["count"]),
        "functional_verdict_count": bucket["functional"]["count"],
        "test_outcome_agreement": _safe_ratio(bucket["tests"]["matches"], bucket["tests"]["count"]),
        "test_outcome_count": bucket["tests"]["count"],
        "score_mae": scores["absolute_error"] / scores["count"] if scores["count"] else None,
        "score_count": scores["count"],
        "rubric_within_0_01": _safe_ratio(scores["within_0_01"], scores["count"]),
        "category_agreement": _safe_ratio(bucket["categories"]["matches"], bucket["categories"]["count"]),
        "category_count": bucket["categories"]["count"],
        "concept_precision": concepts["precision"],
        "concept_recall": concepts["recall"],
        "concept_f1": concepts["f1"],
        "concept_counts": {key: concepts[key] for key in ("tp", "fp", "fn")},
        "recommendation_precision": recommendations["precision"],
        "recommendation_recall": recommendations["recall"],
        "recommendation_f1": recommendations["f1"],
        "recommendation_counts": {key: recommendations[key] for key in ("tp", "fp", "fn")},
        "feedback_agreement": _safe_ratio(bucket["feedback"]["matches"], bucket["feedback"]["count"]),
        "feedback_count": bucket["feedback"]["count"],
        "feedback_grounding_agreement": _safe_ratio(bucket["feedback_grounding"]["matches"], bucket["feedback_grounding"]["count"]),
        "feedback_grounding_count": bucket["feedback_grounding"]["count"],
        "latency_ms_mean": sum(latency) / len(latency) if latency else None,
        "latency_ms_p95": latency[p95_index] if latency else None,
        "sequential_throughput_cases_per_second": (1000.0 * len(latency) / sum(latency)) if latency and sum(latency) > 0 else None,
    }


def _record_case(bucket: dict[str, Any], labels: dict[str, Any], prediction: dict[str, Any]) -> None:
    bucket["count"] += 1
    if "syntax_ok" in labels:
        actual, predicted = bool(labels["syntax_ok"]), bool(prediction.get("syntax_ok"))
        key = "tp" if actual and predicted else "tn" if not actual and not predicted else "fp" if not actual else "fn"
        bucket["syntax"][key] += 1
    if "functional_verdict" in labels:
        bucket["functional"]["count"] += 1
        bucket["functional"]["matches"] += labels["functional_verdict"] == prediction.get("functional_verdict")
    for test_id, expected in labels.get("test_outcomes", {}).items():
        bucket["tests"]["count"] += 1
        bucket["tests"]["matches"] += prediction.get("test_outcomes", {}).get(test_id) == expected
    if labels.get("score") is not None and prediction.get("score") is not None:
        error = abs(float(labels["score"]) - float(prediction["score"]))
        bucket["scores"]["absolute_error"] += error
        bucket["scores"]["count"] += 1
        bucket["scores"]["within_0_01"] += error <= 0.01
    if labels.get("category") is not None:
        bucket["categories"]["count"] += 1
        bucket["categories"]["matches"] += labels["category"] == prediction.get("category")
    for field, target in (("concepts", "concepts"), ("recommendations", "recommendations")):
        expected, predicted = set(labels.get(field, [])), set(prediction.get(field, []))
        bucket[target]["tp"] += len(expected & predicted)
        bucket[target]["fp"] += len(predicted - expected)
        bucket[target]["fn"] += len(expected - predicted)
    if "feedback_codes" in labels:
        bucket["feedback"]["count"] += 1
        bucket["feedback"]["matches"] += list(labels["feedback_codes"]) == list(prediction.get("feedback_codes", []))
    if "feedback_grounded" in labels:
        bucket["feedback_grounding"]["count"] += 1
        bucket["feedback_grounding"]["matches"] += bool(labels["feedback_grounded"]) == bool(prediction.get("feedback_grounded"))
    duration = prediction.get("duration_ms")
    if isinstance(duration, (int, float)) and not isinstance(duration, bool) and 0 <= duration <= 3_600_000:
        bucket["latency_ms"].append(float(duration))


def calculate_metrics(corpus: dict, predictions: dict[str, dict[str, Any]]) -> dict:
    by_language: dict[str, dict[str, Any]] = {}
    global_bucket = _new_bucket()
    for case in corpus["cases"]:
        prediction = predictions.get(case["id"])
        if prediction is None:
            raise CorpusError(f"missing prediction: {case['id']}")
        labels = case.get("labels", {})
        language = case["language"]
        language_bucket = by_language.setdefault(language, _new_bucket())
        _record_case(language_bucket, labels, prediction)
        _record_case(global_bucket, labels, prediction)
    finalized = _finalize_bucket(global_bucket)
    return {
        "corpus_version": corpus["corpus_version"],
        "case_count": len(corpus["cases"]),
        "per_language": {language: _finalize_bucket(bucket) for language, bucket in sorted(by_language.items())},
        **{key: value for key, value in finalized.items() if key != "count"},
    }


def calculate_repeatability(first: dict[str, dict[str, Any]], second: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if set(first) != set(second):
        raise CorpusError("repeat predictions must contain identical case ids")
    decision_fields = (
        "syntax_ok", "functional_verdict", "test_outcomes", "score", "category",
        "concepts", "recommendations", "feedback_codes",
    )
    mismatches = [case_id for case_id in sorted(first) if any(first[case_id].get(field) != second[case_id].get(field) for field in decision_fields)]
    return {
        "case_count": len(first),
        "matching_cases": len(first) - len(mismatches),
        "agreement": _safe_ratio(len(first) - len(mismatches), len(first)),
        "mismatched_case_ids": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate predictions against an independently approved benchmark")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeat-predictions", type=Path)
    args = parser.parse_args()
    corpus = load_benchmark(args.corpus, require_approved=True)
    predictions_document = json.loads(args.predictions.read_text(encoding="utf-8"))
    predictions = {item["id"]: item for item in predictions_document["predictions"]}
    report = calculate_metrics(corpus, predictions)
    report["corpus_sha256"] = hashlib.sha256(args.corpus.read_bytes()).hexdigest()
    report["predictions_sha256"] = hashlib.sha256(args.predictions.read_bytes()).hexdigest()
    report["versions"] = predictions_document.get("versions", {})
    if args.repeat_predictions:
        repeat_document = json.loads(args.repeat_predictions.read_text(encoding="utf-8"))
        repeat = {item["id"]: item for item in repeat_document["predictions"]}
        report["repeatability"] = calculate_repeatability(predictions, repeat)
        report["repeat_predictions_sha256"] = hashlib.sha256(args.repeat_predictions.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
