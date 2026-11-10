# Research evaluation plan

## Current evidence boundary

The repository implements a deterministic two-agent assessment pipeline, metric calculator, versioned candidate corpora, and review gates. It does **not** yet contain independently approved labels or verified real-worker predictions. Consequently, no project accuracy, human-feedback-quality, resource, or latency result is currently reportable. Unit-test pass rates measure software conformance, not grading accuracy.

## Research questions

| ID | Question | Required evidence | Current status |
| --- | --- | --- | --- |
| RQ1 | How accurately does the system classify correct, partially correct, and incorrect supported programs? | Independently approved held-out labels and real isolated predictions for all three languages | Blocked |
| RQ2 | How reliably are valid alternative implementations distinguished from incorrect structure? | Reviewed alternate-loop, conditional, decomposition, naming, and algorithm cases | Candidate cases exist; independent review and execution blocked |
| RQ3 | Does Knowledge Graph reasoning improve recommendation relevance? | Blinded human ratings plus a no-KG baseline using identical evaluation evidence | Protocol defined; ratings and baseline predictions absent |
| RQ4 | What latency and resource overhead does the two-agent pipeline add? | Pinned worker, repeated cold/warm runs, stage timings, CPU and peak-memory observations | Blocked by real-worker verification |

These questions remain preregistered evaluation targets, not answered research claims.

## Experimental units and split

- Unit: one immutable task-version/source pair with a unique source hash.
- Languages: Python 3.11, C11 with approved Clang, and Java 17.
- Development and held-out hashes must be disjoint before tuning.
- Required strata: correct, partial, incorrect, alternative-valid, syntax/compile failure, runtime failure, boundary behavior, timeout, and resource failure.
- Labels must be created from the task contract and source, never copied from CodeAssess predictions.
- At least one independent reviewer is required for reporting; two reviewers and documented disagreement resolution are preferred for feedback-quality claims.

## Systems to compare

1. Test-case-only: functional outcomes only, with the same hidden tests and no static/KG evidence.
2. Static-only: syntax, concepts, structure, and complexity indicators without functional outcomes.
3. Evaluation without Knowledge Graph reasoning: identical Agent 1 result and deterministic feedback templates, but no prerequisite traversal or KG-derived recommendations.
4. Full two-agent system: complete approved pipeline.

Baseline and ablation outputs must use the same corpus split and retain null scores when required evidence is absent. These experiment modes are not currently implemented as publishable prediction runners and must not be approximated by manually editing full-system output.

## Measures

- Classification: confusion matrix, accuracy, macro/per-class precision, recall, and F1.
- Functional behavior: per-case verdict accuracy and per-test agreement.
- Rubric: component agreement, score MAE, agreement within 0.01, and category agreement.
- Concepts and recommendations: precision, recall, and F1 with explicit zero-denominator handling.
- Repeatability: decision agreement over two identical held-out runs.
- Performance: median, p95, and maximum end-to-end/stage latency; peak memory and CPU time where the approved worker exposes reliable measurements.
- Feedback quality: blinded reviewer rubric for correctness, evidence support, actionability, concept relevance, and contradiction absence; report inter-rater agreement when two reviewers participate.

## Reproducible procedure

1. Approve a new immutable corpus version following `docs/backend/BENCHMARK_REVIEW.md`.
2. Record corpus hash, graph version, rubric version, parser/toolchain versions, worker image digest, seccomp hash, configuration limits, hardware/OS, and timestamp.
3. Produce two prediction documents from unchanged code/configuration in the verified isolated worker.
4. Run:

```powershell
.\.venv\Scripts\python.exe -m backend.benchmark `
  --corpus data\benchmarks\<approved-corpus>.json `
  --predictions <first-predictions>.json `
  --repeat-predictions <second-predictions>.json `
  --output <report>.json
```

5. Preserve the machine-readable report and failure/exclusion ledger. Report null metrics as unavailable, never as perfect scores.

## Threats to validity

- Candidate cases may reflect developer expectations and are not independent evidence.
- A single programming task cannot establish general grading validity.
- Static complexity indicators are bounded heuristics, not exact asymptotic proofs.
- Test outcomes depend on hidden-test adequacy.
- Human feedback ratings can be subjective; blinded review and agreement reporting reduce but do not remove this risk.
- Results from one worker image/hardware configuration may not generalize to other environments.

## Publication gate

Research-result tables and figures may be produced only after label approval, real-worker verification, repeat runs, and provenance capture. Until then, documentation must show methods, candidate coverage, and blockers without numeric accuracy or novelty claims.
