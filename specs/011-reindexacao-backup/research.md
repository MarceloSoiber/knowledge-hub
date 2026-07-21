# Research: Reindexacao e Backup

## Decision 1: Use CLI as the MVP operational surface

**Decision**: Implement reindexation and backup helpers as project scripts backed by services, not as primary REST/MCP endpoints.

**Rationale**: The operation is administrative, potentially long-running and sensitive. The repository already uses argparse-based CLI for operational config. CLI keeps the first slice simple while still testable.

**Alternatives considered**:

- REST endpoints first: useful for UI later, but requires more auth/timeout/job-status design.
- MCP tools first: convenient for agents, but backup/reindex can expose sensitive operational data and should mature after CLI/runbook.

## Decision 2: Persist reindex runs and items

**Decision**: Store `ReindexRun` and `ReindexItem` rows so dry-run results, execution progress, per-source failures and resume state survive process interruption.

**Rationale**: Resumability cannot rely on in-memory state. Per-item records make retries deterministic and auditable.

**Alternatives considered**:

- Infer all state from chunks on each run: idempotent but loses operator intent, errors and progress history.
- Log files only: hard to query, test and correlate with chunk/batch state.

## Decision 3: Reindex from `DocumentSource.content_text`

**Decision**: Rebuild/re-embed from the preserved original text stored on `DocumentSource.content_text`, using existing chunking/normalization behavior.

**Rationale**: The plan explicitly depends on preserved original content. Existing chunk content may be enough for pure re-embedding, but source-level reprocessing gives a safer path when chunking rules change.

**Alternatives considered**:

- Re-embed existing `KnowledgeChunk.content` only: simpler and can be used for a narrow compatibility reindex, but does not satisfy "reprocessar a partir do conteudo original" when chunking changes.
- Re-read original files/URIs: not reliable if files moved or private sources changed.

## Decision 4: Validate before declaring success

**Decision**: A reindex run is successful only after candidate counts, embedded counts, vector dimensions and sample search behavior are checked for the target filters/config.

**Rationale**: Embedding provider success alone does not prove the active search corpus is usable or compatible.

**Alternatives considered**:

- Mark success after provider calls: can hide wrong dimensions, missed candidates or search filtering bugs.
- Require exhaustive search validation: too expensive and unnecessary for MVP.

## Decision 5: Backup runbook uses PostgreSQL-native dump/restore

**Decision**: Document `pg_dump` custom-format backup and `pg_restore`/`psql` restoration, including pgvector prerequisite and empty-database validation.

**Rationale**: PostgreSQL-native tools preserve relational data, JSONB, vector columns, indexes and constraints more reliably than ad hoc exports.

**Alternatives considered**:

- Application-level JSON export: portable but likely to miss indexes, config and relational consistency.
- Filesystem volume snapshots only: fast, but less transparent and harder to validate across environments.

## Decision 6: Scheduling is gated by restore evidence

**Decision**: Backup scheduling remains disabled/documented until a real restore test is executed and recorded.

**Rationale**: The plan explicitly says automation should happen only after restore testing. This also prevents unverified backup scripts from creating false confidence.

**Alternatives considered**:

- Add cron/systemd timer immediately: convenient, but violates the acceptance order.
- Leave scheduling entirely out of scope: misses retention/destination automation planning.

## Decision 7: Do not log raw source content or secrets

**Decision**: Reindex and backup output must use ids, counts, statuses and short sanitized errors. Full `content_text`, auth tokens, connection URLs with passwords and encryption keys must not be printed.

**Rationale**: The database contains personal knowledge. Backups necessarily contain sensitive content; logs should not duplicate it.

**Alternatives considered**:

- Verbose debug dumps for troubleshooting: too risky as default; use targeted local debugging only with explicit operator action.

## Decision 8: Keep backup evidence as runbook evidence in v1

**Decision**: Do not add `BackupArtifact` or `RestoreValidation` tables in this slice. Use `doc/OPERATIONS.md` and the `knowledge-backup` helper for command/checklist rendering, with restore evidence recorded manually.

**Rationale**: The most important first step is a reliable restore runbook. Persisting backup evidence adds schema surface without automating a real restore.

**Alternatives considered**:

- Persist backup/restore evidence now: useful later, but premature before the exact operational destination and scheduling mechanism are known.

## Decision 9: Default reindex batch size and retry behavior

**Decision**: Default `--batch-size` is 50. Failed items are marked `failed_retryable`; `--resume-run-id` retries pending or retryable items and rechecks compatibility before every provider call.

**Rationale**: A bounded default avoids large memory/provider bursts. Compatibility rechecks make repeated commands idempotent.

**Alternatives considered**:

- Process all candidates by default: too risky for a local/provider-backed embedding flow.
- Mark failures final immediately: too harsh for transient provider errors.
