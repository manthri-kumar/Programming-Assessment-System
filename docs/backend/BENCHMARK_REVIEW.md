# Benchmark review workflow

`corpus-candidate-v2.json` contains a frozen candidate split with disjoint case IDs and source hashes across Python, C, and Java. Its labels are deliberately marked `pending-independent-review`. They must not be used to publish project accuracy.

An independent reviewer who did not implement the grader must check each source and label against the task contract, record their identity or stable reviewer ID, and sign a new immutable corpus version by changing review status to `approved`. Disagreements are resolved outside the grader; corrections create another version and retain a correction log. Development and held-out source hashes must remain disjoint.

`python -m backend.benchmark` refuses unapproved corpora. For approved labels and a predictions JSON file, it writes a machine-readable report containing per-language syntax confusion counts, precision, recall and F1; test-outcome agreement; score MAE; category agreement; and recommendation precision/recall. Missing labels remain `null` rather than being treated as perfect results.

The current repository has no independently approved corpus, so no project benchmark metric is reported.

## Data-quality review on 2026-10-25

`corpus-candidate-v2.json` is suitable only for exercising the syntax-metric path. It has six cases—one valid and one invalid source per language—but lacks task contracts, functional tests, runtime errors, partial correctness, boundary values, alternate correct algorithms, concept labels, structural expectations, rubric totals/categories, feedback codes, Knowledge Graph recommendations, timeouts and resource outcomes. It therefore cannot support a project-level accuracy claim even after its six syntax labels are reviewed.

`agent-expected-outcomes-v1.json` names correct, incorrect, partial, syntax, concept, alternate-algorithm, structure, complexity, prerequisite, contradiction and unavailable-execution scenarios. Those are candidate acceptance expectations rather than independently labeled source programs. They remain useful regression fixtures but are not an empirical benchmark.

`corpus-candidate-v3.json` expands the candidate set to twelve source programs: correct, partially correct, incorrect, and boundary-correct implementations in each of Python, C, and Java. All cases use the versioned `sum-to-n-v1` contract with four weighted boundary tests and include candidate functional verdicts, per-test outcomes, structural relations, concepts, recommendations, and source hashes. Scores/categories are deliberately null because those labels require a reviewed reference/rubric calculation. The entire corpus remains `pending-independent-review`; it has not been executed and must not be used for accuracy reporting.

`corpus-execution-candidate-v1.json` adds six supplemental cases: one syntax/compilation error and one runtime error for each supported language. It has disjoint source hashes and explicit candidate outcome labels, but remains `pending-independent-review` and has not been executed by the isolated worker. It closes a candidate-data coverage gap; it does not provide accuracy evidence.

Before review, the next immutable corpus version must provide for every case: task contract/version; split; language/support boundary; source and reference hashes; test inputs, expected outputs and weights; expected syntax/compiler status; functional verdict and per-test outcomes; structural relation or explicit non-applicability; score/category; concept IDs; ordered recommendation IDs; feedback codes; and any exclusion rationale. Development and held-out source hashes must remain disjoint.

## Independent reviewer requirements

The reviewer must not derive labels from this grader's output and must not be the person tuning the evaluated rules. The review record needs a stable reviewer ID, review date, corpus hash, reviewed case IDs, decision for every label group, disagreements/corrections, and an independence attestation. Approval requires at least one such record; higher-confidence academic reporting should use two reviewers and document disagreement resolution. A correction after freeze creates a new corpus version and preserves the old file and correction rationale.

## Metrics command

After approval, create a predictions document with stable case IDs and run:

```powershell
.\.venv\Scripts\python.exe -m backend.benchmark `
  --corpus data\benchmarks\<approved-corpus>.json `
  --predictions <first-predictions>.json `
  --repeat-predictions <second-predictions>.json `
  --output <report>.json
```

The report includes corpus/prediction hashes, case counts, per-language and aggregate syntax precision/recall/F1, functional-verdict accuracy, per-test agreement, score MAE, rubric agreement within 0.01, category agreement, concept precision/recall/F1, feedback agreement, recommendation precision/recall/F1, and repeated-run agreement. Missing labels yield null metrics or zero denominators rather than perfect scores. The command still refuses a corpus without genuine independent approval.
