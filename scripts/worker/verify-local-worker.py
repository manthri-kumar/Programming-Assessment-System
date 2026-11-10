#!/usr/bin/env python3
"""Real-worker smoke/security checks. Run only against the approved Linux worker."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
import uuid

from backend.container_runner import ContainerJob, ContainerPolicy
from backend.runner import RunnerUnavailable
from backend.worker_http import MtlsWorkerEngine, TlsWorkerConfig


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    value = json.loads(args.config.read_text(encoding="utf-8"))
    policy = ContainerPolicy(value["image"], value["image_digest"])
    tls = value["tls"]
    engine = MtlsWorkerEngine(TlsWorkerConfig(
        endpoint=value["endpoint"], ca_certificate=Path(tls["ca_certificate"]),
        client_certificate=Path(tls["client_certificate"]), client_private_key=Path(tls["client_private_key"]),
        server_name=value["server_name"],
    ))
    if not engine.ready(policy.image_reference):
        raise SystemExit("approved worker is not ready; no submissions were executed")

    smoke_cases = (
        ("python", "print(input())\n", "hello\n", "hello\n"),
        ("c", "#include <stdio.h>\nint main(void){char s[32]; if(fgets(s,sizeof s,stdin)) fputs(s,stdout);}\n", "hello\n", "hello\n"),
        ("java", "class Main { public static void main(String[] a) throws Exception { System.out.print(new String(System.in.readAllBytes())); } }\n", "hello\n", "hello\n"),
    )
    def execute(name, language, source, expected_status, stdin="", expected=""):
        job = ContainerJob(uuid.uuid4().hex, language, source, "", ({"id": name, "input": stdin, "expected_output": expected, "weight": 1.0},))
        try:
            outcome = engine.execute(job, policy)[0]
            return {"name": name, "language": language, "status": outcome.status.value, "expected_status": expected_status, "passed": outcome.status.value == expected_status}
        finally:
            engine.cleanup(job.id)

    evidence = [execute(f"{language}-echo", language, source, "passed", stdin, expected) for language, source, stdin, expected in smoke_cases]
    evidence.extend([
        execute("python-compile", "python", "def broken(:\n", "compile_error"),
        execute("c-compile", "c", "int main( { return 0; }\n", "compile_error"),
        execute("java-compile", "java", "class Main { public static void main(String[] a) { }\n", "compile_error"),
        execute("runtime-error", "python", "raise SystemExit(7)\n", "runtime_error"),
        execute("crash-after-output", "python", "print('expected')\nraise SystemExit(7)\n", "runtime_error", expected="expected\n"),
        execute("timeout", "python", "while True: pass\n", "timeout"),
        execute("timeout-with-child", "python", "import subprocess,sys\nsubprocess.Popen([sys.executable,'-c','while True: pass'])\nwhile True: pass\n", "timeout"),
        execute("output-limit", "python", "print('x' * 70000)\n", "resource_limit"),
        execute("memory-limit", "python", "x=[]\nwhile True: x.append(bytearray(1024*1024))\n", "resource_limit"),
        execute("process-limit", "python", "import os\nwhile True: os.fork()\n", "resource_limit"),
        execute("scratch-limit", "python", "open('/work/fill','wb').write(b'x' * (20*1024*1024))\n", "resource_limit"),
        execute("network-denied", "python", "import socket\nsocket.create_connection(('1.1.1.1',80),1)\n", "runtime_error"),
        execute("host-file-denied", "python", "open('/etc/shadow').read()\n", "runtime_error"),
        execute("outer-whitespace", "python", "print('  expected  ')\n", "passed", expected="expected\n"),
        execute("internal-whitespace", "python", "print('a  b')\n", "wrong_output", expected="a b\n"),
    ])

    # DELETE is the protocol's cancellation operation. The request must stop
    # the opaque job container; a completed result after cancellation fails
    # this check. A final idempotent cleanup is still required.
    cancellation_job = ContainerJob(uuid.uuid4().hex, "python", "while True: pass\n", "", ({"id": "cancel", "input": "", "expected_output": "", "weight": 1.0},))
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(engine.execute, cancellation_job, policy)
        time.sleep(0.25)
        engine.cleanup(cancellation_job.id)
        try:
            pending.result(timeout=10)
            cancellation_passed = False
            cancellation_observed = "completed"
        except RunnerUnavailable:
            cancellation_passed = True
            cancellation_observed = "worker-stopped"
        except Exception as exc:
            cancellation_passed = False
            cancellation_observed = type(exc).__name__
        finally:
            engine.cleanup(cancellation_job.id)
    evidence.append({"name": "cancellation", "language": "python", "status": cancellation_observed, "expected_status": "worker-stopped", "passed": cancellation_passed})

    concurrent = list(smoke_cases)
    with ThreadPoolExecutor(max_workers=3) as pool:
        concurrent_results = list(pool.map(lambda item: execute(f"concurrent-{item[0]}", item[0], item[1], "passed", item[2], item[3]), concurrent))
    evidence.extend(concurrent_results)

    # Repeated execution with fresh opaque job IDs exercises stale-container and
    # workspace cleanup without asking the API process to inspect runtime state.
    evidence.append(execute("cleanup-repeat-1", "python", "print('first')\n", "passed", expected="first\n"))
    evidence.append(execute("cleanup-repeat-2", "python", "print('second')\n", "passed", expected="second\n"))

    report = {"image_reference": policy.image_reference, "results": evidence, "passed": all(item["passed"] for item in evidence)}
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
