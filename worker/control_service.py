#!/usr/bin/env python3
"""Mutually authenticated control service for a dedicated Linux worker host.

This service is intentionally separate from FastAPI. It may invoke rootless
Podman, while the API receives neither the Podman socket nor registry secrets.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import stat
import subprocess
from typing import Any

if __package__:
    from .entrypoint import capture_process
else:
    from entrypoint import capture_process


MAX_CONTROL_BYTES = 8 * 1024 * 1024
JOB_ID = re.compile(r"^[a-f0-9]{32}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
PROTOCOL_VERSION = "worker-policy-v1"
ALLOWED_RAW_STATUSES = {"completed", "compile_error", "runtime_error", "timeout", "resource_limit"}


def prepare_container_job(raw_job: bytes) -> tuple[dict[str, Any], bytes]:
    """Validate the protected request and remove hidden expectations."""
    if len(raw_job) > MAX_CONTROL_BYTES:
        raise ValueError("request too large")
    job = json.loads(raw_job)
    if not isinstance(job, dict) or not JOB_ID.fullmatch(job.get("id", "")) or job.get("language") not in {"python", "c", "java"}:
        raise ValueError("invalid job")
    if not isinstance(job.get("source"), str) or len(job["source"].encode("utf-8")) > 64 * 1024:
        raise ValueError("invalid source")
    tests = job.get("tests")
    if not isinstance(tests, list) or not 1 <= len(tests) <= 50:
        raise ValueError("invalid tests")
    seen: set[str] = set()
    sanitized_tests = []
    for case in tests:
        if not isinstance(case, dict):
            raise ValueError("invalid test")
        case_id, stdin, expected, weight = case.get("id"), case.get("input", ""), case.get("expected_output", ""), case.get("weight")
        if not isinstance(case_id, str) or not case_id or len(case_id) > 128 or case_id in seen:
            raise ValueError("invalid test id")
        if not isinstance(stdin, str) or len(stdin.encode("utf-8")) > 64 * 1024:
            raise ValueError("invalid test input")
        if not isinstance(expected, str) or len(expected.encode("utf-8")) > 64 * 1024:
            raise ValueError("invalid expected output")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or not 0 < float(weight) < float("inf"):
            raise ValueError("invalid test weight")
        seen.add(case_id)
        sanitized_tests.append({"id": case_id, "input": stdin})
    sanitized = {"id": job["id"], "language": job["language"], "source": job["source"], "tests": sanitized_tests}
    return job, json.dumps(sanitized, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def finalize_container_response(job: dict[str, Any], raw_response: bytes) -> bytes:
    """Compare actual output outside the untrusted job container."""
    if len(raw_response) > MAX_CONTROL_BYTES:
        raise ValueError("response too large")
    response = json.loads(raw_response)
    if not isinstance(response, dict) or response.get("job_id") != job["id"] or not isinstance(response.get("outcomes"), list):
        raise ValueError("invalid worker response")
    expected = {case["id"]: case for case in job["tests"]}
    if len(response["outcomes"]) != len(expected):
        raise ValueError("missing outcomes")
    finalized = []
    seen: set[str] = set()
    for outcome in response["outcomes"]:
        if not isinstance(outcome, dict) or outcome.get("case_id") not in expected or outcome["case_id"] in seen:
            raise ValueError("invalid outcome id")
        if outcome.get("status") not in ALLOWED_RAW_STATUSES:
            raise ValueError("invalid outcome status")
        stdout, stderr = outcome.get("stdout", ""), outcome.get("stderr", "")
        if not isinstance(stdout, str) or not isinstance(stderr, str) or len(stdout.encode()) > 64 * 1024 or len(stderr.encode()) > 64 * 1024:
            raise ValueError("invalid outcome streams")
        case = expected[outcome["case_id"]]
        status = outcome["status"]
        exit_code = outcome.get("exit_code")
        if exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
            raise ValueError("invalid outcome exit code")
        if status == "completed":
            if exit_code is None:
                raise ValueError("completed outcome requires an exit code")
            status = "runtime_error" if exit_code != 0 else ("passed" if stdout.strip() == case["expected_output"].strip() else "wrong_output")
        finalized.append({
            "case_id": outcome["case_id"], "status": status, "stdout": stdout, "stderr": stderr,
            "exit_code": outcome.get("exit_code"), "weight": float(case["weight"]),
        })
        seen.add(outcome["case_id"])
    return json.dumps({"job_id": job["id"], "outcomes": finalized}, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class ControlConfig:
    listen_host: str
    listen_port: int
    image: str
    image_digest: str
    podman: str
    seccomp_profile: Path
    seccomp_sha256: str
    ca_certificate: Path
    server_certificate: Path
    server_private_key: Path
    expected_toolchains: dict[str, str]

    @property
    def image_reference(self) -> str:
        return f"{self.image}@{self.image_digest}"

    @classmethod
    def load(cls, path: Path) -> "ControlConfig":
        value = json.loads(path.read_text(encoding="utf-8"))
        config = cls(
            listen_host=value["listen_host"],
            listen_port=int(value["listen_port"]),
            image=value["image"],
            image_digest=value["image_digest"],
            podman=value.get("podman", "podman"),
            seccomp_profile=Path(value["seccomp_profile"]),
            seccomp_sha256=value["seccomp_sha256"],
            ca_certificate=Path(value["tls"]["ca_certificate"]),
            server_certificate=Path(value["tls"]["server_certificate"]),
            server_private_key=Path(value["tls"]["server_private_key"]),
            expected_toolchains=dict(value["expected_toolchains"]),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.listen_host not in {"127.0.0.1", "::1"} or not 1 <= self.listen_port <= 65535:
            raise ValueError("local worker must bind only to a loopback address")
        if not self.image.startswith("localhost:") or not DIGEST.fullmatch(self.image_digest):
            raise ValueError("a project-local registry image with immutable digest is required")
        if not self.podman.startswith("/") or not self.seccomp_profile.is_absolute() or not re.fullmatch(r"[0-9a-f]{64}", self.seccomp_sha256):
            raise ValueError("rootless Podman and an absolute seccomp profile are required")
        if set(self.expected_toolchains) != {"python", "clang", "java"} or not all(self.expected_toolchains.values()):
            raise ValueError("all expected toolchain versions are required")
        for path in (self.seccomp_profile, self.ca_certificate, self.server_certificate, self.server_private_key):
            if not path.is_absolute() or not path.is_file():
                raise ValueError(f"required worker file is unavailable: {path}")
        if os.name == "posix" and stat.S_IMODE(self.server_private_key.stat().st_mode) & 0o077:
            raise ValueError("worker private key must not be group/world accessible")
        if hashlib.sha256(self.seccomp_profile.read_bytes()).hexdigest() != self.seccomp_sha256:
            raise ValueError("seccomp profile hash does not match approved configuration")


class PodmanEngine:
    def __init__(self, config: ControlConfig) -> None:
        self.config = config

    def container_name(self, job_id: str) -> str:
        if not JOB_ID.fullmatch(job_id):
            raise ValueError("invalid job id")
        return f"assessment-{job_id}"

    def command(self, job_id: str, language: str) -> tuple[str, ...]:
        if language not in {"python", "c", "java"}:
            raise ValueError("unsupported language")
        memory = "536870912" if language == "java" else "268435456"
        return (
            self.config.podman, "run", "--interactive", "--pull", "never", "--name", self.container_name(job_id),
            "--network", "none", "--ipc", "private", "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--security-opt", f"seccomp={self.config.seccomp_profile}",
            "--pids-limit", "64", "--memory", memory, "--memory-swap", memory, "--cpus", "1",
            "--ulimit", "nofile=64:64", "--ulimit", "fsize=16777216:16777216",
            "--tmpfs", "/work:rw,nosuid,nodev,size=16777216,mode=1770,uid=65532,gid=65532", "--init",
            "--log-driver", "none", "--stop-timeout", "1",
            "--user", "65532:65532", self.config.image_reference,
        )

    def inspect(self) -> tuple[bool, dict[str, str]]:
        runtime = subprocess.run(
            [self.config.podman, "info", "--format", "json"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=10, check=False,
        )
        try:
            info = json.loads(runtime.stdout)
            host = info["host"]
            if runtime.returncode != 0 or len(runtime.stdout) > 64 * 1024 or host["security"]["rootless"] is not True:
                return False, {}
            if host["cgroupVersion"] != "v2" or not {"cpu", "memory", "pids"} <= set(host["cgroupControllers"]):
                return False, {}
        except (KeyError, TypeError, UnicodeError, json.JSONDecodeError):
            return False, {}
        result = subprocess.run(
            [self.config.podman, "image", "inspect", self.config.image_reference, "--format", "{{json .Labels}}"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=10, check=False,
        )
        if result.returncode != 0 or len(result.stdout) > 64 * 1024:
            return False, {}
        try:
            labels = json.loads(result.stdout)
        except (UnicodeError, json.JSONDecodeError):
            return False, {}
        if not isinstance(labels, dict):
            return False, {}
        observed = {
            "python": labels.get("org.opencontainers.image.assessment.python", ""),
            "clang": labels.get("org.opencontainers.image.assessment.clang", ""),
            "java": labels.get("org.opencontainers.image.assessment.java", ""),
        }
        return observed == self.config.expected_toolchains, observed

    def execute(self, raw_job: bytes) -> tuple[int, bytes]:
        if len(raw_job) > MAX_CONTROL_BYTES:
            return 413, b'{"error":{"code":"request_too_large"}}'
        try:
            job, container_job = prepare_container_job(raw_job)
            job_id, language = job["id"], job["language"]
            command = self.command(job_id, language)
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
            return 422, b'{"error":{"code":"invalid_job"}}'
        ready, _ = self.inspect()
        if not ready:
            return 503, b'{"error":{"code":"toolchain_unverified"}}'
        try:
            # Rootless Podman needs the dedicated account's runtime directory.
            # This environment belongs to the control process, never the job.
            environment = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
            environment.update({key: os.environ[key] for key in ("HOME", "XDG_RUNTIME_DIR") if key in os.environ})
            result = capture_process(command, Path.cwd(), container_job.decode("utf-8"), 125, MAX_CONTROL_BYTES, environment=environment)
            if result["status"] == "resource_limit":
                return 502, b'{"error":{"code":"worker_response_too_large"}}'
            if result["status"] == "timeout":
                return 504, b'{"error":{"code":"worker_deadline"}}'
            if result["exit_code"] != 0:
                return 502, json.dumps({"error": {"code": "worker_failed", "exit_code": result["exit_code"]}}).encode()
            try:
                return 200, finalize_container_response(job, result["stdout"].encode("utf-8"))
            except (TypeError, ValueError, UnicodeError, json.JSONDecodeError):
                return 502, b'{"error":{"code":"invalid_worker_response"}}'
        except (OSError, subprocess.SubprocessError):
            return 503, b'{"error":{"code":"worker_unavailable"}}'
        finally:
            try:
                cleaned = self.cleanup(job_id)
            except (OSError, subprocess.SubprocessError):
                cleaned = False
            if not cleaned:
                return 503, b'{"error":{"code":"worker_cleanup_failed"}}'

    def cleanup(self, job_id: str) -> bool:
        name = self.container_name(job_id)
        result = subprocess.run(
            [self.config.podman, "rm", "--force", "--ignore", name],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, check=False,
        )
        return result.returncode == 0


class WorkerServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], engine: PodmanEngine) -> None:
        self.engine = engine
        super().__init__(address, WorkerHandler)


class WorkerHandler(BaseHTTPRequestHandler):
    server: WorkerServer

    def _authorized_protocol(self) -> bool:
        return self.headers.get("X-Worker-Protocol") == PROTOCOL_VERSION

    def _send(self, status: int, payload: bytes = b"") -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path != "/v1/ready" or not self._authorized_protocol():
            self._send(404)
            return
        ready, observed = self.server.engine.inspect()
        payload = json.dumps({
            "ready": ready, "protocol_version": PROTOCOL_VERSION,
            "image_reference": self.server.engine.config.image_reference,
            "toolchains_verified": ready, "observed_toolchains": observed,
        }, sort_keys=True, separators=(",", ":")).encode()
        self._send(200 if ready else 503, payload)

    def do_POST(self) -> None:
        if self.path != "/v1/jobs" or not self._authorized_protocol():
            self._send(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if not 0 <= length <= MAX_CONTROL_BYTES:
            self._send(413, b'{"error":{"code":"request_too_large"}}')
            return
        status, payload = self.server.engine.execute(self.rfile.read(length))
        self._send(status, payload)

    def do_DELETE(self) -> None:
        if not self.path.startswith("/v1/jobs/") or not self._authorized_protocol():
            self._send(404)
            return
        job_id = self.path.removeprefix("/v1/jobs/")
        if not JOB_ID.fullmatch(job_id):
            self._send(422)
            return
        self._send(204 if self.server.engine.cleanup(job_id) else 503)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(config: ControlConfig) -> None:
    if os.name != "posix" or os.geteuid() == 0:
        raise RuntimeError("worker control service requires a dedicated non-root Linux account")
    engine = PodmanEngine(config)
    server = WorkerServer((config.listen_host, config.listen_port), engine)
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(cafile=str(config.ca_certificate))
    context.load_cert_chain(str(config.server_certificate), str(config.server_private_key))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    serve(ControlConfig.load(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
