# Faculty demonstration script

## Exact local startup

Backend, from the repository root in PowerShell:

```powershell
$env:ASSESSMENT_SECRET = "replace-with-a-long-private-demo-secret"
$env:ASSESSMENT_TEACHER_REGISTRATION_CODE = "choose-a-private-demo-invitation"
$env:ASSESSMENT_DB = "$PWD\codeassess-demo.db"
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Frontend, in a second PowerShell terminal:

```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`. Do not put the private invitation or bearer tokens in screenshots or presentation materials. The demonstration database is separate from benchmark corpora and must not be described as research data.

## Preconditions

- Start FastAPI and the frontend using `docs/FRONTEND.md` with private local values for `ASSESSMENT_SECRET` and `ASSESSMENT_TEACHER_REGISTRATION_CODE`.
- Use newly created demonstration accounts; do not place credentials or invitation values in slides, logs, or source control.
- Check `/ready` before the demonstration. A 503 response means static assessment remains available but real functional execution is unavailable and must be demonstrated honestly as fail-closed.
- Real Python/C/Java execution is permitted only when the approved Linux worker has passed `scripts/worker/verify-local-worker.py`.

## Main workflow

1. Register or sign in as a teacher using the configured invitation.
2. Create an assignment with language, task statement, reference source, hidden tests, concepts, deadline, and valid rubric weights.
3. Show that the teacher can edit the assignment while another user cannot access its hidden reference/tests.
4. Sign out and register or sign in as a student.
5. Open the assignment, save a draft, then submit source.
6. Open the submission report and identify the two top-level agents: `ImplementationEvaluationAgent` followed by `FeedbackAgent`.
7. Show syntax, concept, structural, complexity, functional-test, scoring, evidence, and limitation sections.
8. Open Knowledge Graph recommendations and trace a weak concept to its evidence and prerequisite path.
9. Show the persisted submission in student history and progress.
10. Sign in as the owning teacher and review the same persisted report and updated analytics.

## Required cases

| Case | Expected observable outcome |
| --- | --- |
| Correct supported submission | Valid syntax/static evidence; functional score only if the verified worker ran every required test |
| Partially correct submission | Failed cases and component evidence remain visible; no weight redistribution for missing evidence |
| Incorrect submission | Evidence-linked findings and feedback agree with the evaluation result |
| Alternative valid solution | Different names/structure are not by themselves a functional failure; report labels structural similarity separately |
| Syntax error | Learner diagnostic is reported; unsafe/dependent execution stages are skipped |
| Worker unavailable | Submission persists, execution is explicitly unavailable, and total/category remain null rather than fabricated |

## Demo-only assignment and submissions

Create an assignment called **Sum integers** using Python, concept `input`, reference source:

```python
values = list(map(int, input().split()))
print(sum(values))
```

Use hidden cases such as `1 2 3 -> 6` and `-2 2 -> 0`; do not expose them in student-facing screenshots. Demonstrate these submissions:

| Scenario | Demo source | Expected observation |
| --- | --- | --- |
| Correct | `print(sum(map(int, input().split())))` | Static evidence succeeds; functional evidence appears only with a verified worker. |
| Partial | `values=list(map(int,input().split())); print(values[0] + values[1])` | Some functional cases may pass with a verified worker; otherwise the report remains incomplete. |
| Incorrect | `print(0)` | Structural/concept evidence is visible; do not claim functional failure without worker evidence. |
| Alternative valid | loop-based accumulation | Different structure is reported separately from behavior. |
| Syntax error | `print(sum(` | Syntax diagnostic; execution is skipped. |
| Worker unavailable | any syntactically valid source | Persisted report shows null total/category and an explicit isolation limitation. |

For repeatable UI verification rather than a presentation database, follow `frontend/e2e/README.md`; that suite creates disposable accounts and data and is not research evidence.

## Registration failure demonstration

- Invalid teacher invitation: `Invalid teacher invitation code.`
- Duplicate email: `An account with this email already exists.`
- Backend stopped: `Unable to connect to the server. Please try again.`
- Teacher invitation not configured: explicit administrator-facing unavailable message.

The initial invitation mechanism is reusable and has no expiry/single-use lifecycle; do not claim otherwise.

## Demonstration limitations to state aloud

- Real execution and performance claims remain blocked until the dedicated Linux worker is built, pinned, and verified.
- Accuracy and feedback-quality claims remain blocked until independent corpus review and held-out experiments.
- Static complexity evidence is heuristic and bounded.
- Unsupported product features remain visibly unavailable rather than simulated.

## Recovery

- If the frontend cannot reach the API, verify `http://127.0.0.1:8000/health` and restart only the local processes.
- If `/ready` returns 503, continue with the documented fail-closed case; do not enable host execution.
- If an account already exists, use a new demo-only email instead of deleting data.
- If the teacher invitation fails, confirm the backend terminal and registration form use the same private value; never hardcode it into source.
