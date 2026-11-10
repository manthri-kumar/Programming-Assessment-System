# CodeAssess architecture and verified boundary

```text
React student/teacher UI
  -> optional private assignment import (image/PDF -> embedded text/local OCR adapter -> teacher-confirmed draft)
  -> canonical assignment validation/persistence
  -> FastAPI authentication/authorization/rate limits
  -> transactional SQLite submission + immutable configuration + evaluation job
  -> ImplementationEvaluationAgent
       -> Python/C/Java static services
       -> approved isolated worker adapter (fail closed)
       -> core-v1 rubric and evidence
  -> FeedbackAgent
       -> Knowledge Graph reasoning and prerequisites
       -> feedback-v3 + assessment-report-v3
  -> canonical SQLite report
  -> audience-redacted API/UI
```

Exactly two top-level agents are registered. Internal services never become agents. Persisted v2 reports replay through a read adapter without rewriting their stored version.

SQLite schema 7 provides the local transactional milestone: private assignment-import metadata/events, stable jobs/leases/retries/cancellation, immutable snapshots, backups, and default-local institution/course foundations. Import source bytes remain in path-confined private project storage rather than the database or web root; provider/provenance state never enters student serializers. No measured evidence currently justifies a PostgreSQL or external-queue migration; institutional concurrency/latency thresholds remain pending, so SQLite is retained for local development rather than presented as universally sufficient.

Embedded PDF text extraction is in-process and bounded. Image/scan OCR uses a provider boundary and is unavailable by default; no cloud provider is configured. Assignment import is authoring infrastructure and does not add a top-level agent. Imported assignments enter the same immutable submission snapshot, two-agent assessment, report-v3, and audience-redaction path as manual assignments.

Observed worker environment on 2026-11-08: WSL2 Ubuntu, non-root UID 1000, kernel `6.6.87.2-microsoft-standard-WSL2`, `/usr/bin/python3` present; `podman`, `clang`, and `java` absent. Image/toolchain provenance, registry, project mTLS identities, and containment verification cannot proceed without separately authorized provisioning. The application continues to fail closed.

