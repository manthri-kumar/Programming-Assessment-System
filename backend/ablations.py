from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Mapping


ABLATION_VERSION = "assessment-ablation-v1"
ABLATIONS: Mapping[str, Mapping[str, bool]] = MappingProxyType({
    "full": MappingProxyType({"functional_tests": True, "static_analysis": True, "concept_analysis": True, "graph_reasoning": True, "feedback_composition": True}),
    "no-functional-tests": MappingProxyType({"functional_tests": False, "static_analysis": True, "concept_analysis": True, "graph_reasoning": True, "feedback_composition": True}),
    "no-static-analysis": MappingProxyType({"functional_tests": True, "static_analysis": False, "concept_analysis": False, "graph_reasoning": False, "feedback_composition": True}),
    "no-concept-analysis": MappingProxyType({"functional_tests": True, "static_analysis": True, "concept_analysis": False, "graph_reasoning": False, "feedback_composition": True}),
    "no-graph-reasoning": MappingProxyType({"functional_tests": True, "static_analysis": True, "concept_analysis": True, "graph_reasoning": False, "feedback_composition": True}),
    "no-feedback-composition": MappingProxyType({"functional_tests": True, "static_analysis": True, "concept_analysis": True, "graph_reasoning": True, "feedback_composition": False}),
})


def ablation_manifest(name: str, corpus_sha256: str) -> dict:
    if name not in ABLATIONS or len(corpus_sha256) != 64:
        raise ValueError("known ablation and corpus SHA-256 are required")
    configuration = dict(ABLATIONS[name])
    payload = {"version": ABLATION_VERSION, "name": name, "corpus_sha256": corpus_sha256, "configuration": configuration}
    payload["configuration_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return payload

