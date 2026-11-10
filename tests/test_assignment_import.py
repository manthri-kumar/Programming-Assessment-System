from __future__ import annotations

import asyncio
import io
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from PIL import Image
from pydantic import ValidationError
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from backend.api import create_app
from backend.assignment_import import AssignmentImportService, CandidateTest, DraftField, DraftPatch, ExtractionSegment, ImportConfig, ImportDraft, ImportError, TesseractProvider
from backend.auth import TokenManager
from backend.knowledge import Concept, ConceptGraph
from backend.persistence import SQLiteRepository
from backend.runner import FailClosedRunner
from backend.service import AssessmentService


def png() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (80, 40), "white").save(output, "PNG")
    return output.getvalue()


def image_bytes(format_name: str, size: tuple[int, int] = (80, 40)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, "white").save(output, format_name)
    return output.getvalue()


def text_pdf(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=200)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    stream = DecodedStreamObject(); stream.set_data(f"BT /F1 12 Tf 20 160 Td ({text}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO(); writer.write(output); return output.getvalue()


def pdf_bytes(*, pages: int = 1, encrypted: bool = False, active: bool = False) -> bytes:
    writer = PdfWriter()
    for _ in range(pages): writer.add_blank_page(width=300, height=200)
    if encrypted: writer.encrypt("test-password")
    if active: writer._root_object[NameObject("/OpenAction")] = DictionaryObject()
    output = io.BytesIO(); writer.write(output); return output.getvalue()


def mixed_pdf() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=200)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    stream = DecodedStreamObject(); stream.set_data(b"BT /F1 12 Tf 20 160 Td (Title Embedded) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    writer.add_blank_page(width=300, height=200)
    output = io.BytesIO(); writer.write(output); return output.getvalue()


class FakeOcr:
    name, version, executable = "deterministic-test-ocr", "test-v1", True
    def extract(self, path: Path):
        return [ExtractionSegment(page=1, method="ocr", text="Array Sum\nDescription: Add values\nLanguage: Python 3.11\nConcepts: Arrays", confidence=.9)]


class PageTwoOcr:
    name, version, executable = "deterministic-test-ocr", "test-v1", True
    def extract(self, path: Path):
        return [ExtractionSegment(page=2, method="ocr", text="Description: OCR page\nLanguage: Python", confidence=.8)]


def setup(tmp_path: Path, *, ocr=None):
    repository = SQLiteRepository(tmp_path / "test.db")
    graph = ConceptGraph("concept-v1", {"arrays": Concept("arrays", "Arrays", "Practice arrays")}, {})
    config = ImportConfig(True, tmp_path / "private", max_bytes=1024 * 1024, max_pages=3, max_dimension=1000, max_pixels=1_000_000, retention_hours=1)
    imports = AssignmentImportService(repository, graph, config, ocr=ocr)
    app = create_app(repository, AssessmentService(FailClosedRunner(), graph), TokenManager(b"test-secret"), teacher_registration_code="teacher-code", assignment_import_service=imports)
    return repository, imports, app


def request(app, method: str, path: str, **kwargs):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(run())


def token(app, email: str, role: str) -> str:
    body = {"email": email, "password": "password123", "role": role}
    if role == "teacher": body["teacher_registration_code"] = "teacher-code"
    assert request(app, "POST", "/auth/register", json=body).status_code == 201
    return request(app, "POST", "/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]


def auth(value: str) -> dict[str, str]: return {"Authorization": f"Bearer {value}"}


def test_models_are_bounded_and_forbid_unknown_fields():
    with pytest.raises(ValidationError): DraftField(value="x", origin="extracted", confidence=1.1)
    with pytest.raises(ValidationError): ExtractionSegment(page=0, method="ocr", text="x")
    with pytest.raises(ValidationError): ImportDraft(fields={"invented": DraftField()}, config_hash="a" * 64)
    with pytest.raises(ValidationError): CandidateTest(id="x", input="", expected_output="", origin="invented")
    with pytest.raises(ValidationError): DraftPatch(fields={"title": "x" * 140_000})


def test_configuration_and_storage_paths_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEASSESS_IMPORT_ROOT", str(tmp_path / "outside"))
    with pytest.raises(ValueError, match="project data directory"): ImportConfig.from_environment()
    safe = tmp_path / "safe"; safe.mkdir()
    repository, service, _ = setup(safe)
    with pytest.raises(ImportError): service._path("../escape.png")


def test_image_validation_deterministic_ocr_and_canonical_concepts(tmp_path):
    repository, service, _ = setup(tmp_path, ocr=FakeOcr())
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    created = service.create(teacher["id"], "question.png", "image/png", png(), "image-key-1")
    assert created["metadata"] == {"width": 80, "height": 40, "orientation": 1, "pages": 1, "text_pages": [], "ocr_pages": [1]}
    extracted = service.extract(created["public_id"], teacher["id"])
    assert extracted["state"] == "review-ready"
    assert extracted["draft"]["fields"]["title"]["value"] == "Array Sum"
    assert extracted["draft"]["fields"]["language"]["value"] == "python"
    assert extracted["draft"]["fields"]["concept_ids"]["value"] == ["arrays"]
    assert extracted["draft"]["fields"]["deadline"]["origin"] == "missing"
    assert service.extract(created["public_id"], teacher["id"])["draft"] == extracted["draft"]


def test_pdf_embedded_text_is_used_without_ocr(tmp_path):
    repository, service, _ = setup(tmp_path)
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    created = service.create(teacher["id"], "question.pdf", "application/pdf", text_pdf("Array Sum Description: Add values Language: Python"))
    extracted = service.extract(created["public_id"], teacher["id"])
    assert extracted["extraction"]["provider"] == "embedded-pdf-text"
    assert extracted["extraction"]["segments"][0]["method"] == "embedded-text"


@pytest.mark.parametrize(("name", "media", "format_name"), [
    ("question.jpg", "image/jpeg", "JPEG"),
    ("question.webp", "image/webp", "WEBP"),
])
def test_jpeg_and_webp_are_safely_decoded(tmp_path, name, media, format_name):
    repository, service, _ = setup(tmp_path, ocr=FakeOcr())
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    created = service.create(teacher["id"], name, media, image_bytes(format_name))
    assert created["media_type"] == media
    assert created["metadata"]["width"] == 80
    assert service.extract(created["public_id"], teacher["id"])["state"] == "review-ready"


def test_image_pixel_bomb_and_truncated_image_fail_closed(tmp_path):
    repository, service, _ = setup(tmp_path)
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    service.config = replace(service.config, max_pixels=2_000, max_dimension=1_000)
    with pytest.raises(ImportError) as bomb:
        service.create(teacher["id"], "large.png", "image/png", image_bytes("PNG", (80, 40)))
    assert bomb.value.code == "image_dimensions_exceeded" and bomb.value.status_code == 413
    with pytest.raises(ImportError) as truncated:
        service.create(teacher["id"], "broken.png", "image/png", png()[:40])
    assert truncated.value.code == "malformed_image"
    assert not list(service.config.root.glob("*.tmp"))


@pytest.mark.parametrize(("body", "code"), [
    (pdf_bytes(encrypted=True), "encrypted_pdf"),
    (pdf_bytes(active=True), "active_pdf"),
    (b"%PDF-1.7\nmalformed", "malformed_pdf"),
    (pdf_bytes(pages=4), "page_limit_exceeded"),
])
def test_pdf_rejects_encrypted_active_malformed_and_excessive_pages(tmp_path, body, code):
    repository, service, _ = setup(tmp_path)
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    with pytest.raises(ImportError) as error:
        service.create(teacher["id"], "question.pdf", "application/pdf", body)
    assert error.value.code == code
    assert not list(service.config.root.glob("*.tmp"))


def test_mixed_pdf_uses_embedded_text_and_ocr_only_for_missing_page(tmp_path):
    repository, service, _ = setup(tmp_path, ocr=PageTwoOcr())
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    created = service.create(teacher["id"], "question.pdf", "application/pdf", mixed_pdf())
    assert created["metadata"]["text_pages"] == [1]
    assert created["metadata"]["ocr_pages"] == [2]
    extracted = service.extract(created["public_id"], teacher["id"])
    assert [(segment["page"], segment["method"]) for segment in extracted["extraction"]["segments"]] == [(1, "embedded-text"), (2, "ocr")]


@pytest.mark.parametrize("name,media,body,code", [
    ("fake.png", "image/png", b"not a png", "invalid_file_type"),
    ("fake.jpg", "image/png", png(), "invalid_file_type"),
])
def test_spoofed_or_malformed_files_are_rejected_and_not_persisted(tmp_path, name, media, body, code):
    repository, service, _ = setup(tmp_path)
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    with pytest.raises(ImportError) as error: service.create(teacher["id"], name, media, body)
    assert error.value.code == code
    assert not list(service.config.root.glob("*"))


def test_teacher_only_api_review_confirmation_and_student_redaction(tmp_path):
    repository, _, app = setup(tmp_path, ocr=FakeOcr())
    teacher = token(app, "teacher@example.test", "teacher"); other = token(app, "other@example.test", "teacher"); student = token(app, "student@example.test", "student")
    files = {"file": ("question.png", png(), "image/png")}
    assert request(app, "POST", "/assignment-imports", files=files, headers=auth(student)).status_code == 403
    created = request(app, "POST", "/assignment-imports", files=files, headers={**auth(teacher), "Idempotency-Key": "request-123"})
    assert created.status_code == 201
    public_id = created.json()["public_id"]
    replay = request(app, "POST", "/assignment-imports", files=files, headers={**auth(teacher), "Idempotency-Key": "request-123"})
    assert replay.json()["public_id"] == public_id
    assert request(app, "GET", f"/assignment-imports/{public_id}", headers=auth(other)).status_code == 404
    extracted = request(app, "POST", f"/assignment-imports/{public_id}/extract", headers=auth(teacher))
    assert extracted.status_code == 200
    payload = {"title":"Imported Array Sum","description":"Add","language":"python","reference_source":"print(sum(map(int,input().split())))","tests":[{"id":"case-1","input":"1 2","expected_output":"3","weight":1,"concept_ids":["arrays"]}],"rubric":{"policy_version":"core-v1"},"requirements":"","input_notes":"","output_notes":"","examples":[],"constraints":"","concept_ids":["arrays"],"deadline":None}
    confirmed = request(app, "POST", f"/assignment-imports/{public_id}/confirm", headers=auth(teacher), json=payload)
    assert confirmed.status_code == 201
    assignment_id = confirmed.json()["id"]
    assert request(app, "POST", f"/assignment-imports/{public_id}/confirm", headers=auth(teacher), json=payload).json()["id"] == assignment_id
    student_view = request(app, "GET", f"/assignments/{assignment_id}", headers=auth(student)).json()
    assert "reference_source" not in student_view and "tests" not in student_view
    assert not ({"public_id", "content_hash", "extraction", "draft", "config_hash", "storage_key"} & set(student_view))
    assert repository.schema_version() == 7


def test_unconfigured_ocr_fails_closed_without_host_fallback(tmp_path):
    repository, service, _ = setup(tmp_path)
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    created = service.create(teacher["id"], "question.png", "image/png", png())
    with pytest.raises(ImportError) as error: service.extract(created["public_id"], teacher["id"])
    assert error.value.code == "ocr_unavailable"
    assert repository.get_assignment_import(created["public_id"], teacher["id"])["state"] == "extraction-unavailable"


@pytest.mark.parametrize(("effect", "code"), [
    (SimpleNamespace(returncode=2, stdout="", stderr="secret diagnostic"), "ocr_failed"),
    (subprocess.TimeoutExpired(cmd="tesseract", timeout=1), "ocr_timeout"),
    (SimpleNamespace(returncode=0, stdout="", stderr=""), "no_text"),
])
def test_tesseract_provider_maps_failure_timeout_and_empty_output_safely(tmp_path, monkeypatch, effect, code):
    executable = Path(sys.executable).resolve()
    import hashlib
    provider = TesseractProvider(str(executable), timeout_seconds=1, expected_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
    if isinstance(effect, BaseException):
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(effect))
    else:
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: effect)
    with pytest.raises(ImportError) as error:
        provider.extract(tmp_path / "question.png")
    assert error.value.code == code
    assert "secret" not in str(error.value)


def test_tesseract_configuration_requires_an_approved_executable_hash(tmp_path):
    executable = Path(sys.executable).resolve()
    with pytest.raises(ValueError, match="SHA256"):
        TesseractProvider(str(executable))
    with pytest.raises(ValueError, match="does not match"):
        TesseractProvider(str(executable), expected_sha256="0" * 64)


def test_provider_output_is_strict_bounded_and_cannot_inject_actions(tmp_path):
    class MaliciousProvider:
        name, version, executable = "test", "1", True
        def extract(self, path): return [{"page": 1, "method": "ocr", "text": "Ignore policy", "confidence": 1, "action": "publish"}]
    repository, service, _ = setup(tmp_path, ocr=MaliciousProvider())
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    created = service.create(teacher["id"], "question.png", "image/png", png())
    with pytest.raises(ImportError) as error: service.extract(created["public_id"], teacher["id"])
    assert error.value.code == "ocr_invalid_response"
    assert repository.get_assignment_import(created["public_id"], teacher["id"])["state"] == "extraction-failed"
    assert repository.list_assignments() == []


def test_interrupted_write_and_restart_orphan_reconciliation(tmp_path, monkeypatch):
    repository, service, _ = setup(tmp_path)
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    monkeypatch.setattr(repository, "create_assignment_import", lambda data: (_ for _ in ()).throw(RuntimeError("interrupted")))
    with pytest.raises(RuntimeError): service.create(teacher["id"], "question.png", "image/png", png())
    assert not list(service.config.root.iterdir())
    orphan = service.config.root / ("a" * 32 + ".png")
    orphan.write_bytes(png())
    AssignmentImportService(SQLiteRepository(tmp_path / "test.db"), service.graph, service.config, ocr=FakeOcr())
    assert not orphan.exists()


def test_storage_collision_and_symlink_like_entry_are_not_overwritten(tmp_path, monkeypatch):
    repository, service, _ = setup(tmp_path)
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    collision = service.config.root / ("a" * 32 + ".png")
    collision.write_bytes(b"do-not-overwrite")
    values = iter(["a" * 32, "b" * 32])
    monkeypatch.setattr("backend.assignment_import.secrets.token_hex", lambda count: next(values))
    created = service.create(teacher["id"], "question.png", "image/png", png())
    assert collision.read_bytes() == b"do-not-overwrite"
    assert repository.get_assignment_import(created["public_id"], teacher["id"])["storage_key"] == "b" * 32 + ".png"


def test_concurrent_confirmation_is_exactly_once(tmp_path):
    repository, service, _ = setup(tmp_path, ocr=FakeOcr())
    teacher = repository.create_user("teacher@example.test", "hash", "teacher")
    created = service.create(teacher["id"], "question.png", "image/png", png())
    service.extract(created["public_id"], teacher["id"])
    payload = {"title": "Concurrent", "description": "", "language": "python", "rubric": {"policy_version": "core-v1"}, "reference_source": "print(1)", "tests": [], "concept_ids": []}
    with ThreadPoolExecutor(max_workers=8) as pool:
        assignments = list(pool.map(lambda _: repository.confirm_assignment_import(created["public_id"], teacher["id"], payload), range(20)))
    assert len({item["id"] for item in assignments}) == 1
    assert len(repository.list_assignments()) == 1
    events = repository.assignment_import_events(created["public_id"], teacher["id"])
    assert [item["event"] for item in events].count("confirmed") == 1


def test_idempotency_conflict_preview_headers_rate_limit_and_cleanup(tmp_path):
    repository, service, app = setup(tmp_path, ocr=FakeOcr())
    teacher = token(app, "teacher@example.test", "teacher")
    files = {"file": ("question.png", png(), "image/png")}
    created = request(app, "POST", "/assignment-imports", files=files, headers={**auth(teacher), "Idempotency-Key": "stable-key"})
    public_id = created.json()["public_id"]
    conflict = request(app, "POST", "/assignment-imports", files={"file": ("different.png", png()+b"x", "image/png")}, headers={**auth(teacher), "Idempotency-Key": "stable-key"})
    assert conflict.status_code == 409
    preview = request(app, "GET", f"/assignment-imports/{public_id}/preview", headers=auth(teacher))
    assert preview.status_code == 200 and preview.headers["cache-control"] == "no-store" and preview.headers["x-content-type-options"] == "nosniff"
    stored = repository.get_assignment_import(public_id, 1); assert stored is not None
    path = service._path(stored["storage_key"]); assert path.exists()
    assert request(app, "DELETE", f"/assignment-imports/{public_id}", headers=auth(teacher)).status_code == 204
    assert not path.exists()


def test_rate_limit_and_startup_expiry_cleanup(tmp_path):
    repository, service, _ = setup(tmp_path, ocr=FakeOcr())
    app = create_app(repository, AssessmentService(FailClosedRunner(), service.graph), TokenManager(b"rate-secret"), teacher_registration_code="teacher-code", assignment_import_service=service, rate_limits={"import": 1})
    teacher = token(app, "teacher@example.test", "teacher")
    first = request(app, "POST", "/assignment-imports", files={"file": ("one.png", png(), "image/png")}, headers=auth(teacher))
    assert first.status_code == 201
    second = request(app, "POST", "/assignment-imports", files={"file": ("two.png", png(), "image/png")}, headers=auth(teacher))
    assert second.status_code == 429 and int(second.headers["retry-after"]) >= 1
    item = repository.get_assignment_import(first.json()["public_id"], 1); assert item is not None
    path = service._path(item["storage_key"])
    with repository.transaction() as db: db.execute("UPDATE assignment_imports SET expires_at='2000-01-01T00:00:00+00:00' WHERE public_id=?", (item["public_id"],))
    AssignmentImportService(repository, service.graph, service.config, ocr=FakeOcr())
    assert not path.exists() and repository.get_assignment_import(item["public_id"], 1) is None


def test_imported_assignment_runs_both_real_agents_and_persists_report_v3_fail_closed(tmp_path):
    repository, _, app = setup(tmp_path, ocr=FakeOcr())
    teacher = token(app, "teacher@example.test", "teacher"); student = token(app, "student@example.test", "student")
    created = request(app, "POST", "/assignment-imports", files={"file": ("question.png", png(), "image/png")}, headers=auth(teacher)).json()
    assert request(app, "POST", f"/assignment-imports/{created['public_id']}/extract", headers=auth(teacher)).status_code == 200
    assignment = request(app, "POST", f"/assignment-imports/{created['public_id']}/confirm", headers=auth(teacher), json={"title":"Array Sum","description":"Add","language":"python","reference_source":"values=list(map(int,input().split()))\nprint(sum(values))","tests":[{"id":"case-1","input":"1 2","expected_output":"3","weight":1,"concept_ids":["arrays"]}],"rubric":{"policy_version":"core-v1"},"concept_ids":["arrays"]}).json()
    submission = request(app, "POST", "/submissions", headers=auth(student), json={"assignment_id":assignment["id"],"language":"python","source":"values=list(map(int,input().split()))\nprint(sum(values))"}).json()
    unavailable = request(app, "POST", f"/submissions/{submission['id']}/evaluate", headers=auth(student))
    assert unavailable.status_code == 503
    result = request(app, "GET", f"/submissions/{submission['id']}/evaluation", headers=auth(student)).json()["result"]
    assert result["agent_trace"] == ["implementation-evaluation", "feedback"]
    assert result["report"]["report_version"] == "assessment-report-v3"
    assert result["status"] == "incomplete" and result["total"] is None
    assert any("execution" in value.lower() for value in result["limitations"])
    assert "teacher_explanation" not in result["report"]
    teacher_result = request(app, "GET", f"/submissions/{submission['id']}/evaluation", headers=auth(teacher)).json()["result"]
    assert "teacher_explanation" in teacher_result["report"]
    assert request(app, "GET", "/teacher/analytics", headers=auth(teacher)).json()["evaluated_count"] == 1
