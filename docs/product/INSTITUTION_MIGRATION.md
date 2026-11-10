# Institution/course migration and rollback boundary

Schema version 6 adds institutions, courses, cohorts, enrollments, course-teacher membership, assignment course scope, and availability time without removing existing columns or records. Migration creates a `local` institution/course, assigns all existing assignments to it, enrolls existing students, and associates existing teachers. New local users receive the same default membership, preserving current workflows while institutional routes remain disabled by default.

The migration is forward-only. Before upgrading, create and integrity-check a protected SQLite backup. Rollback means stopping the upgraded application and restoring that backup to a new database path; it never means dropping the new tables in place. Verify ownership and report replay before switching paths. Institution/course UI and cross-tenant contracts must remain feature-gated until their authorization matrix passes; schema presence alone is not authorization acceptance.

