# Automated Code Assessment System

This project implements a deterministic, evidence-linked programming assessment backend for Python, C, and Java. It uses exactly two top-level agents and no external LLM API.

## Features
- `ImplementationEvaluationAgent`: preprocessing, parsing, syntax, concepts, structure, complexity, isolated test delegation, rubric scoring, and limitations
- `FeedbackAgent`: explanations, strengths and weaknesses, Knowledge Graph traversal, recommendations, and additive `assessment-report-v3` with v2 replay compatibility
- FastAPI teacher/student workflow with role and assignment-ownership checks
- SQLite assignments, submissions, reports, history, analytics, and progress
- Versioned rubric, parser, graph, evidence, and benchmark contracts
- Fail-closed execution when the approved Linux worker is unavailable
- Responsive React/TypeScript student and teacher application with server-backed assignments, drafts, bookmarks, reports, progress, and Knowledge Graph views
- Private teacher assignment import from PNG/JPEG/WebP/PDF with embedded PDF text extraction, provenance review, canonical concepts, and disabled-by-default local OCR

## Technologies
- Python 3.11 and FastAPI
- Python AST plus pinned tree-sitter C and Java parsers
- SQLite
- Authoritative Clang C11 and Java 17 compilation inside the pending project-owned Linux worker

## Usage
See `docs/backend/SETUP.md`, `docs/backend/API.md`, `docs/backend/LOCAL_LINUX_WORKER.md`, and `docs/FRONTEND.md`. Run the local environment-independent backend checks with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The guarded compatibility CLI is available through `python main.py`; importing it performs no compilation, execution, or plotting. The frontend displays worker-unavailable and benchmark limitations truthfully; its existence does not change the blocked backend acceptance status.
