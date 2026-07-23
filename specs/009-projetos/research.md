# Research: Projetos

## Decision 1: Projects are work context, not classification

**Decision**: Project represents a work context. Categories remain controlled broad subjects, and tags remain granular reusable markers.

**Rationale**: The source plan explicitly says to keep categories as subject and project as context. This avoids turning projects into taxonomy and allows one document to be reused across contexts.

## Decision 2: Project association is optional

**Decision**: Sources may have zero projects. Search without `project_ids` includes general knowledge and project-associated knowledge.

**Rationale**: The plan says "conhecimento geral continua sem associação". Making projects mandatory would create artificial projects and reduce reuse.

## Decision 3: Project filters are strict

**Decision**: When `project_ids` is provided, only sources associated with at least one requested project participate. General unassociated sources are excluded.

**Rationale**: The acceptance criterion says IA must be able to restrict a query to the current project. Strict filtering is safer for agents. A future `include_general=true` option can be added if users need blended context.

## Decision 4: Archive, do not delete, is MVP lifecycle

**Decision**: MVP supports `active` and `archived` statuses. Archive/reactivate changes status and never deletes sources, chunks or associations. Project deletion is out of MVP.

**Rationale**: The plan asks to define archiving without excluding knowledge. Deletion adds dangerous edge cases and can be added later as a safe no-association operation if needed.

**Implementation result**: v1 exposes `archive` and `reactivate` endpoints only.
No project delete endpoint is implemented.

## Decision 5: API and MCP use `project_ids`

**Decision**: Associations and filters use project ids, mirroring `category_ids` and `tag_ids`.

**Rationale**: ID-based contracts avoid ambiguity from duplicate-like names and make missing-project validation predictable.

## Decision 6: Empty project list in source patch clears associations

**Decision**: Source patch accepts `project_ids: []` to remove all project associations from a source.

**Rationale**: Projects are optional metadata. Clearing project context should not require a separate endpoint and must not regenerate embeddings.

## Decision 7: Project listing includes archived projects by default

**Decision**: `GET /knowledge/projects` returns all projects unless a `status`
query parameter is supplied.

**Rationale**: Archived projects remain part of the knowledge context and should
stay discoverable. Clients that only want active contexts can call
`GET /knowledge/projects?status=active`.
