# Research: Tags

## Decision 1: Tag identity uses normalized key

**Decision**: Store a unique normalized key for every tag using trim, lowercase and accent removal. Use the normalized key as `name` in v1 unless a display-name field is later required.

**Rationale**: The source plan explicitly asks for a policy on accents and capitalization. Accent-insensitive uniqueness prevents `Imposto`, `imposto` and `impostó` variants from fragmenting filters.

**Alternatives considered**:

- Preserve exact user spelling as unique name: rejected because it creates duplicate-equivalent tags.
- Case-insensitive only: rejected because Portuguese labels commonly vary by accent usage.
- Separate `display_name` immediately: deferred because it adds UI/API decisions not required for v1.

## Decision 2: API association starts with tag ids

**Decision**: Use `tag_ids` as the stable association contract for source patch, search and answer. Add name-based create/reuse only where it improves ingestion ergonomics and is explicitly tested.

**Rationale**: The existing category contract uses ids, and ids make validation/error mapping clearer. Autocomplete gives clients a way to discover ids before association.

**Alternatives considered**:

- Only `tag_names`: easier for quick ingestion but more likely to persist typos.
- Both ids and names everywhere: flexible but increases validation combinations and ambiguity.

**Implementation result**: v1 uses only `tag_ids` for ingestion, source patch,
search, answer and MCP. Clients create or discover tags through CRUD/list and
autocomplete endpoints before assigning them.

## Decision 3: Tags are optional metadata

**Decision**: Categories remain mandatory for ingestion; tags are optional.

**Rationale**: Tags complement the controlled category taxonomy. Making tags mandatory would block ingestion and encourage low-quality placeholder tags.

## Decision 4: Search tag filters use ANY for MVP

**Decision**: `tag_ids` filters match sources associated with any requested tag. Categories and tags combine as separate AND dimensions.

**Rationale**: This mirrors current category behavior and satisfies the roadmap line "Permitir filtro ANY". ALL is explicitly conditional on a real case.

**Alternatives considered**:

- ALL from day one: rejected until a concrete workflow needs it.
- OR across categories and tags: rejected because users expect category and tag filters to narrow results when combined.

## Decision 5: Metadata-only tag changes must not reprocess embeddings

**Decision**: `update_source()` must update tags without rebuilding chunks or calling the embedding client when title/content are unchanged.

**Rationale**: The acceptance criteria in `plan/07-tags.md` require tag changes not to reprocess embeddings, and this protects local embedding/runtime cost.

## Decision 6: Confirmed classification case

**Decision**: Keep the feature active because broad categories like `software`
and `financas` do not express reusable cross-cutting specifics such as `python`,
`postgres`, `rag`, `imposto` and `hnsw`.

**Rationale**: A source can remain in a controlled category like `software` while
tags distinguish implementation details used for retrieval and agent context.
Using only categories for these details would turn the category list into an
administrative taxonomy of technologies, mechanisms and temporary topics.

## Decision 7: Empty tag list in source patch clears tags

**Decision**: `PATCH /knowledge/sources/{source_id}` accepts `tag_ids: []` to
remove all tags from a source.

**Rationale**: Tags are optional metadata. Clearing them should not require a
separate endpoint and must remain a metadata-only update that does not regenerate
embeddings.
