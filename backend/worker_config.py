from __future__ import annotations

import json
import os
from pathlib import Path

from backend.container_runner import ContainerPolicy, ContainerRunner
from backend.runner import FailClosedRunner, SubmissionRunner
from backend.worker_http import MtlsWorkerEngine, TlsWorkerConfig


def load_worker_runner(path: Path) -> ContainerRunner:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != "worker-client-v1":
        raise ValueError("unsupported worker client configuration")
    tls = value["tls"]
    paths = [Path(tls[key]) for key in ("ca_certificate", "client_certificate", "client_private_key")]
    if not all(item.is_absolute() for item in paths):
        raise ValueError("worker TLS paths must be absolute")
    config = TlsWorkerConfig(
        endpoint=value["endpoint"], ca_certificate=paths[0], client_certificate=paths[1],
        client_private_key=paths[2], server_name=value["server_name"],
    )
    config.validate(require_files=False)
    policy = ContainerPolicy(value["image"], value["image_digest"])
    policy.validate()
    return ContainerRunner(MtlsWorkerEngine(config), policy)


def runner_from_environment() -> SubmissionRunner:
    configured = os.environ.get("ASSESSMENT_WORKER_CONFIG")
    if not configured:
        return FailClosedRunner("isolated execution worker configuration is absent")
    try:
        return load_worker_runner(Path(configured))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return FailClosedRunner("isolated execution worker configuration is invalid")
