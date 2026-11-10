from __future__ import annotations

import hashlib
import json
from typing import Any
from collections.abc import Mapping

from backend.agents import AgentContext, AssessmentOrchestrator
from backend.knowledge import ConceptGraph
from backend.runner import SubmissionRunner
from backend.observability import AuditLogger
from backend.persistence import AssessmentRepository


class AssessmentService:
    def __init__(self, runner: SubmissionRunner, graph: ConceptGraph | None = None, audit_logger: AuditLogger | None = None, repository: AssessmentRepository | None = None) -> None:
        self.runner = runner
        self.graph = graph
        self.audit_logger = audit_logger or AuditLogger()
        self.repository = repository

    def readiness(self) -> dict:
        graph_ready = self.graph is not None
        if graph_ready:
            try: self.graph.validate()
            except ValueError: graph_ready = False
        return {"ready": self.runner.ready() and graph_ready, "runner": self.runner.ready(), "graph": graph_ready}

    def assess(
        self,
        language: str,
        source: str,
        reference_source: str,
        tests: tuple[Any, ...] = (),
        policy_version: str = "core-v1",
        correlation_id: str = "",
        rubric: Mapping[str, float] | None = None,
        *,
        required_concepts: tuple[str, ...] = (),
    ) -> dict:
        normalized_tests = [case.model_dump(mode="json") if hasattr(case, "model_dump") else dict(case) if isinstance(case, dict) else vars(case) for case in tests]
        request_payload = {
            "schema_version": "assessment-config-v1", "language": language, "source": source,
            "reference_source": reference_source, "tests": normalized_tests,
            "policy_version": policy_version, "rubric": dict(rubric or {}),
            "graph_version": self.graph.version if self.graph else None,
            "required_concepts": sorted(set(required_concepts)),
        }
        request_hash = hashlib.sha256(json.dumps(request_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if self.repository is not None:
            existing = self.repository.get_assessment_record_by_hash(request_hash)
            if existing is not None and existing["status"] != "incomplete":
                replay = dict(existing["result"])
                replay["assessment_record_id"] = existing["id"]
                replay["request_hash"] = request_hash
                return replay
        context = AgentContext(
            language,
            source,
            reference_source,
            self.graph,
            required_concepts=required_concepts,
            tests=tests,
            rubric=rubric or {},
            policy_version=policy_version,
            correlation_id=correlation_id,
        )
        pipeline = AssessmentOrchestrator(self.runner, self.audit_logger).run(context)
        evaluation = pipeline["evaluation"]
        feedback = pipeline["feedback"]
        recommendations = pipeline["recommendations"]
        graph_reasoning = pipeline["knowledge_graph"]
        implementation_agent = pipeline["implementation_evaluation"]
        feedback_agent = pipeline["feedback_agent"]
        report = pipeline["report"].payload["report"]
        result = {
            "status": evaluation.status,
            "policy_version": policy_version,
            "total": evaluation.payload.get("total"),
            "category": evaluation.payload.get("category"),
            "components": evaluation.payload.get("components", {}),
            "weights": evaluation.payload.get("weights", {}),
            "test_outcomes": evaluation.payload.get("test_outcomes", ()),
            "agents": [
                {
                    "agent": implementation_agent.agent,
                    "agent_version": implementation_agent.agent_version,
                    "status": implementation_agent.status,
                    "evidence": list(implementation_agent.evidence),
                    "limitations": list(implementation_agent.limitations),
                },
                {
                    "agent": feedback_agent.agent,
                    "agent_version": feedback_agent.agent_version,
                    "status": feedback_agent.status,
                    "evidence": list(feedback_agent.evidence),
                    "limitations": list(feedback_agent.limitations),
                },
            ],
            "agent_trace": report["trace"],
            "analysis": {item["service"]: item for item in report["stages"]},
            "knowledge_graph": graph_reasoning.payload,
            "feedback": feedback.payload.get("items", []),
            "recommendations": recommendations.payload.get("recommendations", []),
            "limitations": report["limitations"],
            "report": report,
        }
        result["request_hash"] = request_hash
        if self.repository is not None and evaluation.status != "incomplete":
            existing = self.repository.create_assessment_record(
                request_hash, evaluation.status, report["versions"], report["evidence_lineage"], result,
            )
            result["assessment_record_id"] = existing["id"]
        return result
