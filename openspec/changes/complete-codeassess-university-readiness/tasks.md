# Tasks

## 1. Reconciliation and Baseline

- [x] 1.1 Audit every active/completed OpenSpec ledger against code, tests, migrations, APIs, and current documents; update `docs/product/IMPLEMENTATION_STATUS.md` with VERIFIED, PARTIALLY VERIFIED, BLOCKED, and NOT IMPLEMENTED evidence and verify no unchecked prerequisite is reported complete.
- [x] 1.2 Write `docs/product/PRODUCT_REQUIREMENTS.md` from the approved specifications, preserving exactly two top-level agents and existing supported-language/core-v1 boundaries; verify every product requirement links to an OpenSpec requirement and acceptance evidence owner.
- [x] 1.3 Rerun the environment-independent backend/frontend/type/lint/build/OpenSpec baselines before implementation, record exact counts and failures in the status document, and verify historical results are not reused as current proof.

## 2. Phase 0 Core Acceptance Dependency

- [x] 2.1 Reconcile the 14 unchecked `backend-core-audit` tasks with current worker/corpus state and verify each remains owned by that ledger without duplicate completion claims.
- [ ] 2.2 On the approved dedicated WSL2/Linux worker, resolve official immutable base/snapshot/package provenance and record observed digests/versions; verify no digest is invented and stop for explicit authorization if privileged provisioning is required.
- [ ] 2.3 Build and inspect the rootless worker, configure project-owned registry/mTLS/policy identities, and run the mandatory real Python 3.11/C11/Java 17 execution and containment suite; verify the corresponding `backend-core-audit` worker/compiler tasks before checking this task.
- [ ] 2.4 Obtain qualified independent corpus review and run the held-out benchmark twice; verify review manifests, hashes, repeatability, exclusions, and actual metrics before checking the corresponding backend acceptance tasks.
- [ ] 2.5 Reproduce backend setup from a clean environment and update `docs/product/ARCHITECTURE.md` with observed worker/control/data flow and remaining limits; verify backend acceptance is PASS only if all mandatory real-worker and review gates pass.

## 3. Versioned Evidence and ImplementationEvaluationAgent

- [x] 3.1 Define versioned typed stage, diagnostic, source-location, classification, limitation, confidence, and operational-timing models; verify schema/serialization tests reject invalid or unbounded evidence.
- [x] 3.2 Update Python, C, and Java parsing/analysis services to emit supported locations and explicit unsupported/limit classifications without execution; verify correct, partial, incorrect, syntax, alternate-algorithm, malformed, and empty fixtures per language.
- [ ] 3.3 Extend secure execution evidence for compilation, runtime, timeout, resource, output, and worker failures while keeping hidden inputs/expected outputs outside student-visible evidence; verify real-worker and redaction tests.
- [x] 3.4 Preserve core-v1 scoring semantics and attach criterion evidence/limitations to every component; verify null handling, no redistribution, custom weights, deterministic totals, policy persistence, and originality disclaimer regressions.
- [x] 3.5 Add immutable assessment-configuration snapshots and deterministic idempotency keys so assignment edits cannot change historical evaluations; verify duplicate requests and restart replay return one canonical result.
- [x] 3.6 Expand two-agent integration tests to prove Agent 1 processes actual submitted source and Agent 2 receives the exact typed result; update `docs/product/AGENT_VERIFICATION.md` with evidence and verify only two main agents are registered/traced.

## 4. Evidence-Grounded FeedbackAgent

- [x] 4.1 Define `feedback-v3` typed overall explanation, strength, issue, root-cause, guidance, teacher-explanation, confidence, and limitation models; verify every item requires valid evidence references and canonical concept IDs where applicable.
- [x] 4.2 Implement evidence-to-feedback composition for syntax, functional, structural, complexity, conceptual, contradictory, and unavailable states; verify no generic or unsupported issue is emitted.
- [x] 4.3 Implement supported source-level guidance and actionable correction steps without revealing hidden tests or reference source; verify student/teacher redaction and location-absent cases.
- [x] 4.4 Strengthen Knowledge Graph weak-concept/prerequisite reasoning, recommendation deduplication, selection rationale, and learning paths; verify canonical nodes, stable order, evidence paths, unknown states, and no invented mastery.
- [x] 4.5 Verify deterministic feedback equality and provisional static feedback when execution is unavailable; update `docs/product/AGENT_VERIFICATION.md` with positive, negative, contradiction, and limitation cases.

## 5. Assessment Report and Learning Experience

- [x] 5.1 Add additive `assessment-report-v3` composition and v2 compatibility/replay adapter; verify persisted v2 reports remain readable and v3 reports preserve core score/evidence fields.
- [x] 5.2 Redesign the student report around overview, verified status, rubric, strengths, issues, causes, graph insights, actions, learning path, source, and expandable technical evidence; verify empty panels are omitted and unavailable execution remains prominent.
- [x] 5.3 Add the authorized teacher evidence/review presentation without exposing protected data to other users; verify student, owning-teacher, other-teacher, and other-student API/browser cases.
- [x] 5.4 Update dashboard, submissions, progress, recommendations, and learning-path views to use only persisted evidence-backed metrics; verify null scores, incomplete assessments, concept status, and recommendations never fabricate progress.
- [x] 5.5 Run component/accessibility/responsive/browser regression suites on desktop, tablet, and mobile and document verified report behavior in `docs/product/END_TO_END_ACCEPTANCE.md`.

## 6. Reliability, Security, and Privacy

- [x] 6.1 Implement a transactional local evaluation lifecycle with stable job IDs, leases, states, cancellation, bounded infrastructure retry, and canonical result linkage; verify learner failures are not retried and concurrent requests do not duplicate reports.
- [x] 6.2 Add a non-registerable server-provisioned operator identity and sanitized worker/queue status contract; verify students/teachers cannot obtain privileged configuration and operators cannot read grading secrets by default.
- [x] 6.3 Add configurable role-aware rate limits for authentication, submission, and evaluation endpoints; verify stable responses, bounded retry metadata, and no authorization bypass.
- [x] 6.4 Audit authentication, ownership, hidden data, logs, secrets, dependencies, retention, cancellation, and worker transport; fix confirmed defects and verify security regression tests without weakening controls.
- [x] 6.5 Define/test retention, redaction, backup, restore, and recovery procedures for application and worker metadata; verify sensitive content is minimized and recovery preserves ownership and immutable results.
- [x] 6.6 Publish `docs/product/SECURITY_REVIEW.md` separating code review, automated tests, real worker tests, dependency results, unresolved risks, and dates; verify every claim has reproducible evidence or a non-VERIFIED status.

## 7. Institutional Foundations

- [x] 7.1 Add migration-safe institution, course, cohort, enrollment, course-teacher, and availability models with default local scope for existing data; verify upgrade/restart/rollback documentation and no data loss.
- [ ] 7.2 Enforce institution/course/enrollment scope across assignment, submission, report, analytics, and review APIs; verify a complete cross-tenant authorization matrix.
- [ ] 7.3 Add authorized course/cohort management and enrollment contracts without public operator/admin registration; verify role and ownership tests and preserve current local workflows.
- [ ] 7.4 Implement audited grade review/adjustment that preserves original agent results separately; verify reviewer identity, reason, history, effective-grade display, and unauthorized denial.
- [ ] 7.5 Add evidence-backed teacher analytics for completion, evaluated/unavailable counts, valid averages, missed concepts, concept performance, and progress over time; verify definitions, denominators, null handling, and tenant scope.
- [ ] 7.6 Measure SQLite lifecycle concurrency, latency, recovery, and data-isolation thresholds; update `docs/product/ARCHITECTURE.md` with an evidence-based PostgreSQL/durable-queue decision while keeping local development functional.

## 8. Research and Product Validation

- [ ] 8.1 Expand versioned Python/C/Java candidate corpora across correct, partial, incorrect, syntax, runtime, timeout, boundary, alternative, and conceptual cases; verify hashes, provenance, split leakage checks, and pending-review status.
- [ ] 8.2 Prepare and execute qualified independent label review plus a preregistered feedback-usefulness review; verify reviewer manifests and keep metrics BLOCKED until real approvals exist.
- [x] 8.3 Extend benchmark reporting for per-language grading, concepts, recommendations, feedback grounding, latency, throughput, and repeatability; verify calculations with hand-computable tests before approved held-out runs.
- [x] 8.4 Implement fixed ablation configurations for functional tests, static analysis, concept analysis, graph reasoning, and feedback composition; verify identical held-out labels and recorded version/configuration hashes.
- [x] 8.5 Research Gradescope, PrairieLearn, CodeGrade, Moodle CodeRunner, HackerRank, CodeSignal, and relevant university tools using official public sources; publish dated citations and fair comparisons in `docs/product/COMPETITIVE_RESEARCH.md` without unsupported uniqueness claims.
- [ ] 8.6 Publish `docs/product/RESEARCH_EVALUATION.md` with actual approved metrics, failures, exclusions, ablations, human-review results, and limitations; verify no candidate/fake-runner result is presented as project accuracy.

## 9. Final Acceptance and Readiness

- [ ] 9.1 Run real end-to-end acceptance for correct, partial, incorrect, syntax, runtime, timeout, worker-unavailable, duplicate, unauthorized, hidden-data, restart, and concurrent cases through UI, API, both agents, worker, persistence, and dashboards; record exact results in `docs/product/END_TO_END_ACCEPTANCE.md`.
- [ ] 9.2 Run complete backend, frontend, Playwright, typecheck, lint, build, OpenSpec, worker-security, load, migration, backup/restore, and dependency checks; verify exact pass/fail/blocked counts are recorded without skipped mandatory gates.
- [ ] 9.3 Reconcile `docs/product/IMPLEMENTATION_STATUS.md` and all required product documents against final evidence and verify duplicate/outdated statements are removed or explicitly superseded.
- [ ] 9.4 Publish `docs/product/UNIVERSITY_READINESS.md` with architecture, verified features, defects/fixes, agent/worker/scoring/feedback/graph/database/security/research evidence, blockers, startup commands, and manual acceptance workflow.
- [ ] 9.5 Classify backend and pilot readiness as PASS, FAIL, or BLOCKED from mandatory gates; verify real execution and independent review are required for PASS and obtain user acceptance before sync/archive.

## Workflow follow-up

- Sync and archive completed changes only after explicit user acceptance and all mandatory evidence gates are satisfied.
- Deployment and production-data migration require a separate reviewed change and explicit authorization.
