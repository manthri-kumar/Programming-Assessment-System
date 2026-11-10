# Project workflow

Project: Knowledge Graph-Driven Multi-Agent Framework for Intelligent Programming Assessment.

- Use OpenSpec specification-driven development for all further implementation. Read `openspec/config.yaml`, applicable specifications, and the active change before editing application code.
- The first change is `openspec/changes/backend-core-audit`. It is a draft awaiting human review. Do not begin implementation until the user explicitly approves the specifications and asks to apply the change. Artifact completeness or CLI validation is not approval.
- For later behavior changes, prepare or update proposal, design, delta specifications, and verifiable tasks before implementation. Record changes to scope for review before implementing them.
- Finish and verify the backend before frontend work. No frontend implementation is authorized by the initial change.
- Build deterministic agents without external LLM APIs. Preserve and characterize the existing rubric before improving it; make score policy changes explicit and versioned.
- Never run untrusted submissions directly on the host. Execution requires the approved isolated runner; if unavailable, fail closed.
- Measure results against versioned, reproducible labeled fixtures. Aim for all defined supported-behavior tests passing; never claim universal grading accuracy.
- Ask before installing global tools or performing destructive changes. Do not delete tracked binaries or caches as incidental cleanup.
- At completion, report tests actually run, failures, skipped checks, supported versions and limitations. Do not equate specification validation with backend correctness.
