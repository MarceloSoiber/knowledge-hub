# Research: Avaliacao do RAG

## Decision: Use a separate CLI runner, not pytest, as the evaluation entry point

**Rationale**: The source plan explicitly asks for a runner separated from unit tests. RAG evaluation can call providers, use a live database and produce reports; mixing that with normal pytest would make CI slow and flaky.

**Alternatives considered**:

- Pytest-only evaluation: rejected because provider calls and latency reports do not belong in the fast unit-test suite.
- New API endpoint: rejected for MVP because evaluation is an operator workflow and should not expand public surface area.

## Decision: Store datasets and reports as versioned files

**Rationale**: The feature needs reproducible baselines and candidate comparisons. JSON files are simple to review, diff, archive as CI artifacts and use locally.

**Alternatives considered**:

- Persist evaluation runs in PostgreSQL: rejected for MVP because it adds schema and lifecycle complexity without being required for the first gate.
- Markdown-only datasets: rejected because metric computation needs strict validation.

## Decision: Grade answer correctness with deterministic essential points in MVP

**Rationale**: LLM judges add cost, nondeterminism and another model dependency. Essential-point matching is simple, testable and enough to catch many regressions.

**Alternatives considered**:

- Exact answer matching: rejected because acceptable RAG answers can vary in wording.
- LLM-as-judge by default: deferred until there is a specific need and stable evaluation budget.

## Decision: Match expected chunks by stable public references

**Rationale**: Internal integer ids can change across reingestion and restores. Public source ids plus chunk metadata make datasets more portable.

**Alternatives considered**:

- Integer chunk ids only: rejected because it makes baselines fragile.
- Full-content matching only: rejected because chunk text can change with normalization/chunking and would make authoring datasets noisy.

## Decision: Keep API/MCP contracts unchanged

**Rationale**: The feature evaluates existing behavior. Adding endpoints would expand security, documentation and support scope without solving the core requirement.

**Alternatives considered**:

- Diagnostics endpoint for evaluation: deferred until a frontend or remote automation use case exists.
