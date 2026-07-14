# Research: Categorias Muitos-Para-Muitos

## Decision: Use an association table managed by SQLAlchemy ORM

**Rationale**: The current domain already models sources and categories in SQLAlchemy. A composed association table keeps queries explicit and supports cascade on document deletion.

**Alternatives considered**: Array column on `document_sources`, rejected because it weakens referential integrity and makes category management harder.

## Decision: Keep idempotent migration in `backend/app/db/init.py`

**Rationale**: The repository does not currently use Alembic migrations. The existing initialization function already performs schema repair/migration work.

**Alternatives considered**: Introduce Alembic, rejected for this feature because it would add a migration framework beyond the requested scope.

## Decision: Normalize category names in service code and database index

**Rationale**: Service normalization gives consistent API/MCP behavior while a unique lower-name index protects data integrity.

**Alternatives considered**: Case-sensitive uniqueness only, rejected because the feature requires case-insensitive uniqueness.

## Decision: Filter category matches with EXISTS

**Rationale**: EXISTS preserves one row per chunk even when a source belongs to multiple selected categories.

**Alternatives considered**: Joining categories directly with DISTINCT, accepted as a fallback but more expensive and easier to regress.
