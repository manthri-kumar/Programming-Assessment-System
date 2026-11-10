from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from backend.agents import AgentContext, AssessmentOrchestrator
from backend.api import create_app
from backend.auth import TokenManager
from backend.knowledge import load_graph
from backend.observability import AuditEvent
from backend.persistence import SQLiteRepository
from backend.runner import FakeRunner, RunStatus, TestRun
from backend.service import AssessmentService


ROOT = Path(__file__).parents[1]
GRAPH = load_graph(ROOT / "data" / "concepts" / "concept-v1.json")

SOURCES = {
    "python": "total = 0\nfor value in [0, 1, 2]:\n    total += value\nprint(total)\n",
    "c": "#include <stdio.h>\nint main(void){int total=0;for(int i=0;i<3;i++){total+=i;}printf(\"%d\\n\",total);return 0;}",
    "java": "public class Main { public static void main(String[] args) { int total=0; for(int i=0;i<3;i++){total+=i;} System.out.println(total); } }",
}


class Recorder:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def emit(self, event: AuditEvent) -> None:
        self.events.append(event)


@pytest.mark.parametrize(
    ("case_name", "language", "outcomes", "expected_test_score"),
    (
        ("correct-python", "python", (RunStatus.PASSED,), 100.0),
        ("incorrect-python", "python", (RunStatus.WRONG_OUTPUT,), 0.0),
        ("partial-python", "python", (RunStatus.PASSED, RunStatus.WRONG_OUTPUT), 50.0),
        ("correct-c", "c", (RunStatus.PASSED,), 100.0),
        ("incorrect-c", "c", (RunStatus.WRONG_OUTPUT,), 0.0),
        ("correct-java", "java", (RunStatus.PASSED,), 100.0),
        ("incorrect-java", "java", (RunStatus.WRONG_OUTPUT,), 0.0),
    ),
)
def test_two_agent_pipeline_across_supported_languages(case_name, language, outcomes, expected_test_score):
    tests = tuple({"id": f"case-{index}", "concept_ids": [], "weight": 1} for index in range(len(outcomes)))
    runs = tuple(TestRun(f"case-{index}", status, weight=1) for index, status in enumerate(outcomes))
    recorder = Recorder()
    context = AgentContext(language, SOURCES[language], SOURCES[language], GRAPH, tests=tests, correlation_id=case_name)

    pipeline = AssessmentOrchestrator(FakeRunner(runs), recorder).run(context)
    evaluation = pipeline["implementation_evaluation"]
    feedback = pipeline["feedback_agent"]

    assert evaluation.stages["code-preprocessing"].ir is not None
    assert evaluation.stages["syntax-analysis"].status == "complete"
    assert evaluation.stages["concept-analysis"].status == "complete"
    assert evaluation.stages["structural-comparison"].status == "complete"
    assert evaluation.stages["complexity-analysis"].status == "complete"
    assert evaluation.stages["test-execution"].status == "complete"
    assert evaluation.evaluation.payload["components"]["tests"] == expected_test_score
    assert feedback.evaluation is evaluation
    assert feedback.report.payload["report"]["trace"] == ["implementation-evaluation", "feedback"]
    assert feedback.report.payload["report"]["evaluation"] == evaluation.evaluation.payload
    assert [event.agent for event in recorder.events if event.event == "agent_complete"] == ["implementation-evaluation", "feedback"]
    assert not any("source" in str(event.details).lower() for event in recorder.events)
    feedback_codes = {item["code"] for item in feedback.feedback.payload["items"]}
    assert ("failed-test" in feedback_codes) is (expected_test_score < 100.0)


def test_syntax_alternative_and_missing_concept_flow_through_both_agents():
    syntax = AssessmentOrchestrator(FakeRunner(())).run(AgentContext("python", "def broken(:", "pass", GRAPH))
    assert syntax["implementation_evaluation"].status == "invalid_submission"
    assert syntax["implementation_evaluation"].stages["test-execution"].status == "skipped"
    assert syntax["feedback_agent"].feedback.payload["items"][0]["code"] == "fix-syntax"

    alternative = AssessmentOrchestrator(FakeRunner((TestRun("sum", RunStatus.PASSED, weight=1),))).run(AgentContext(
        "python",
        "total=0\nfor value in range(4):\n    total+=value\nprint(total)\n",
        "print(sum([0,1,2,3]))\n",
        GRAPH,
        tests=({"id": "sum", "concept_ids": ["loops"], "weight": 1},),
    ))
    assert alternative["implementation_evaluation"].evaluation.payload["components"]["tests"] == 100.0
    assert alternative["implementation_evaluation"].stages["structural-comparison"].payload["relation"] == "different"

    missing = AssessmentOrchestrator(FakeRunner((TestRun("zero", RunStatus.WRONG_OUTPUT, weight=1),))).run(AgentContext(
        "python", "print(1)", "print(1)", GRAPH,
        tests=({"id": "zero", "concept_ids": ["zero-division-guard"], "weight": 1},),
    ))
    assert missing["implementation_evaluation"].stages["concept-analysis"].payload["findings"]["zero-division-guard"] == "absent"
    assert missing["feedback_agent"].weaknesses[-1] == "zero-division-guard"
    assert missing["feedback_agent"].recommendations.payload["recommendations"][-1]["concept_id"] == "zero-division-guard"


def _request(app, method: str, path: str, **kwargs):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


def _register_and_login(app, email: str, role: str) -> str:
    payload = {"email": email, "password": "verification-password", "role": role}
    if role == "teacher":
        payload["teacher_registration_code"] = "verification-invitation"
    assert _request(app, "POST", "/auth/register", json=payload).status_code == 201
    response = _request(app, "POST", "/auth/login", json={"email": email, "password": payload["password"]})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_api_persists_two_agent_report_across_repository_reopen_and_enforces_ownership(tmp_path):
    database = tmp_path / "restart.db"
    runner = FakeRunner((TestRun("case-1", RunStatus.PASSED, weight=1),))
    first_app = create_app(
        SQLiteRepository(database), AssessmentService(runner, GRAPH), TokenManager(b"restart-secret"),
        teacher_registration_code="verification-invitation",
    )
    teacher = _register_and_login(first_app, "owner@example.test", "teacher")
    student = _register_and_login(first_app, "student@example.test", "student")
    assignment = _request(first_app, "POST", "/assignments", headers={"Authorization": f"Bearer {teacher}"}, json={
        "title": "Persisted", "language": "python", "reference_source": "print(1)",
        "tests": [{"id": "case-1", "input": "", "expected_output": "1", "weight": 1, "concept_ids": ["input"]}],
    }).json()
    submission = _request(first_app, "POST", "/submissions", headers={"Authorization": f"Bearer {student}"}, json={
        "assignment_id": assignment["id"], "language": "python", "source": "print(1)",
    }).json()
    evaluated = _request(first_app, "POST", f"/submissions/{submission['id']}/evaluate", headers={"Authorization": f"Bearer {student}"})
    assert evaluated.status_code == 200

    reopened_app = create_app(
        SQLiteRepository(database), AssessmentService(runner, GRAPH), TokenManager(b"restart-secret"),
        teacher_registration_code="verification-invitation",
    )
    student_after_restart = _request(reopened_app, "POST", "/auth/login", json={"email": "student@example.test", "password": "verification-password"}).json()["access_token"]
    teacher_after_restart = _request(reopened_app, "POST", "/auth/login", json={"email": "owner@example.test", "password": "verification-password"}).json()["access_token"]
    report = _request(reopened_app, "GET", f"/submissions/{submission['id']}/evaluation", headers={"Authorization": f"Bearer {student_after_restart}"})
    assert report.status_code == 200
    stored = report.json()["result"]
    assert stored["agent_trace"] == ["implementation-evaluation", "feedback"]
    assert stored["feedback"] and stored["report"]["report_version"] == "assessment-report-v3"
    assert stored["report"]["compatible_versions"] == ["assessment-report-v2"]
    assert _request(reopened_app, "GET", f"/submissions/{submission['id']}/evaluation", headers={"Authorization": f"Bearer {teacher_after_restart}"}).status_code == 200

    other_teacher = _register_and_login(reopened_app, "other@example.test", "teacher")
    denied = _request(reopened_app, "GET", f"/submissions/{submission['id']}/evaluation", headers={"Authorization": f"Bearer {other_teacher}"})
    assert denied.status_code == 403
