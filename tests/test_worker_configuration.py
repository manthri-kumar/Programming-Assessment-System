import json

from backend.container_runner import ContainerRunner
from backend.runner import FailClosedRunner
from backend.worker_config import load_worker_runner, runner_from_environment


DIGEST = "sha256:" + "a" * 64


def write_config(tmp_path, digest=DIGEST):
    value = {
        "schema_version": "worker-client-v1", "endpoint": "https://127.0.0.1:9443",
        "server_name": "127.0.0.1", "image": "localhost:5000/assessment/worker", "image_digest": digest,
        "tls": {
            "ca_certificate": str((tmp_path / "ca.pem").resolve()),
            "client_certificate": str((tmp_path / "client.pem").resolve()),
            "client_private_key": str((tmp_path / "client.key").resolve()),
        },
    }
    path = tmp_path / "client.actual.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_environment_worker_configuration_defaults_fail_closed(monkeypatch):
    monkeypatch.delenv("ASSESSMENT_WORKER_CONFIG", raising=False)
    runner = runner_from_environment()
    assert isinstance(runner, FailClosedRunner) and runner.ready() is False


def test_invalid_environment_worker_configuration_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("ASSESSMENT_WORKER_CONFIG", str(write_config(tmp_path, "latest")))
    runner = runner_from_environment()
    assert isinstance(runner, FailClosedRunner) and runner.ready() is False


def test_valid_structure_loads_mtls_container_runner_but_missing_certificates_keep_it_unready(tmp_path):
    runner = load_worker_runner(write_config(tmp_path))
    assert isinstance(runner, ContainerRunner)
    assert runner.ready() is False
