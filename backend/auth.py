from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
import time


PBKDF2_ITERATIONS = 210_000


def _decode_canonical_base64url(value: str) -> bytes:
    """Decode unpadded Base64URL while rejecting alternate textual encodings."""
    if not value or "=" in value:
        raise ValueError("invalid base64url")
    padding = "=" * (-len(value) % 4)
    decoded = base64.b64decode(value + padding, altchars=b"-_", validate=True)
    canonical = base64.urlsafe_b64encode(decoded).decode().rstrip("=")
    if not hmac.compare_digest(value, canonical):
        raise ValueError("non-canonical base64url")
    return decoded


def hash_password(password: str, salt: bytes | None = None) -> str:
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(iterations))
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError):
        return False


@dataclass(frozen=True)
class TokenManager:
    secret: bytes
    ttl_seconds: int = 3600

    def issue(self, user_id: int, role: str, now: int | None = None) -> str:
        timestamp = now if now is not None else int(time.time())
        payload = {"sub": user_id, "role": role, "exp": timestamp + self.ttl_seconds}
        body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).rstrip(b"=")
        signature = hmac.new(self.secret, body, hashlib.sha256).digest()
        return f"{body.decode()}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"

    def verify(self, token: str, now: int | None = None) -> dict:
        try:
            body_text, signature_text = token.split(".", 1)
            body = body_text.encode()
            signature = _decode_canonical_base64url(signature_text)
            if not hmac.compare_digest(signature, hmac.new(self.secret, body, hashlib.sha256).digest()):
                raise ValueError("invalid token")
            payload = json.loads(_decode_canonical_base64url(body_text))
            timestamp = now if now is not None else int(time.time())
            if payload["exp"] < timestamp:
                raise ValueError("expired token")
            return payload
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid token") from exc
