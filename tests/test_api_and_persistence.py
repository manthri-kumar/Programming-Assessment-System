from pathlib import Path
import asyncio
import json
import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import httpx

from backend.api import AssessmentTestRequest, create_app
from backend.auth import TokenManager, hash_password, verify_password
from backend.knowledge import Concept, ConceptGraph
from backend.persistence import SQLiteRepository
from backend.persistence import RepositoryError
from backend.runner import FailClosedRunner, FakeRunner, RunStatus, TestRun
from backend.service import AssessmentService
from backend.observability import AuditEvent, AuditLogger


def build_app(tmp_path: Path):
    repository = SQLiteRepository(tmp_path / "test.db")
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    return create_app(repository, AssessmentService(FailClosedRunner(), graph), TokenManager(b"test-secret"), teacher_registration_code="teacher-code")


def request(app, method: str, path: str, **kwargs):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(run())


def register_and_login(app, email: str, role: str) -> str:
    payload = {"email": email, "password": "password123", "role": role}
    if role == "teacher":
        payload["teacher_registration_code"] = "teacher-code"
    assert request(app, "POST", "/auth/register", json=payload).status_code == 201
    response = request(app, "POST", "/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]: return {"Authorization": f"Bearer {token}"}


def test_password_hash_round_trip():
    encoded = hash_password("password123", salt=b"0123456789abcdef")
    assert verify_password("password123", encoded)
    assert not verify_password("wrong-password", encoded)
    assert not verify_password("password123", "malformed")


def test_expired_and_altered_tokens_are_rejected(tmp_path):
    manager = TokenManager(b"test-secret", ttl_seconds=1)
    expired_app = create_app(
        SQLiteRepository(tmp_path / "expired.db"),
        AssessmentService(FailClosedRunner(), ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})),
        manager,
        teacher_registration_code="teacher-code",
    )
    response = request(expired_app, "POST", "/auth/register", json={"email": "expiry@example.test", "password": "password123", "role": "student"})
    assert response.status_code == 201
    token = manager.issue(response.json()["id"], "student", now=1)
    assert request(expired_app, "GET", "/auth/me", headers=headers(token)).status_code == 401
    current = manager.issue(response.json()["id"], "student")
    altered = current[:-1] + ("A" if current[-1] != "A" else "B")
    assert request(expired_app, "GET", "/auth/me", headers=headers(altered)).status_code == 401


def test_api_test_weight_must_be_finite():
    with pytest.raises(ValidationError):
        AssessmentTestRequest(id="case", input="", expected_output="", weight=float("inf"))


def test_health_and_fail_closed_readiness(tmp_path):
    app = build_app(tmp_path)
    assert request(app, "GET", "/health").status_code == 200
    response = request(app, "GET", "/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["runner"] is False
    schema = app.openapi()
    assert {"/health", "/ready", "/assessments", "/auth/register", "/auth/login", "/assignments", "/submissions"}.issubset(schema["paths"])
    published = json.loads((Path(__file__).parents[1] / "docs" / "backend" / "openapi.json").read_text(encoding="utf-8"))
    assert published == schema


def test_server_provisioned_operator_status_is_sanitized_and_not_registerable(tmp_path):
    repository = SQLiteRepository(tmp_path / "operator.db")
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    app = create_app(repository, AssessmentService(FailClosedRunner(), graph), TokenManager(b"operator-secret"), teacher_registration_code="teacher-code", operator_key="server-provisioned-key")
    denied = request(app, "GET", "/operations/status")
    assert denied.status_code == 403
    denied = request(app, "GET", "/operations/status", headers={"x-operator-key": "wrong"})
    assert denied.status_code == 403
    allowed = request(app, "GET", "/operations/status", headers={"x-operator-key": "server-provisioned-key"})
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload == {
        "status_version": "operations-status-v1",
        "worker": {"ready": False, "failure_category": "worker-unavailable"},
        "graph": {"ready": True, "version": "concept-v1"},
        "evaluation_jobs": {"states": {}, "total": 0},
    }
    assert "server-provisioned-key" not in allowed.text
    registration = request(app, "POST", "/auth/register", json={"email": "operator@example.test", "password": "password123", "role": "operator"})
    assert registration.status_code == 422


def test_role_aware_rate_limits_return_bounded_retry_without_bypassing_auth(tmp_path):
    repository = SQLiteRepository(tmp_path / "rate.db")
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    app = create_app(repository, AssessmentService(FailClosedRunner(), graph), TokenManager(b"rate-secret"), teacher_registration_code="teacher-code", rate_limits={"auth": 1, "submission": 1, "evaluation": 1})
    assert request(app, "POST", "/auth/login", json={"email": "nobody@example.test", "password": "password123"}).status_code == 401
    limited_login = request(app, "POST", "/auth/login", json={"email": "nobody@example.test", "password": "password123"})
    assert limited_login.status_code == 429
    assert 1 <= int(limited_login.headers["retry-after"]) <= 60

    teacher_user = repository.create_user("rate-teacher@example.test", hash_password("password123"), "teacher")
    student_user = repository.create_user("rate-student@example.test", hash_password("password123"), "student")
    student_token = TokenManager(b"rate-secret").issue(student_user["id"], "student")
    assignment = repository.create_assignment(teacher_user["id"], {
        "title": "Rate", "description": "", "language": "python", "rubric": {"policy_version": "core-v1"},
        "reference_source": "print(1)", "tests": [{"id": "case", "input": "", "expected_output": "1", "weight": 1, "concept_ids": []}],
    })
    first = request(app, "POST", "/submissions", headers=headers(student_token), json={"assignment_id": assignment["id"], "language": "python", "source": "print(1)"})
    assert first.status_code == 201
    second = request(app, "POST", "/submissions", headers=headers(student_token), json={"assignment_id": assignment["id"], "language": "python", "source": "print(2)"})
    assert second.status_code == 429
    unauthenticated = request(app, "POST", "/submissions", json={"assignment_id": assignment["id"], "language": "python", "source": "print(3)"})
    assert unauthenticated.status_code == 401

    invalid_graph = ConceptGraph("bad", {"input": Concept("input", "Input", "Practice")}, {"input": ("missing",)})
    unavailable = AssessmentService(FailClosedRunner(), invalid_graph).readiness()
    assert unavailable == {"ready": False, "runner": False, "graph": False}


def test_api_errors_are_correlated_and_sanitized(tmp_path):
    app = build_app(tmp_path)
    unauthorized = request(app, "GET", "/auth/me", headers={"x-request-id": "known-request"})
    assert unauthorized.status_code == 401
    assert unauthorized.headers["x-request-id"] == "known-request"
    assert unauthorized.json()["error"] == {
        "code": "authorization_error",
        "message": "request could not be completed",
        "request_id": "known-request",
    }
    invalid = request(app, "POST", "/auth/register", json={})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"
    too_large = request(app, "POST", "/auth/login", headers={"content-length": str(8 * 1024 * 1024 + 1)}, content=b"{}")
    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "limit_exceeded"

    class BrokenService:
        graph = None
        def readiness(self):
            raise RuntimeError("sensitive internal detail")
    broken = create_app(SQLiteRepository(tmp_path / "broken.db"), BrokenService(), TokenManager(b"test-secret"))
    failed = request(broken, "GET", "/ready", headers={"x-request-id": "failure-request"})
    assert failed.status_code == 500
    assert failed.json() == {"error": {"code": "internal_error", "message": "internal server error", "request_id": "failure-request"}}
    assert "sensitive" not in failed.text


def test_direct_assessment_distinguishes_student_and_infrastructure_failures(tmp_path):
    app = build_app(tmp_path)
    student = register_and_login(app, "direct@example.test", "student")
    payload = {
        "language": "python",
        "source": "def broken(:",
        "reference_source": "print(1)",
        "tests": [{"id": "case-1", "input": "", "expected_output": "1\n", "weight": 1, "concept_ids": ["input"]}],
    }
    invalid = request(app, "POST", "/assessments", headers=headers(student), json=payload)
    assert invalid.status_code == 200
    assert invalid.json()["status"] == "invalid_submission"
    assert invalid.json()["total"] is None

    payload["source"] = "print(1)"
    unavailable = request(app, "POST", "/assessments", headers=headers(student), json=payload)
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"]["status"] == "incomplete"

    payload["tests"].append(dict(payload["tests"][0]))
    duplicate = request(app, "POST", "/assessments", headers=headers(student), json=payload)
    assert duplicate.status_code == 422
    payload["tests"] = payload["tests"][:1]
    payload["policy_version"] = "legacy-v1"
    unsupported = request(app, "POST", "/assessments", headers=headers(student), json=payload)
    assert unsupported.status_code == 422
    assert unsupported.json()["error"]["code"] == "validation_error"


def test_direct_assessment_uses_evaluation_agent_and_real_rubric_math(tmp_path):
    repository = SQLiteRepository(tmp_path / "complete.db")
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    runner = FakeRunner((TestRun("case-1", RunStatus.PASSED, weight=1),))
    app = create_app(repository, AssessmentService(runner, graph), TokenManager(b"test-secret"), teacher_registration_code="teacher-code")
    teacher = register_and_login(app, "complete@example.test", "teacher")
    payload = {
        "language": "python",
        "source": "print(1)",
        "reference_source": "print(1)",
        "tests": [{"id": "case-1", "input": "", "expected_output": "1\n", "weight": 1, "concept_ids": ["input"]}],
    }
    response = request(app, "POST", "/assessments", headers=headers(teacher), json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "complete"
    assert result["components"] == {"structure": 100.0, "syntax": 100.0, "tests": 100.0, "originality": 0.0}
    assert result["total"] == 80.0
    assert result["category"] == "Good"
    assert result["assessment_record_id"] > 0
    assert result["report"]["report_version"] == "assessment-report-v3"
    assert result["report"]["compatible_versions"] == ["assessment-report-v2"]
    assert result["agent_trace"] == ["implementation-evaluation", "feedback"]
    assert [item["agent"] for item in result["agents"]] == ["implementation-evaluation", "feedback"]
    assert len(result["agents"]) == 2
    assert result["analysis"]["knowledge-graph-reasoning"]["status"] == "complete"
    replay = repository.get_assessment_record(result["assessment_record_id"])
    assert replay["result"]["report"] == result["report"]


def test_direct_assessment_rejects_blank_source_before_runner(tmp_path):
    repository = SQLiteRepository(tmp_path / "blank.db")
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    runner = FakeRunner((TestRun("case", RunStatus.PASSED, weight=1),))
    app = create_app(repository, AssessmentService(runner, graph), TokenManager(b"blank-secret"), teacher_registration_code="teacher-code")
    teacher = register_and_login(app, "blank@example.test", "teacher")
    response = request(app, "POST", "/assessments", headers=headers(teacher), json={
        "language": "python", "source": " ", "reference_source": "print(1)",
        "tests": [{"id": "case", "input": "", "expected_output": "1", "weight": 1, "concept_ids": []}],
    })
    assert response.status_code == 422


def test_roles_hidden_data_submission_and_blocked_evaluation(tmp_path):
    app = build_app(tmp_path)
    teacher = register_and_login(app, "teacher@example.test", "teacher")
    student = register_and_login(app, "student@example.test", "student")

    denied = request(app, "POST", "/assignments", headers=headers(student), json={"title": "Denied", "language": "python", "reference_source": "pass", "tests": []})
    assert denied.status_code == 403

    created = request(app, "POST", "/assignments", headers=headers(teacher), json={"title": "Addition", "description": "Add", "language": "python", "reference_source": "print(2)", "tests": [{"id": "case-1", "input": "", "expected_output": "2", "weight": 1, "concept_ids": []}]})
    assert created.status_code == 201
    assignment_id = created.json()["id"]

    student_view = request(app, "GET", f"/assignments/{assignment_id}", headers=headers(student)).json()
    assert "reference_source" not in student_view and "tests" not in student_view
    teacher_view = request(app, "GET", f"/assignments/{assignment_id}", headers=headers(teacher)).json()
    assert teacher_view["reference_source"] == "print(2)"

    submitted = request(app, "POST", "/submissions", headers=headers(student), json={"assignment_id": assignment_id, "language": "python", "source": "print(2)"})
    assert submitted.status_code == 201 and "source" not in submitted.json()
    submission_id = submitted.json()["id"]

    evaluation = request(app, "POST", f"/submissions/{submission_id}/evaluate", headers=headers(student))
    assert evaluation.status_code == 503
    assert evaluation.json()["detail"]["status"] == "incomplete"
    stored = request(app, "GET", f"/submissions/{submission_id}/evaluation", headers=headers(student))
    assert stored.status_code == 200
    assert stored.json()["result"]["status"] == "incomplete"


def test_assignment_creation_contract_validation_and_visibility(tmp_path):
    database = tmp_path / "assignment-contract.db"
    repository = SQLiteRepository(database)
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    app = create_app(repository, AssessmentService(FailClosedRunner(), graph), TokenManager(b"test-secret"), teacher_registration_code="teacher-code")
    owner = register_and_login(app, "contract-owner@example.test", "teacher")
    other_teacher = register_and_login(app, "contract-other@example.test", "teacher")
    student = register_and_login(app, "contract-student@example.test", "student")
    valid = {
        "title": "Input Echo",
        "description": "Echo one value.",
        "language": "python",
        "reference_source": "print(input())",
        "tests": [{"id": "echo-1", "input": "hello\n", "expected_output": "hello\n", "weight": 1, "concept_ids": ["input"]}],
        "rubric": {"policy_version": "core-v1", "weights": {"structure": .25, "syntax": .15, "tests": .5, "originality": .1}},
        "requirements": "Read and echo one line.",
        "input_notes": "One line.",
        "output_notes": "The same line.",
        "examples": ["hello -> hello"],
        "constraints": "UTF-8 text.",
        "concept_ids": ["input"],
        "deadline": "2026-12-01T12:00:00+05:30",
    }
    created = request(app, "POST", "/assignments", headers=headers(owner), json=valid)
    assert created.status_code == 201
    assignment_id = created.json()["id"]
    assert created.json()["teacher_id"] > 0
    assert {"reference_source", "tests"}.isdisjoint(created.json())

    owner_view = request(app, "GET", f"/assignments/{assignment_id}", headers=headers(owner))
    assert owner_view.status_code == 200
    assert owner_view.json()["reference_source"] == valid["reference_source"]
    assert owner_view.json()["tests"][0]["id"] == "echo-1"
    for token in (student, other_teacher):
        public_view = request(app, "GET", f"/assignments/{assignment_id}", headers=headers(token))
        assert public_view.status_code == 200
        assert {"reference_source", "tests", "rubric"}.isdisjoint(public_view.json())
    assert request(app, "PATCH", f"/assignments/{assignment_id}", headers=headers(other_teacher), json={"title": "stolen"}).status_code == 404
    assert [item["id"] for item in request(app, "GET", "/assignments", headers=headers(student)).json()] == [assignment_id]
    reloaded = SQLiteRepository(database).get_assignment(assignment_id)
    assert reloaded is not None
    assert reloaded["teacher_id"] == owner_view.json()["teacher_id"]
    assert reloaded["reference_source"] == valid["reference_source"]
    updated = request(app, "PATCH", f"/assignments/{assignment_id}", headers=headers(owner), json={"title": "Input Echo Updated", "deadline": None})
    assert updated.status_code == 200
    assert updated.json()["title"] == "Input Echo Updated"
    assert updated.json()["deadline"] is None

    invalid_payloads = (
        ({**valid, "title": ""}, 422),
        ({**valid, "language": "javascript"}, 422),
        ({**valid, "reference_source": "   "}, 422),
        ({**valid, "rubric": {"policy_version": "core-v1", "weights": {"structure": 1, "syntax": 1, "tests": 1, "originality": 1}}}, 422),
        ({**valid, "tests": [{"id": "", "input": "", "expected_output": "", "weight": 1, "concept_ids": []}]}, 422),
        ({**valid, "tests": [{"id": "same", "input": "", "expected_output": "", "weight": 1, "concept_ids": []}, {"id": "same", "input": "", "expected_output": "", "weight": 1, "concept_ids": []}]}, 422),
        ({**valid, "tests": [{"id": "bad-weight", "input": "", "expected_output": "", "weight": 0, "concept_ids": []}]}, 422),
        ({**valid, "concept_ids": ["not-in-graph"]}, 422),
    )
    for payload, expected_status in invalid_payloads:
        response = request(app, "POST", "/assignments", headers=headers(owner), json=payload)
        assert response.status_code == expected_status
        assert response.json()["error"]["code"] == "validation_error"
    unknown = request(app, "POST", "/assignments", headers=headers(owner), json={**valid, "concept_ids": ["not-in-graph"]})
    assert unknown.json()["detail"] == {"unknown_concepts": ["not-in-graph"]}
    assert request(app, "POST", "/assignments", json=valid).status_code == 401
    assert request(app, "POST", "/assignments", headers=headers(student), json=valid).status_code == 403


def test_student_cannot_read_another_students_submission(tmp_path):
    app = build_app(tmp_path)
    teacher = register_and_login(app, "teacher@example.test", "teacher")
    student_a = register_and_login(app, "a@example.test", "student")
    student_b = register_and_login(app, "b@example.test", "student")
    assignment = request(app, "POST", "/assignments", headers=headers(teacher), json={"title": "A", "language": "python", "reference_source": "pass", "tests": []}).json()
    submission = request(app, "POST", "/submissions", headers=headers(student_a), json={"assignment_id": assignment["id"], "language": "python", "source": "pass"}).json()
    assert request(app, "GET", f"/submissions/{submission['id']}/evaluation", headers=headers(student_b)).status_code == 403
    assert request(app, "GET", "/submissions", headers=headers(student_b)).json() == []
    own_history = request(app, "GET", "/submissions", headers=headers(student_a)).json()
    assert [item["id"] for item in own_history] == [submission["id"]]


def test_teacher_registration_requires_server_invitation(tmp_path):
    app = build_app(tmp_path)
    payload = {"email": "new-teacher@example.test", "password": "password123", "role": "teacher"}
    missing = request(app, "POST", "/auth/register", json=payload)
    assert missing.status_code == 422
    assert request(app, "POST", "/auth/login", json={"email": payload["email"], "password": payload["password"]}).status_code == 401
    payload["teacher_registration_code"] = "wrong"
    invalid = request(app, "POST", "/auth/register", json=payload)
    assert invalid.status_code == 403
    assert invalid.json()["detail"] == "invalid teacher registration code"
    assert request(app, "POST", "/auth/login", json={"email": payload["email"], "password": payload["password"]}).status_code == 401
    payload["teacher_registration_code"] = "teacher-code"
    created = request(app, "POST", "/auth/register", json=payload)
    assert created.status_code == 201
    assert created.json()["role"] == "teacher"


def test_registration_validates_inputs_duplicates_and_configuration(tmp_path, monkeypatch):
    app = build_app(tmp_path)
    invalid_payloads = (
        {"email": "not-an-email", "password": "password123", "role": "student"},
        {"email": "valid@example.test", "password": "short", "role": "student"},
        {"email": "valid@example.test", "password": "x" * 129, "role": "student"},
        {"email": "valid@example.test", "password": "password123", "role": "administrator"},
    )
    for payload in invalid_payloads:
        assert request(app, "POST", "/auth/register", json=payload).status_code == 422
    assert request(app, "POST", "/auth/login", json={"email": "valid@example.test", "password": "password123"}).status_code == 401

    student = {"email": "  learner@example.test  ", "password": "password123", "role": "student"}
    created = request(app, "POST", "/auth/register", json=student)
    assert created.status_code == 201
    assert created.json() == {"id": created.json()["id"], "email": "learner@example.test", "role": "student"}
    duplicate = request(app, "POST", "/auth/register", json={**student, "email": "LEARNER@example.test"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "email already registered"

    monkeypatch.delenv("ASSESSMENT_TEACHER_REGISTRATION_CODE", raising=False)
    unconfigured = create_app(
        SQLiteRepository(tmp_path / "unconfigured.db"),
        AssessmentService(FailClosedRunner(), ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})),
        TokenManager(b"test-secret"),
        teacher_registration_code=None,
    )
    response = request(unconfigured, "POST", "/auth/register", json={
        "email": "teacher@example.test", "password": "password123", "role": "teacher", "teacher_registration_code": "supplied-code",
    })
    assert response.status_code == 503
    assert response.json()["detail"] == "teacher registration is not configured"
    assert request(unconfigured, "POST", "/auth/login", json={"email": "teacher@example.test", "password": "password123"}).status_code == 401


def test_teacher_ownership_protects_hidden_assignment_and_submission_data(tmp_path):
    app = build_app(tmp_path)
    owner = register_and_login(app, "owner@example.test", "teacher")
    other = register_and_login(app, "other@example.test", "teacher")
    student = register_and_login(app, "learner@example.test", "student")
    created = request(app, "POST", "/assignments", headers=headers(owner), json={
        "title": "Private", "language": "python", "reference_source": "print(1)",
        "tests": [{"id": "hidden", "input": "", "expected_output": "1", "weight": 1, "concept_ids": []}],
    }).json()
    assignment_id = created["id"]
    other_view = request(app, "GET", f"/assignments/{assignment_id}", headers=headers(other))
    assert other_view.status_code == 200
    assert {"reference_source", "tests", "rubric"}.isdisjoint(other_view.json())
    assert request(app, "PATCH", f"/assignments/{assignment_id}", headers=headers(other), json={"title": "stolen"}).status_code == 404

    submission = request(app, "POST", "/submissions", headers=headers(student), json={
        "assignment_id": assignment_id, "language": "python", "source": "print(1)"
    }).json()
    submission_id = submission["id"]
    assert request(app, "GET", f"/submissions/{submission_id}", headers=headers(other)).status_code == 403
    assert request(app, "POST", f"/submissions/{submission_id}/evaluate", headers=headers(other)).status_code == 403
    assert request(app, "GET", "/submissions", headers=headers(other)).json() == []


def test_custom_rubric_history_analytics_and_progress(tmp_path):
    repository = SQLiteRepository(tmp_path / "workflow.db")
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    runner = FakeRunner((TestRun("case-1", RunStatus.PASSED, weight=1),))
    app = create_app(repository, AssessmentService(runner, graph), TokenManager(b"test-secret"), teacher_registration_code="teacher-code")
    teacher = register_and_login(app, "workflow-teacher@example.test", "teacher")
    student = register_and_login(app, "workflow-student@example.test", "student")
    rubric = {"policy_version": "core-v1", "weights": {"structure": 0.1, "syntax": 0.1, "tests": 0.1, "originality": 0.7}}
    assignment = request(app, "POST", "/assignments", headers=headers(teacher), json={
        "title": "Weighted", "language": "python", "reference_source": "print(1)", "rubric": rubric,
        "tests": [{"id": "case-1", "input": "", "expected_output": "1", "weight": 1, "concept_ids": ["input"]}],
    }).json()
    assignment_id = assignment["id"]
    updated = request(app, "PATCH", f"/assignments/{assignment_id}", headers=headers(teacher), json={"description": "Updated"})
    assert updated.status_code == 200 and updated.json()["description"] == "Updated"
    invalid = request(app, "PATCH", f"/assignments/{assignment_id}", headers=headers(teacher), json={
        "rubric": {"policy_version": "core-v1", "weights": {"structure": 1, "syntax": 1, "tests": 1, "originality": 1}}
    })
    assert invalid.status_code == 422

    submission = request(app, "POST", "/submissions", headers=headers(student), json={
        "assignment_id": assignment_id, "language": "python", "source": "print(1)"
    }).json()
    result = request(app, "POST", f"/submissions/{submission['id']}/evaluate", headers=headers(student))
    assert result.status_code == 200
    assert result.json()["weights"] == rubric["weights"]
    assert result.json()["total"] == 30.0

    student_history = request(app, "GET", "/submissions?limit=10&offset=0", headers=headers(student)).json()
    assert len(student_history) == 1 and "source" not in student_history[0]
    teacher_history = request(app, "GET", f"/submissions?assignment_id={assignment_id}", headers=headers(teacher)).json()
    assert len(teacher_history) == 1
    progress = request(app, "GET", "/student/progress", headers=headers(student)).json()
    assert progress["submission_count"] == 1 and progress["average_score"] == 30.0
    analytics = request(app, "GET", "/teacher/analytics", headers=headers(teacher)).json()
    assert analytics["assignment_count"] == 1 and analytics["average_score"] == 30.0
    assert request(app, "GET", "/student/progress", headers=headers(teacher)).status_code == 403
    assert request(app, "GET", "/submissions?limit=101", headers=headers(student)).status_code == 422


def test_sqlite_round_trip_migration_and_redaction(tmp_path):
    repository = SQLiteRepository(tmp_path / "roundtrip.db")
    assert repository.schema_version() == 8
    user = repository.create_user("student@example.test", hash_password("password123"), "student")
    teacher = repository.create_user("teacher@example.test", hash_password("password123"), "teacher")
    assignment = repository.create_assignment(teacher["id"], {"title": "A", "description": "", "language": "python", "rubric": {"policy_version": "core-v1"}, "reference_source": "pass", "tests": []})
    submission = repository.create_submission(assignment["id"], user["id"], "python", "secret source")
    repository.save_evaluation(submission["id"], "core-v1", {"status": "incomplete", "total": None})
    assert repository.get_evaluation(submission["id"])["result"]["status"] == "incomplete"
    repository.redact_submission_source(submission["id"])
    assert repository.get_submission(submission["id"])["source"] == "[REDACTED]"


def test_assessment_record_replay_duplicate_rollback_and_retention(tmp_path):
    repository = SQLiteRepository(tmp_path / "records.db")
    record = repository.create_assessment_record(
        "hash-1",
        "complete",
        {"policy": "core-v1", "graph": "concept-v1", "ir": "ir-v1"},
        ["syntax:abc"],
        {"status": "complete", "source": "secret source", "test_outcomes": [{"stdout": "secret output", "status": "passed"}]},
    )
    replay = repository.get_assessment_record(record["id"])
    assert replay["request_hash"] == "hash-1"
    assert replay["versions"]["graph"] == "concept-v1"
    assert replay["evidence"] == ["syntax:abc"]
    with pytest.raises(RepositoryError):
        repository.create_assessment_record("hash-1", "complete", {}, [], {})

    with pytest.raises(Exception):
        with repository.transaction() as db:
            db.execute("INSERT INTO users(email,password_hash,role) VALUES('rollback@example.test','x','invalid')")
    assert repository.find_user("rollback@example.test") is None

    with repository.transaction() as db:
        db.execute("UPDATE assessment_records SET created_at='2000-01-01 00:00:00' WHERE id=?", (record["id"],))
    counts = repository.redact_expired(30, datetime(2026, 10, 19, tzinfo=timezone.utc))
    assert counts["assessment_records"] == 1
    redacted = repository.get_assessment_record(record["id"])
    assert redacted["result"]["source"] == "[REDACTED]"
    assert redacted["result"]["test_outcomes"][0]["stdout"] == "[REDACTED]"
    assert redacted["versions"]["policy"] == "core-v1"


def test_submission_configuration_is_immutable_hidden_and_duplicate_evaluation_is_canonical(tmp_path):
    repository = SQLiteRepository(tmp_path / "snapshot.db")
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    runner = FakeRunner((TestRun("original", RunStatus.PASSED, weight=1),))
    app = create_app(repository, AssessmentService(runner, graph, repository=repository), TokenManager(b"snapshot-secret"), teacher_registration_code="teacher-code")
    teacher = register_and_login(app, "snapshot-teacher@example.test", "teacher")
    student = register_and_login(app, "snapshot-student@example.test", "student")
    assignment = request(app, "POST", "/assignments", headers=headers(teacher), json={
        "title": "Snapshot", "language": "python", "reference_source": "print(1)",
        "tests": [{"id": "original", "input": "", "expected_output": "1", "weight": 1, "concept_ids": ["input"]}],
    }).json()
    submission_response = request(app, "POST", "/submissions", headers=headers(student), json={
        "assignment_id": assignment["id"], "language": "python", "source": "print(1)",
    })
    assert submission_response.status_code == 201
    assert "config_snapshot_json" not in submission_response.json()
    submission_id = submission_response.json()["id"]
    repository.update_assignment(assignment["id"], repository.find_user("snapshot-teacher@example.test")["id"], {
        "reference_source": "print(2)",
        "tests": [{"id": "changed", "input": "", "expected_output": "2", "weight": 1, "concept_ids": []}],
    })
    first = request(app, "POST", f"/submissions/{submission_id}/evaluate", headers=headers(student))
    second = request(app, "POST", f"/submissions/{submission_id}/evaluate", headers=headers(student))
    assert first.status_code == second.status_code == 200
    assert first.json()["request_hash"] == second.json()["request_hash"]
    assert first.json()["assessment_record_id"] == second.json()["assessment_record_id"]
    assert first.json()["test_outcomes"][0]["case_id"] == "original"
    assert "teacher_explanation" not in first.json()["report"]
    teacher_view = request(app, "GET", f"/submissions/{submission_id}/evaluation", headers=headers(teacher))
    assert teacher_view.status_code == 200
    assert teacher_view.json()["result"]["report"]["teacher_explanation"]["evidence_refs"]
    detail = request(app, "GET", f"/submissions/{submission_id}", headers=headers(student)).json()
    assert "config_snapshot_json" not in detail and "config_hash" not in detail


def test_persisted_v2_report_replays_without_mutating_its_version(tmp_path):
    repository = SQLiteRepository(tmp_path / "v2-replay.db")
    teacher = repository.create_user("v2-teacher@example.test", hash_password("password123"), "teacher")
    student = repository.create_user("v2-student@example.test", hash_password("password123"), "student")
    assignment = repository.create_assignment(teacher["id"], {
        "title": "Historical", "description": "", "language": "python", "rubric": {"policy_version": "core-v1"},
        "reference_source": "print(1)", "tests": [{"id": "case", "input": "", "expected_output": "1", "weight": 1, "concept_ids": []}],
    })
    submission = repository.create_submission(assignment["id"], student["id"], "python", "print(1)")
    repository.save_evaluation(submission["id"], "core-v1", {
        "status": "complete", "total": 80.0, "category": "Good", "report": {
            "report_version": "assessment-report-v2", "status": "complete",
            "evaluation": {"total": 80.0, "category": "Good"}, "stages": [], "feedback": [],
        },
    })
    replay = repository.get_evaluation(submission["id"])["result"]["report"]
    assert replay["report_version"] == "assessment-report-v2"
    assert replay["overview"]["total"] == 80.0
    raw = repository._connection.execute("SELECT result_json FROM evaluations WHERE submission_id=?", (submission["id"],)).fetchone()["result_json"]
    assert "overview" not in json.loads(raw)["report"]


def test_concurrent_submissions_receive_unique_ids_and_remain_isolated(tmp_path):
    repository = SQLiteRepository(tmp_path / "concurrent.db")
    teacher = repository.create_user("concurrent-teacher@example.test", hash_password("password123"), "teacher")
    student = repository.create_user("concurrent-student@example.test", hash_password("password123"), "student")
    assignment = repository.create_assignment(teacher["id"], {
        "title": "Concurrent", "description": "", "language": "python",
        "rubric": {"policy_version": "core-v1"}, "reference_source": "print(1)", "tests": [],
    })
    def submit(index):
        return repository.create_submission(assignment["id"], student["id"], "python", f"print({index})")
    with ThreadPoolExecutor(max_workers=8) as pool:
        submissions = list(pool.map(submit, range(20)))
    ids = {item["id"] for item in submissions}
    assert len(ids) == 20
    stored_sources = {repository.get_submission(item["id"])["source"] for item in submissions}
    assert stored_sources == {f"print({index})" for index in range(20)}


def test_evaluation_job_lease_cancellation_and_bounded_retry(tmp_path):
    repository = SQLiteRepository(tmp_path / "jobs.db")
    teacher = repository.create_user("job-teacher@example.test", hash_password("password123"), "teacher")
    student = repository.create_user("job-student@example.test", hash_password("password123"), "student")
    assignment = repository.create_assignment(teacher["id"], {
        "title": "Job", "description": "", "language": "python", "rubric": {"policy_version": "core-v1"},
        "reference_source": "print(1)", "tests": [{"id": "case", "input": "", "expected_output": "1", "weight": 1, "concept_ids": []}],
    })
    submission = repository.create_submission(assignment["id"], student["id"], "python", "print(1)")
    config = repository.get_submission_configuration(submission["id"])
    job = repository.create_evaluation_job(submission["id"], config["hash"], max_attempts=2)
    assert repository.create_evaluation_job(submission["id"], config["hash"])["job_id"] == job["job_id"]
    claimed = repository.claim_evaluation_job(job["job_id"], "worker-one", lease_seconds=30)
    assert claimed["state"] == "running" and claimed["attempts"] == 1
    assert repository.claim_evaluation_job(job["job_id"], "worker-two") is None
    failed = repository.fail_evaluation_job(job["job_id"], "worker-unavailable", retryable=True)
    assert failed["state"] == "failed"
    claimed = repository.claim_evaluation_job(job["job_id"], "worker-two")
    assert claimed["attempts"] == 2
    failed = repository.fail_evaluation_job(job["job_id"], "worker-unavailable", retryable=True)
    assert failed["state"] == "failed"
    assert repository.claim_evaluation_job(job["job_id"], "worker-three") is None

    second = repository.create_submission(assignment["id"], student["id"], "python", "print(2)")
    second_config = repository.get_submission_configuration(second["id"])
    cancellable = repository.create_evaluation_job(second["id"], second_config["hash"])
    assert repository.cancel_evaluation_job(cancellable["job_id"])["state"] == "cancelled"
    assert repository.claim_evaluation_job(cancellable["job_id"], "worker") is None


def test_backup_restore_preserves_ownership_snapshot_and_immutable_result(tmp_path):
    repository = SQLiteRepository(tmp_path / "primary.db")
    teacher = repository.create_user("backup-teacher@example.test", hash_password("password123"), "teacher")
    student = repository.create_user("backup-student@example.test", hash_password("password123"), "student")
    assignment = repository.create_assignment(teacher["id"], {
        "title": "Backup", "description": "", "language": "python", "rubric": {"policy_version": "core-v1"},
        "reference_source": "print(1)", "tests": [{"id": "case", "input": "", "expected_output": "1", "weight": 1, "concept_ids": []}],
    })
    submission = repository.create_submission(assignment["id"], student["id"], "python", "print(1)")
    repository.save_evaluation(submission["id"], "core-v1", {"status": "complete", "total": 80.0, "report": {"report_version": "assessment-report-v3"}})
    backup = repository.backup_to(tmp_path / "backup.db")
    with pytest.raises(RepositoryError, match="already exists"):
        repository.backup_to(backup)
    restored = SQLiteRepository.restore_from_backup(backup, tmp_path / "restored.db")
    assert restored.find_user("backup-teacher@example.test")["id"] == teacher["id"]
    assert restored.get_submission(submission["id"])["student_id"] == student["id"]
    assert restored.get_submission_configuration(submission["id"])["snapshot"]["reference_source"] == "print(1)"
    assert restored.get_evaluation(submission["id"])["result"]["total"] == 80.0


def test_default_local_institution_scope_preserves_existing_workflows(tmp_path):
    repository = SQLiteRepository(tmp_path / "institution.db")
    teacher = repository.create_user("scope-teacher@example.test", hash_password("password123"), "teacher")
    student = repository.create_user("scope-student@example.test", hash_password("password123"), "student")
    assignment = repository.create_assignment(teacher["id"], {
        "title": "Scoped", "description": "", "language": "python", "rubric": {"policy_version": "core-v1"},
        "reference_source": "print(1)", "tests": [{"id": "case", "input": "", "expected_output": "1", "weight": 1, "concept_ids": []}],
    })
    institution = repository._connection.execute("SELECT * FROM institutions WHERE code='local'").fetchone()
    course = repository._connection.execute("SELECT * FROM courses WHERE institution_id=? AND code='local'", (institution["id"],)).fetchone()
    assert assignment["course_id"] == course["id"]
    assert repository._connection.execute("SELECT 1 FROM course_teachers WHERE course_id=? AND teacher_id=?", (course["id"], teacher["id"])).fetchone()
    assert repository._connection.execute("SELECT 1 FROM enrollments WHERE course_id=? AND student_id=? AND status='active'", (course["id"], student["id"])).fetchone()


def test_transient_execution_unavailability_retries_then_completes_once(tmp_path):
    repository = SQLiteRepository(tmp_path / "retry.db")
    graph = ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice")}, {})
    runner = FakeRunner((TestRun("case", RunStatus.PASSED, weight=1),), available=False)
    app = create_app(repository, AssessmentService(runner, graph), TokenManager(b"retry-secret"), teacher_registration_code="teacher-code")
    teacher = register_and_login(app, "retry-teacher@example.test", "teacher")
    student = register_and_login(app, "retry-student@example.test", "student")
    assignment = request(app, "POST", "/assignments", headers=headers(teacher), json={
        "title": "Retry", "language": "python", "reference_source": "print(1)",
        "tests": [{"id": "case", "input": "", "expected_output": "1", "weight": 1, "concept_ids": ["input"]}],
    }).json()
    submission = request(app, "POST", "/submissions", headers=headers(student), json={
        "assignment_id": assignment["id"], "language": "python", "source": "print(1)",
    }).json()
    first = request(app, "POST", f"/submissions/{submission['id']}/evaluate", headers=headers(student))
    assert first.status_code == 503
    runner.available = True
    second = request(app, "POST", f"/submissions/{submission['id']}/evaluate", headers=headers(student))
    assert second.status_code == 200 and second.json()["status"] == "complete"
    third = request(app, "POST", f"/submissions/{submission['id']}/evaluate", headers=headers(student))
    assert third.status_code == 200
    assert third.json()["assessment_record_id"] == second.json()["assessment_record_id"]
    status_response = request(app, "GET", f"/submissions/{submission['id']}/evaluation-job", headers=headers(student))
    assert status_response.json()["state"] == "completed"
    assert set(status_response.json()) <= {"job_id", "state", "attempts", "max_attempts", "failure_category", "created_at", "updated_at"}


def test_audit_log_redacts_sensitive_fields_and_preserves_evidence():
    serialized = AuditLogger().serialize(AuditEvent(
        "request-1", "agent_complete", "complete", "evaluation", "1", 2.5,
        ("evidence-1",), {"source": "student secret", "authorization": "Bearer secret", "count": 2},
    ))
    assert "student secret" not in serialized
    assert "Bearer secret" not in serialized
    payload = json.loads(serialized)
    assert payload["details"] == {"authorization": "[REDACTED]", "count": 2, "source": "[REDACTED]"}
    assert payload["evidence_ids"] == ["evidence-1"]


def test_audit_log_redacts_assignment_import_content_and_provider_secrets():
    sensitive = {
        "document_bytes": "private bytes",
        "extracted_text": "faculty question",
        "reference_source": "private solution",
        "hidden_tests": [{"input": "secret case"}],
        "prompt": "provider prompt",
        "raw_provider_response": {"text": "raw result"},
        "path": "C:/private/import.png",
        "storage_key": "opaque-private-key",
        "token": "access-token",
        "credentials": {"api_key": "super-sensitive-api-value"},
    }
    serialized = AuditLogger().serialize(AuditEvent(
        "request-2", "assignment_import", "invalid_file_type", details={**sensitive, "teacher_id": 7, "byte_size": 128},
    ))
    for secret in ("private bytes", "faculty question", "private solution", "secret case", "provider prompt", "raw result", "C:/private", "opaque-private-key", "access-token", "super-sensitive-api-value"):
        assert secret not in serialized
    payload = json.loads(serialized)
    assert payload["details"]["teacher_id"] == 7
    assert payload["details"]["byte_size"] == 128
    assert all(payload["details"][key] == "[REDACTED]" for key in sensitive)


def test_frontend_support_contracts_are_scoped_and_do_not_execute(tmp_path):
    repository = SQLiteRepository(tmp_path / "frontend.db")
    graph = ConceptGraph(
        "concept-v1",
        {
            "input": Concept("input", "Input", "Practice input"),
            "loops": Concept("loops", "Loops", "Practice bounded loops"),
        },
        {"loops": ("input",)},
    )
    service = AssessmentService(FailClosedRunner(), graph)
    app = create_app(repository, service, TokenManager(b"test-secret"), teacher_registration_code="teacher-code")
    teacher = register_and_login(app, "front-teacher@example.test", "teacher")
    student_a = register_and_login(app, "front-a@example.test", "student")
    student_b = register_and_login(app, "front-b@example.test", "student")
    created = request(app, "POST", "/assignments", headers=headers(teacher), json={
        "title": "Loop safely",
        "description": "Use a bounded loop",
        "requirements": "Read one integer",
        "input_notes": "A positive integer",
        "output_notes": "One integer",
        "examples": ["3 -> 6"],
        "constraints": "1 <= n <= 100",
        "concept_ids": ["loops"],
        "deadline": "2026-12-01T12:00:00+05:30",
        "language": "python",
        "reference_source": "print(6)",
        "tests": [{"id": "hidden", "input": "3", "expected_output": "6", "weight": 1, "concept_ids": ["loops"]}],
    })
    assert created.status_code == 201
    assignment_id = created.json()["id"]
    detail = request(app, "GET", f"/assignments/{assignment_id}", headers=headers(student_a)).json()
    assert detail["concept_ids"] == ["loops"]
    assert detail["deadline"] == "2026-12-01T12:00:00+05:30"
    assert {"reference_source", "tests", "rubric"}.isdisjoint(detail)

    public_graph = request(app, "GET", "/concept-graph", headers=headers(student_a))
    assert public_graph.status_code == 200
    assert public_graph.json()["edges"] == [{"id": "input->loops", "source": "input", "target": "loops", "type": "prerequisite"}]
    assert "source_code" not in public_graph.text and "reference_source" not in public_graph.text and "path" not in public_graph.text

    assert request(app, "PUT", f"/bookmarks/{assignment_id}", headers=headers(student_a)).status_code == 204
    assert request(app, "PUT", f"/bookmarks/{assignment_id}", headers=headers(student_a)).status_code == 204
    assert [item["id"] for item in request(app, "GET", "/bookmarks", headers=headers(student_a)).json()] == [assignment_id]
    assert request(app, "GET", "/bookmarks", headers=headers(student_b)).json() == []

    draft = {"language": "python", "source": "print('draft')"}
    assert request(app, "PUT", f"/assignments/{assignment_id}/draft", headers=headers(student_a), json=draft).status_code == 200
    assert request(app, "GET", f"/assignments/{assignment_id}/draft", headers=headers(student_a)).json()["source"] == draft["source"]
    assert request(app, "GET", f"/assignments/{assignment_id}/draft", headers=headers(student_b)).status_code == 404
    assert request(app, "GET", "/student/activity", headers=headers(student_a)).json()
    assert service.readiness()["runner"] is False
    assert request(app, "DELETE", f"/assignments/{assignment_id}/draft", headers=headers(student_a)).status_code == 204
    assert request(app, "DELETE", f"/bookmarks/{assignment_id}", headers=headers(student_a)).status_code == 204


def test_frontend_support_validation_and_roles(tmp_path):
    app = build_app(tmp_path)
    teacher = register_and_login(app, "meta-teacher@example.test", "teacher")
    student = register_and_login(app, "meta-student@example.test", "student")
    invalid = request(app, "POST", "/assignments", headers=headers(teacher), json={
        "title": "Bad deadline", "language": "python", "reference_source": "pass", "tests": [],
        "deadline": "2026-12-01T12:00:00",
    })
    assert invalid.status_code == 422
    assert request(app, "GET", "/bookmarks", headers=headers(teacher)).status_code == 403
    assert request(app, "GET", "/student/activity", headers=headers(teacher)).status_code == 403
    assert request(app, "GET", "/concept-graph").status_code == 401
    missing = request(app, "PUT", "/bookmarks/999", headers=headers(student))
    assert missing.status_code == 404
