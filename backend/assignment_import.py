from __future__ import annotations

import hashlib
import io
import json
import os
import re
import secrets
import subprocess
import stat
import tempfile
import threading
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Protocol

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from pypdf import PdfReader

from backend.knowledge import ConceptGraph
from backend.persistence import RepositoryError, SQLiteRepository
from backend.scoring import resolve_weights


SUPPORTED_MEDIA = {
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/webp": (".webp", b"RIFF"),
    "application/pdf": (".pdf", b"%PDF-"),
}
MAX_TEXT = 64_000


class ImportError(ValueError):
    def __init__(self, code: str, message: str, status_code: int = 422):
        super().__init__(message)
        self.code, self.status_code = code, status_code


class SourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(ge=1, le=100)
    text: str = Field(default="", max_length=1000)


class DraftField(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str | list[str] | dict | list[dict] | None = None
    origin: Literal["missing", "extracted", "provider-suggested", "teacher-confirmed"] = "missing"
    confidence: float | None = Field(default=None, ge=0, le=1)
    sources: list[SourceRef] = Field(default_factory=list, max_length=20)
    warnings: list[str] = Field(default_factory=list, max_length=20)
    verification: Literal["unverified", "source-provided", "teacher-confirmed", "worker-verified"] = "unverified"


class CandidateTest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=128)
    input: str = Field(max_length=65536)
    expected_output: str = Field(max_length=65536)
    origin: Literal["extracted", "provider-generated"]
    verification: Literal["unverified", "teacher-confirmed", "worker-verified"] = "unverified"
    sources: list[SourceRef] = Field(default_factory=list, max_length=20)


class ExtractionSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(ge=1, le=100)
    method: Literal["embedded-text", "ocr"]
    text: str = Field(max_length=MAX_TEXT)
    confidence: float | None = Field(default=None, ge=0, le=1)


class ImportDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["assignment-import-draft-v1"] = "assignment-import-draft-v1"
    fields: dict[str, DraftField]
    unresolved_concepts: list[str] = Field(default_factory=list, max_length=50)
    candidate_tests: list[CandidateTest] = Field(default_factory=list, max_length=50)
    history: list[dict] = Field(default_factory=list, max_length=200)
    config_hash: str = Field(min_length=64, max_length=64)

    @field_validator("fields")
    @classmethod
    def bounded_fields(cls, value: dict[str, DraftField]) -> dict[str, DraftField]:
        allowed = {"title", "description", "requirements", "language", "input_notes", "output_notes", "constraints", "examples", "concept_ids", "reference_source", "tests", "rubric", "deadline"}
        if set(value) - allowed:
            raise ValueError("unknown draft field")
        return value


class DraftPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fields: dict[str, object] = Field(default_factory=dict, max_length=20)
    rejected_fields: list[str] = Field(default_factory=list, max_length=20)
    confirmed_candidate_ids: list[str] = Field(default_factory=list, max_length=50)
    rejected_candidate_ids: list[str] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def bounded_payload(self):
        if len(json.dumps(self.model_dump(), default=str).encode()) > 128 * 1024:
            raise ValueError("draft patch exceeds 131072 bytes")
        return self


class OcrProvider(Protocol):
    name: str
    version: str
    def extract(self, path: Path) -> list[ExtractionSegment]: ...


class TesseractProvider:
    name = "local-tesseract"
    version = "adapter-v1"

    def __init__(self, executable: str | None, timeout_seconds: int = 30, expected_sha256: str | None = None):
        if executable and not Path(executable).is_absolute():
            raise ValueError("CODEASSESS_TESSERACT_PATH must be an existing absolute file")
        self.executable = Path(executable).resolve() if executable else None
        self.timeout_seconds = timeout_seconds
        if self.executable and (not self.executable.is_absolute() or not self.executable.is_file()):
            raise ValueError("CODEASSESS_TESSERACT_PATH must be an existing absolute file")
        if self.executable:
            if not expected_sha256 or not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
                raise ValueError("CODEASSESS_TESSERACT_SHA256 must pin the approved executable")
            observed = hashlib.sha256(self.executable.read_bytes()).hexdigest()
            if not secrets.compare_digest(observed, expected_sha256.lower()):
                raise ValueError("configured Tesseract executable does not match its approved SHA-256")

    @staticmethod
    def _capture(command: list[str], timeout: int) -> subprocess.CompletedProcess:
        """Bound both OCR streams as they arrive; never interpret document text."""
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        streams = {"stdout": bytearray(), "stderr": bytearray()}
        exceeded = threading.Event()
        failed = threading.Event()

        def drain(name: str, pipe) -> None:
            try:
                while chunk := pipe.read(8192):
                    room = MAX_TEXT - len(streams[name])
                    streams[name].extend(chunk[:max(0, room)])
                    if len(chunk) > room:
                        exceeded.set()
                        try:
                            process.kill()
                        except OSError:
                            pass
                        break
            except (OSError, ValueError):
                failed.set()

        readers = [threading.Thread(target=drain, args=(name, getattr(process, name)), daemon=True) for name in streams]
        try:
            for reader in readers:
                reader.start()
            process.wait(timeout=timeout)
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
            for reader in readers:
                reader.join(timeout=1)
            if all(not reader.is_alive() for reader in readers):
                process.stdout.close()
                process.stderr.close()
        if exceeded.is_set():
            raise ImportError("ocr_output_exceeded", "Local OCR output exceeded configured limits", 503)
        if failed.is_set() or any(reader.is_alive() for reader in readers):
            raise ImportError("ocr_failed", "Local OCR failed", 503)
        return subprocess.CompletedProcess(command, process.returncode, bytes(streams["stdout"]).decode("utf-8", errors="replace"), "")

    def extract(self, path: Path) -> list[ExtractionSegment]:
        if not self.executable:
            raise ImportError("ocr_unavailable", "Local OCR is not configured", 503)
        if path.suffix.lower() == ".pdf":
            raise ImportError("ocr_pdf_rendering_unavailable", "Local PDF OCR rendering is not configured", 503)
        try:
            result = self._capture([str(self.executable), str(path), "stdout", "-l", "eng", "--psm", "6"], self.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            raise ImportError("ocr_timeout", "Local OCR timed out", 503) from exc
        except OSError as exc:
            raise ImportError("ocr_failed", "Local OCR could not be started", 503) from exc
        if result.returncode != 0:
            raise ImportError("ocr_failed", "Local OCR failed", 503)
        text = result.stdout[:MAX_TEXT].strip()
        if not text:
            raise ImportError("no_text", "No text could be extracted")
        return [ExtractionSegment(page=1, method="ocr", text=text, confidence=None)]


@dataclass(frozen=True)
class ImportConfig:
    enabled: bool
    root: Path
    max_bytes: int = 10 * 1024 * 1024
    max_pages: int = 20
    max_dimension: int = 12_000
    max_pixels: int = 40_000_000
    retention_hours: int = 72
    audit_retention_days: int = 30
    timeout_seconds: int = 30
    ocr_concurrency: int = 2

    @classmethod
    def from_environment(cls) -> "ImportConfig":
        project = Path(__file__).parents[1].resolve()
        data_root = (project / "data").resolve()
        configured = Path(os.getenv("CODEASSESS_IMPORT_ROOT", str(data_root / "private-imports")))
        root = configured.resolve()
        if root != data_root and data_root not in root.parents:
            raise ValueError("CODEASSESS_IMPORT_ROOT must be inside the project data directory")
        def bounded(name: str, default: int, low: int, high: int) -> int:
            value = int(os.getenv(name, str(default)))
            if not low <= value <= high: raise ValueError(f"{name} is outside safe limits")
            return value
        return cls(
            enabled=os.getenv("CODEASSESS_IMPORT_ENABLED", "1") == "1", root=root,
            max_bytes=bounded("CODEASSESS_IMPORT_MAX_BYTES", 10 * 1024 * 1024, 1024, 20 * 1024 * 1024),
            max_pages=bounded("CODEASSESS_IMPORT_MAX_PAGES", 20, 1, 50),
            max_dimension=bounded("CODEASSESS_IMPORT_MAX_DIMENSION", 12_000, 64, 20_000),
            max_pixels=bounded("CODEASSESS_IMPORT_MAX_PIXELS", 40_000_000, 4096, 80_000_000),
            retention_hours=bounded("CODEASSESS_IMPORT_RETENTION_HOURS", 72, 1, 720),
            audit_retention_days=bounded("CODEASSESS_IMPORT_AUDIT_RETENTION_DAYS", 30, 1, 365),
            timeout_seconds=bounded("CODEASSESS_IMPORT_TIMEOUT_SECONDS", 30, 1, 60),
            ocr_concurrency=bounded("CODEASSESS_IMPORT_OCR_CONCURRENCY", 2, 1, 8),
        )


class AssignmentImportService:
    def __init__(self, repository: SQLiteRepository, graph: ConceptGraph, config: ImportConfig | None = None, ocr: OcrProvider | None = None):
        self.repository = repository
        self.graph = graph
        self.config = config or ImportConfig.from_environment()
        self.ocr = ocr or TesseractProvider(os.getenv("CODEASSESS_TESSERACT_PATH"), self.config.timeout_seconds, os.getenv("CODEASSESS_TESSERACT_SHA256"))
        self._ocr_slots = threading.BoundedSemaphore(self.config.ocr_concurrency)
        self.config.root.mkdir(parents=True, exist_ok=True)
        self.cleanup_temporary()
        self.cleanup_orphans()
        self.cleanup_expired()
        self.repository.purge_assignment_import_tombstones()

    @property
    def available(self) -> dict:
        return {"enabled": self.config.enabled, "embedded_pdf_text": True, "ocr": bool(getattr(self.ocr, "executable", None)), "ocr_provider": getattr(self.ocr, "name", "configured") if getattr(self.ocr, "executable", None) else None}

    def cleanup_temporary(self) -> None:
        for item in self.config.root.glob("*.tmp"):
            try: item.unlink()
            except OSError: pass

    def cleanup_orphans(self) -> int:
        """Remove interrupted-upload artifacts that have no persistence record."""
        referenced = self.repository.assignment_import_storage_keys()
        removed = 0
        for item in self.config.root.iterdir():
            if not item.is_file() or item.name in referenced or not re.fullmatch(r"[a-f0-9]{32}\.(png|jpg|webp|pdf)", item.name):
                continue
            try:
                item.unlink()
                removed += 1
            except OSError:
                continue
        return removed

    def cleanup_expired(self) -> int:
        removed = 0
        for item in self.repository.expired_assignment_imports():
            try:
                self._path(item["storage_key"]).unlink(missing_ok=True)
                self.repository.delete_assignment_import(item["public_id"], item["teacher_id"], reason="expired", tombstone_days=self.config.audit_retention_days)
                removed += 1
            except (OSError, RepositoryError, ImportError):
                continue
        return removed

    def _path(self, key: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{32}\.(png|jpg|webp|pdf)", key):
            raise ImportError("invalid_storage_key", "Invalid storage key")
        candidate = self.config.root / key
        try:
            attributes = getattr(os.lstat(candidate), "st_file_attributes", 0)
            if candidate.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ImportError("invalid_storage_key", "Invalid storage key")
        except FileNotFoundError:
            pass
        path = candidate.resolve()
        if self.config.root != path.parent:
            raise ImportError("invalid_storage_key", "Invalid storage key")
        return path

    def _detect(self, name: str, declared: str, content: bytes) -> tuple[str, str]:
        extension = Path(name).suffix.lower()
        if extension == ".jpeg": extension = ".jpg"
        detected = None
        for media, (suffix, magic) in SUPPORTED_MEDIA.items():
            if content.startswith(magic) and (media != "image/webp" or len(content) >= 12 and content[8:12] == b"WEBP"):
                detected = (media, suffix); break
        if not detected or declared.split(";", 1)[0].lower() != detected[0] or extension != detected[1]:
            raise ImportError("invalid_file_type", "File type, signature, and extension must agree")
        return detected

    def _inspect(self, media: str, content: bytes) -> tuple[dict, list[ExtractionSegment]]:
        if media.startswith("image/"):
            Image.MAX_IMAGE_PIXELS = self.config.max_pixels
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(content)) as image:
                        image.verify()
                    with Image.open(io.BytesIO(content)) as image:
                        width, height = image.size
                        orientation = int(image.getexif().get(274, 1))
                        if width > self.config.max_dimension or height > self.config.max_dimension or width * height > self.config.max_pixels:
                            raise ImportError("image_dimensions_exceeded", "Image dimensions exceed configured limits", 413)
                        image.load()
            except (Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
                raise ImportError("image_dimensions_exceeded", "Image dimensions exceed configured limits", 413) from exc
            except (UnidentifiedImageError, OSError) as exc:
                raise ImportError("malformed_image", "Image could not be decoded safely") from exc
            return {"width": width, "height": height, "orientation": orientation, "pages": 1, "text_pages": [], "ocr_pages": [1]}, []
        try:
            reader = PdfReader(io.BytesIO(content), strict=True)
            if reader.is_encrypted: raise ImportError("encrypted_pdf", "Encrypted PDFs are not supported")
            if len(reader.pages) > self.config.max_pages: raise ImportError("page_limit_exceeded", "PDF page count exceeds configured limit", 413)
            root = reader.trailer.get("/Root", {})
            if hasattr(root, "get_object"): root = root.get_object()
            if any(key in root for key in ("/OpenAction", "/AA", "/Names")):
                raise ImportError("active_pdf", "PDF active or embedded content is not supported")
            segments = []
            ocr_pages = []
            for number, page in enumerate(reader.pages, 1):
                text = (page.extract_text() or "").strip()[:MAX_TEXT]
                if text:
                    segments.append(ExtractionSegment(page=number, method="embedded-text", text=text, confidence=1.0))
                else:
                    ocr_pages.append(number)
            return {"pages": len(reader.pages), "text_pages": [segment.page for segment in segments], "ocr_pages": ocr_pages}, segments
        except ImportError: raise
        except Exception as exc:
            raise ImportError("malformed_pdf", "PDF could not be parsed safely") from exc

    def create(self, teacher_id: int, name: str, media_type: str, content: bytes, idempotency_key: str | None = None, *, expected_hash: str | None = None) -> dict:
        if not self.config.enabled: raise ImportError("import_disabled", "Assignment import is disabled", 503)
        if not content or len(content) > self.config.max_bytes: raise ImportError("upload_size_exceeded", "Upload exceeds configured size limit", 413)
        if idempotency_key and not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", idempotency_key): raise ImportError("invalid_idempotency_key", "Invalid idempotency key")
        digest = hashlib.sha256(content).hexdigest()
        if expected_hash is not None and (not re.fullmatch(r"[a-f0-9]{64}", expected_hash) or not secrets.compare_digest(digest, expected_hash)):
            raise ImportError("upload_hash_mismatch", "Upload integrity verification failed", 422)
        if idempotency_key:
            existing = self.repository.get_assignment_import_by_idempotency(teacher_id, idempotency_key)
            if existing:
                if existing["content_hash"] != digest: raise ImportError("idempotency_conflict", "Idempotency key was used for different content", 409)
                return self.public(existing)
        media, suffix = self._detect(name, media_type, content)
        metadata, segments = self._inspect(media, content)
        key = ""
        final: Path | None = None
        for _ in range(10):
            candidate = f"{secrets.token_hex(16)}{suffix}"
            try:
                candidate_path = self._path(candidate)
                descriptor = os.open(candidate_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(descriptor)
                key, final = candidate, candidate_path
                break
            except (FileExistsError, ImportError):
                continue
        if final is None:
            raise ImportError("storage_unavailable", "Private upload storage is unavailable", 503)
        fd, temporary = tempfile.mkstemp(prefix="upload-", suffix=".tmp", dir=self.config.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, final)
            config_hash = hashlib.sha256(json.dumps({"schema": "assignment-import-v1", "graph": self.graph.version, "limits": self.config.__dict__ | {"root": "private"}}, sort_keys=True, default=str).encode()).hexdigest()
            try:
                item = self.repository.create_assignment_import({
                    "public_id": secrets.token_urlsafe(24), "teacher_id": teacher_id, "state": "validated", "media_type": media,
                    "original_name": Path(name).name[:255], "byte_size": len(content), "content_hash": digest, "storage_key": key,
                    "metadata": metadata, "extraction": {"schema_version": "assignment-import-extraction-v1", "segments": [s.model_dump() for s in segments]},
                    "draft": {}, "config_hash": config_hash, "idempotency_key": idempotency_key,
                    "expires_at": (datetime.now(timezone.utc) + timedelta(hours=self.config.retention_hours)).isoformat(),
                })
            except RepositoryError as exc:
                existing = self.repository.get_assignment_import_by_idempotency(teacher_id, idempotency_key) if idempotency_key else None
                if existing and existing["content_hash"] == digest:
                    final.unlink(missing_ok=True)
                    return self.public(existing)
                if existing:
                    raise ImportError("idempotency_conflict", "Idempotency key was used for different content", 409) from exc
                raise
            return self.public(item)
        except Exception:
            for path in (Path(temporary), final):
                try: path.unlink(missing_ok=True)
                except OSError: pass
            raise

    def _owned(self, public_id: str, teacher_id: int) -> dict:
        item = self.repository.get_assignment_import(public_id, teacher_id)
        if not item: raise ImportError("import_not_found", "Assignment import not found", 404)
        if datetime.fromisoformat(item["expires_at"]) <= datetime.now(timezone.utc) and not item.get("assignment_id"):
            self._path(item["storage_key"]).unlink(missing_ok=True)
            self.repository.delete_assignment_import(public_id, teacher_id, reason="expired", tombstone_days=self.config.audit_retention_days)
            raise ImportError("import_expired", "Assignment import has expired", 410)
        return item

    def extract(self, public_id: str, teacher_id: int) -> dict:
        item = self._owned(public_id, teacher_id)
        if item["state"] == "confirmed":
            raise ImportError("import_confirmed", "This import has already been published", 409)
        if item["state"] == "review-ready":
            return self.public(item)
        segments = [ExtractionSegment.model_validate(s) for s in item["extraction"].get("segments", [])]
        required_pages = set(item["metadata"].get("ocr_pages", [])) - {segment.page for segment in segments if segment.method == "ocr"}
        if required_pages:
            if not self._ocr_slots.acquire(timeout=self.config.timeout_seconds):
                raise ImportError("ocr_busy", "Local OCR capacity is temporarily unavailable", 503)
            try:
                raw_segments = self.ocr.extract(self._path(item["storage_key"]))
                if not isinstance(raw_segments, list) or len(raw_segments) > self.config.max_pages:
                    raise ImportError("ocr_invalid_response", "Local OCR returned an invalid response", 503)
                ocr_segments = [ExtractionSegment.model_validate(segment) for segment in raw_segments]
                if any(segment.method != "ocr" or segment.page not in required_pages for segment in ocr_segments):
                    raise ImportError("ocr_page_mismatch", "Local OCR returned an invalid page mapping", 503)
                if sum(len(segment.text) for segment in ocr_segments) > MAX_TEXT * max(1, len(required_pages)):
                    raise ImportError("ocr_output_exceeded", "Local OCR output exceeded configured limits", 503)
                segments.extend(ocr_segments)
                if required_pages - {segment.page for segment in ocr_segments}:
                    raise ImportError("ocr_incomplete", "Local OCR did not return every required page", 503)
            except ValidationError as exc:
                failure = ImportError("ocr_invalid_response", "Local OCR returned an invalid response", 503)
                try:
                    self.repository.update_assignment_import(public_id, teacher_id, state="extraction-failed", event=failure.code)
                except RepositoryError:
                    pass
                raise failure from exc
            except ImportError as exc:
                failure_state = "extraction-unavailable" if exc.code in {"ocr_unavailable", "ocr_pdf_rendering_unavailable", "ocr_failed", "ocr_timeout"} else "extraction-failed"
                try:
                    self.repository.update_assignment_import(public_id, teacher_id, state=failure_state, event=exc.code)
                except RepositoryError:
                    pass
                raise
            except Exception as exc:
                self.repository.update_assignment_import(public_id, teacher_id, state="extraction-failed", event="ocr_failed")
                raise ImportError("ocr_failed", "Local OCR failed", 503) from exc
            finally:
                self._ocr_slots.release()
        if required_pages - {segment.page for segment in segments}:
            raise ImportError("ocr_incomplete", "Local OCR did not return every required page", 503)
        extraction = {"schema_version": "assignment-import-extraction-v1", "segments": [s.model_dump() for s in sorted(segments, key=lambda x: x.page)], "provider": getattr(self.ocr, "name", None) if any(s.method == "ocr" for s in segments) else "embedded-pdf-text"}
        draft = self._draft(segments, item["config_hash"])
        try:
            updated = self.repository.update_assignment_import(public_id, teacher_id, state="review-ready", extraction=extraction, draft=draft.model_dump(), event="extracted", expected_draft=item["draft"])
        except RepositoryError as exc:
            latest = self._owned(public_id, teacher_id)
            if latest["state"] == "review-ready": return self.public(latest)
            raise ImportError("draft_conflict", "Import changed during extraction; reload before retrying", 409) from exc
        return self.public(updated)

    def _draft(self, segments: list[ExtractionSegment], config_hash: str) -> ImportDraft:
        text = "\n\n".join(s.text for s in segments).strip()
        first = next((line.strip() for line in text.splitlines() if line.strip()), "")[:200]
        source = [SourceRef(page=s.page, text=s.text[:500]) for s in segments[:20]]
        def section(label: str, following: tuple[str, ...]) -> str:
            stops = "|".join(re.escape(x) for x in following)
            match = re.search(rf"(?ims)^[ \t]*{re.escape(label)}[ \t]*(?::[ \t]*|\r?\n)(.+?)(?=^[ \t]*(?:{stops})[ \t]*(?::|\r?\n)|\Z)", text)
            return match.group(1).strip()[:8000] if match else ""
        labels = ("title", "description", "requirements", "input", "output", "constraints", "examples", "concepts", "language", "deadline", "reference solution", "reference source", "tests", "rubric", "sample input", "sample output")
        values = {label: section(label, labels) for label in labels}
        explicit_language = None
        lang_text = values["language"] or text
        matches = {lang for pattern, lang in ((r"\bpython(?:\s*3(?:\.11)?)?\b", "python"), (r"\b(?:c11|clang)\b", "c"), (r"\bjava(?:\s*17)?\b", "java")) if re.search(pattern, lang_text, re.I)}
        if len(matches) == 1: explicit_language = next(iter(matches))
        graph_matches = []
        lowered = text.casefold()
        for concept in sorted(self.graph.concepts.values(), key=lambda value: value.id):
            if re.search(rf"(?<![\w-]){re.escape(concept.id.casefold())}(?![\w-])", lowered) or re.search(rf"(?<!\w){re.escape(concept.label.casefold())}(?!\w)", lowered): graph_matches.append(concept.id)
        def field(value, origin="extracted", warnings=None):
            present = value not in ("", [], None)
            relevant = [s for s in segments if isinstance(value, str) and value in s.text] or segments
            confidence = min(s.confidence for s in relevant) if relevant and all(s.confidence is not None for s in relevant) else None
            notes = list(warnings or [])
            if present and (confidence is None or confidence < .8): notes.append("Extraction confidence is low or unknown; compare with the source.")
            references = [SourceRef(page=s.page, text=s.text[:500]) for s in relevant[:20]]
            return DraftField(value=value if present else None, origin=origin if present else "missing", confidence=confidence if present else None, sources=references if present else [], warnings=notes)
        reference = values["reference solution"] or values["reference source"]
        if reference.startswith("```"):
            reference = re.sub(r"\A```[^\n]*\n|\n```\Z", "", reference)
        deadline = None
        if values["deadline"]:
            try:
                parsed_deadline = datetime.fromisoformat(values["deadline"])
                if parsed_deadline.tzinfo is not None: deadline = parsed_deadline.isoformat()
            except ValueError:
                pass
        rubric = None
        if values["rubric"]:
            try:
                proposed = json.loads(values["rubric"])
                if isinstance(proposed, dict) and set(proposed) <= {"policy_version", "weights"}:
                    resolve_weights(proposed.get("policy_version", "core-v1"), proposed.get("weights"))
                    rubric = proposed
            except (ValueError, TypeError):
                pass
        candidates = []
        if values["sample input"] and values["sample output"]:
            candidates.append(CandidateTest(id="sample-1", input=values["sample input"], expected_output=values["sample output"], origin="extracted", sources=source))
        if values["tests"]:
            try:
                raw_tests = json.loads(values["tests"])
                if isinstance(raw_tests, list) and len(raw_tests) <= 50:
                    for index, case in enumerate(raw_tests):
                        if isinstance(case, dict) and set(case) <= {"id", "input", "expected_output"}:
                            candidates.append(CandidateTest(id=case.get("id", f"extracted-{index + 1}"), input=case["input"], expected_output=case["expected_output"], origin="extracted", sources=source))
            except (ValueError, TypeError, KeyError):
                candidates = []
        if len({case.id for case in candidates}) != len(candidates): candidates = []
        fields = {
            "title": field((values["title"] or first)[:200]), "description": field(values["description"][:4000]), "requirements": field(values["requirements"]),
            "language": field(explicit_language, warnings=[] if explicit_language else ["Choose Python, C, or Java."]),
            "input_notes": field(values["input"][:4000]), "output_notes": field(values["output"][:4000]), "constraints": field(values["constraints"][:4000]),
            "examples": field([values["examples"]] if values["examples"] else []), "concept_ids": field(graph_matches),
            "reference_source": field(reference), "tests": field([]), "rubric": field(rubric),
            "deadline": field(deadline, warnings=["Enter an explicit date, time, and timezone."] if values["deadline"] and not deadline else []),
        }
        if reference: fields["reference_source"].verification = "source-provided"
        unresolved = [part.strip() for part in re.split(r"[,\n]", values["concepts"]) if part.strip() and part.strip().casefold() not in {c.id.casefold() for c in self.graph.concepts.values()} | {c.label.casefold() for c in self.graph.concepts.values()}]
        return ImportDraft(fields=fields, unresolved_concepts=unresolved[:50], candidate_tests=candidates[:50], config_hash=config_hash)

    def patch(self, public_id: str, teacher_id: int, patch: DraftPatch) -> dict:
        item = self._owned(public_id, teacher_id)
        if item["state"] != "review-ready":
            raise ImportError("import_not_ready", "Extract the document before editing its draft", 409)
        draft = ImportDraft.model_validate(item["draft"])
        if set(patch.fields) & set(patch.rejected_fields) or set(patch.confirmed_candidate_ids) & set(patch.rejected_candidate_ids):
            raise ImportError("conflicting_decisions", "A suggestion cannot be accepted and rejected together")
        changes = len(patch.fields) + len(patch.rejected_fields) + len(patch.confirmed_candidate_ids) + len(patch.rejected_candidate_ids)
        if len(draft.history) + changes > 200:
            raise ImportError("review_history_limit", "The review history limit has been reached; create a new import", 409)
        known_candidates = {case.id for case in draft.candidate_tests}
        if (set(patch.confirmed_candidate_ids) | set(patch.rejected_candidate_ids)) - known_candidates:
            raise ImportError("unknown_candidate", "Unknown candidate test")
        for name, value in patch.fields.items():
            if name not in draft.fields: raise ImportError("unknown_field", f"Unknown draft field: {name}")
            previous = draft.fields[name]
            try:
                replacement = DraftField(value=value, origin="teacher-confirmed", confidence=1.0, verification="teacher-confirmed", sources=previous.sources)
            except ValidationError as exc:
                raise ImportError("invalid_draft_field", f"Invalid draft value for {name}") from exc
            draft.history.append({"field": name, "decision": "confirmed", "previous": previous.model_dump()})
            draft.fields[name] = replacement
        for name in patch.rejected_fields:
            if name not in draft.fields: raise ImportError("unknown_field", f"Unknown draft field: {name}")
            draft.history.append({"field": name, "decision": "rejected", "previous": draft.fields[name].model_dump()})
            draft.fields[name] = DraftField()
        for candidate in draft.candidate_tests:
            if candidate.id in patch.confirmed_candidate_ids or candidate.id in patch.rejected_candidate_ids:
                decision = "confirmed" if candidate.id in patch.confirmed_candidate_ids else "rejected"
                draft.history.append({"field": f"candidate:{candidate.id}", "decision": decision, "previous": candidate.model_dump()})
                if decision == "confirmed": candidate.verification = "teacher-confirmed"
        draft.candidate_tests = [case for case in draft.candidate_tests if case.id not in patch.rejected_candidate_ids]
        if len(draft.model_dump_json().encode()) > 512 * 1024:
            raise ImportError("draft_size_exceeded", "Draft and review history exceed the configured limit", 413)
        try:
            updated = self.repository.update_assignment_import(public_id, teacher_id, state="review-ready", draft=draft.model_dump(), event="draft-updated", expected_draft=item["draft"])
        except RepositoryError as exc:
            raise ImportError("draft_conflict", "Draft changed during review; reload before saving", 409) from exc
        return self.public(updated)

    def validate_confirmation(self, item: dict, data: dict) -> None:
        if item.get("assignment_id") is not None:
            return
        if item["state"] != "review-ready":
            raise ImportError("import_not_ready", "Extract and review the document before publishing", 409)
        draft = ImportDraft.model_validate(item["draft"])
        reference = draft.fields.get("reference_source", DraftField())
        if reference.value and reference.value == data["reference_source"] and reference.verification not in {"teacher-confirmed", "worker-verified"}:
            raise ImportError("reference_unverified", "Review and explicitly confirm the imported reference solution")
        reviewed_tests = draft.fields.get("tests", DraftField())
        reviewed_pairs = {(case.get("input"), case.get("expected_output")) for case in (reviewed_tests.value or []) if isinstance(case, dict)} if reviewed_tests.verification == "teacher-confirmed" else set()
        pairs = {(case["input"], case["expected_output"]) for case in data["tests"]}
        for case in draft.candidate_tests:
            pair = (case.input, case.expected_output)
            if pair in pairs and pair not in reviewed_pairs and case.verification not in {"teacher-confirmed", "worker-verified"}:
                raise ImportError("test_unverified", "Review and explicitly confirm each imported test and expected output")

    def preview(self, public_id: str, teacher_id: int) -> tuple[Path, str, str]:
        item = self._owned(public_id, teacher_id)
        disposition = "attachment" if item["media_type"] == "application/pdf" else "inline"
        path = self._path(item["storage_key"])
        if not path.is_file():
            raise ImportError("source_unavailable", "The original source is no longer retained", 410)
        return path, item["media_type"], disposition

    def delete(self, public_id: str, teacher_id: int) -> None:
        item = self.repository.delete_assignment_import(public_id, teacher_id, tombstone_days=self.config.audit_retention_days)
        self._path(item["storage_key"]).unlink(missing_ok=True)

    def discard_confirmed_source(self, public_id: str, teacher_id: int) -> None:
        item = self.repository.get_assignment_import(public_id, teacher_id)
        if not item or item.get("assignment_id") is None:
            raise ImportError("import_not_found", "Assignment import not found", 404)
        path = self._path(item["storage_key"])
        if path.exists():
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                raise ImportError("source_cleanup_failed", "Assignment saved; source cleanup is pending. Retry confirmation.", 503) from exc
            self.repository.record_assignment_import_event(public_id, teacher_id, "source-deleted-after-confirmation")

    def public(self, item: dict) -> dict:
        return {key: item[key] for key in ("public_id", "state", "media_type", "original_name", "byte_size", "content_hash", "metadata", "extraction", "draft", "config_hash", "assignment_id", "expires_at", "created_at", "updated_at")}
