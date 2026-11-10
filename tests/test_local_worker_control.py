import json
import hashlib
import os
from pathlib import Path
import ssl

import pytest

from backend.container_runner import ContainerJob, ContainerPolicy
from backend.runner import RunStatus, RunnerUnavailable
from backend.worker_http import MtlsWorkerEngine, TlsWorkerConfig
from worker.control_service import ControlConfig, PodmanEngine, finalize_container_response, prepare_container_job


DIGEST = "sha256:" + "a" * 64


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self.body = body
        self.length = len(body)

    def read(self, amount):
        return self.body[:amount]


class FakeConnection:
    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    def request(self, method, path, body=None, headers=None):
        self.requests.append((method, path, body, headers))

    def getresponse(self):
        return self.responses.pop(0)

    def close(self):
        pass


def client_config(tmp_path: Path) -> TlsWorkerConfig:
    return TlsWorkerConfig(
        "https://127.0.0.1:9443", tmp_path / "ca.pem", tmp_path / "client.pem",
        tmp_path / "client.key", "127.0.0.1",
    )


def test_tls_worker_configuration_is_fail_closed(tmp_path):
    config = client_config(tmp_path)
    with pytest.raises(ValueError, match="TLS material"):
        config.validate()
    insecure = TlsWorkerConfig("http://127.0.0.1:9443", tmp_path / "ca", tmp_path / "cert", tmp_path / "key", "127.0.0.1")
    with pytest.raises(ValueError, match="HTTPS"):
        insecure.validate(require_files=False)


def test_mtls_engine_validates_readiness_response_and_worker_outcomes(tmp_path):
    image = "localhost:5000/assessment/worker"
    reference = f"{image}@{DIGEST}"
    ready = json.dumps({"ready": True, "protocol_version": "worker-policy-v1", "image_reference": reference, "toolchains_verified": True}).encode()
    outcome = json.dumps({"job_id": "a" * 32, "outcomes": [{"case_id": "case", "status": "passed", "stdout": "1\n", "stderr": "", "exit_code": 0, "weight": 1.0}]}).encode()
    connection = FakeConnection([FakeResponse(200, ready), FakeResponse(200, outcome), FakeResponse(204, b"")])
    engine = MtlsWorkerEngine(
        client_config(tmp_path), connection_factory=lambda *args: connection,
        context_factory=lambda: ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
    )
    assert engine.ready(reference)
    job = ContainerJob("a" * 32, "python", "print(1)", "", ({"id": "case", "input": "", "expected_output": "1", "weight": 1.0},))
    result = engine.execute(job, ContainerPolicy(image, DIGEST))
    assert result[0].status is RunStatus.PASSED
    engine.cleanup(job.id)
    assert [request[:2] for request in connection.requests] == [("GET", "/v1/ready"), ("POST", "/v1/jobs"), ("DELETE", f"/v1/jobs/{job.id}")]
    assert all(request[3]["X-Worker-Protocol"] == "worker-policy-v1" for request in connection.requests)


def test_mtls_engine_rejects_endpoint_name_mismatch(tmp_path):
    config = TlsWorkerConfig("https://127.0.0.1:9443", tmp_path / "ca", tmp_path / "cert", tmp_path / "key", "worker.local")
    engine = MtlsWorkerEngine(config, context_factory=lambda: ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
    with pytest.raises(RunnerUnavailable, match="server name"):
        engine.execute(ContainerJob("a" * 32, "python", "", "", ()), ContainerPolicy("localhost:5000/assessment/worker", DIGEST))


def test_control_configuration_and_podman_command_are_server_owned(tmp_path):
    files = [tmp_path / name for name in ("seccomp.json", "ca.pem", "server.pem", "server.key")]
    for path in files:
        path.write_text("fixture", encoding="utf-8")
    os.chmod(files[3], 0o600)
    config = ControlConfig(
        "127.0.0.1", 9443, "localhost:5000/assessment/worker", DIGEST, "/usr/bin/podman",
        files[0], hashlib.sha256(files[0].read_bytes()).hexdigest(), files[1], files[2], files[3],
        {"python": "3.11.2-6+deb12u9", "clang": "1:14.0.6-12", "java": "17.0.21+9-1~deb12u1"},
    )
    config.validate()
    command = PodmanEngine(config).command("a" * 32, "java")
    joined = " ".join(str(value) for value in command)
    for required in ("--pull never", "--network none", "--ipc private", "--read-only", "--cap-drop ALL", "no-new-privileges", "--pids-limit 64", "--memory 536870912", "--memory-swap 536870912", "--cpus 1", "nofile=64:64", "fsize=16777216:16777216", "mode=1770,uid=65532,gid=65532", "--log-driver none", "--user 65532:65532", f"{config.image}@{DIGEST}"):
        assert required in joined
    assert "--volume" not in command and "--mount" not in command and "docker.sock" not in joined


def test_hidden_expectations_never_enter_the_job_container():
    protected = json.dumps({
        "id": "a" * 32, "language": "python", "source": "print(input())",
        "tests": [{"id": "hidden", "input": "hello\n", "expected_output": "secret\n", "weight": 2.0}],
    }).encode()
    job, container_payload = prepare_container_job(protected)
    assert b"secret" not in container_payload and b"expected_output" not in container_payload and b"weight" not in container_payload
    raw = json.dumps({"job_id": "a" * 32, "outcomes": [{"case_id": "hidden", "status": "completed", "stdout": "secret\n", "stderr": "", "exit_code": 0}]}).encode()
    final = json.loads(finalize_container_response(job, raw))
    assert final["outcomes"][0]["status"] == "passed"
    assert final["outcomes"][0]["weight"] == 2.0


def test_control_service_classifies_wrong_output_and_rejects_unexpected_cases():
    protected = json.dumps({
        "id": "b" * 32, "language": "c", "source": "int main(void){return 0;}",
        "tests": [{"id": "hidden", "input": "", "expected_output": "expected", "weight": 1}],
    }).encode()
    job, _ = prepare_container_job(protected)
    raw = json.dumps({"job_id": "b" * 32, "outcomes": [{"case_id": "hidden", "status": "completed", "stdout": "actual", "stderr": "", "exit_code": 0}]}).encode()
    assert json.loads(finalize_container_response(job, raw))["outcomes"][0]["status"] == "wrong_output"
    altered = raw.replace(b'"hidden"', b'"other"')
    with pytest.raises(ValueError, match="outcome id"):
        finalize_container_response(job, altered)


def test_checked_in_worker_configuration_cannot_enable_execution():
    root = Path(__file__).parents[1]
    control = json.loads((root / "worker" / "control.example.json").read_text(encoding="utf-8"))
    client = json.loads((root / "worker" / "client.example.json").read_text(encoding="utf-8"))
    toolchains = json.loads((root / "worker" / "toolchain-policy.json").read_text(encoding="utf-8"))
    assert control["image_digest"].startswith("REPLACE_")
    assert client["image_digest"].startswith("REPLACE_")
    assert toolchains["base_image_digest"] is None
    assert toolchains["verification_status"].endswith("not-yet-built-or-inspected")
