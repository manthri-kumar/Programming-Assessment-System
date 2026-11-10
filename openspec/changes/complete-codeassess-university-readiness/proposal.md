# Proposal

## Why

CodeAssess now has a verified authenticated academic workflow and exactly two deterministic top-level agents, but it cannot yet establish functional correctness without the unverified isolated Linux worker, its feedback contract is too shallow for educational use, and university adoption claims lack independently reviewed evidence and operational foundations. This change completes the evidence path from submission to auditable learning guidance while preserving fail-closed security and the existing `core-v1` scoring contract.

## What Changes

- Reconcile every active OpenSpec change and implementation claim into one evidence-backed product status, without reopening completed assignment-authoring, registration, or frontend work.
- Complete the already-approved `backend-core-audit` worker, compiler-authority, benchmark-review, and backend-acceptance gates as prerequisites; do not duplicate or prematurely check those 14 tasks.
- Strengthen `ImplementationEvaluationAgent` internal stage evidence with deterministic diagnostics, supported source locations, durations, limitations, and explicit failure classifications while retaining exactly two top-level agents.
- Expand `FeedbackAgent` into an evidence-grounded educational contract covering verified behavior, strengths, issues, root causes, source guidance, Knowledge Graph reasoning, learning paths, teacher explanations, confidence, and limitations.
- Redesign student and teacher assessment reports around actionable findings while keeping raw traces expandable, hidden tests/reference solutions confidential, null scores honest, and the existing black/charcoal/yellow identity accessible and responsive.
- Preserve `core-v1` criteria and semantics; add no silent weight redistribution, plagiarism accusation, fabricated execution result, or unreviewed score policy.
- Add idempotent evaluation requests, explicit worker/queue operational status for authorized operators, auditable human review/override foundations, and institution/course/cohort/tenant boundaries only after backend acceptance gates pass.
- Establish independent corpus review, held-out and ablation evaluation, performance/security acceptance, competitive research from public official sources, and university-readiness documentation without fabricated labels, metrics, or uniqueness claims.
- Keep local development functional and avoid Kubernetes, microservices, external LLM APIs, privileged installation, host execution, deployment, or production-data changes.

## Capabilities

### New Capabilities

- `verified-assessment-pipeline`: Observable correctness, idempotency, evidence, failure, persistence, and worker-readiness behavior for the two-agent pipeline, building on the active worker acceptance tasks.
- `evidence-grounded-feedback`: Structured student and teacher feedback derived only from Agent 1 evidence and canonical Knowledge Graph relationships.
- `assessment-reporting-experience`: Accessible student and teacher report presentation that prioritizes actionable evidence and safely handles incomplete assessment.
- `university-operations`: Incremental institution, course, cohort, tenant-isolation, human-review, queue, and operational-management foundations gated behind core backend acceptance.
- `security-privacy-assurance`: Product-level authentication, authorization, confidentiality, retention, rate-limit, audit, dependency, and worker-isolation verification.
- `research-product-validation`: Independently reviewed benchmarks, repeatability, ablations, performance evaluation, competitive research, and evidence-bounded university-readiness decisions.

### Modified Capabilities

None. No capabilities have been synchronized into `openspec/specs`; existing contracts remain in their active/completed change directories and are treated as dependencies rather than silently rewritten.

## Impact

- Backend agents, typed evidence models, orchestration, execution adapter, persistence, API contracts, authorization, observability, benchmark tooling, and worker deployment evidence.
- Student/teacher report, progress, recommendation, analytics, and authorized operational-status interfaces.
- SQLite-compatible migration foundations with a measured decision gate for PostgreSQL and durable queues; no immediate infrastructure replacement.
- Product, architecture, security, research, competitive, agent-verification, acceptance, and university-readiness documentation.
- Depends on resolving approved worker configuration on a dedicated WSL2/Linux environment and obtaining qualified independent label review; those external gates may remain BLOCKED without being represented as complete.
