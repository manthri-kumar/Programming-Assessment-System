# Persistence and retention

SQLite schema version 3 stores users, assignments, presentation metadata/deadlines, submissions, evaluation results, immutable assessment replay records, student-scoped bookmarks and drafts, and role-scoped activity events. Replay records include a unique request hash, status, version metadata, evidence lineage, result JSON, creation time, and redaction time. `AssessmentRepository` defines the portable replay and retention boundary.

Transactions commit atomically and roll back on errors. Duplicate request hashes are explicit repository errors. The retention operation takes a configured number of days, redacts expired submission source and sensitive source/output fields in assessment records, and preserves aggregate status, version, and evidence metadata. The project has not selected a production retention duration, so cleanup is never scheduled implicitly.

Access remains role-scoped through the API. Logs use the separate redaction layer and never serialize password, token, source, stdout, or stderr values.

Draft source is readable only by its student owner and is never passed to the runner by draft operations. Bookmark insertion is idempotent. Activity rows store event kind and record identifiers only; they do not duplicate source, credentials, hidden tests, or execution output.
