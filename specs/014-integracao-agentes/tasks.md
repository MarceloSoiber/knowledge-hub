# Tasks: Integracao com Agentes

**Input**: Design documents from `/specs/014-integracao-agentes/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mcp-agent-policy.md

**Tests**: Tests are required because this changes agent-facing behavior, write safety, prompt-injection boundaries and privacy behavior.

## Phase 1: Setup and Contract Decisions

**Purpose**: Lock the policy text and verify current MCP/RAG behavior before implementation.

- [X] T001 Review current MCP server instructions and tool descriptions in `mcp_server/server.py`.
- [X] T002 Review current MCP tool schemas and validation in `mcp_server/tools/knowledge.py`.
- [X] T003 Review current RAG prompt construction in `backend/app/services/rag.py`.
- [X] T004 Confirm final sensitive category setting names in `specs/014-integracao-agentes/research.md`.

---

## Phase 2: Foundational Policy Helpers

**Purpose**: Add reusable policy/guardrail services before changing adapters.

- [X] T005 Add `backend/app/services/agent_policy.py` with category-driven MCP instruction text, tool description helpers and decision-example fixtures.
- [X] T006 [P] Add `tests/test_agent_policy.py` covering category-driven search triggers, no-search cases, reformulation, write confirmation and untrusted context policy.
- [X] T007 Add sensitive category settings to `backend/app/core/settings.py`.
- [X] T008 [P] Add `backend/app/services/privacy.py` with normalized category matching and external-provider blocking helpers.
- [X] T009 [P] Add unit tests for sensitive category normalization and provider decisions in `tests/test_agent_policy.py` or `tests/test_knowledge_service.py`.

**Checkpoint**: Policy text and privacy checks are testable independently of MCP runtime wiring.

---

## Phase 3: User Story 1 - Agente consulta memoria quando ajuda (Priority: P1) MVP

**Goal**: MCP-connected agents receive clear search/no-search guidance by default.

**Independent Test**: Inspect server instructions from `mcp_server/server.py` and assert they tell agents to use `categories()` as the dynamic memory-domain inventory, while preserving no-search exclusions.

### Tests for User Story 1

- [X] T010 [P] [US1] Add MCP instruction test in `tests/test_mcp_knowledge.py` proving server instructions mention category inventory, self-contained tasks and one reformulation.
- [X] T011 [P] [US1] Add decision-example test in `tests/test_agent_policy.py` proving adding a category can make a matching request search-worthy without code changes.

### Implementation for User Story 1

- [X] T012 [US1] Wire `build_mcp_instructions()` from `backend/app/services/agent_policy.py` into `FastMCP(..., instructions=...)` in `mcp_server/server.py`.
- [X] T013 [US1] Ensure instruction text stays concise, ASCII-safe and treats fixed domains as examples only in `backend/app/services/agent_policy.py`.

**Checkpoint**: Agent clients see explicit memory-use policy before choosing tools.

---

## Phase 4: User Story 2 - Agente usa filtros e fontes adequadamente (Priority: P2)

**Goal**: Tool descriptions guide global-first search, valid filter discovery and detailed source retrieval.

**Independent Test**: Registered tool metadata/descriptions describe when to use search, categories/tags/projects/sources/source and filters.

### Tests for User Story 2

- [X] T014 [P] [US2] Add tests in `tests/test_mcp_knowledge.py` for `search` description covering global-first, optional filters and reformulation.
- [X] T015 [P] [US2] Add tests in `tests/test_mcp_knowledge.py` for discovery tool descriptions: `categories`, `tags`, `projects`, `project_sources`, `sources`, `source`, `tag_autocomplete`, including `categories` as memory-domain discovery.
- [X] T016 [P] [US2] Keep or extend forwarding tests proving `search` passes `category_ids`, `tag_ids`, `project_ids`, `min_score` and `include_match_reasons`.

### Implementation for User Story 2

- [X] T017 [US2] Add explicit descriptions to read tools in `mcp_server/server.py`.
- [X] T018 [US2] Refine `KnowledgeHit` and input field descriptions in `mcp_server/tools/knowledge.py` where useful for agent planning.
- [X] T019 [US2] Update `specs/014-integracao-agentes/contracts/mcp-agent-policy.md` if runtime descriptions differ from planned contract.

**Checkpoint**: Agents have enough metadata to choose global search, filters and source detail without guessing.

---

## Phase 5: User Story 3 - Escrita exige intencao explicita e permissao auditavel (Priority: P3)

**Goal**: Read-only and read-write MCP profiles remain distinct, and persistence stays confirmation-gated.

**Independent Test**: `build_mcp_scopes()` exposes only read by default; `ingest_text` rejects missing `knowledge:write`; docs and descriptions require confirmation.

### Tests for User Story 3

- [X] T020 [P] [US3] Add tests in `tests/test_mcp_knowledge.py` for `build_mcp_scopes()` with `MCP_WRITE_ENABLED=false` and `true`.
- [X] T021 [P] [US3] Extend `ingest_text` description test to assert explicit confirmation and no automatic conversation archiving.
- [X] T022 [P] [US3] Keep regression test proving `ingest_mcp_text` denies read-only scope before calling ingestion.

### Implementation for User Story 3

- [X] T023 [US3] Route `ingest_text` description through `backend/app/services/agent_policy.py`.
- [X] T024 [US3] Ensure `mcp_server/tools/knowledge.py:require_mcp_scope` remains the single write-scope gate for MCP ingestion.
- [X] T025 [US3] Document read-only/read-write profiles in `doc/API.md`.

**Checkpoint**: MCP persistence is opt-in by user intent and server profile.

---

## Phase 6: User Story 4 - Conteudo recuperado nao vira instrucao (Priority: P4)

**Goal**: Retrieved chunks are clearly treated as untrusted evidence in agent policy and RAG prompts.

**Independent Test**: A malicious retrieved chunk appears only as context, while prompt instructions preserve the trust boundary.

### Tests for User Story 4

- [X] T026 [P] [US4] Add RAG prompt test in `tests/test_knowledge_service.py` with retrieved text containing prompt injection.
- [X] T027 [P] [US4] Add agent policy test in `tests/test_agent_policy.py` for untrusted retrieved content wording.

### Implementation for User Story 4

- [X] T028 [US4] Update `backend/app/services/rag.py` prompt instructions to classify retrieved excerpts as untrusted evidence.
- [X] T029 [US4] Update MCP instructions in `backend/app/services/agent_policy.py` with the same trust boundary.

**Checkpoint**: Prompt injection in stored documents cannot masquerade as system/developer instruction.

---

## Phase 7: User Story 5 - Privacidade bloqueia envio externo de categorias sensiveis (Priority: P5)

**Goal**: Sensitive categories are not sent to external providers unless explicitly allowed by future override policy.

**Independent Test**: With provider `api` and sensitive category match, answer generation blocks before provider call; with provider `local`, it proceeds.

### Tests for User Story 5

- [X] T030 [P] [US5] Add service test in `tests/test_knowledge_service.py` proving answer generation blocks sensitive category context for external provider.
- [X] T031 [P] [US5] Add service test proving local provider permits the same sensitive category context.
- [X] T032 [P] [US5] Add test proving the privacy error message avoids leaking sensitive query/content.

### Implementation for User Story 5

- [X] T033 [US5] Call `backend/app/services/privacy.py` from `backend/app/services/rag.py` before external answer provider invocation.
- [X] T034 [US5] Add a focused exception type and sanitized error message for sensitive external-provider blocking.
- [X] T035 [US5] Decide whether ingestion/embedding also needs the same block with current provider settings; document final MVP behavior in `specs/014-integracao-agentes/contracts/mcp-agent-policy.md`.

**Checkpoint**: Sensitive retrieved content has an enforceable local-provider boundary.

---

## Phase 8: Documentation and Verification

**Purpose**: Align public docs, contracts and automated verification.

- [X] T036 [P] Update `doc/API.md` MCP section with search/no-search policy, global-first filters, reformulation, write confirmation, profiles, trust boundary and privacy behavior.
- [X] T037 [P] Update `specs/014-integracao-agentes/quickstart.md` if final test names or settings differ.
- [X] T038 [P] Update `specs/014-integracao-agentes/contracts/mcp-agent-policy.md` to match final runtime wording.
- [X] T039 Run `.venv/bin/python -m pytest tests/test_agent_policy.py tests/test_mcp_knowledge.py tests/test_knowledge_service.py tests/test_knowledge_api_integration.py`.
- [X] T040 Run any targeted quickstart checks from `specs/014-integracao-agentes/quickstart.md`.

---

## Dependencies & Execution Order

- **Phase 1**: Starts immediately and confirms existing behavior.
- **Phase 2**: Depends on Phase 1 decisions; blocks all policy wiring.
- **US1 (Phase 3)**: Depends on `agent_policy.py`; delivers MVP guidance.
- **US2 (Phase 4)**: Depends on policy descriptions; can run after US1.
- **US3 (Phase 5)**: Can run after Phase 2 and mostly in parallel with US2.
- **US4 (Phase 6)**: Depends on policy helper and RAG prompt inspection.
- **US5 (Phase 7)**: Depends on privacy helper and RAG flow understanding.
- **Phase 8**: Depends on final behavior.

## Parallel Opportunities

- T006, T008 and T009 can run in parallel after T005/T007 shape is known.
- T010 and T011 can be written in parallel.
- T014, T015 and T016 can be written in parallel.
- T020, T021 and T022 can be written in parallel.
- T026 and T027 can be written in parallel.
- T030, T031 and T032 can be written in parallel.
- T036, T037 and T038 can run in parallel after implementation stabilizes.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 so agents receive the correct default policy.
3. Complete US3 to keep persistence permissioned and confirmed.
4. Complete US4 to harden prompt-injection handling.
5. Validate with MCP and service tests.

### Incremental Delivery

1. Add policy helper and tests.
2. Wire MCP instructions.
3. Improve tool descriptions.
4. Verify read/write profile behavior.
5. Harden RAG trust boundary.
6. Add sensitive category privacy blocking.
7. Update docs and run full targeted test set.
