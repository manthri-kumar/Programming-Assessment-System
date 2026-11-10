# Design

## Context

See `proposal.md` for motivation and `audit.md` for the complete source inventory. There is no service to extend: the current entry point compiles and executes C on import. Preserve useful functions behind adapters and add characterization coverage before changing behavior. All choices below are proposed defaults for review, not implemented capabilities.

## Goals / Non-Goals

**Goals:** a traceable backend pipeline with typed evidence, deterministic agents, explicit language support, isolated execution, transparent score policies, graph-based learning feedback, and reproducible validation.

**Non-Goals:** frontend, external LLMs, autonomous model reasoning, universal semantic equivalence, definitive plagiarism detection, arbitrary language/package support, public multi-tenant hosting, authentication/billing, or incidental deletion of generated files. Initial service is local-only; public deployment requires a separate reviewed threat model and access-control change.

## Decisions

### 1. Add a thin service around a testable domain pipeline

Proposed layout: `backend/api/`, `backend/models/`, `backend/agents/`, `backend/languages/`, `backend/runner/`, `backend/scoring/`, `backend/knowledge/`, `tests/`, `data/concepts/`, `docs/backend/`. Preserve existing modules through compatibility adapters; only replace internals with characterized evidence. `main.py` becomes a guarded CLI; plotting remains opt-in CLI functionality. FastAPI provides validation and generated OpenAPI; it must not contain grading logic. A monolithic route would hide evidence boundaries and make scoring tests difficult.

Proposed initial API:

- `GET /health`: process liveness, no execution.
- `GET /ready`: toolchain, policy, graph and sandbox readiness plus supported language versions; 503 if required components unavailable.
- `POST /assessments`: synchronous, bounded, one job at a time initially. 200 for a structured assessment outcome (including student syntax/test failures); 422 for invalid payload or unsupported language; 503 for unavailable runner/toolchain; 500 for unexpected internal errors with sanitized details. No asynchronous job persistence is promised.

Request: language enum `python|c|java`, source, reference source, nonempty weighted tests (`id`, input, expected stdout, positive finite weight, concept IDs), policy version. Source fields <=64 KiB UTF-8 each; <=50 tests; input and expected output <=64 KiB per test; request <=8 MiB. No arbitrary host paths, shell strings, compiler flags, packages or client-selected sandbox limits. Treat reference source as untrusted too. Reject malformed, missing, duplicate test IDs, invalid graph IDs and unsupported policies before execution.

Result: schema/policy/parser/toolchain/graph versions; overall status; syntax/structure/tests/originality component records with status, nullable score, evidence IDs and diagnostics; per-case outcomes; nullable total/category; feedback; recommendations; execution metadata. Stable evidence IDs derive from content and configuration hashes, not wall clock. Operational metadata (duration/request ID) is excluded from deterministic equality checks. Generated OpenAPI is the single API contract artifact; Postman duplication is unnecessary for this repository at this stage.

### 2. Expose exactly two deterministic agents

`BaseAgent` defines the typed top-level contract. Exactly two implementations are discoverable and orchestrated: `ImplementationEvaluationAgent.run(context)` coordinates preprocessing, language syntax analysis, concept detection, structural comparison, complexity analysis, approved secure functional execution, rubric scoring, evidence collection, and limitations; `FeedbackAgent.run(context, evaluation)` consumes that typed evaluation and coordinates Knowledge Graph reasoning, prerequisite traversal, strengths/weaknesses, deterministic feedback, learning recommendations, and final report composition. The orchestrator always invokes Agent 1 before Agent 2.

All other components are internal services with typed results. They are not independently registered, orchestrated, or described as agents in runtime traces. This keeps the two-agent project model while preserving testable separation of parsing, comparison, execution, scoring, graph traversal, recommendation, and reporting logic. No networking/model endpoint or API key is involved.

### 3. Use language-specific parsers and a shared structural representation

Initial pinned support target: Python 3.11 standard-library programs; C11 single translation unit with standard headers; Java 17 single `Main.java`, class `Main`, standard library. No pip/Maven dependencies, JNI, arbitrary compiler options or multi-file projects. Actual patch versions and image digests must be locked in implementation and reported. Windows development uses Linux sandbox workers; native Windows execution is not a fallback.

Use Python `ast` plus compile-only validation; tree-sitter C/Java grammars provide static parsing, Clang provides authoritative C11 diagnostics, and the JDK compiler provides authoritative Java 17 diagnostics. Parser suitability is verified against labeled fixtures before adoption. Parse errors never silently fall back to regex. Compilers and parser workers operate within bounded worker execution. Normalize into functions, loops, branches, calls and operators; ignore comments, whitespace and identifier renaming for structural matching. Keep names/literals in diagnostic evidence where useful. Compare ordered normalized tree edit distance: `100 * max(0, 1 - distance / max(node_count_a, node_count_b, 1))`, with unit insert/delete/rename costs. Cap AST at 10,000 nodes and structural comparison at 100,000 node-pair operations; exceedance returns `analysis_limit`, not an invented score. Pin normalization and metric version. Matching structure is evidence, not proof of equivalent behavior; tests establish only tested behavior.

### 4. Isolate compilation as well as execution

Use a dedicated runner process backed by Linux containers in a dedicated VM/worker boundary. API input cannot control container commands or access Docker credentials/socket. The runtime user is unprivileged, capabilities dropped, no-new-privileges and a restrictive syscall profile; network disabled; read-only root; bounded tmpfs scratch; no host bind mounts, host secrets, devices or inherited credentials. Source enters via controlled transfer. Per-request workspaces are unique and disposed of; artifacts are never reused between submissions. Hardened container execution does not prove resistance to every kernel exploit; production exposure remains out of scope.

For the approved local development/demonstration deployment, the dedicated Linux worker uses project-owned rootless Podman and a project-owned local registry. A separate control service owns the Podman socket; FastAPI reaches it only through a fixed HTTPS endpoint authenticated with project-owned mutual TLS. The API identity may submit, query, and cancel its own opaque jobs only. The control service accepts the bounded `worker-policy-v1` protocol, chooses the immutable image and all runtime arguments from local configuration, streams one job over standard input, validates the bounded response, force-removes the container, and reports cleanup evidence. Certificates, private keys, registry storage, runtime state, and submitted workspaces are excluded from source control. A checked-in example configuration remains fail-closed until exact certificate paths and a verified final image digest are supplied.

Server policy: compile <=10 seconds, each test <=2 seconds, analysis <=5 seconds, aggregate job <=120 seconds; <=256 MiB memory for C/Python and <=512 MiB for Java (JVM heap <=256 MiB), <=64 processes, <=16 MiB writable scratch, <=64 KiB per stdout/stderr stream. Bound aggregate capture and enforce limits while streaming; killing only the parent is insufficient. Always terminate the whole process tree/container and clean up on success, timeout, cancellation and internal failure. Bound compiler diagnostics too. A crashed program fails even if stdout matched. Record timeout/output/memory/resource outcomes separately from wrong output and syntax errors. Missing isolation means no compilation or submission execution. A plain subprocess timeout or virtualenv is insufficient. Provide a fake runner for unit tests and mandatory real-runner security acceptance tests; fakes cannot establish containment.

### 5. Preserve policy arithmetic while separating evidence quality

`legacy-v1` characterizes the original component formulas, thresholds and feedback using fixed inputs and stubbed process outcomes; this is a regression baseline, not a sanctioned host runner. `core-v1` retains weights structure .20, syntax .40, tests .20, originality .20 and Good >=75 / Average >=50. Proposed improvements are explicit: parsed structural metric; syntax 100 on valid compilation, 0 on student syntax failure; weighted tests retain outer `.strip()` equality; originality retains raw-text dissimilarity but is labeled as a heuristic with no misconduct verdict. This preserves the existing rubric's influence while exposing its limitations. Future reweighting requires a separate reviewed policy and benchmark comparison.

Finite scores are constrained to [0,100]; calculate totals from unrounded values, round once for display to two decimals, and classify the unrounded total. Never silently renormalize around missing components. Syntax failure produces syntax=0, unavailable structure/tests, total/category=null and `invalid_submission`. Operational failure produces `incomplete`, null total/category and explicit reason. A complete run with failed test cases is still gradable. No tests or nonpositive/nonfinite weights are invalid input, not zero correctness.

### 6. Implement an actual graph with explainable traversal

Versioned local JSON nodes have stable concept ID, label and learning guidance; typed directed edges include `requires` and `related-to`. Validate unique IDs, existing endpoints and an acyclic prerequisite subgraph on load. Initial concepts cover input/output, arithmetic, conditionals, zero-division guards, loops and functions. A graph is represented by nodes and typed adjacency and is traversed; a score bar chart is not a substitute. Diagnostics and task/test metadata associate evidence with concepts; no whole-program mastery is inferred from a single failure. Recommend failed concepts and unmet prerequisite ancestors in prerequisite-first topological order, breaking ties by concept ID. Unknown mastery is explicit; successful task evidence can satisfy prerequisites only under a documented evidence rule. Every recommendation includes the triggering evidence, path and graph version. Missing graph invalidates readiness rather than producing generic invented recommendations.

### 7. Separate regression pass rate from empirical grading accuracy

Introduce pytest characterization/unit/integration/security suites alongside versioned labeled corpus JSON and source fixtures. Each case specifies language, task, source hash, expected syntax status, structural relation, test outcomes, score/category, diagnostic concept IDs and recommendation ordering. Every spec scenario receives a stable test mapping. Ground truth is reviewed independently of the grader and then frozen; corrections create a new corpus version. Include equivalent rewrites, malformed code, comments/strings containing keywords, runtime crashes, output floods, loops, process attempts, filesystem/network attempts, policy boundaries and graph cycles.

Split tuning/development cases from a locked held-out evaluation set before tuning scoring or normalization. Report corpus/environment hashes, seeds, exact command, counts, exclusions, skips, syntax classification precision/recall/F1 and confusion matrix per language, test-outcome agreement, score MAE, category agreement and concept recommendation precision/recall against labels. Targets: 100% of mandatory tests on defined supported behaviors, all isolation checks, exact expected scores within 0.01, and no unreported skips. Held-out metrics are empirical results, never universal grading accuracy; publish failures honestly rather than weakening labels to reach 100%.

### 8. Keep graph reasoning and report assembly inside FeedbackAgent

Knowledge Graph reasoning and report assembly remain explicit typed internal stages owned by `FeedbackAgent`. The graph reasoner consumes only the typed evaluation from Agent 1, records task-scoped weak, satisfied, unknown, and contradictory concept findings, and provides prerequisite paths to feedback and recommendation services. It does not change rubric weights or infer global learner mastery. The report composer creates the single `assessment-report-v2` used by persistence and the API.

The declared workflow is `ImplementationEvaluationAgent` followed by `FeedbackAgent`, persistence, and API response. Agent 1 internally performs preprocessing, syntax, concept analysis, structural comparison, complexity analysis, secure functional testing, and scoring. Agent 2 internally performs graph reasoning, error/strength/weakness explanation, prerequisite traversal, learning recommendations, feedback, and report composition. Syntax/preprocessing failure creates explicit skipped internal-stage results and never invokes execution. Runner unavailability remains an explicit incomplete evaluation with a null total; Agent 2 still reports valid static evidence and limitations.

## Risks / Trade-offs

- Existing originality weight penalizes identical correct code -> expose heuristic and policy version; retain for continuity, revisit only with reviewed evidence.
- AST comparison penalizes alternate valid algorithms -> keep a distinct structural criterion; include alternate implementations in labeled evaluation and avoid semantic claims.
- Docker/VM availability on Windows -> readiness check and documented setup; no host fallback and no claim of security from PATH discovery.
- Java memory/startup overhead -> separate pinned limits and resource fixtures; any policy adjustment is documented and retested.
- Large scope -> implement vertical backend increments in task order; each lands tests and docs before the next. No frontend until acceptance.

## Migration Plan

1. Review proposal, seven specs, design defaults and fixture correction. Record explicit approval in `review.md`; no artifact or CLI state substitutes for it.
2. Characterize existing behavior with safe stubs; add reproducible dependencies, fixtures and shared contracts.
3. Build and verify containment before executing submissions; then add language adapters, scoring, agents, graph and service in dependency order.
4. Run mandatory suites and held-out evaluation; document support matrix, actual versions, limitations and API examples. Preserve original samples and show intentional before/after score differences.
5. On acceptance, sync specs and archive via OpenSpec. Rollback application commits and policy/image versions explicitly if needed; never restore unsafe host execution as fallback. Data is local/versioned; no database migration exists.

## Complete architecture map

```text
HTTP/Future clients
        |
FastAPI validation + error envelope
        |
Assessment orchestrator
  |
  +-> ImplementationEvaluationAgent
  |     [preprocess -> syntax -> concepts -> structure -> complexity
  |      -> secure test executor -> rubric evaluator]
  |
  +-> FeedbackAgent
        [error/strength/weakness analysis -> graph reasoner
         -> prerequisite traversal -> recommendations -> report composer]
  |
  +-> Persistence -> API response
```

The API never invokes compilers directly. Language adapters produce normalized IR; the internal secure test executor delegates only to the isolated worker. `ImplementationEvaluationAgent` owns analysis order and score composition. `FeedbackAgent` owns graph reasoning, recommendations, and final report composition. Persistence stores immutable versioned results, not executable artifacts by default. Observability records two top-level agent events plus typed internal-stage traces.

## Explicit contradiction resolutions

1. The old zero-division fixture expected only `Error`, but the teacher program prints sum, difference, product and then `Error`. The approved expected behavior is the teacher's complete output `5\n5\n0\nError\n`; the old expected label is invalid and will be versioned as corrected rather than silently mutated.
2. The existing `main.py` executes GCC and plotting at import time. The specification preserves its useful scoring intent but requires a guarded compatibility CLI and forbids import-time execution in the backend.
3. The legacy syntax score counts the word `error`; the internal syntax-analysis service uses parser status and structured diagnostics, with C/Java compiler authority pending the isolated worker. `legacy-v1` remains a characterization baseline; `core-v1` is the approved behavior.
4. Docker availability is not security evidence. Until a pinned Linux worker is running and tested, the production runner reports unavailable and performs no host execution.

## Implementation phases

Phase 0: approval, repository audit, support matrix, fixture correction and contract freeze.

Phase 1: dependency manifests, pure legacy characterization, corpus schema, typed models and fake runner.

Phase 2: isolated Linux worker, resource enforcement, cleanup and security acceptance. This phase gates all submission execution.

Phase 3: Python/C/Java parsers and normalized IR with bounded comparison and complexity evidence.

Phase 4: exactly two agent interfaces, internal syntax/concept/structure/execution/complexity services, rubric and evaluation orchestration.

Phase 5: graph, recommendations, feedback, persistence and redacted observability.

Phase 6: FastAPI health/readiness/assessment contracts, compatibility CLI, benchmark reports and backend acceptance.

Phase 7: a separate approved change for authenticated teacher/student frontend integration after backend acceptance.

## Decision status and remaining approvals

- Linux container isolation and a project-owned local worker are approved as the required development/demonstration boundary. Rootless Podman, a project-owned local registry, and project-owned mutual TLS are the selected deployment design; exact image digests, certificate identities, and real containment evidence still require local build/configuration and verification.
- SQLite is approved for the initial backend milestone. The source/output retention duration and automatic deletion schedule remain open.
- Python uses CPython 3.11 `ast`; the approved design's parser evaluation selected tree-sitter-c 0.24.2 and tree-sitter-java 0.23.5 for static IR. Clang is the approved authoritative C11 compiler and JDK 17 is authoritative for Java diagnostics inside the worker. This does not replace tree-sitter with a Clang AST or JavaParser architecture.
- Teacher/student role authorization is implemented for the local API. Production secret management, account recovery, tenant boundaries and a public-deployment threat model remain open.
- Minimal retention is the policy, but only explicit source redaction is implemented; an approved duration is required for automatic retention enforcement.
- Benchmark labels must be independently reviewed. Named reviewers and a frozen held-out corpus remain open, so no empirical accuracy result is claimed.

## Academic workflow amendment

The local FastAPI backend owns authentication and resource authorization. Passwords use the existing salted PBKDF2 format and signed access tokens remain short lived. Student registration is public; teacher registration requires the server-owned `ASSESSMENT_TEACHER_REGISTRATION_CODE`. Assignment ownership is checked on every operation that can reveal or use reference source, hidden tests, rubrics, student source, or aggregate results. Listing endpoints use bounded offset/limit pagination. The assignment record remains the aggregate for its reference, rubric, and tests in this SQLite milestone; updates replace validated fields transactionally. Analytics and progress are derived from persisted evaluations and never expose hidden tests or another student's source.

The API passes validated rubric weights into `ImplementationEvaluationAgent`; score arithmetic and evidence remain deterministic and versioned. Existing `core-v1` defaults remain unchanged. This work adds backend contracts only. Frontend implementation remains gated on real-worker acceptance and independent benchmark evidence.
