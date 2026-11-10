from __future__ import annotations

from dataclasses import dataclass
import http.client
import json
from pathlib import Path
import ssl
from typing import Callable
from urllib.parse import urlsplit

from backend.container_runner import (
    MAX_CONTROL_BYTES,
    ContainerJob,
    ContainerPolicy,
    parse_worker_response,
    serialize_worker_job,
)
from backend.runner import RunnerUnavailable, TestRun


PROTOCOL_VERSION = "worker-policy-v1"
ConnectionFactory = Callable[[str, int, ssl.SSLContext, float], http.client.HTTPSConnection]


@dataclass(frozen=True)
class TlsWorkerConfig:
    endpoint: str
    ca_certificate: Path
    client_certificate: Path
    client_private_key: Path
    server_name: str
    connect_timeout_seconds: float = 5.0
    request_timeout_seconds: float = 125.0

    def validate(self, *, require_files: bool = True) -> tuple[str, int]:
        parsed = urlsplit(self.endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("worker endpoint must be an authenticated HTTPS origin")
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("worker endpoint must not include a path, query, or fragment")
        if not self.server_name or self.connect_timeout_seconds <= 0 or self.request_timeout_seconds <= 0:
            raise ValueError("worker TLS settings and timeouts must be positive")
        if require_files:
            for path in (self.ca_certificate, self.client_certificate, self.client_private_key):
                if not path.is_file():
                    raise ValueError("worker TLS material is unavailable")
        return parsed.hostname, parsed.port or 443

    def ssl_context(self) -> ssl.SSLContext:
        self.validate()
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(self.ca_certificate))
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.check_hostname = True
        context.load_cert_chain(str(self.client_certificate), str(self.client_private_key))
        return context


def _default_connection(host: str, port: int, context: ssl.SSLContext, timeout: float) -> http.client.HTTPSConnection:
    return http.client.HTTPSConnection(host, port, context=context, timeout=timeout)


class MtlsWorkerEngine:
    """Narrow HTTPS client for the dedicated local Linux worker.

    The client has no container-runtime access. Mutual TLS authenticates both
    ends, and every response is bounded and validated before becoming evidence.
    """

    def __init__(
        self,
        config: TlsWorkerConfig,
        connection_factory: ConnectionFactory = _default_connection,
        context_factory: Callable[[], ssl.SSLContext] | None = None,
    ) -> None:
        self.config = config
        self.connection_factory = connection_factory
        self.context_factory = context_factory or config.ssl_context

    def _request(self, method: str, path: str, body: bytes | None = None) -> tuple[int, bytes]:
        host, port = self.config.validate(require_files=False)
        if host != self.config.server_name:
            raise RunnerUnavailable("worker endpoint does not match the approved TLS server name")
        connection = self.connection_factory(host, port, self.context_factory(), self.config.request_timeout_seconds)
        headers = {"Accept": "application/json", "X-Worker-Protocol": PROTOCOL_VERSION}
        if body is not None:
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            if response.length is not None and response.length > MAX_CONTROL_BYTES:
                raise RunnerUnavailable("worker response exceeds control-channel limit")
            data = response.read(MAX_CONTROL_BYTES + 1)
            if len(data) > MAX_CONTROL_BYTES:
                raise RunnerUnavailable("worker response exceeds control-channel limit")
            return response.status, data
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            raise RunnerUnavailable("protected worker control channel is unavailable") from exc
        finally:
            connection.close()

    def ready(self, image_reference: str) -> bool:
        try:
            status, data = self._request("GET", "/v1/ready")
            payload = json.loads(data)
            return (
                status == 200
                and isinstance(payload, dict)
                and payload.get("ready") is True
                and payload.get("protocol_version") == PROTOCOL_VERSION
                and payload.get("image_reference") == image_reference
                and payload.get("toolchains_verified") is True
            )
        except (RunnerUnavailable, UnicodeError, json.JSONDecodeError, ValueError):
            return False

    def execute(self, job: ContainerJob, policy: ContainerPolicy) -> tuple[TestRun, ...]:
        body = serialize_worker_job(job)
        status, data = self._request("POST", "/v1/jobs", body)
        if status != 200:
            raise RunnerUnavailable(f"isolated worker rejected job with status {status}")
        return parse_worker_response(data, job, policy)

    def cleanup(self, job_id: str) -> None:
        if len(job_id) != 32 or any(character not in "0123456789abcdef" for character in job_id):
            raise RunnerUnavailable("invalid cleanup job id")
        status, _ = self._request("DELETE", f"/v1/jobs/{job_id}")
        if status not in {200, 204, 404}:
            raise RunnerUnavailable(f"isolated worker cleanup failed with status {status}")
