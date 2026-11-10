# OpenSpec implementation evidence audit

Date: 2026-10-25  
Change: `backend-core-audit`

All 53 checked tasks were compared with current code, tests, generated contracts and documentation. The two-agent amendment supersedes older task wording that names former agent components; those components remain typed internal services. No checked task was reopened after this audit. Two previously weak evidence areas were strengthened: clean-environment discovery now succeeds in a disposable Python 3.11 environment, and SQLite concurrent-submission isolation now has an executable test.

| Checked groups | Implementation evidence | Verification conclusion |
| --- | --- | --- |
| 1.1-1.2 review/support | `review.md`, `support.md`, approval record and support boundaries | Verified after correcting stale Docker and label-review wording. |
| 2.1-2.2, 2.4-2.5 baseline/contracts | Pinned manifests, legacy goldens, frozen split, typed models | Verified. Fresh disposable installation previously collected the complete suite without importing `main.py`; current collection contains 93 tests. Independent label approval remains correctly open in 2.3. |
| 3.1, 3.5 runner foundation | `SubmissionRunner`, `FakeRunner`, `FailClosedRunner`, `ContainerRunner` policy/protocol tests | Verified as interface/fail-closed behavior only. Real containment remains open in 3.2-3.4. |
| 4.6 analysis documentation | Parser/IR documentation and cross-language fixtures | Verified for the declared static subset. Compiler authority remains open in 10.2-10.3. |
| 5.1-5.4 rubric | Legacy/core policies, finite bounds, null totals, category boundaries and heuristic wording | Verified with deterministic goldens and new isolated-compile-failure handling. |
| 6.1-6.4 graph/recommendations | Versioned graph loader, validation, traversal and evidence-linked ordering | Verified. Accuracy against independently reviewed cases remains open. |
| 7.1-7.3 deterministic pipeline | Two top-level agents, internal services, evidence lineage, repeated/no-network tests | Verified under amendment 16. Exactly two registered agent classes remain. |
| 8.1-8.2, 8.4 API/CLI | Health/readiness, bounded assessment route, stable errors, guarded CLI | Verified for local/fail-closed behavior. Real isolated example remains open in 8.3. |
| 9.2 metrics | Machine-readable metrics command and hand-computable tests | Verified and expanded with functional, concept, feedback, per-language and repeatability metrics. Empirical runs remain open. |
| 10.1, 10.4-10.5 parsing/IR | Python AST, normalized IR, bounded comparison and complexity | Verified. C/Java static parsing exists, while authoritative compilers remain open. |
| 11.1-11.6 agent contracts | Typed context/results, stage order, failure propagation, recommendations | Verified as two main agents with former components internalized. |
| 12.1-12.4 graph/persistence/logging | Validation/traversal, SQLite transactions/replay/redaction, logs | Verified. Concurrent submissions now produce unique isolated records. |
| 13.1-13.4 API/client contracts | Generated OpenAPI equality, role contracts, two-agent route and guarded CLI | Verified within current local backend scope. |
| 15.1-15.4 integration amendment | Agent audit, expected-outcome fixtures, complete report/persistence/API flow | Verified as historical capability coverage; candidate labels remain unreviewed. |
| 16.1-16.4 two-agent correction | Registry, typed handoff, trace, report v2 and regressions | Verified: `BaseAgent` protocol plus exactly `ImplementationEvaluationAgent` and `FeedbackAgent`. |
| 17.1-17.4 academic workflow | Teacher invitation, ownership, hidden data, custom rubric, histories, analytics/progress and docs | Verified by API/persistence tests and OpenAPI equality. |

## Security evidence boundary

The installed gstack CSO launcher required by the optional formal security-audit skill is unavailable, so no formal gstack security assessment is claimed. The repository was still reviewed directly under the OpenSpec workflow. Static findings are reflected in `WORKER_APPROVAL.md`: no protected control service, digest-pinned image, explicit seccomp/LSM policy, toolchain manifest or real resource/cleanup evidence exists yet.
