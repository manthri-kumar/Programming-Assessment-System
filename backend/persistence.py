from __future__ import annotations

import json
import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Iterator, Protocol

from backend.reporting import replay_compatible_result


SCHEMA_VERSION = 8

ASSIGNMENT_IMPORT_TRANSITIONS = {
    "validated": {"validated", "review-ready", "extraction-unavailable", "extraction-failed"},
    "extraction-unavailable": {"extraction-unavailable", "extraction-failed", "review-ready"},
    "extraction-failed": {"extraction-unavailable", "extraction-failed", "review-ready"},
    "review-ready": {"review-ready", "extraction-unavailable", "extraction-failed"},
}


class RepositoryError(RuntimeError):
    pass


class AssessmentRepository(Protocol):
    def create_assessment_record(self, request_hash: str, status: str, versions: dict, evidence: list, result: dict) -> dict: ...
    def get_assessment_record(self, record_id: int) -> dict | None: ...
    def get_assessment_record_by_hash(self, request_hash: str) -> dict | None: ...
    def redact_expired(self, retention_days: int, now: datetime | None = None) -> dict[str, int]: ...


class SQLiteRepository:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = Lock()
        self.migrate()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self._connection
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def migrate(self) -> None:
        with self.transaction() as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.executescript("""
            CREATE TABLE IF NOT EXISTS schema_meta(version INTEGER NOT NULL);
            INSERT INTO schema_meta(version) SELECT 2 WHERE NOT EXISTS(SELECT 1 FROM schema_meta);
            CREATE TABLE IF NOT EXISTS users(
              id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('teacher','student')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS assignments(
              id INTEGER PRIMARY KEY, teacher_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL,
              language TEXT NOT NULL, rubric_json TEXT NOT NULL, reference_source TEXT NOT NULL,
              tests_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(teacher_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS submissions(
              id INTEGER PRIMARY KEY, assignment_id INTEGER NOT NULL, student_id INTEGER NOT NULL,
              source TEXT NOT NULL, language TEXT NOT NULL, status TEXT NOT NULL,
              config_snapshot_json TEXT, config_hash TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(assignment_id) REFERENCES assignments(id), FOREIGN KEY(student_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS evaluations(
              id INTEGER PRIMARY KEY, submission_id INTEGER UNIQUE NOT NULL, policy_version TEXT NOT NULL,
              result_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(submission_id) REFERENCES submissions(id)
            );
            CREATE TABLE IF NOT EXISTS assessment_records(
              id INTEGER PRIMARY KEY, request_hash TEXT UNIQUE NOT NULL, status TEXT NOT NULL,
              versions_json TEXT NOT NULL, evidence_json TEXT NOT NULL, result_json TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, redacted_at TEXT
            );
            CREATE TABLE IF NOT EXISTS bookmarks(
              student_id INTEGER NOT NULL, assignment_id INTEGER NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY(student_id, assignment_id),
              FOREIGN KEY(student_id) REFERENCES users(id), FOREIGN KEY(assignment_id) REFERENCES assignments(id)
            );
            CREATE TABLE IF NOT EXISTS drafts(
              student_id INTEGER NOT NULL, assignment_id INTEGER NOT NULL, language TEXT NOT NULL,
              source TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY(student_id, assignment_id),
              FOREIGN KEY(student_id) REFERENCES users(id), FOREIGN KEY(assignment_id) REFERENCES assignments(id)
            );
            CREATE TABLE IF NOT EXISTS activity_events(
              id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, kind TEXT NOT NULL,
              assignment_id INTEGER, submission_id INTEGER,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(user_id) REFERENCES users(id),
              FOREIGN KEY(assignment_id) REFERENCES assignments(id),
              FOREIGN KEY(submission_id) REFERENCES submissions(id)
            );
            CREATE TABLE IF NOT EXISTS evaluation_jobs(
              job_id TEXT PRIMARY KEY, submission_id INTEGER NOT NULL, config_hash TEXT NOT NULL,
              state TEXT NOT NULL CHECK(state IN ('queued','running','completed','failed','cancelled')),
              attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 2,
              lease_owner TEXT, lease_expires_at TEXT, failure_category TEXT,
              assessment_record_id INTEGER, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(submission_id,config_hash), FOREIGN KEY(submission_id) REFERENCES submissions(id)
            );
            CREATE TABLE IF NOT EXISTS institutions(
              id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
              is_default INTEGER NOT NULL DEFAULT 0 CHECK(is_default IN (0,1))
            );
            CREATE TABLE IF NOT EXISTS courses(
              id INTEGER PRIMARY KEY, institution_id INTEGER NOT NULL, code TEXT NOT NULL, name TEXT NOT NULL,
              enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)), UNIQUE(institution_id,code),
              FOREIGN KEY(institution_id) REFERENCES institutions(id)
            );
            CREATE TABLE IF NOT EXISTS cohorts(
              id INTEGER PRIMARY KEY, course_id INTEGER NOT NULL, name TEXT NOT NULL, UNIQUE(course_id,name),
              FOREIGN KEY(course_id) REFERENCES courses(id)
            );
            CREATE TABLE IF NOT EXISTS enrollments(
              course_id INTEGER NOT NULL, student_id INTEGER NOT NULL, cohort_id INTEGER,
              status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','inactive')),
              PRIMARY KEY(course_id,student_id), FOREIGN KEY(course_id) REFERENCES courses(id),
              FOREIGN KEY(student_id) REFERENCES users(id), FOREIGN KEY(cohort_id) REFERENCES cohorts(id)
            );
            CREATE TABLE IF NOT EXISTS course_teachers(
              course_id INTEGER NOT NULL, teacher_id INTEGER NOT NULL,
              PRIMARY KEY(course_id,teacher_id), FOREIGN KEY(course_id) REFERENCES courses(id),
              FOREIGN KEY(teacher_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS assignment_imports(
              id INTEGER PRIMARY KEY, public_id TEXT UNIQUE NOT NULL, teacher_id INTEGER NOT NULL,
              state TEXT NOT NULL, media_type TEXT NOT NULL, original_name TEXT NOT NULL,
              byte_size INTEGER NOT NULL, content_hash TEXT NOT NULL, storage_key TEXT NOT NULL,
              metadata_json TEXT NOT NULL DEFAULT '{}', extraction_json TEXT NOT NULL DEFAULT '{}',
              draft_json TEXT NOT NULL DEFAULT '{}', config_hash TEXT NOT NULL,
              idempotency_key TEXT, assignment_id INTEGER, expires_at TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(teacher_id,idempotency_key), FOREIGN KEY(teacher_id) REFERENCES users(id),
              FOREIGN KEY(assignment_id) REFERENCES assignments(id)
            );
            CREATE TABLE IF NOT EXISTS assignment_import_events(
              id INTEGER PRIMARY KEY, import_id INTEGER NOT NULL, event TEXT NOT NULL,
              details_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(import_id) REFERENCES assignment_imports(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS assignment_import_tombstones(
              public_id TEXT PRIMARY KEY, teacher_id INTEGER NOT NULL, reason TEXT NOT NULL,
              media_type TEXT NOT NULL, byte_size INTEGER NOT NULL,
              import_created_at TEXT NOT NULL, deleted_at TEXT NOT NULL, purge_after TEXT NOT NULL
            );
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(assignments)")}
            additions = {
                "requirements": "TEXT NOT NULL DEFAULT ''",
                "input_notes": "TEXT NOT NULL DEFAULT ''",
                "output_notes": "TEXT NOT NULL DEFAULT ''",
                "examples_json": "TEXT NOT NULL DEFAULT '[]'",
                "constraints_text": "TEXT NOT NULL DEFAULT ''",
                "concept_ids_json": "TEXT NOT NULL DEFAULT '[]'",
                "deadline": "TEXT",
            }
            for name, definition in additions.items():
                if name not in columns:
                    db.execute(f"ALTER TABLE assignments ADD COLUMN {name} {definition}")
            submission_columns = {row["name"] for row in db.execute("PRAGMA table_info(submissions)")}
            if "config_snapshot_json" not in submission_columns:
                db.execute("ALTER TABLE submissions ADD COLUMN config_snapshot_json TEXT")
            if "config_hash" not in submission_columns:
                db.execute("ALTER TABLE submissions ADD COLUMN config_hash TEXT")
            assignment_columns = {row["name"] for row in db.execute("PRAGMA table_info(assignments)")}
            if "course_id" not in assignment_columns:
                db.execute("ALTER TABLE assignments ADD COLUMN course_id INTEGER")
            if "available_from" not in assignment_columns:
                db.execute("ALTER TABLE assignments ADD COLUMN available_from TEXT")
            db.execute("INSERT OR IGNORE INTO institutions(code,name,is_default) VALUES('local','Local institution',1)")
            institution_id = db.execute("SELECT id FROM institutions WHERE code='local'").fetchone()["id"]
            db.execute("INSERT OR IGNORE INTO courses(institution_id,code,name,enabled) VALUES(?, 'local', 'Local course', 1)", (institution_id,))
            local_course_id = db.execute("SELECT id FROM courses WHERE institution_id=? AND code='local'", (institution_id,)).fetchone()["id"]
            db.execute("UPDATE assignments SET course_id=? WHERE course_id IS NULL", (local_course_id,))
            db.execute("INSERT OR IGNORE INTO course_teachers(course_id,teacher_id) SELECT ?,id FROM users WHERE role='teacher'", (local_course_id,))
            db.execute("INSERT OR IGNORE INTO enrollments(course_id,student_id,status) SELECT ?,id,'active' FROM users WHERE role='student'", (local_course_id,))
            rows = db.execute(
                "SELECT s.id,s.assignment_id,a.language,a.rubric_json,a.reference_source,a.tests_json,a.concept_ids_json "
                "FROM submissions s JOIN assignments a ON a.id=s.assignment_id WHERE s.config_snapshot_json IS NULL"
            ).fetchall()
            for row in rows:
                snapshot = {
                    "schema_version": "assessment-config-v1", "assignment_id": row["assignment_id"],
                    "language": row["language"], "rubric": json.loads(row["rubric_json"]),
                    "reference_source": row["reference_source"], "tests": json.loads(row["tests_json"]),
                    "concept_ids": json.loads(row["concept_ids_json"] or "[]"),
                }
                encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
                db.execute("UPDATE submissions SET config_snapshot_json=?,config_hash=? WHERE id=?", (encoded, hashlib.sha256(encoded.encode()).hexdigest(), row["id"]))
            db.execute("UPDATE schema_meta SET version=?", (SCHEMA_VERSION,))

    def create_assignment_import(self, data: dict) -> dict:
        try:
            with self.transaction() as db:
                cursor = db.execute(
                    "INSERT INTO assignment_imports(public_id,teacher_id,state,media_type,original_name,byte_size,content_hash,storage_key,metadata_json,extraction_json,draft_json,config_hash,idempotency_key,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (data["public_id"], data["teacher_id"], data["state"], data["media_type"], data["original_name"], data["byte_size"], data["content_hash"], data["storage_key"], json.dumps(data.get("metadata", {}), sort_keys=True), json.dumps(data.get("extraction", {}), sort_keys=True), json.dumps(data.get("draft", {}), sort_keys=True), data["config_hash"], data.get("idempotency_key"), data["expires_at"]),
                )
                import_id = int(cursor.lastrowid)
                db.execute("INSERT INTO assignment_import_events(import_id,event,details_json) VALUES(?,?,?)", (import_id, "created", json.dumps({"media_type": data["media_type"], "byte_size": data["byte_size"]}, sort_keys=True)))
        except sqlite3.IntegrityError as exc:
            raise RepositoryError("assignment import conflict") from exc
        item = self.get_assignment_import(data["public_id"], data["teacher_id"])
        assert item is not None
        return item

    def get_assignment_import(self, public_id: str, teacher_id: int) -> dict | None:
        row = self._connection.execute("SELECT * FROM assignment_imports WHERE public_id=? AND teacher_id=?", (public_id, teacher_id)).fetchone()
        if not row:
            return None
        data = dict(row)
        for source, target in (("metadata_json", "metadata"), ("extraction_json", "extraction"), ("draft_json", "draft")):
            data[target] = json.loads(data.pop(source) or "{}")
        return data

    def get_assignment_import_by_idempotency(self, teacher_id: int, key: str) -> dict | None:
        row = self._connection.execute("SELECT public_id FROM assignment_imports WHERE teacher_id=? AND idempotency_key=?", (teacher_id, key)).fetchone()
        return self.get_assignment_import(row["public_id"], teacher_id) if row else None

    def list_assignment_imports(self, teacher_id: int) -> list[dict]:
        rows = self._connection.execute("SELECT public_id FROM assignment_imports WHERE teacher_id=? AND assignment_id IS NULL ORDER BY id DESC", (teacher_id,)).fetchall()
        return [item for row in rows if (item := self.get_assignment_import(row["public_id"], teacher_id)) is not None]

    def expired_assignment_imports(self, now: datetime | None = None) -> list[dict]:
        current = (now or datetime.now(timezone.utc)).isoformat()
        rows = self._connection.execute("SELECT public_id,teacher_id FROM assignment_imports WHERE assignment_id IS NULL AND expires_at<=?", (current,)).fetchall()
        return [item for row in rows if (item := self.get_assignment_import(row["public_id"], row["teacher_id"])) is not None]

    def assignment_import_storage_keys(self) -> set[str]:
        rows = self._connection.execute("SELECT storage_key FROM assignment_imports").fetchall()
        return {str(row["storage_key"]) for row in rows}

    def assignment_import_events(self, public_id: str, teacher_id: int) -> list[dict]:
        rows = self._connection.execute(
            "SELECT e.event,e.details_json,e.created_at FROM assignment_import_events e "
            "JOIN assignment_imports i ON i.id=e.import_id WHERE i.public_id=? AND i.teacher_id=? ORDER BY e.id",
            (public_id, teacher_id),
        ).fetchall()
        return [{"event": row["event"], "details": json.loads(row["details_json"] or "{}"), "created_at": row["created_at"]} for row in rows]

    def update_assignment_import(self, public_id: str, teacher_id: int, *, state: str | None = None, metadata: dict | None = None, extraction: dict | None = None, draft: dict | None = None, event: str = "updated", expected_draft: dict | None = None) -> dict:
        fields: dict[str, object] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if state is not None: fields["state"] = state
        if metadata is not None: fields["metadata_json"] = json.dumps(metadata, sort_keys=True)
        if extraction is not None: fields["extraction_json"] = json.dumps(extraction, sort_keys=True)
        if draft is not None: fields["draft_json"] = json.dumps(draft, sort_keys=True)
        clause = ",".join(f"{key}=?" for key in fields)
        with self.transaction() as db:
            current = db.execute(
                "SELECT id,state,assignment_id,draft_json FROM assignment_imports WHERE public_id=? AND teacher_id=?",
                (public_id, teacher_id),
            ).fetchone()
            if not current or current["assignment_id"] is not None:
                raise RepositoryError("assignment import not found or already confirmed")
            if expected_draft is not None and json.loads(current["draft_json"]) != expected_draft:
                raise RepositoryError("assignment import draft changed")
            if state is not None and state not in ASSIGNMENT_IMPORT_TRANSITIONS.get(str(current["state"]), set()):
                raise RepositoryError("invalid assignment import state transition")
            db.execute(f"UPDATE assignment_imports SET {clause} WHERE id=?", (*fields.values(), current["id"]))
            db.execute("INSERT INTO assignment_import_events(import_id,event,details_json) VALUES(?,?,?)", (current["id"], event, "{}"))
        item = self.get_assignment_import(public_id, teacher_id)
        assert item is not None
        return item

    def delete_assignment_import(self, public_id: str, teacher_id: int, *, reason: str = "owner-deleted", tombstone_days: int = 30) -> dict:
        deleted_at = datetime.now(timezone.utc)
        with self.transaction() as db:
            item = self.get_assignment_import(public_id, teacher_id)
            if not item or item.get("assignment_id") is not None:
                raise RepositoryError("assignment import not found or already confirmed")
            db.execute(
                "INSERT OR REPLACE INTO assignment_import_tombstones(public_id,teacher_id,reason,media_type,byte_size,import_created_at,deleted_at,purge_after) VALUES(?,?,?,?,?,?,?,?)",
                (public_id, teacher_id, reason, item["media_type"], item["byte_size"], item["created_at"], deleted_at.isoformat(), (deleted_at + timedelta(days=tombstone_days)).isoformat()),
            )
            db.execute("DELETE FROM assignment_import_events WHERE import_id=?", (item["id"],))
            db.execute("DELETE FROM assignment_imports WHERE id=?", (item["id"],))
        return item

    def assignment_import_tombstones(self, teacher_id: int) -> list[dict]:
        rows = self._connection.execute(
            "SELECT public_id,reason,media_type,byte_size,import_created_at,deleted_at,purge_after FROM assignment_import_tombstones WHERE teacher_id=? ORDER BY deleted_at",
            (teacher_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def purge_assignment_import_tombstones(self, now: datetime | None = None) -> int:
        with self.transaction() as db:
            cursor = db.execute("DELETE FROM assignment_import_tombstones WHERE purge_after<=?", ((now or datetime.now(timezone.utc)).isoformat(),))
            return cursor.rowcount

    def record_assignment_import_event(self, public_id: str, teacher_id: int, event: str) -> None:
        with self.transaction() as db:
            row = db.execute("SELECT id FROM assignment_imports WHERE public_id=? AND teacher_id=?", (public_id, teacher_id)).fetchone()
            if not row:
                raise RepositoryError("assignment import not found")
            db.execute("INSERT INTO assignment_import_events(import_id,event,details_json) VALUES(?,?,?)", (row["id"], event, "{}"))

    def confirm_assignment_import(self, public_id: str, teacher_id: int, data: dict, *, expected_draft: dict | None = None) -> dict:
        with self.transaction() as db:
            item = db.execute("SELECT * FROM assignment_imports WHERE public_id=? AND teacher_id=?", (public_id, teacher_id)).fetchone()
            if not item:
                raise RepositoryError("assignment import not found")
            if item["assignment_id"] is not None:
                assignment_id = int(item["assignment_id"])
            else:
                if item["state"] != "review-ready":
                    raise RepositoryError("assignment import is not ready for confirmation")
                if expected_draft is not None and json.loads(item["draft_json"]) != expected_draft:
                    raise RepositoryError("assignment import changed during confirmation")
                local = db.execute("SELECT c.id FROM courses c JOIN institutions i ON i.id=c.institution_id WHERE i.code='local' AND c.code='local'").fetchone()
                cursor = db.execute(
                    "INSERT INTO assignments(teacher_id,title,description,language,rubric_json,reference_source,tests_json,requirements,input_notes,output_notes,examples_json,constraints_text,concept_ids_json,deadline,course_id,available_from) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (teacher_id, data["title"], data.get("description", ""), data["language"], json.dumps(data["rubric"]), data["reference_source"], json.dumps(data["tests"]), data.get("requirements", ""), data.get("input_notes", ""), data.get("output_notes", ""), json.dumps(data.get("examples", [])), data.get("constraints", ""), json.dumps(data.get("concept_ids", [])), data.get("deadline"), local["id"] if local else None, data.get("available_from")),
                )
                assignment_id = int(cursor.lastrowid)
                db.execute("UPDATE assignment_imports SET assignment_id=?,state='confirmed',updated_at=CURRENT_TIMESTAMP WHERE id=?", (assignment_id, item["id"]))
                db.execute("INSERT INTO assignment_import_events(import_id,event,details_json) VALUES(?,?,?)", (item["id"], "confirmed", json.dumps({"assignment_id": assignment_id})))
        assignment = self.get_assignment(assignment_id)
        assert assignment is not None
        return assignment

    def create_user(self, email: str, password_hash: str, role: str) -> dict:
        try:
            with self.transaction() as db:
                cursor = db.execute("INSERT INTO users(email,password_hash,role) VALUES(?,?,?)", (email.lower(), password_hash, role))
                user_id = int(cursor.lastrowid)
                local_course = db.execute("SELECT c.id FROM courses c JOIN institutions i ON i.id=c.institution_id WHERE i.code='local' AND c.code='local'").fetchone()
                if local_course and role == "teacher":
                    db.execute("INSERT OR IGNORE INTO course_teachers(course_id,teacher_id) VALUES(?,?)", (local_course["id"], user_id))
                elif local_course and role == "student":
                    db.execute("INSERT OR IGNORE INTO enrollments(course_id,student_id,status) VALUES(?,?,'active')", (local_course["id"], user_id))
                return self.get_user(user_id)
        except sqlite3.IntegrityError as exc:
            raise RepositoryError("email already registered") from exc

    def get_user(self, user_id: int) -> dict | None:
        row = self._connection.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def find_user(self, email: str) -> dict | None:
        row = self._connection.execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
        return dict(row) if row else None

    def create_assignment(self, teacher_id: int, data: dict) -> dict:
        with self.transaction() as db:
            local_course = db.execute("SELECT c.id FROM courses c JOIN institutions i ON i.id=c.institution_id WHERE i.code='local' AND c.code='local'").fetchone()
            course_id = data.get("course_id") or (local_course["id"] if local_course else None)
            cursor = db.execute(
                "INSERT INTO assignments(teacher_id,title,description,language,rubric_json,reference_source,tests_json,requirements,input_notes,output_notes,examples_json,constraints_text,concept_ids_json,deadline,course_id,available_from) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (teacher_id, data["title"], data.get("description", ""), data["language"], json.dumps(data["rubric"]), data["reference_source"], json.dumps(data["tests"]), data.get("requirements", ""), data.get("input_notes", ""), data.get("output_notes", ""), json.dumps(data.get("examples", [])), data.get("constraints", ""), json.dumps(data.get("concept_ids", [])), data.get("deadline"), course_id, data.get("available_from")),
            )
            return self.get_assignment(cursor.lastrowid)

    def get_assignment(self, assignment_id: int) -> dict | None:
        row = self._connection.execute("SELECT * FROM assignments WHERE id=?", (assignment_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["rubric"] = json.loads(data.pop("rubric_json"))
        data["tests"] = json.loads(data.pop("tests_json"))
        data["examples"] = json.loads(data.pop("examples_json", "[]"))
        data["concept_ids"] = json.loads(data.pop("concept_ids_json", "[]"))
        return data

    def list_assignments(self, teacher_id: int | None = None) -> list[dict]:
        if teacher_id is None:
            rows = self._connection.execute("SELECT id FROM assignments ORDER BY id")
        else:
            rows = self._connection.execute("SELECT id FROM assignments WHERE teacher_id=? ORDER BY id", (teacher_id,))
        ids = [row["id"] for row in rows]
        return [self.get_assignment(value) for value in ids]

    def update_assignment(self, assignment_id: int, teacher_id: int, data: dict) -> dict:
        fields = {
            "title": data.get("title"),
            "description": data.get("description"),
            "language": data.get("language"),
            "rubric_json": json.dumps(data["rubric"]) if data.get("rubric") is not None else None,
            "reference_source": data.get("reference_source"),
            "tests_json": json.dumps(data["tests"]) if data.get("tests") is not None else None,
            "requirements": data.get("requirements"),
            "input_notes": data.get("input_notes"),
            "output_notes": data.get("output_notes"),
            "examples_json": json.dumps(data["examples"]) if data.get("examples") is not None else None,
            "constraints_text": data.get("constraints"),
            "concept_ids_json": json.dumps(data["concept_ids"]) if data.get("concept_ids") is not None else None,
            "deadline": data.get("deadline") if "deadline" in data else None,
        }
        selected = {key: value for key, value in fields.items() if value is not None or (key == "deadline" and "deadline" in data)}
        if not selected:
            raise RepositoryError("at least one assignment field is required")
        clause = ",".join(f"{key}=?" for key in selected)
        with self.transaction() as db:
            cursor = db.execute(
                f"UPDATE assignments SET {clause} WHERE id=? AND teacher_id=?",
                (*selected.values(), assignment_id, teacher_id),
            )
            if cursor.rowcount != 1:
                raise RepositoryError("assignment not found or not owned by teacher")
        assignment = self.get_assignment(assignment_id)
        assert assignment is not None
        return assignment

    def create_submission(self, assignment_id: int, student_id: int, language: str, source: str) -> dict:
        assignment = self.get_assignment(assignment_id)
        if not assignment:
            raise RepositoryError("assignment not found")
        snapshot = {
            "schema_version": "assessment-config-v1", "assignment_id": assignment_id,
            "language": assignment["language"], "rubric": assignment["rubric"],
            "reference_source": assignment["reference_source"], "tests": assignment["tests"],
            "concept_ids": assignment.get("concept_ids", []),
        }
        encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
        config_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        with self.transaction() as db:
            cursor = db.execute("INSERT INTO submissions(assignment_id,student_id,source,language,status,config_snapshot_json,config_hash) VALUES(?,?,?,?,?,?,?)", (assignment_id, student_id, source, language, "pending", encoded, config_hash))
            submission_id = int(cursor.lastrowid)
            db.execute("INSERT INTO activity_events(user_id,kind,assignment_id,submission_id) VALUES(?,?,?,?)", (student_id, "submission_created", assignment_id, submission_id))
            return self.get_submission(submission_id)

    def get_submission(self, submission_id: int) -> dict | None:
        row = self._connection.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone()
        return dict(row) if row else None

    def get_submission_configuration(self, submission_id: int) -> dict | None:
        row = self._connection.execute("SELECT config_snapshot_json,config_hash FROM submissions WHERE id=?", (submission_id,)).fetchone()
        if not row or not row["config_snapshot_json"]:
            return None
        return {"snapshot": json.loads(row["config_snapshot_json"]), "hash": row["config_hash"]}

    def create_evaluation_job(self, submission_id: int, config_hash: str, max_attempts: int = 2) -> dict:
        if not config_hash or max_attempts < 1 or max_attempts > 5:
            raise RepositoryError("invalid evaluation job configuration")
        job_id = hashlib.sha256(f"evaluation-job-v1:{submission_id}:{config_hash}".encode()).hexdigest()
        with self.transaction() as db:
            if not db.execute("SELECT 1 FROM submissions WHERE id=?", (submission_id,)).fetchone():
                raise RepositoryError("submission not found")
            db.execute(
                "INSERT OR IGNORE INTO evaluation_jobs(job_id,submission_id,config_hash,state,max_attempts) VALUES(?,?,?,?,?)",
                (job_id, submission_id, config_hash, "queued", max_attempts),
            )
        job = self.get_evaluation_job(job_id)
        assert job is not None
        return job

    def get_evaluation_job(self, job_id: str) -> dict | None:
        row = self._connection.execute("SELECT * FROM evaluation_jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def claim_evaluation_job(self, job_id: str, lease_owner: str, lease_seconds: int = 120) -> dict | None:
        if not lease_owner or lease_seconds < 1 or lease_seconds > 600:
            raise RepositoryError("invalid evaluation lease")
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(seconds=lease_seconds)).isoformat()
        with self.transaction() as db:
            row = db.execute("SELECT * FROM evaluation_jobs WHERE job_id=?", (job_id,)).fetchone()
            if not row or row["state"] in {"completed", "cancelled"} or row["attempts"] >= row["max_attempts"]:
                return None
            lease_expired = row["lease_expires_at"] is not None and row["lease_expires_at"] <= now.isoformat()
            if row["state"] == "running" and not lease_expired:
                return None
            if row["state"] not in {"queued", "failed", "running"}:
                return None
            db.execute(
                "UPDATE evaluation_jobs SET state='running',attempts=attempts+1,lease_owner=?,lease_expires_at=?,failure_category=NULL,updated_at=CURRENT_TIMESTAMP WHERE job_id=?",
                (lease_owner, expires, job_id),
            )
        return self.get_evaluation_job(job_id)

    def complete_evaluation_job(self, job_id: str, assessment_record_id: int | None) -> dict:
        with self.transaction() as db:
            cursor = db.execute(
                "UPDATE evaluation_jobs SET state='completed',assessment_record_id=?,lease_owner=NULL,lease_expires_at=NULL,failure_category=NULL,updated_at=CURRENT_TIMESTAMP WHERE job_id=? AND state='running'",
                (assessment_record_id, job_id),
            )
            if cursor.rowcount != 1:
                raise RepositoryError("evaluation job is not running")
        return self.get_evaluation_job(job_id)

    def fail_evaluation_job(self, job_id: str, category: str, retryable: bool) -> dict:
        allowed = {"worker-unavailable", "worker-timeout", "worker-transport", "learner", "cancelled", "internal"}
        if category not in allowed:
            raise RepositoryError("invalid evaluation failure category")
        with self.transaction() as db:
            row = db.execute("SELECT attempts,max_attempts,state FROM evaluation_jobs WHERE job_id=?", (job_id,)).fetchone()
            if not row or row["state"] != "running":
                raise RepositoryError("evaluation job is not running")
            terminal = not retryable or row["attempts"] >= row["max_attempts"]
            state = "cancelled" if category == "cancelled" else "failed"
            db.execute(
                "UPDATE evaluation_jobs SET state=?,max_attempts=CASE WHEN ? THEN attempts ELSE max_attempts END,lease_owner=NULL,lease_expires_at=NULL,failure_category=?,updated_at=CURRENT_TIMESTAMP WHERE job_id=?",
                (state, terminal, category, job_id),
            )
        return self.get_evaluation_job(job_id)

    def cancel_evaluation_job(self, job_id: str) -> dict:
        with self.transaction() as db:
            cursor = db.execute(
                "UPDATE evaluation_jobs SET state='cancelled',lease_owner=NULL,lease_expires_at=NULL,failure_category='cancelled',updated_at=CURRENT_TIMESTAMP WHERE job_id=? AND state IN ('queued','running','failed')",
                (job_id,),
            )
            if cursor.rowcount != 1:
                raise RepositoryError("evaluation job cannot be cancelled")
        return self.get_evaluation_job(job_id)

    def evaluation_job_summary(self) -> dict:
        rows = self._connection.execute("SELECT state,COUNT(*) count FROM evaluation_jobs GROUP BY state ORDER BY state").fetchall()
        return {"states": {row["state"]: int(row["count"]) for row in rows}, "total": sum(int(row["count"]) for row in rows)}

    def list_submissions(
        self,
        *,
        student_id: int | None = None,
        teacher_id: int | None = None,
        assignment_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        if limit < 1 or limit > 100 or offset < 0:
            raise RepositoryError("invalid pagination")
        where, values = [], []
        if student_id is not None:
            where.append("s.student_id=?"); values.append(student_id)
        if teacher_id is not None:
            where.append("a.teacher_id=?"); values.append(teacher_id)
        if assignment_id is not None:
            where.append("s.assignment_id=?"); values.append(assignment_id)
        predicate = " WHERE " + " AND ".join(where) if where else ""
        rows = self._connection.execute(
            "SELECT s.*, e.result_json FROM submissions s "
            "JOIN assignments a ON a.id=s.assignment_id "
            "LEFT JOIN evaluations e ON e.submission_id=s.id" + predicate +
            " ORDER BY s.id DESC LIMIT ? OFFSET ?",
            (*values, limit, offset),
        ).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            result_json = item.pop("result_json")
            if result_json:
                result = json.loads(result_json)
                item["evaluation"] = {
                    "status": result.get("status"),
                    "total": result.get("total"),
                    "category": result.get("category"),
                }
            else:
                item["evaluation"] = None
            results.append(item)
        return results

    def teacher_analytics(self, teacher_id: int) -> dict:
        assignment_count = int(self._connection.execute(
            "SELECT COUNT(*) count FROM assignments WHERE teacher_id=?", (teacher_id,)
        ).fetchone()["count"])
        rows = self._connection.execute(
            "SELECT s.status, e.result_json FROM submissions s "
            "JOIN assignments a ON a.id=s.assignment_id "
            "LEFT JOIN evaluations e ON e.submission_id=s.id WHERE a.teacher_id=?",
            (teacher_id,),
        ).fetchall()
        return _aggregate_evaluations(assignment_count, rows)

    def student_progress(self, student_id: int) -> dict:
        rows = self._connection.execute(
            "SELECT s.status, e.result_json FROM submissions s "
            "LEFT JOIN evaluations e ON e.submission_id=s.id WHERE s.student_id=?",
            (student_id,),
        ).fetchall()
        result = _aggregate_evaluations(None, rows)
        result["student_id"] = student_id
        return result

    def save_evaluation(self, submission_id: int, policy_version: str, result: dict) -> dict:
        with self.transaction() as db:
            db.execute("UPDATE submissions SET status=? WHERE id=?", (result["status"], submission_id))
            cursor = db.execute("INSERT OR REPLACE INTO evaluations(submission_id,policy_version,result_json) VALUES(?,?,?)", (submission_id, policy_version, json.dumps(result)))
            submission = db.execute("SELECT student_id,assignment_id FROM submissions WHERE id=?", (submission_id,)).fetchone()
            if submission:
                db.execute("INSERT INTO activity_events(user_id,kind,assignment_id,submission_id) VALUES(?,?,?,?)", (submission["student_id"], "evaluation_completed", submission["assignment_id"], submission_id))
            return {"id": cursor.lastrowid, "submission_id": submission_id, "policy_version": policy_version, "result": result}

    def list_bookmarks(self, student_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
        if limit < 1 or limit > 100 or offset < 0:
            raise RepositoryError("invalid pagination")
        rows = self._connection.execute(
            "SELECT a.* FROM bookmarks b JOIN assignments a ON a.id=b.assignment_id WHERE b.student_id=? ORDER BY b.created_at DESC LIMIT ? OFFSET ?",
            (student_id, limit, offset),
        ).fetchall()
        return [self.get_assignment(int(row["id"])) for row in rows]

    def add_bookmark(self, student_id: int, assignment_id: int) -> None:
        with self.transaction() as db:
            if not db.execute("SELECT 1 FROM assignments WHERE id=?", (assignment_id,)).fetchone():
                raise RepositoryError("assignment not found")
            cursor = db.execute("INSERT OR IGNORE INTO bookmarks(student_id,assignment_id) VALUES(?,?)", (student_id, assignment_id))
            if cursor.rowcount:
                db.execute("INSERT INTO activity_events(user_id,kind,assignment_id) VALUES(?,?,?)", (student_id, "bookmark_added", assignment_id))

    def remove_bookmark(self, student_id: int, assignment_id: int) -> None:
        with self.transaction() as db:
            db.execute("DELETE FROM bookmarks WHERE student_id=? AND assignment_id=?", (student_id, assignment_id))

    def get_draft(self, student_id: int, assignment_id: int) -> dict | None:
        row = self._connection.execute("SELECT * FROM drafts WHERE student_id=? AND assignment_id=?", (student_id, assignment_id)).fetchone()
        return dict(row) if row else None

    def save_draft(self, student_id: int, assignment_id: int, language: str, source: str) -> dict:
        with self.transaction() as db:
            assignment = db.execute("SELECT language FROM assignments WHERE id=?", (assignment_id,)).fetchone()
            if not assignment:
                raise RepositoryError("assignment not found")
            if assignment["language"] != language:
                raise RepositoryError("draft language does not match assignment")
            db.execute(
                "INSERT INTO drafts(student_id,assignment_id,language,source,updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(student_id,assignment_id) DO UPDATE SET language=excluded.language,source=excluded.source,updated_at=CURRENT_TIMESTAMP",
                (student_id, assignment_id, language, source),
            )
            db.execute("INSERT INTO activity_events(user_id,kind,assignment_id) VALUES(?,?,?)", (student_id, "draft_saved", assignment_id))
        draft = self.get_draft(student_id, assignment_id)
        assert draft is not None
        return draft

    def delete_draft(self, student_id: int, assignment_id: int) -> None:
        with self.transaction() as db:
            db.execute("DELETE FROM drafts WHERE student_id=? AND assignment_id=?", (student_id, assignment_id))

    def list_activity(self, user_id: int, limit: int = 20, offset: int = 0) -> list[dict]:
        if limit < 1 or limit > 100 or offset < 0:
            raise RepositoryError("invalid pagination")
        rows = self._connection.execute(
            "SELECT id,kind,assignment_id,submission_id,created_at FROM activity_events WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_evaluation(self, submission_id: int) -> dict | None:
        row = self._connection.execute("SELECT * FROM evaluations WHERE submission_id=?", (submission_id,)).fetchone()
        if not row: return None
        data = dict(row); data["result"] = replay_compatible_result(json.loads(data.pop("result_json"))); return data

    def schema_version(self) -> int:
        return int(self._connection.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()["version"])

    def backup_to(self, destination: str | Path) -> Path:
        target = Path(destination).resolve()
        if target.exists():
            raise RepositoryError("backup destination already exists")
        if not target.parent.exists():
            raise RepositoryError("backup destination parent does not exist")
        output = sqlite3.connect(target)
        try:
            with self._lock:
                self._connection.backup(output)
            if output.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RepositoryError("backup integrity check failed")
        finally:
            output.close()
        return target

    @classmethod
    def restore_from_backup(cls, backup: str | Path, destination: str | Path) -> "SQLiteRepository":
        source_path, target = Path(backup).resolve(), Path(destination).resolve()
        if not source_path.is_file():
            raise RepositoryError("backup file does not exist")
        if target.exists() or not target.parent.exists():
            raise RepositoryError("restore destination must be a new file in an existing directory")
        source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
        output = sqlite3.connect(target)
        try:
            if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RepositoryError("backup integrity check failed")
            source.backup(output)
        finally:
            source.close(); output.close()
        return cls(target)

    def redact_submission_source(self, submission_id: int) -> None:
        with self.transaction() as db:
            cursor = db.execute("UPDATE submissions SET source='[REDACTED]' WHERE id=?", (submission_id,))
            if cursor.rowcount != 1:
                raise RepositoryError("submission not found")

    def create_assessment_record(self, request_hash: str, status: str, versions: dict, evidence: list, result: dict) -> dict:
        if not request_hash:
            raise RepositoryError("request hash is required")
        try:
            with self.transaction() as db:
                cursor = db.execute(
                    "INSERT INTO assessment_records(request_hash,status,versions_json,evidence_json,result_json) VALUES(?,?,?,?,?)",
                    (request_hash, status, json.dumps(versions, sort_keys=True), json.dumps(evidence, sort_keys=True), json.dumps(result, sort_keys=True)),
                )
                record_id = cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            raise RepositoryError("assessment request hash already exists") from exc
        record = self.get_assessment_record(record_id)
        assert record is not None
        return record

    def get_assessment_record(self, record_id: int) -> dict | None:
        row = self._connection.execute("SELECT * FROM assessment_records WHERE id=?", (record_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["versions"] = json.loads(data.pop("versions_json"))
        data["evidence"] = json.loads(data.pop("evidence_json"))
        data["result"] = json.loads(data.pop("result_json"))
        return data

    def get_assessment_record_by_hash(self, request_hash: str) -> dict | None:
        row = self._connection.execute("SELECT id FROM assessment_records WHERE request_hash=?", (request_hash,)).fetchone()
        return self.get_assessment_record(int(row["id"])) if row else None

    def redact_expired(self, retention_days: int, now: datetime | None = None) -> dict[str, int]:
        if retention_days < 0:
            raise RepositoryError("retention_days must be nonnegative")
        current = now or datetime.now(timezone.utc)
        cutoff = (current - timedelta(days=retention_days)).strftime("%Y-%m-%d %H:%M:%S")

        def redact(value):
            if isinstance(value, dict):
                return {key: ("[REDACTED]" if key.lower() in {"source", "reference_source", "stdout", "stderr", "output"} else redact(item)) for key, item in value.items()}
            if isinstance(value, list):
                return [redact(item) for item in value]
            return value

        with self.transaction() as db:
            submissions = db.execute("UPDATE submissions SET source='[REDACTED]' WHERE created_at < ? AND source <> '[REDACTED]'", (cutoff,)).rowcount
            rows = db.execute("SELECT id,result_json FROM assessment_records WHERE created_at < ? AND redacted_at IS NULL", (cutoff,)).fetchall()
            for row in rows:
                sanitized = redact(json.loads(row["result_json"]))
                db.execute("UPDATE assessment_records SET result_json=?, redacted_at=? WHERE id=?", (json.dumps(sanitized, sort_keys=True), current.isoformat(), row["id"]))
        return {"submissions": submissions, "assessment_records": len(rows)}


def _aggregate_evaluations(assignment_count: int | None, rows: list[sqlite3.Row]) -> dict:
    statuses: dict[str, int] = {}
    categories: dict[str, int] = {}
    totals: list[float] = []
    evaluated = 0
    for row in rows:
        status_name = str(row["status"])
        result_json = row["result_json"]
        if result_json:
            evaluated += 1
            result = json.loads(result_json)
            status_name = str(result.get("status", status_name))
            if result.get("total") is not None:
                totals.append(float(result["total"]))
            if result.get("category") is not None:
                category = str(result["category"])
                categories[category] = categories.get(category, 0) + 1
        statuses[status_name] = statuses.get(status_name, 0) + 1
    output = {
        "submission_count": len(rows),
        "evaluated_count": evaluated,
        "average_score": round(sum(totals) / len(totals), 2) if totals else None,
        "status_counts": dict(sorted(statuses.items())),
        "category_counts": dict(sorted(categories.items())),
    }
    if assignment_count is not None:
        output["assignment_count"] = assignment_count
    return output
