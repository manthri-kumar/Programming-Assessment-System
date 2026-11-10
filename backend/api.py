from __future__ import annotations

import os
import re
import secrets
from copy import deepcopy
from math import isfinite
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Mapping

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError as PydanticValidationError, field_validator, model_validator

from backend.auth import TokenManager, hash_password, verify_password
from backend.knowledge import Concept, ConceptGraph, load_graph
from backend.persistence import RepositoryError, SQLiteRepository
from backend.service import AssessmentService
from backend.worker_config import runner_from_environment
from backend.observability import AuditEvent, AuditLogger, ErrorCode
from backend.scoring import resolve_weights
from backend.rate_limit import RateLimiter
from backend.assignment_import import AssignmentImportService, DraftPatch, ImportError as AssignmentImportError


MAX_REQUEST_BYTES = 8 * 1024 * 1024
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _audience_result(result: dict, role: str) -> dict:
    output = deepcopy(result)
    if role != "teacher" and isinstance(output.get("report"), dict):
        output["report"].pop("teacher_explanation", None)
    return output


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["teacher", "student"]
    teacher_registration_code: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        normalized = value.strip()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("email must contain a local part and dotted domain")
        return normalized

    @model_validator(mode="after")
    def teacher_invitation_required(self):
        if self.role == "teacher" and self.teacher_registration_code is None:
            raise ValueError("teacher_registration_code is required for teacher registration")
        return self


class LoginRequest(BaseModel):
    email: str
    password: str


class RubricRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    policy_version: Literal["core-v1"] = "core-v1"
    weights: dict[str, float] | None = None

    @model_validator(mode="after")
    def valid_weights(self):
        resolve_weights(self.policy_version, self.weights)
        return self


class AssignmentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    language: Literal["python", "c", "java"]
    rubric: RubricRequest = Field(default_factory=RubricRequest)
    reference_source: str = Field(max_length=65536)
    tests: list[dict] = Field(default_factory=list, max_length=50)
    requirements: str = Field(default="", max_length=8000)
    input_notes: str = Field(default="", max_length=4000)
    output_notes: str = Field(default="", max_length=4000)
    examples: list[str] = Field(default_factory=list, max_length=10)
    constraints: str = Field(default="", max_length=4000)
    concept_ids: list[str] = Field(default_factory=list, max_length=50)
    deadline: datetime | None = None

    @field_validator("deadline")
    @classmethod
    def aware_deadline(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("deadline must include a timezone")
        return value

    @field_validator("reference_source")
    @classmethod
    def bounded_reference_source(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reference_source must not be blank")
        if len(value.encode("utf-8")) > 65536:
            raise ValueError("reference_source exceeds 65536 UTF-8 bytes")
        return value

    @model_validator(mode="after")
    def unique_test_ids(self):
        ids = [item.get("id") for item in self.tests]
        if len(ids) != len(set(ids)):
            raise ValueError("test ids must be unique")
        return self


class AssignmentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    language: Literal["python", "c", "java"] | None = None
    rubric: RubricRequest | None = None
    reference_source: str | None = Field(default=None, max_length=65536)
    tests: list[dict] | None = Field(default=None, max_length=50)
    requirements: str | None = Field(default=None, max_length=8000)
    input_notes: str | None = Field(default=None, max_length=4000)
    output_notes: str | None = Field(default=None, max_length=4000)
    examples: list[str] | None = Field(default=None, max_length=10)
    constraints: str | None = Field(default=None, max_length=4000)
    concept_ids: list[str] | None = Field(default=None, max_length=50)
    deadline: datetime | None = None

    @field_validator("deadline")
    @classmethod
    def aware_deadline(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("deadline must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("at least one assignment field is required")
        if self.reference_source is not None and not self.reference_source.strip():
            raise ValueError("reference_source must not be blank")
        if self.reference_source is not None and len(self.reference_source.encode("utf-8")) > 65536:
            raise ValueError("reference_source exceeds 65536 UTF-8 bytes")
        if self.tests is not None:
            ids = [item.get("id") for item in self.tests]
            if len(ids) != len(set(ids)):
                raise ValueError("test ids must be unique")
        return self


class SubmissionRequest(BaseModel):
    assignment_id: int
    language: Literal["python", "c", "java"]
    source: str = Field(max_length=65536)

    @field_validator("source")
    @classmethod
    def bounded_submission_source(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source must not be blank")
        if len(value.encode("utf-8")) > 65536:
            raise ValueError("source exceeds 65536 UTF-8 bytes")
        return value


class DraftRequest(BaseModel):
    language: Literal["python", "c", "java"]
    source: str = Field(max_length=65536)

    @field_validator("source")
    @classmethod
    def bounded_source(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source must not be blank")
        if len(value.encode("utf-8")) > 65536:
            raise ValueError("source exceeds 65536 UTF-8 bytes")
        return value


class AssessmentTestRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    id: str = Field(min_length=1, max_length=128)
    input: str = Field(max_length=65536)
    expected_output: str = Field(max_length=65536)
    weight: float = Field(gt=0)
    concept_ids: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def nonblank_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("test id must not be blank")
        return value

    @field_validator("input", "expected_output")
    @classmethod
    def bounded_utf8(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 65536:
            raise ValueError("value exceeds 65536 UTF-8 bytes")
        return value

    @field_validator("weight")
    @classmethod
    def finite_weight(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("weight must be finite")
        return value


class DirectAssessmentRequest(BaseModel):
    language: Literal["python", "c", "java"]
    source: str
    reference_source: str
    policy_version: Literal["core-v1"] = "core-v1"
    rubric: RubricRequest | None = None
    tests: list[AssessmentTestRequest] = Field(min_length=1, max_length=50)

    @field_validator("source", "reference_source")
    @classmethod
    def bounded_source(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source and reference_source must not be blank")
        if len(value.encode("utf-8")) > 65536:
            raise ValueError("source exceeds 65536 UTF-8 bytes")
        return value

    @model_validator(mode="after")
    def unique_test_ids(self):
        ids = [case.id for case in self.tests]
        if len(ids) != len(set(ids)):
            raise ValueError("test ids must be unique")
        return self


def create_app(
    repository: SQLiteRepository | None = None,
    service: AssessmentService | None = None,
    token_manager: TokenManager | None = None,
    audit_logger: AuditLogger | None = None,
    teacher_registration_code: str | None = None,
    operator_key: str | None = None,
    rate_limits: Mapping[str, int] | None = None,
    assignment_import_service: AssignmentImportService | None = None,
) -> FastAPI:
    repository = repository or SQLiteRepository(os.getenv("ASSESSMENT_DB", "assessment.db"))
    graph_path = Path(__file__).parents[1] / "data" / "concepts" / "concept-v1.json"
    graph = load_graph(graph_path) if graph_path.exists() else ConceptGraph("concept-v1", {"input": Concept("input", "Input", "Practice input handling")}, {})
    token_manager = token_manager or TokenManager(os.getenv("ASSESSMENT_SECRET", secrets.token_hex(32)).encode())
    teacher_registration_code = teacher_registration_code or os.getenv("ASSESSMENT_TEACHER_REGISTRATION_CODE")
    configured_operator_key = operator_key or os.getenv("CODEASSESS_OPERATOR_KEY")
    limiter = RateLimiter(dict(rate_limits or {}))
    audit_logger = audit_logger or AuditLogger()
    service = service or AssessmentService(runner_from_environment(), graph, audit_logger)
    if hasattr(service, "repository") and service.repository is None:
        service.repository = repository
    assignment_import_service = assignment_import_service or AssignmentImportService(repository, graph)
    app = FastAPI(title="Intelligent Programming Assessment API", version="0.3.0")

    @app.middleware("http")
    async def correlation(request: Request, call_next):
        supplied = request.headers.get("x-request-id", "")
        request.state.request_id = supplied if supplied and len(supplied) <= 128 and supplied.isascii() else uuid.uuid4().hex
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                request_limit = max(MAX_REQUEST_BYTES, assignment_import_service.config.max_bytes + 1024 * 1024) if request.url.path == "/assignment-imports" else MAX_REQUEST_BYTES
                if int(content_length) > request_limit:
                    response = JSONResponse(status_code=413, content={"error": {"code": ErrorCode.LIMIT.value, "message": "request body exceeds 8 MiB", "request_id": request.state.request_id}})
                    response.headers["x-request-id"] = request.state.request_id
                    return response
            except ValueError:
                response = JSONResponse(status_code=422, content={"error": {"code": ErrorCode.VALIDATION.value, "message": "invalid content-length", "request_id": request.state.request_id}})
                response.headers["x-request-id"] = request.state.request_id
                return response
        try:
            response = await call_next(request)
        except Exception as exc:
            audit_logger.emit(AuditEvent(request.state.request_id, "internal_error", "failed", details={"exception_type": type(exc).__name__}))
            response = JSONResponse(status_code=500, content={"error": {"code": ErrorCode.INTERNAL.value, "message": "internal server error", "request_id": request.state.request_id}})
        response.headers["x-request-id"] = request.state.request_id
        audit_logger.emit(AuditEvent(request.state.request_id, "http_request", str(response.status_code), details={"method": request.method, "path": request.url.path}))
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [{key: value for key, value in item.items() if key in {"type", "loc", "msg", "input", "url"}} for item in exc.errors()]
        return JSONResponse(status_code=422, content={"error": {"code": ErrorCode.VALIDATION.value, "message": "request validation failed", "request_id": request.state.request_id}, "detail": details})

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        code = {
            401: ErrorCode.AUTHORIZATION,
            403: ErrorCode.AUTHORIZATION,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.CONFLICT,
            410: ErrorCode.NOT_FOUND,
            413: ErrorCode.LIMIT,
            429: ErrorCode.RATE_LIMIT,
            422: ErrorCode.VALIDATION,
            503: ErrorCode.INFRASTRUCTURE,
        }.get(exc.status_code, ErrorCode.INTERNAL)
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": code.value, "message": "request could not be completed", "request_id": request.state.request_id}, "detail": exc.detail}, headers=exc.headers)

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        audit_logger.emit(AuditEvent(request.state.request_id, "internal_error", "failed", details={"exception_type": type(exc).__name__}))
        return JSONResponse(status_code=500, content={"error": {"code": ErrorCode.INTERNAL.value, "message": "internal server error", "request_id": request.state.request_id}})

    async def current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
        try: payload = token_manager.verify(authorization[7:])
        except ValueError: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")
        user = repository.get_user(int(payload["sub"]))
        if not user: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown user")
        return user

    async def teacher(user: dict = Depends(current_user)) -> dict:
        if user["role"] != "teacher": raise HTTPException(status.HTTP_403_FORBIDDEN, "teacher role required")
        return user

    async def student(user: dict = Depends(current_user)) -> dict:
        if user["role"] != "student": raise HTTPException(status.HTTP_403_FORBIDDEN, "student role required")
        return user

    def enforce_rate(bucket: str, identity: str) -> None:
        decision = limiter.check(bucket, identity)
        if not decision.allowed:
            raise HTTPException(429, {"code": "rate_limited", "message": "request rate limit exceeded", "retry_after": decision.retry_after}, headers={"Retry-After": str(decision.retry_after)})

    @app.get("/health")
    async def health() -> dict: return {"status": "ok", "api_version": app.version}

    @app.get("/ready")
    async def ready() -> dict:
        result = service.readiness()
        if not result["ready"]: raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=result)
        return result

    def operator_identity(x_operator_key: Annotated[str | None, Header()] = None) -> dict:
        if not configured_operator_key:
            raise HTTPException(503, "operator identity is not provisioned")
        if not x_operator_key or not secrets.compare_digest(x_operator_key, configured_operator_key):
            raise HTTPException(403, "operator access denied")
        return {"role": "operator", "provisioning": "server-only"}

    @app.get("/operations/status")
    async def operations_status(_: dict = Depends(operator_identity)) -> dict:
        readiness = service.readiness()
        return {
            "status_version": "operations-status-v1",
            "worker": {"ready": bool(readiness["runner"]), "failure_category": None if readiness["runner"] else "worker-unavailable"},
            "graph": {"ready": bool(readiness["graph"]), "version": service.graph.version if readiness["graph"] else None},
            "evaluation_jobs": repository.evaluation_job_summary(),
        }

    @app.post("/assessments")
    async def assess(request: DirectAssessmentRequest, http_request: Request, user: dict = Depends(current_user)) -> dict:
        known_concepts = set(service.graph.concepts) if service.graph else set()
        unknown = sorted({concept for case in request.tests for concept in case.concept_ids} - known_concepts)
        if unknown:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"unknown_concepts": unknown})
        result = service.assess(
            request.language,
            request.source,
            request.reference_source,
            tuple(request.tests),
            request.policy_version,
            http_request.state.request_id,
            request.rubric.weights if request.rubric else None,
        )
        if result["status"] == "incomplete":
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=result)
        return result

    @app.post("/auth/register", status_code=201)
    async def register(request: RegisterRequest, http_request: Request) -> dict:
        enforce_rate("auth", f"register:{http_request.client.host if http_request.client else 'local'}")
        if request.role == "teacher":
            if teacher_registration_code is None:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "teacher registration is not configured")
            supplied = request.teacher_registration_code or ""
            if not secrets.compare_digest(supplied, teacher_registration_code):
                raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid teacher registration code")
        try: user = repository.create_user(request.email, hash_password(request.password), request.role)
        except (RepositoryError, ValueError) as exc: raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
        return {"id": user["id"], "email": user["email"], "role": user["role"]}

    @app.post("/auth/login")
    async def login(request: LoginRequest, http_request: Request) -> dict:
        enforce_rate("auth", f"login:{http_request.client.host if http_request.client else 'local'}")
        user = repository.find_user(request.email)
        if not user or not verify_password(request.password, user["password_hash"]): raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
        return {"access_token": token_manager.issue(user["id"], user["role"]), "token_type": "bearer"}

    @app.get("/auth/me")
    async def me(user: dict = Depends(current_user)) -> dict: return {"id": user["id"], "email": user["email"], "role": user["role"]}

    @app.get("/concept-graph")
    async def concept_graph(user: dict = Depends(current_user)) -> dict:
        active = service.graph or graph
        active.validate()
        return {
            "version": active.version,
            "nodes": [{"id": item.id, "label": item.label, "guidance": item.guidance} for item in sorted(active.concepts.values(), key=lambda value: value.id)],
            "edges": [{"id": f"{parent}->{child}", "source": parent, "target": child, "type": "prerequisite"} for child, parents in sorted(active.requires.items()) for parent in sorted(parents)],
        }

    def import_failure(exc: AssignmentImportError) -> HTTPException:
        return HTTPException(exc.status_code, {"code": exc.code, "message": str(exc)})

    @app.get("/assignment-imports/capabilities")
    async def assignment_import_capabilities(_: dict = Depends(teacher)) -> dict:
        return assignment_import_service.available

    @app.get("/assignment-imports")
    async def list_assignment_imports(user: dict = Depends(teacher)) -> list[dict]:
        assignment_import_service.cleanup_expired()
        return [assignment_import_service.public(item) for item in repository.list_assignment_imports(user["id"])]

    @app.post("/assignment-imports", status_code=201)
    async def create_assignment_import(
        http_request: Request,
        file: UploadFile = File(...),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
        user: dict = Depends(teacher),
    ) -> dict:
        enforce_rate("import", f"teacher:{user['id']}")
        content = await file.read(assignment_import_service.config.max_bytes + 1)
        try:
            return assignment_import_service.create(user["id"], file.filename or "upload", file.content_type or "application/octet-stream", content, idempotency_key)
        except AssignmentImportError as exc:
            audit_logger.emit(AuditEvent(http_request.state.request_id, "assignment_import", exc.code, details={"teacher_id": user["id"], "byte_size": len(content)}))
            raise import_failure(exc) from exc
        finally:
            await file.close()

    @app.get("/assignment-imports/{public_id}")
    async def get_assignment_import(public_id: str, user: dict = Depends(teacher)) -> dict:
        try: return assignment_import_service.public(assignment_import_service._owned(public_id, user["id"]))
        except AssignmentImportError as exc: raise import_failure(exc) from exc

    @app.get("/assignment-imports/{public_id}/preview")
    async def preview_assignment_import(public_id: str, user: dict = Depends(teacher)):
        try: path, media, disposition = assignment_import_service.preview(public_id, user["id"])
        except AssignmentImportError as exc: raise import_failure(exc) from exc
        response = FileResponse(path, media_type=media, filename=path.name, content_disposition_type=disposition)
        response.headers.update({"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'; sandbox"})
        return response

    @app.post("/assignment-imports/{public_id}/extract")
    async def extract_assignment_import(public_id: str, user: dict = Depends(teacher)) -> dict:
        enforce_rate("extraction", f"teacher:{user['id']}")
        try: return assignment_import_service.extract(public_id, user["id"])
        except AssignmentImportError as exc: raise import_failure(exc) from exc

    @app.patch("/assignment-imports/{public_id}/draft")
    async def patch_assignment_import(public_id: str, request: DraftPatch, user: dict = Depends(teacher)) -> dict:
        try: return assignment_import_service.patch(public_id, user["id"], request)
        except AssignmentImportError as exc: raise import_failure(exc) from exc

    @app.delete("/assignment-imports/{public_id}", status_code=204)
    async def delete_assignment_import(public_id: str, user: dict = Depends(teacher)) -> Response:
        try: assignment_import_service.delete(public_id, user["id"])
        except (AssignmentImportError, RepositoryError) as exc:
            if isinstance(exc, AssignmentImportError): raise import_failure(exc) from exc
            raise HTTPException(404, "assignment import not found") from exc
        return Response(status_code=204)

    @app.post("/assignment-imports/{public_id}/confirm", status_code=201)
    async def confirm_assignment_import(public_id: str, request: AssignmentRequest, user: dict = Depends(teacher)) -> dict:
        try:
            assignment_import_service._owned(public_id, user["id"])
            validated_tests = [AssessmentTestRequest.model_validate(item) for item in request.tests]
            known = set(service.graph.concepts if service.graph else ())
            unknown = sorted(({concept for case in validated_tests for concept in case.concept_ids} | set(request.concept_ids)) - known)
            if unknown: raise HTTPException(422, {"unknown_concepts": unknown})
            data = request.model_dump(); data["deadline"] = request.deadline.isoformat() if request.deadline else None
            data["rubric"] = request.rubric.model_dump(exclude_none=True); data["tests"] = [case.model_dump() for case in validated_tests]
            assignment = repository.confirm_assignment_import(public_id, user["id"], data)
            return {key: value for key, value in assignment.items() if key not in {"reference_source", "tests"}}
        except AssignmentImportError as exc: raise import_failure(exc) from exc

    @app.post("/assignments", status_code=201)
    async def create_assignment(request: AssignmentRequest, user: dict = Depends(teacher)) -> dict:
        try:
            validated_tests = [AssessmentTestRequest.model_validate(item) for item in request.tests]
        except PydanticValidationError as exc:
            details = [{key: value for key, value in item.items() if key in {"type", "loc", "msg", "input", "url"}} for item in exc.errors()]
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=details) from exc
        unknown = sorted({concept for case in validated_tests for concept in case.concept_ids} - set(service.graph.concepts if service.graph else ()))
        unknown.extend(sorted(set(request.concept_ids) - set(service.graph.concepts if service.graph else ())))
        unknown = sorted(set(unknown))
        if unknown:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"unknown_concepts": unknown})
        data = request.model_dump()
        data["deadline"] = request.deadline.isoformat() if request.deadline else None
        data["rubric"] = request.rubric.model_dump(exclude_none=True)
        data["tests"] = [case.model_dump() for case in validated_tests]
        assignment = repository.create_assignment(user["id"], data)
        return {key: value for key, value in assignment.items() if key not in {"reference_source", "tests"}}

    @app.get("/assignments")
    async def list_assignments(user: dict = Depends(current_user)) -> list[dict]:
        assignments = repository.list_assignments(user["id"] if user["role"] == "teacher" else None)
        hidden = {"reference_source", "tests"} if user["role"] == "teacher" else {"reference_source", "tests", "rubric"}
        return [{key: value for key, value in assignment.items() if key not in hidden} for assignment in assignments]

    @app.get("/assignments/{assignment_id}")
    async def get_assignment(assignment_id: int, user: dict = Depends(current_user)) -> dict:
        assignment = repository.get_assignment(assignment_id)
        if not assignment: raise HTTPException(404, "assignment not found")
        if user["role"] != "teacher" or assignment["teacher_id"] != user["id"]:
            assignment = {key: value for key, value in assignment.items() if key not in {"reference_source", "tests", "rubric"}}
        return assignment

    @app.patch("/assignments/{assignment_id}")
    async def update_assignment(assignment_id: int, request: AssignmentUpdateRequest, user: dict = Depends(teacher)) -> dict:
        data = request.model_dump(exclude_unset=True)
        if request.deadline is not None:
            data["deadline"] = request.deadline.isoformat()
        if request.rubric is not None:
            data["rubric"] = request.rubric.model_dump(exclude_none=True)
        if request.tests is not None:
            try:
                validated_tests = [AssessmentTestRequest.model_validate(item) for item in request.tests]
            except PydanticValidationError as exc:
                details = [{key: value for key, value in item.items() if key in {"type", "loc", "msg", "input", "url"}} for item in exc.errors()]
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=details) from exc
            unknown = sorted({concept for case in validated_tests for concept in case.concept_ids} - set(service.graph.concepts if service.graph else ()))
            if unknown:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"unknown_concepts": unknown})
            data["tests"] = [case.model_dump() for case in validated_tests]
        if request.concept_ids is not None:
            unknown = sorted(set(request.concept_ids) - set(service.graph.concepts if service.graph else ()))
            if unknown:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"unknown_concepts": unknown})
        try:
            assignment = repository.update_assignment(assignment_id, user["id"], data)
        except RepositoryError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        return assignment

    @app.post("/submissions", status_code=201)
    async def submit(request: SubmissionRequest, user: dict = Depends(current_user)) -> dict:
        if user["role"] != "student": raise HTTPException(403, "student role required")
        enforce_rate("submission", f"{user['role']}:{user['id']}")
        assignment = repository.get_assignment(request.assignment_id)
        if not assignment: raise HTTPException(404, "assignment not found")
        if assignment["language"] != request.language: raise HTTPException(422, "submission language does not match assignment")
        submission = repository.create_submission(request.assignment_id, user["id"], request.language, request.source)
        return {key: value for key, value in submission.items() if key not in {"source", "config_snapshot_json", "config_hash"}}

    @app.post("/submissions/{submission_id}/evaluate")
    async def evaluate(submission_id: int, http_request: Request, user: dict = Depends(current_user)) -> dict:
        enforce_rate("evaluation", f"{user['role']}:{user['id']}")
        submission = repository.get_submission(submission_id)
        if not submission: raise HTTPException(404, "submission not found")
        assignment = repository.get_assignment(submission["assignment_id"])
        if user["role"] == "student" and submission["student_id"] != user["id"]: raise HTTPException(403, "submission access denied")
        if user["role"] == "teacher" and assignment["teacher_id"] != user["id"]: raise HTTPException(403, "submission access denied")
        configuration = repository.get_submission_configuration(submission_id)
        if not configuration:
            raise HTTPException(409, "immutable assessment configuration unavailable")
        snapshot = configuration["snapshot"]
        job = repository.create_evaluation_job(submission_id, configuration["hash"])
        existing_evaluation = repository.get_evaluation(submission_id)
        if existing_evaluation and existing_evaluation["result"].get("status") != "incomplete":
            if job["state"] != "completed":
                claimed = repository.claim_evaluation_job(job["job_id"], http_request.state.request_id)
                if claimed:
                    repository.complete_evaluation_job(job["job_id"], existing_evaluation["result"].get("assessment_record_id"))
            return _audience_result(existing_evaluation["result"], user["role"])
        claimed = repository.claim_evaluation_job(job["job_id"], http_request.state.request_id)
        if not claimed:
            if existing_evaluation and job["state"] == "failed" and job["attempts"] >= job["max_attempts"]:
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=_audience_result(existing_evaluation["result"], user["role"]))
            raise HTTPException(409, "evaluation is already running, completed, or cancelled")
        rubric = snapshot["rubric"]
        result = service.assess(
            submission["language"],
            submission["source"],
            snapshot["reference_source"],
            tuple(snapshot["tests"]),
            rubric.get("policy_version", "core-v1"),
            http_request.state.request_id,
            rubric.get("weights"),
        )
        result["evaluation_job_id"] = job["job_id"]
        current_job = repository.get_evaluation_job(job["job_id"])
        if current_job and current_job["state"] == "cancelled":
            raise HTTPException(409, "evaluation was cancelled")
        repository.save_evaluation(submission_id, result["policy_version"], result)
        if result["status"] == "incomplete":
            repository.fail_evaluation_job(job["job_id"], "worker-unavailable", retryable=True)
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=_audience_result(result, user["role"]))
        repository.complete_evaluation_job(job["job_id"], result.get("assessment_record_id"))
        return _audience_result(result, user["role"])

    @app.get("/submissions/{submission_id}/evaluation")
    async def evaluation(submission_id: int, user: dict = Depends(current_user)) -> dict:
        submission = repository.get_submission(submission_id)
        if not submission: raise HTTPException(404, "submission not found")
        assignment = repository.get_assignment(submission["assignment_id"])
        if user["role"] == "student" and submission["student_id"] != user["id"]: raise HTTPException(403, "submission access denied")
        if user["role"] == "teacher" and assignment["teacher_id"] != user["id"]: raise HTTPException(403, "submission access denied")
        result = repository.get_evaluation(submission_id)
        if not result: raise HTTPException(404, "evaluation not found")
        result["result"] = _audience_result(result["result"], user["role"])
        return result

    def authorized_job(submission_id: int, user: dict) -> tuple[dict, dict]:
        submission = repository.get_submission(submission_id)
        if not submission:
            raise HTTPException(404, "submission not found")
        assignment = repository.get_assignment(submission["assignment_id"])
        if user["role"] == "student" and submission["student_id"] != user["id"]:
            raise HTTPException(403, "submission access denied")
        if user["role"] == "teacher" and assignment["teacher_id"] != user["id"]:
            raise HTTPException(403, "submission access denied")
        configuration = repository.get_submission_configuration(submission_id)
        if not configuration:
            raise HTTPException(409, "immutable assessment configuration unavailable")
        job = repository.create_evaluation_job(submission_id, configuration["hash"])
        return submission, job

    @app.get("/submissions/{submission_id}/evaluation-job")
    async def evaluation_job(submission_id: int, user: dict = Depends(current_user)) -> dict:
        _, job = authorized_job(submission_id, user)
        allowed = {"job_id", "state", "attempts", "max_attempts", "failure_category", "created_at", "updated_at"}
        return {key: value for key, value in job.items() if key in allowed}

    @app.post("/submissions/{submission_id}/evaluation-job/cancel")
    async def cancel_evaluation_job(submission_id: int, user: dict = Depends(current_user)) -> dict:
        _, job = authorized_job(submission_id, user)
        try:
            cancelled = repository.cancel_evaluation_job(job["job_id"])
        except RepositoryError as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"job_id": cancelled["job_id"], "state": cancelled["state"]}

    @app.get("/submissions")
    async def list_submissions(
        assignment_id: int | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
        user: dict = Depends(current_user),
    ) -> list[dict]:
        if user["role"] == "student":
            rows = repository.list_submissions(student_id=user["id"], assignment_id=assignment_id, limit=limit, offset=offset)
        else:
            rows = repository.list_submissions(teacher_id=user["id"], assignment_id=assignment_id, limit=limit, offset=offset)
        return [{key: value for key, value in row.items() if key not in {"source", "config_snapshot_json", "config_hash"}} for row in rows]

    @app.get("/submissions/{submission_id}")
    async def get_submission(submission_id: int, user: dict = Depends(current_user)) -> dict:
        submission = repository.get_submission(submission_id)
        if not submission:
            raise HTTPException(404, "submission not found")
        assignment = repository.get_assignment(submission["assignment_id"])
        if user["role"] == "student" and submission["student_id"] != user["id"]:
            raise HTTPException(403, "submission access denied")
        if user["role"] == "teacher" and assignment["teacher_id"] != user["id"]:
            raise HTTPException(403, "submission access denied")
        return {key: value for key, value in submission.items() if key not in {"config_snapshot_json", "config_hash"}}

    @app.get("/teacher/analytics")
    async def teacher_analytics(user: dict = Depends(teacher)) -> dict:
        return repository.teacher_analytics(user["id"])

    @app.get("/student/progress")
    async def student_progress(user: dict = Depends(current_user)) -> dict:
        if user["role"] != "student":
            raise HTTPException(403, "student role required")
        return repository.student_progress(user["id"])

    @app.get("/bookmarks")
    async def bookmarks(limit: Annotated[int, Query(ge=1, le=100)] = 50, offset: Annotated[int, Query(ge=0)] = 0, user: dict = Depends(student)) -> list[dict]:
        return [{key: value for key, value in item.items() if key not in {"reference_source", "tests", "rubric"}} for item in repository.list_bookmarks(user["id"], limit, offset)]

    @app.put("/bookmarks/{assignment_id}", status_code=204, response_class=Response)
    async def add_bookmark(assignment_id: int, user: dict = Depends(student)) -> Response:
        try: repository.add_bookmark(user["id"], assignment_id)
        except RepositoryError as exc: raise HTTPException(404, str(exc)) from exc
        return Response(status_code=204)

    @app.delete("/bookmarks/{assignment_id}", status_code=204, response_class=Response)
    async def delete_bookmark(assignment_id: int, user: dict = Depends(student)) -> Response:
        repository.remove_bookmark(user["id"], assignment_id)
        return Response(status_code=204)

    @app.get("/assignments/{assignment_id}/draft")
    async def get_draft(assignment_id: int, user: dict = Depends(student)) -> dict:
        draft = repository.get_draft(user["id"], assignment_id)
        if not draft: raise HTTPException(404, "draft not found")
        return draft

    @app.put("/assignments/{assignment_id}/draft")
    async def save_draft(assignment_id: int, request: DraftRequest, user: dict = Depends(student)) -> dict:
        try: return repository.save_draft(user["id"], assignment_id, request.language, request.source)
        except RepositoryError as exc: raise HTTPException(422 if "language" in str(exc) else 404, str(exc)) from exc

    @app.delete("/assignments/{assignment_id}/draft", status_code=204, response_class=Response)
    async def delete_draft(assignment_id: int, user: dict = Depends(student)) -> Response:
        repository.delete_draft(user["id"], assignment_id)
        return Response(status_code=204)

    @app.get("/student/activity")
    async def activity(limit: Annotated[int, Query(ge=1, le=100)] = 20, offset: Annotated[int, Query(ge=0)] = 0, user: dict = Depends(student)) -> list[dict]:
        return repository.list_activity(user["id"], limit, offset)

    return app


app = create_app()
