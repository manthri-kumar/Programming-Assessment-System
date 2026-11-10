# SQLite backup, retention, and recovery

1. Stop new evaluation requests or place the application in a maintenance window.
2. Call `SQLiteRepository.backup_to()` with a new file in a protected existing directory. Existing files are never overwritten.
3. Record the backup hash, creation time, schema version, and access-controlled storage location outside public logs.
4. Test recovery with `SQLiteRepository.restore_from_backup()` into a new path. It validates source integrity before copying and runs normal forward migrations when the restored repository opens.
5. Verify user/assignment/submission ownership, immutable configuration snapshots, evaluation reports, and job states before switching configuration to the restored file.
6. Back up the configured private import directory separately with restrictive access if unexpired import sources must be recoverable. The SQLite backup contains import metadata and opaque storage keys, not document bytes. Restore the directory only to the same path-confined configuration and verify hashes before enabling previews.
7. Keep the original database unchanged until manual acceptance. Switching databases or deleting old backups is an operator action outside this code path.

Retention uses `redact_expired(retention_days)`: old submission source and sensitive result fields are replaced with `[REDACTED]` while identifiers, ownership, versions, scores, and non-sensitive evidence remain replayable. Worker scratch cleanup remains a separate real-worker acceptance gate.

Unpublished assignment-import sources use their own short expiry. Startup and authorized access cleanup remove expired source files and import rows; explicit owner deletion removes both. Published assignments remain valid after source expiry because their canonical fields are stored independently. Real institutional encrypted-backup controls remain an operational deployment gate.

