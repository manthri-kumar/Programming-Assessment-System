# Design

## Context

See `proposal.md` for motivation. Repository inspection confirms three completed changes and one active backend change at 55/69 tasks. The remaining backend tasks own real rootless-Podman worker verification, authoritative C/Java compiler evidence, independent corpus review, held-out metrics, and backend acceptance. Worker code, mTLS transport, fixed policy, image recipe, security inventory, benchmark runner, two-agent orchestration, FastAPI, SQLite, and React views exist; real image/kernel evidence and independent accuracy evidence do not.

Current feedback is deterministic and evidence-linked but mostly code/message pairs with coarse strengths and weaknesses. Reports expose useful data but still emphasize component panels and raw structured payloads. There is no institution/course model, durable lifecycle, grade-review model, rate limiting, or operator role.

## Goals / Non-Goals

**Goals:**

- Finish core grading acceptance before claiming functional correctness or university readiness.
- Strengthen evidence and feedback without changing `core-v1` semantics or the two-agent boundary.
- Make student and teacher reports educational, auditable, confidential, and accessible.
- Add institutional foundations incrementally with reversible migrations and measured infrastructure decisions.
- Produce reproducible security, research, product, and acceptance evidence.

**Non-Goals:**

- Host execution, external LLM grading, definitive semantic equivalence, plagiarism accusation, arbitrary packages/languages, or fabricated benchmarks.
- Production deployment, Kubernetes, microservice decomposition, or immediate PostgreSQL/external-queue migration.
- Privileged WSL/Linux package installation, certificate generation, registry changes, or host security changes without separate explicit authorization.
- Reimplementation of completed assignment creation, registration, frontend shell, or existing two-agent work.

## Decisions

### 1. Treat `backend-core-audit` acceptance as Phase 0

The existing 14 open tasks remain the source of truth for worker and benchmark acceptance. This change records dependencies and consumes verified outputs; it does not mirror their checkboxes. Real execution work stops at the exact missing prerequisite if rootless Podman, immutable image resolution, mTLS material, or approved policy cannot be provisioned safely.

Alternative: mark the worker complete from contract/fake-engine tests. Rejected because those tests do not establish Linux containment or real Python/C/Java behavior.

### 2. Preserve exactly two main agents and version internal contracts

Internal service results gain a versioned evidence envelope: stable stage/status/classification, diagnostics, bounded locations, evidence/lineage IDs, limitations, and duration as excluded operational metadata. Agent 1 returns the typed evaluation; Agent 2 alone turns that evaluation into feedback, graph reasoning, recommendations, and report composition.

Alternative: promote each analysis stage to an agent. Rejected because it violates the approved architecture and adds no necessary behavior.

### 3. Introduce `assessment-report-v3` additively

Version 3 adds structured overview, strengths, issues, root causes, audience-safe evidence, improvements, learning paths, and teacher explanation while retaining v2-compatible score, stages, evidence, feedback, recommendations, and trace fields during migration. The API selects the stored report version; old reports remain readable.

Alternative: mutate v2 in place. Rejected because persisted reports and frontend clients need replay compatibility.

### 4. Keep `core-v1` unchanged

Scoring continues to use structure, syntax, tests, and originality with explicit configured weights. The feedback/report layers explain criterion evidence and the originality heuristic's limits. Any future concept-aware policy requires a different policy version and separate approval.

### 5. Snapshot assignment configuration at submission/evaluation boundary

Persist a versioned assessment configuration hash/snapshot sufficient to reproduce rubric, tests, reference, graph, parser/toolchain, and policy decisions. Duplicate evaluations use an idempotency key derived from submission plus immutable configuration and return the canonical record. Sensitive snapshot fields remain protected.

Alternative: always read the latest mutable assignment. Rejected because teacher edits could change historical grades.

### 6. Add a local durable lifecycle before an external queue

After backend acceptance, use transactional SQLite job records with stable IDs, leases, bounded infrastructure retry, cancellation, and canonical evaluation linkage. Measure concurrent load and recovery. PostgreSQL and a dedicated queue become migration decisions only if thresholds are exceeded.

Alternative: introduce a broker immediately. Rejected as premature operational complexity for the academic/local milestone.

### 7. Add institutional scope through migrations, not replacement

Introduce institution, course, cohort, enrollment, course-teacher, and assignment-availability records with a default local institution/course migration for existing data. Existing teacher/student roles remain. A non-registerable, server-provisioned `operator` identity may read sanitized operational status but cannot read student source or grading secrets by default.

This operator model is security-sensitive and is part of the approval requested for this design; there is no public operator registration endpoint.

### 8. Separate agent result from human adjustment

Grade reviews store original assessment ID/score, effective adjustment, reason, owning reviewer, and timestamps in an append-only audit model. The original agent result is immutable. Student and teacher views label original and adjusted values distinctly.

### 9. Research gates are external evidence gates

Candidate corpora remain unusable for published accuracy until qualified independent reviewers sign a versioned review manifest. Held-out and ablation runners reject unapproved labels. Competitive research uses official public sources and dated citations. Human feedback usefulness uses a preregistered rubric; missing review remains BLOCKED.

### 10. Documentation is generated from evidence ledgers

`docs/product/IMPLEMENTATION_STATUS.md` is the status source using VERIFIED, PARTIALLY VERIFIED, BLOCKED, and NOT IMPLEMENTED. Architecture, agent, security, research, acceptance, competitive, requirements, and readiness documents reference commands, artifact hashes, and dated results rather than repeating unsupported claims.

## Risks / Trade-offs

- [WSL2 lacks approved rootless tooling] → Complete independent code/tests/docs, keep execution blocked, and request explicit authorization for privileged provisioning.
- [Immutable base/package candidates become unavailable] → Resolve current official manifests/snapshots on the worker and amend the approved policy before building; never invent a digest.
- [Richer feedback overstates static inference] → Require evidence references, confidence/limitation fields, contradiction tests, and confidentiality review.
- [Report v3 breaks old records] → Maintain a compatibility adapter and golden replay tests for v2.
- [Tenant migration changes local workflows] → Seed a default local scope, preserve current routes during transition, and test cross-scope denial before enabling institutional UI.
- [SQLite lifecycle cannot meet concurrency/recovery targets] → Publish measured limits and trigger the documented PostgreSQL/queue decision rather than hiding failures.
- [Independent reviewers are unavailable] → Keep accuracy and feedback-usefulness outcomes BLOCKED; publish tooling results only.
- [Scope is large] → Enforce phase gates: Phase 0 core acceptance, Phase 1 feedback/report, Phase 2 institutional foundations, Phase 3 research/readiness.

## Migration Plan

1. Reconcile status and rerun environment-independent baselines.
2. Complete or explicitly block existing worker/benchmark acceptance tasks with real evidence.
3. Add versioned evidence and report-v3 models with v2 read compatibility.
4. Implement deterministic feedback and report UI, then verify both audiences end to end.
5. Add idempotency, configuration snapshots, job lifecycle, operator status, rate limits, and audits.
6. After core acceptance, add institutional migrations and authorized workflows behind a disabled-by-default feature gate.
7. Run security, load, independent benchmark, ablation, feedback review, competitive research, and university-readiness evaluation.

Rollback preserves existing v2 reports and core-v1 results. New schema migrations must be forward-only with tested backup/restore; feature-gated institutional routes can be disabled without deleting migrated data.
