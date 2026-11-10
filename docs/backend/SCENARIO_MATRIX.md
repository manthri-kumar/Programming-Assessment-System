# Backend scenario matrix

Machine-readable source: `data/validation/scenario-matrix-v1.json`. An automated test compares that ledger with every `#### Scenario:` heading in all active `backend-core-audit` capability specifications, so adding or renaming a scenario without evidence mapping fails the suite.

This matrix distinguishes executable environment-independent coverage from checks that require the approved real worker or independent label review.

| Capability | Executable evidence | Current state |
| --- | --- | --- |
| Academic workflow | `test_api_and_persistence.py` | Teacher invitation, canonical/expired/altered token rejection, owner-only hidden data, concurrent submission isolation, custom rubrics, histories, analytics, progress and pagination pass |
| Backend/API | `test_api_and_persistence.py` | Health, readiness, auth, roles, 200/413/422/500/503, assignments, updates and submissions pass |
| Python analysis | `test_analysis_and_agents.py` | AST, syntax, node limit, comments/strings, unsupported imports pass |
| C analysis | `test_analysis_and_agents.py` | Tree-sitter structure passes; isolated compiler outcomes blocked |
| Java analysis | `test_analysis_and_agents.py` | Tree-sitter syntax, Main layout, package/external import rejection pass; isolated javac blocked |
| Normalized IR | `test_analysis_and_agents.py` | Stable hashes and bounded edit fixtures pass |
| Agent interfaces/orchestration | `test_analysis_and_agents.py` | Contract, order, cancellation, lineage, repeatability and no-network checks pass |
| Concept, syntax, structure, complexity agents | `test_analysis_and_agents.py` | Static supported behavior passes |
| Test execution agent | `test_models_and_runner.py`, `test_container_runner_contract.py`, `test_worker_protocol.py`, `test_local_worker_control.py`, `test_worker_configuration.py` | Fail-closed/mTLS control contract, server-owned Podman arguments, strict codecs, hidden-output separation, simulated outcomes, worker failure and cleanup pass; real containment evidence blocked |
| Evaluation/feedback agents | `test_analysis_and_agents.py`, `test_agent_acceptance_outcomes.py`, `test_api_and_persistence.py` | Policy, authoritative compile failure, distinct execution outcomes, null totals, rubric math, evidence-linked feedback pass |
| Knowledge graph/recommendations | `test_analysis_and_agents.py` | Validation, traversal, paths, evidence and task scope pass |
| Persistence | `test_api_and_persistence.py` | Migration, transaction rollback, replay, duplicates and retention pass |
| Observability | `test_api_and_persistence.py`, `test_analysis_and_agents.py` | Taxonomy, correlation, redaction, stage/cancellation traces pass |
| Legacy scoring | `test_legacy_characterization.py` | Golden structure/syntax/test/feedback/rubric behavior passes without execution |
| Benchmarking | `test_benchmark.py` | Schema, hashes, uniqueness, split, 12-case cross-language candidate coverage, review gate, aggregate/per-language metrics and repeatability arithmetic pass; independent labels blocked |
| Isolation security | `docs/backend/ISOLATED_WORKER.md` | Real network/filesystem/resource/process/workspace checks blocked |
| Frontend contracts | Generated OpenAPI and `docs/backend/API.md` | Backend contract published; frontend implementation deferred |

Blocked rows are not counted as passing security or accuracy evidence. Each blocked scenario has an explicit check or review workflow in the machine-readable ledger, but its acceptance task remains open until that evidence actually runs or an independent reviewer signs it.
