"""API lifecycle and audience checks with no submitted-code execution."""
import json

import pytest

from backend.api import _audience_result, create_app
from backend.auth import TokenManager
from backend.knowledge import Concept, ConceptGraph
from backend.persistence import SQLiteRepository
from backend.runner import FakeRunner, FailClosedRunner, RunStatus, TestRun
from backend.service import AssessmentService
from tests.test_api_and_persistence import headers, register_and_login, request


def workflow(tmp_path, runner=None):
    repository = SQLiteRepository(tmp_path / "recovery.db")
    graph = ConceptGraph("recovery-graph-v1", {"loops": Concept("loops", "Loops", "Practice loops"), "input": Concept("input", "Input", "Practice input")}, {})
    service = AssessmentService(runner or FailClosedRunner(), graph)
    app = create_app(repository, service, TokenManager(b"recovery-secret"), teacher_registration_code="teacher-code")
    teacher = register_and_login(app, "teacher@example.test", "teacher")
    student = register_and_login(app, "student@example.test", "student")
    assignment = request(app, "POST", "/assignments", headers=headers(teacher), json={
        "title": "Required concept", "language": "python", "reference_source": "print(1)",
        "concept_ids": ["loops"], "tests": [{"id": "case", "input": "", "expected_output": "1", "weight": 1, "concept_ids": []}],
    }).json()
    submission = request(app, "POST", "/submissions", headers=headers(student), json={
        "assignment_id": assignment["id"], "language": "python", "source": "print(1)",
    }).json()
    return repository, service, app, teacher, student, assignment, submission


def test_assignment_concepts_reach_agents_from_immutable_submission_snapshot(tmp_path):
    repository, service, app, teacher, student, assignment, submission = workflow(tmp_path)
    updated = request(app, "PATCH", f"/assignments/{assignment['id']}", headers=headers(teacher), json={"concept_ids": ["input"]})
    assert updated.status_code == 200
    evaluated = request(app, "POST", f"/submissions/{submission['id']}/evaluate", headers=headers(student))
    assert evaluated.status_code == 503
    stored = request(app, "GET", f"/submissions/{submission['id']}/evaluation", headers=headers(student)).json()["result"]
    assert stored["analysis"]["concept-analysis"]["payload"]["findings"] == {"loops": "absent"}
    assert stored["recommendations"][0]["concept_id"] == "loops"
    assert stored["agent_trace"] == ["implementation-evaluation", "feedback"]
    assert stored["total"] is None
    assert repository.get_submission_configuration(submission["id"])["snapshot"]["concept_ids"] == ["loops"]


@pytest.mark.parametrize("failure_stage", ["assess", "save_evaluation"])
def test_internal_failure_releases_lease_and_retry_persists_one_report(tmp_path, monkeypatch, failure_stage):
    runner = FakeRunner((TestRun("case", RunStatus.PASSED, weight=1),))
    repository, service, app, teacher, student, assignment, submission = workflow(tmp_path, runner)
    target = service if failure_stage == "assess" else repository
    original = getattr(target, failure_stage)
    calls = 0

    def fail_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("private-diagnostic-with-source-and-secrets")
        return original(*args, **kwargs)

    monkeypatch.setattr(target, failure_stage, fail_once)
    endpoint = f"/submissions/{submission['id']}/evaluate"
    failure = request(app, "POST", endpoint, headers=headers(student))
    assert failure.status_code == 503
    assert failure.json()["detail"]["retryable"] is True
    assert "private-diagnostic" not in failure.text
    job_id = failure.json()["detail"]["evaluation_job_id"]
    job = repository.get_evaluation_job(job_id)
    assert job["state"] == "failed" and job["failure_category"] == "internal"
    assert job["lease_owner"] is None and job["lease_expires_at"] is None
    success = request(app, "POST", endpoint, headers=headers(student))
    replay = request(app, "POST", endpoint, headers=headers(student))
    assert success.status_code == replay.status_code == 200
    assert success.json()["assessment_record_id"] == replay.json()["assessment_record_id"]
    assert repository.get_evaluation_job(job_id)["state"] == "completed"
    assert repository._connection.execute("SELECT COUNT(*) FROM assessment_records").fetchone()[0] == 1
    assert repository._connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0] == 1


def test_repeated_internal_failure_stops_at_configured_retry_bound(tmp_path, monkeypatch):
    repository, service, app, teacher, student, assignment, submission = workflow(tmp_path)
    calls = 0

    def always_fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError("private failure")

    monkeypatch.setattr(service, "assess", always_fail)
    endpoint = f"/submissions/{submission['id']}/evaluate"
    responses = [request(app, "POST", endpoint, headers=headers(student)) for _ in range(3)]
    assert [response.status_code for response in responses] == [503, 503, 503]
    assert [response.json()["detail"]["retryable"] for response in responses] == [True, False, False]
    assert responses[-1].json()["detail"]["code"] == "evaluation_retry_exhausted"
    assert calls == 2
    assert repository.get_evaluation(submission["id"]) is None


def test_student_serializer_removes_nested_grading_secrets_without_mutating_teacher_report():
    private = {"stdout": "private output", "stderr": "private error", "reference_source": "private reference", "input": "private input", "expected_output": "private expectation", "teacher_explanation": "private teacher reasoning"}
    result = {"test_outcomes": [private | {"case_id": "case", "status": "passed"}], "report": {"stages": [{"payload": private}], "teacher_explanation": "private teacher reasoning"}}
    student = _audience_result(result, "student")
    assert "private" not in json.dumps(student)
    assert student["test_outcomes"] == [{"case_id": "case", "status": "passed"}]
    assert _audience_result(result, "teacher") == result
    assert result["report"]["stages"][0]["payload"] == private


def test_student_serializer_preserves_input_concept_evidence():
    result = {"knowledge_graph": {"weak_evidence": {"input": ["concept:input:absent"]}}, "analysis": {"concept-analysis": {"payload": {"findings": {"input": "absent"}}}}}
    assert _audience_result(result, "student") == result


def test_api_student_report_redacts_worker_streams_in_all_nested_copies(tmp_path):
    runner = FakeRunner((TestRun("case", RunStatus.WRONG_OUTPUT, stdout="private worker output", stderr="private worker diagnostic", weight=1),))
    repository, service, app, teacher, student, assignment, submission = workflow(tmp_path, runner)
    endpoint = f"/submissions/{submission['id']}/evaluate"
    student_result = request(app, "POST", endpoint, headers=headers(student))
    teacher_result = request(app, "GET", f"/submissions/{submission['id']}/evaluation", headers=headers(teacher))
    assert student_result.status_code == teacher_result.status_code == 200
    assert "private worker" not in student_result.text
    assert "teacher_explanation" not in student_result.text
    assert "private worker" in teacher_result.text
    assert "teacher_explanation" in teacher_result.text
