# Repository audit

Status: static source audit completed 2026-10-19 against commit `b83616e` (clean working tree before setup). All repository source and documentation files were read, including ignored-file inventory. Git internals and opaque bytecode/executables were inventoried, not treated as source. No application code or student executable was run.

## Complete source inventory

| File | Existing behavior | Reuse / gap |
| --- | --- | --- |
| `main.py` | Top-level GCC compile, reads fixed C paths, calls four scoring functions, weighted total, classification, feedback, GUI bar chart | Retain orchestration intent and policy; separate CLI from service and remove import side effects after approval |
| `modules/sedm.py` | Runs `gcc file` (compile/link), counts lowercase `error` in stderr, deducts 10 per occurrence | Retain syntax component; use exit status and structured diagnostics, syntax-only checking, timeout and isolation |
| `modules/sbcam.py` | Regex counts nonblank lines, `int` function declarations, `for`/`while`, `if`; averages count similarity | Preserve characterization; replace unreliable lexical evidence with parsed structure through adapters |
| `modules/stcam.py` | Weighted stdout comparison using `.strip()`; inverse raw-text SequenceMatcher similarity | Preserve test weighting and comparison default; bound execution, check exit code, expose similarity limitations |
| `modules/feedback.py` | Fixed threshold messages for four components and final score | Reuse deterministic rule approach; tie feedback to diagnostics and graph concepts |
| `testcases.py` | Three weighted arithmetic fixtures (weights 1, 1, 2) | Data, not an automated test suite; third expected output contradicts the teacher solution |
| `teacher_solution/teacher.c` | Reads two ints; prints sum, difference, product, then division or Error | Useful fixture; zero-divisor input prints `5`, `5`, `0`, `Error`, not only `Error` |
| `student_submissions/student1.c` | Same arithmetic without zero-divisor guard | Useful negative example; division uses floating point, so exact zero-division runtime output is toolchain dependent |
| `results/plot.py` | Matplotlib score bars and multi-student bars | Visualization only; not a Knowledge Graph; keep outside backend request flow |
| `README.md` | Features, Python/GCC/Matplotlib, `python main.py` | Only existing documentation; lacks installation pins, API, support boundary, safety, research protocol |
| `.gitignore` | Ignores bytecode, exe and out files | Does not untrack existing artifacts |

Tracked generated files: root `a.exe`, `student.exe`, `student.out`; `__pycache__/testcases.cpython-314.pyc`; four `modules/__pycache__/*.cpython-314.pyc`; `results/__pycache__/plot.cpython-314.pyc`. They are preserved. No additional application source appeared in the full non-Git filesystem inventory.

## Requested components: found versus absent

- FastAPI backend, endpoints, request models, OpenAPI artifact: **absent**.
- Python processing: Python is the implementation language; **no Python submission parser/processor**.
- C processing: the four modules above plus GCC invocations in `main.py`; no AST parser.
- Java processing: **absent**.
- BaseAgent, EvaluationAgent, FeedbackAgent, agent protocol: **absent**. `generate_feedback` is a function, not an agent.
- Concept Knowledge Graph, prerequisite edges, recommendation traversal: **absent**.
- Automated unit/integration/security tests, labeled accuracy dataset, CI, dependency manifest/lock: **absent**.
- Documentation: README only. No project AGENTS.md or OpenSpec existed before this setup.

## Existing scoring rules

All components nominally use 0..100. Total = 0.20 structure + 0.40 syntax + 0.20 test cases + 0.20 originality. Categories: Good >=75, Average >=50, Poor otherwise.

Structure averages four features. For reference count `t > 0`, feature score is `clamp((1 - abs(t-s)/t) * 100, 0, 100)`; for `t=0`, score is 100 if `s=0`, otherwise 0. Blank-line count and regex matches make formatting/comments influence scores. Only `int` functions are recognized; `do...while` and language distinctions are not modeled.

Syntax = `max(0, 100 - 10 * stderr.count('error'))`, independent of return code; exceptions print and return zero. GCC may overwrite default output `a.exe`; main already compiles once and exits early on failure, so intended partial syntax feedback is bypassed.

Test score = `100 * passed_weight / total_weight`, or zero for no weight. Raw stdout is stripped at both ends. Nonzero exit codes are ignored; matching output followed by a crash can pass. Exceptions are swallowed. No timeout, resource/output limits, isolated filesystem, or process-tree cleanup exists.

Originality = `100 * (1 - SequenceMatcher(None, teacher, student).ratio())`. This is text dissimilarity, not proof of plagiarism or correctness. A correct identical reference receives zero originality; rewriting text can increase it without improving behavior.

Feedback thresholds: structure <60, syntax <80, tests <70, originality <50; overall >=75 / >=50. These rules are deterministic and should be characterized before replacement. Similarity-related accusations need evidence-qualified wording.

## Prioritized findings

1. Critical execution boundary gap: arbitrary submissions run with host privileges and inherited environment; both compilation and execution need containment, not just a timeout.
2. No backend or agent infrastructure exists to verify; creation must be described honestly as new work.
3. Contradictory reference fixture: zero-divisor case cannot establish reference correctness. Expected corrected output is `5\n5\n0\nError\n` for `5 0\n`, subject to reviewed task contract.
4. Scoring confounds: regex structure and text dissimilarity measure proxies; do not present them as semantic equivalence or plagiarism verdicts.
5. No exit-code handling or operational-failure distinction; compiler absence and learner mistakes can both become zero.
6. Fixed executable names create collisions/stale-output risk; import-time execution and GUI plotting prevent service reuse.
7. No versioned support matrix or reproducibility evidence. Host bytecode is tagged 3.14, while current discoverable Python is 3.11.4; bytecode must not establish runtime compatibility.

## Verification scope

Read all text source; inspected Git tracking/status and tool discovery. Node v22.22.2 and Python 3.11.4 were observed. GCC, javac and Docker commands are on PATH; their operational readiness and versions were not established. No pytest suite exists and no backend pass rate is claimed. OpenSpec validation is a separate artifact-format check, recorded in `review.md`.
