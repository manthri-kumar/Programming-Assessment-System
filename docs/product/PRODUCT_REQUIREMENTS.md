# CodeAssess product requirements

This document maps the approved university-readiness product contract to its OpenSpec source and evidence owner. It does not broaden implementation scope.

## Product boundary

- The system has exactly two top-level agents: `ImplementationEvaluationAgent` and `FeedbackAgent`. Parsing, execution, graph reasoning, scoring, recommendations, and report composition are internal services or infrastructure.
- Supported languages are the documented Python 3.11, C11/Clang, and Java 17 subsets. Unsupported analysis is explicit.
- `core-v1` rubric weights and grading semantics remain unchanged. New reports are additive `assessment-report-v3`; persisted v2 reports remain readable.
- Student source is never executed on the application host. The system fails closed when the approved isolated worker is unavailable.
- Candidate or unreviewed labels cannot be presented as project accuracy.

## Traceability matrix

| Product requirement | OpenSpec requirement source | Acceptance evidence owner |
| --- | --- | --- |
| Versioned typed diagnostics, evidence, limitations, confidence, timing, and source locations | `verified-assessment-pipeline` | Backend model/service tests and Agent 1 integration tests |
| Deterministic configuration snapshots and idempotent canonical assessment results | `verified-assessment-pipeline` | SQLite repository, restart, concurrency, and replay tests |
| Exact typed Agent 1 to Agent 2 handoff with only two registered agents | `verified-assessment-pipeline` | Orchestrator trace tests and `AGENT_VERIFICATION.md` |
| Evidence-grounded explanations, strengths, issues, causes, guidance, and teacher detail | `evidence-grounded-feedback` | Feedback model/composition tests and redaction tests |
| Canonical graph weaknesses, prerequisite paths, rationale, stable order, and no invented mastery | `evidence-grounded-feedback` | Knowledge Graph unit/integration tests |
| Additive report v3 with v2 replay compatibility and role-appropriate presentation | `assessment-reporting-experience` | Serialization, persistence, API, component, and browser tests |
| Transactional evaluation jobs with leases, bounded infrastructure retry, cancellation, and one canonical result | `verified-assessment-pipeline` | Repository concurrency/restart/failure tests |
| Non-registerable operator identity and sanitized operational status | `security-privacy-assurance` | Auth/API tests and configuration review |
| Role-aware rate limits, hidden-test protection, redaction, retention, backup, and recovery | `security-privacy-assurance` | Security regression tests and `SECURITY_REVIEW.md` |
| Feature-gated institution/course/cohort/enrollment scope with cross-tenant isolation | `university-operations` | Migration and authorization-matrix tests |
| Audited grade adjustment preserves original agent results | `university-operations` | Persistence/API/history tests |
| Evidence-backed teacher analytics with defined denominators and null handling | `university-operations` | Analytics unit/API tests |
| Versioned corpora, independent review, reproducible metrics, ablations, and honest limitations | `research-product-validation` | Corpus manifests, reviewer manifests, benchmark tests, and `RESEARCH_EVALUATION.md` |
| Final backend/pilot readiness is PASS only after real worker and independent-review gates | all six approved capability specifications | `END_TO_END_ACCEPTANCE.md` and user acceptance |

Frontend behavior is authorized only as needed to expose approved backend contracts. Institution/course UI remains feature-gated until its backend data and authorization acceptance criteria pass.

