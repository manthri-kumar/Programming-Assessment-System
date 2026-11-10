# Backend setup

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload
```

Set `ASSESSMENT_SECRET` to a stable private value and `ASSESSMENT_TEACHER_REGISTRATION_CODE` to a private invitation value before creating teacher accounts. The API starts without an execution worker, but `/ready` returns 503 and assessment execution fails closed until the approved pinned Linux worker and protected control channel are configured. Do not run submission binaries directly on Windows or treat local Docker availability as containment evidence.

The project-owned local worker architecture is documented in `LOCAL_LINUX_WORKER.md`. Its image digest, registry instance, certificates, seccomp hash, and observed toolchains remain unset, so execution stays fail-closed. Real-runner security tests must run only against that dedicated worker; the local suite does not probe Docker Desktop.
