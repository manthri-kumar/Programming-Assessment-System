from __future__ import annotations

import json
import hashlib
from pathlib import Path


class CorpusError(ValueError):
    pass


def load(path: str | Path) -> dict:
    corpus_path = Path(path)
    data = json.loads(corpus_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "benchmark-schema-v1":
        raise CorpusError("unsupported benchmark schema")
    if not isinstance(data.get("corpus_version"), str) or not data["corpus_version"]:
        raise CorpusError("corpus_version is required")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CorpusError("cases must be a nonempty list")
    ids = [case.get("id") for case in cases]
    if any(not isinstance(case, dict) for case in cases) or len(ids) != len(set(ids)):
        raise CorpusError("cases must be objects with unique ids")
    for case in cases:
        if case.get("split") not in {"development", "held-out"}:
            raise CorpusError("case split must be development or held-out")
        if not case.get("language") or not isinstance(case.get("expected_output"), str):
            raise CorpusError("case language and expected_output are required")
        if not isinstance(case.get("source_sha256"), str) or len(case["source_sha256"]) != 64:
            raise CorpusError("source_sha256 is required")
        source_path = Path(case.get("source", ""))
        if not source_path.is_absolute():
            candidates = [corpus_path.parents[2] / source_path, corpus_path.parent / source_path]
            source_path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
        if not source_path.exists():
            raise CorpusError(f"source file unavailable: {case['id']}")
        actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual != case["source_sha256"].lower():
            raise CorpusError(f"source hash mismatch: {case['id']}")
    review = data.get("label_review")
    if not isinstance(review, dict) or review.get("status") not in {"pending-independent-review", "approved"}:
        raise CorpusError("label review provenance is required")
    if review["status"] == "approved" and not review.get("reviewers"):
        raise CorpusError("approved labels require an independent reviewer")
    case_by_id = {case["id"]: case for case in cases}
    for correction in data.get("corrections", []):
        if not isinstance(correction, dict) or correction.get("case_id") not in case_by_id:
            raise CorpusError("correction must reference an existing case")
        old_output = correction.get("old_expected_output")
        new_output = correction.get("new_expected_output")
        if not isinstance(old_output, str) or not isinstance(new_output, str) or old_output == new_output:
            raise CorpusError("correction must record distinct old and new expected output")
        if case_by_id[correction["case_id"]]["expected_output"] != new_output:
            raise CorpusError("correction output must match the current case label")
        if not correction.get("reason"):
            raise CorpusError("correction reason is required")
    return data
