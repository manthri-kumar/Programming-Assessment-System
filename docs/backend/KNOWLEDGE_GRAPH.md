# Concept Knowledge Graph

`data/concepts/concept-v1.json` is the versioned graph source. Each concept has a stable ID, display label, and deterministic learning guidance. The `requires` mapping is directed from a dependent concept to its immediate prerequisites. For example, `zero-division-guard` requires both `arithmetic` and `conditionals`; those concepts require `input`.

Graph loading rejects duplicate IDs, dangling endpoints, missing versions, and prerequisite cycles. Readiness fails when the graph is absent or invalid. Traversal returns prerequisites before dependents, deduplicates shared ancestors, and uses concept ID as the stable tie break.

Recommendations are created only from task-labelled failed-test evidence or an explicit weak-concept input. An unlabelled failure does not create a concept claim. Successful evidence can satisfy a prerequisite only for the current assessment, and satisfied prerequisites are omitted. Other prerequisite mastery is reported as `unknown`, never inferred as a learner-wide weakness.

For a failed zero-divisor test labelled `zero-division-guard`, the stable order is `input`, `arithmetic`, `conditionals`, `zero-division-guard`. Each item includes the graph version, prerequisite-to-target path, current-assessment scope, mastery status, guidance, and the triggering failed-test evidence ID. The executable golden is covered by `test_failed_test_concepts_are_explicit_and_unlabelled_failures_invent_nothing`.
