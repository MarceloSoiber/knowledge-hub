# Feature Specification: Reindexacao e Backup

**Feature Branch**: `011-reindexacao-backup`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Com base no planejamento `plan/10-reindexacao-backup.md`, planejar a implementacao."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reindexar embeddings com seguranca (Priority: P1)

Um operador troca provider, modelo, dimensao ou versao de embedding e consegue reprocessar fontes existentes a partir do conteudo original preservado, sem perder a base nem misturar vetores antigos com novos.

**Why this priority**: O valor central do plano e permitir evoluir embeddings preservando conhecimento pessoal. Sem reindexacao segura, troca de modelo exige risco manual ou recriacao completa da base.

**Independent Test**: Criar fontes com chunks pendentes ou incompativeis, executar reindexacao em `--dry-run`, depois executar com lote pequeno e confirmar que novos vetores compativeis sao criados e que a busca usa apenas a configuracao ativa.

**Acceptance Scenarios**:

1. **Given** fontes existentes com embeddings incompativeis com a configuracao ativa, **When** o operador executa reindexacao em `--dry-run`, **Then** o sistema lista candidatos, motivo, totais estimados e nao altera nenhum vetor.
2. **Given** candidatos de uma categoria especifica, **When** o operador executa reindexacao com filtro de categoria e tamanho de lote, **Then** somente chunks dessas fontes sao processados ate o limite informado.
3. **Given** espaco suficiente para manter vetores antigos, **When** uma reindexacao executa, **Then** os novos vetores sao validados antes de os antigos deixarem de ser a versao ativa para busca.

---

### User Story 2 - Retomar reindexacao interrompida (Priority: P2)

Um operador interrompe a reindexacao ou enfrenta falha em uma fonte e consegue retomar o trabalho sem duplicar chunks nem corromper as fontes que ja foram processadas.

**Why this priority**: Reindexacao pode ser demorada e dependente de provider externo/local. Retomada confiavel evita recomeco caro e reduz risco operacional.

**Independent Test**: Simular interrupcao apos um subconjunto de chunks, executar novamente com os mesmos filtros e confirmar que chunks ja compativeis sao ignorados ou reutilizados e erros permanecem rastreaveis por fonte.

**Acceptance Scenarios**:

1. **Given** um job interrompido apos processar parte dos chunks, **When** o operador executa o mesmo comando novamente, **Then** apenas chunks pendentes, falhos ou ainda incompativeis sao reprocessados.
2. **Given** uma fonte que falha durante embedding, **When** o job continua, **Then** a falha fica registrada para essa fonte/chunk e outras fontes podem concluir normalmente.
3. **Given** o mesmo conteudo normalizado e a mesma configuracao ativa, **When** a retomada encontra embedding compativel ja existente, **Then** o sistema evita chamada redundante ao provider quando a reutilizacao estiver habilitada.

---

### User Story 3 - Fazer backup e restaurar a base (Priority: P3)

Um operador cria um backup documentado, guarda fora do volume principal e restaura em um banco vazio reproduzindo fontes, relacoes, conteudo original e capacidade de busca.

**Why this priority**: O objetivo explicito e recuperar a base sem perder conhecimento pessoal. Backup sem restauracao testada nao fecha o risco.

**Independent Test**: Executar `pg_dump` documentado, restaurar em banco vazio, inicializar a aplicacao e confirmar contagens de fontes, categorias, tags, projetos, chunks e busca.

**Acceptance Scenarios**:

1. **Given** uma base com fontes, categorias, tags, projetos, chunks e conteudo original, **When** o operador executa o backup documentado, **Then** o artefato contem tabelas relacionais, configuracao operacional permitida e conteudo original preservado.
2. **Given** um banco vazio com pgvector habilitado, **When** o operador restaura o backup, **Then** fontes, relacoes e buscas basicas voltam a funcionar.
3. **Given** embeddings muito grandes ou caros, **When** a estrategia escolhida for regenerar vetores em vez de inclui-los no dump, **Then** o runbook explicita o custo, os comandos de reindexacao e os criterios de validacao.

---

### User Story 4 - Automatizar backup apos prova de restauracao (Priority: P4)

Um operador configura retencao, criptografia e destino externo para backups agendados somente depois que uma restauracao real foi executada e documentada.

**Why this priority**: Automacao sem restauracao validada cria falsa seguranca. O plano exige testar restauracao antes de agendar.

**Independent Test**: Verificar que o runbook exige evidencia de restauracao antes de habilitar agendamento e que logs/saidas nao imprimem tokens nem conteudo sensivel.

**Acceptance Scenarios**:

1. **Given** nenhuma restauracao documentada, **When** o operador segue o runbook, **Then** o agendamento e tratado como bloqueado.
2. **Given** restauracao validada, retencao definida, criptografia configurada e destino externo escolhido, **When** backup agendado roda, **Then** o artefato e produzido sem imprimir tokens ou conteudo sensivel nos logs.
3. **Given** backups antigos alem da janela de retencao, **When** a rotina de retencao executa, **Then** apenas artefatos elegiveis sao removidos do destino configurado.

### Edge Cases

- Fonte sem `content_text` preservado nao pode ser reindexada automaticamente; deve ser reportada como bloqueada.
- Mudanca de dimensao exige coluna pgvector compativel antes de ativar os novos vetores.
- Falha do provider durante um lote nao deve marcar job nem batch como concluido.
- Reexecutar o mesmo job nao pode duplicar chunks nem apagar associacoes de categorias, tags ou projetos.
- Conteudo sensivel, tokens e textos completos nao devem aparecer em logs de reindexacao, backup ou restauracao.
- Backup pode incluir embeddings ou optar por regeneracao; a escolha deve ser explicita no manifesto/runbook.
- Restauracao com extensao pgvector ausente deve falhar cedo com mensagem acionavel.
- Destino externo indisponivel deve falhar o backup antes de registrar sucesso.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a CLI command for reindexation with `--dry-run`, source/category selection and batch-size limit.
- **FR-002**: System MUST reindex from preserved original source content, not from truncated search snippets.
- **FR-003**: System MUST persist reindex progress, status and sanitized error details per run and per source or chunk.
- **FR-004**: System MUST make reindexation resumable and idempotent for the same active embedding configuration.
- **FR-005**: System MUST create and validate new compatible vectors before changing active search eligibility where storage allows the old vectors to remain available.
- **FR-006**: System MUST validate candidate counts, vector dimensions, embedding statuses and sample search results before reporting reindex success.
- **FR-007**: System MUST ensure a failed source does not corrupt or roll back unrelated successfully processed sources.
- **FR-008**: System MUST provide documented backup and restore commands based on `pg_dump`/`pg_restore` or `psql`.
- **FR-009**: Backup documentation MUST cover tables, app configuration, original source content and the explicit choice to include or regenerate embeddings.
- **FR-010**: System MUST define retention, encryption expectations and an off-primary-volume destination for backups.
- **FR-011**: System MUST require a documented restore test before enabling scheduled backup automation.
- **FR-012**: System MUST avoid printing tokens, full source content or other sensitive values in logs and command output.
- **FR-013**: System MUST document a restore validation checklist covering sources, relations and search behavior.
- **FR-014**: System MUST update `doc/API.md` or operational docs when public commands or operational behavior changes.

### Key Entities *(include if feature involves data)*

- **ReindexRun**: One operator-triggered reindex execution with target embedding config, filters, dry-run flag, status, counters and sanitized errors.
- **ReindexItem**: Per-source or per-chunk progress row used for resumability, failure isolation and audit.
- **BackupArtifact**: A produced database backup with timestamp, include-embeddings choice, checksum, encryption state, destination and restore-test status.
- **RestoreValidation**: Checklist/evidence that a backup was restored into an empty database and validated.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Reindex dry-run reports candidate totals and reasons without modifying `knowledge_chunks` or `embedding_batches`.
- **SC-002**: Re-running an interrupted reindex command processes only remaining incompatible/failed chunks and does not duplicate chunks.
- **SC-003**: A source-level embedding failure is recorded for that source/chunk while other selected sources can finish.
- **SC-004**: Reindex completion validates counts, vector dimensions and at least one sample retrieval before reporting success.
- **SC-005**: A documented restore into an empty database reproduces source counts, relation counts and basic search results.
- **SC-006**: Backup and reindex logs contain no auth tokens and no full original source content.

## Assumptions

- Feature `010-versionamento-embeddings` provides embedding batches, chunk provenance fields, active compatibility checks and pending detection primitives.
- `DocumentSource.content_text` is the preserved original text source for reindexation.
- The first implementation uses synchronous CLI/service execution rather than a long-running worker queue.
- Backup automation can be documented and scaffolded, but scheduling remains disabled until a real restore test is recorded.
- Encryption may be implemented by documented external tooling such as `gpg` or age-compatible command flow, without storing encryption keys in the database.
