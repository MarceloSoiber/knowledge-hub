# Research: Limite Minimo de Relevancia

## Decision 1: Use a global default plus optional request override

**Decision**: Add `SEARCH_MIN_SCORE` as the default threshold and allow optional `min_score` in API/MCP requests.

**Rationale**: A global default protects normal usage, while request overrides support calibration by domain, test suite or client workflow without redeploying.

**Alternatives Considered**:

- Global-only setting: simpler, but slows calibration and makes client-specific experiments harder.
- Endpoint-only setting: flexible, but no safe default for existing callers.

## Decision 2: Filter after score calculation in the shared search service

**Decision**: Keep vector ordering in the repository and apply threshold filtering in `backend/app/services/search.py` after `KnowledgeChunkRead.score` is available.

**Rationale**: The service is shared by API search, API answer and MCP search. Filtering there prevents duplicate policy and keeps routes thin.

**Alternatives Considered**:

- SQL-level filter on cosine distance: possible, but would duplicate score semantics and is less direct while the current public score is built in Python.
- Route-level filtering: would miss MCP or answer flows unless repeated.

## Decision 3: Empty context is the safe RAG behavior

**Decision**: When no source reaches threshold, return `sources=[]` and call the answer client with no context.

**Rationale**: The existing system prompt already instructs the LLM to say it did not find the information when context is insufficient. This keeps one absence behavior across explicit empty context and weak context filtered to empty.

**Alternatives Considered**:

- Short-circuit with a fixed backend answer: safer but changes answer semantics and bypasses provider behavior; can be revisited if model compliance is weak.

## Decision 4: Log score metadata without query text

**Decision**: Log threshold, raw count, filtered count and score range; do not log user query text by default.

**Rationale**: Calibration needs score distribution signals, but questions may contain sensitive data.

**Alternatives Considered**:

- Full query logging: easier analysis, unacceptable privacy risk by default.
- No logging: safer but makes calibration blind.
