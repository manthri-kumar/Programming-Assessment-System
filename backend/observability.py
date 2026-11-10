from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import logging
from typing import Any


class ErrorCode(str, Enum):
    VALIDATION = "validation_error"
    UNSUPPORTED = "unsupported"
    LEARNER = "learner_error"
    LIMIT = "limit_exceeded"
    INFRASTRUCTURE = "infrastructure_unavailable"
    AUTHORIZATION = "authorization_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limited"
    INTERNAL = "internal_error"


SENSITIVE_KEYS = {"password", "password_hash", "secret", "token", "authorization", "source", "reference_source", "stdout", "stderr"}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


@dataclass(frozen=True)
class AuditEvent:
    correlation_id: str
    event: str
    status: str
    agent: str | None = None
    agent_version: str | None = None
    duration_ms: float | None = None
    evidence_ids: tuple[str, ...] = ()
    details: dict[str, Any] | None = None


class AuditLogger:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("assessment.audit")

    def serialize(self, event: AuditEvent) -> str:
        payload = {
            "correlation_id": event.correlation_id,
            "event": event.event,
            "status": event.status,
            "agent": event.agent,
            "agent_version": event.agent_version,
            "duration_ms": event.duration_ms,
            "evidence_ids": list(event.evidence_ids)[:100],
            "details": redact(event.details or {}),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def emit(self, event: AuditEvent) -> None:
        self.logger.info(self.serialize(event))
