# Intelligent Programming Assessment

> A multi-agent programming assessment framework for evaluating student code across Python, C, and Java.

## 📌 Overview

**Intelligent Programming Assessment** is an automated programming assessment system designed to evaluate student programming submissions against reference solutions.

Instead of relying only on traditional test-case execution and a numerical score, the system analyzes programming concepts present in the student's solution and generates structured evaluation and personalized feedback.

The system currently supports:

- 🐍 Python
- ⚙️ C
- ☕ Java

The core assessment pipeline uses two specialized agents:

1. **Evaluation Agent** – analyzes the submission and generates a structured evaluation.
2. **Feedback Agent** – converts the evaluation into personalized learning feedback.

---

## 🎯 Objectives

The main objectives of the project are:

- Automatically assess programming submissions.
- Support multiple programming languages.
- Extract important programming concepts from source code.
- Compare student code with a reference solution.
- Identify matched and missing concepts.
- Perform syntax analysis.
- Perform basic test execution.
- Estimate code complexity.
- Generate a structured score.
- Provide concept-level evaluation.
- Generate personalized feedback.
- Provide an interactive programming assessment interface.

---

## 🏗️ System Architecture

```text
                    Reference Code
                          │
                          ▼
                  Language Detection
                          │
                          ▼
              Language-Specific Parser
                    /      |      \
                   /       |       \
              Python       C       Java
                   \       |       /
                    \      |      /
                          ▼
                Common Code Representation
                          │
                          ▼
                   Comparison Module
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
        Syntax Check   Test Runner  Complexity
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Evaluation Agent│
                 │     Agent 1     │
                 └────────┬────────┘
                          │
                          ▼
                  Evaluation Report
                          │
                          ▼
                 ┌─────────────────┐
                 │  Feedback Agent │
                 │     Agent 2     │
                 └────────┬────────┘
                          │
                          ▼
                Personalized Feedback
                          │
                          ▼
                     FastAPI
                          │
                          ▼
                  React Dashboard
