# Implementation Plan: Organização do acervo no frontend

**Branch**: `019-organizacao-frontend` | **Date**: 2026-07-27 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification based on `plan/frontend/06-organizacao.md`

## Summary

Entregar uma rota Angular privada de Organização para CRUD de categorias/tags, gestão de projetos e consulta de suas fontes. O cliente manterá o HTTP e os contratos em `KnowledgeApiService`, introduzirá um catálogo de metadados pequeno e reativo em `core` e reutilizará o diálogo de confirmação e os estados compartilhados. O `MetadataSelectorComponent` passará a oferecer autocomplete de tags a Ingestão e detalhe, enquanto projetos arquivados deixam o catálogo ativo imediatamente. Não haverá alteração de FastAPI, PostgreSQL, MCP, OpenAPI ou API pública.

## Technical Context

**Language/Version**: TypeScript 6.0, Angular 22.0; API FastAPI existente somente como contrato  
**Primary Dependencies**: Angular standalone components, signals, Router, HttpClient, RxJS (`debounceTime`, `distinctUntilChanged`, `switchMap`); componentes `ConfirmDialog`, `LoadingState`, `ErrorState`, `EmptyState`, `MetadataSelector`  
**Storage**: Estado transitório em memória; PostgreSQL + pgvector permanecem inalterados  
**Testing**: Angular unit tests com `HttpTestingController` e testes de componentes; `npm run typecheck`, `npm test -- --watch=false`, `npm run build`  
**Target Platform**: Navegadores modernos desktop/mobile; Angular servido por Nginx  
**Project Type**: Aplicação web Angular que consome API FastAPI  
**Performance Goals**: Uma carga por coleção/entrada e atualizações locais por resposta; autocomplete com debounce/cancelamento; endpoints sob 1 s em condição normal  
**Constraints**: Tipagem estrita, IDs públicos, sem recarga global, sem expor token/corpo remoto, acessível por teclado e a partir de 320 px  
**Scale/Scope**: Uma rota, páginas/componentes de gestão, expansão pontual de core/shared e adaptação dos consumidores existentes de metadados

## Constitution Check

### Pre-design gate

- **Code quality**: PASS — URLs e payloads ficam em `core`; regras de tela ficam em `features/organization`; o shared mantém comportamento genérico.
- **Testing**: PASS — haverá testes HTTP, catálogo, CRUD, transições de status, conflitos e autocomplete, mais os quality gates Angular.
- **UX/accessibility**: PASS — estados compartilhados, `fieldset`/labels, diálogo, `aria-live`, combobox/listbox e foco são requisitos explícitos.
- **Performance**: PASS — catálogo reativo evita reload completo; autocomplete cancela consultas obsoletas; nenhum fluxo altera embeddings ou busca vetorial.
- **Technology/documentation**: PASS — usa contratos já publicados; sem endpoint novo, portanto `doc/API.md` não muda.

### Post-design re-check

PASS. Os documentos de [dados](data-model.md) e [contrato](contracts/frontend-organization.md) só consomem APIs existentes. Não há violação que justifique complexidade adicional.

## Project Structure

```text
frontend/src/app/
├── app.routes.ts                                      # rota /organizacao
├── core/
│   ├── knowledge.types.ts                             # payloads CRUD tipados
│   ├── knowledge-api.service.ts                       # métodos HTTP de organização
│   ├── knowledge-api.service.spec.ts                  # contratos HTTP
│   ├── metadata-catalog.service.ts                    # signals, carga e aplicação de respostas
│   └── metadata-catalog.service.spec.ts
├── features/
│   ├── organization/
│   │   ├── organization-page.component.{ts,html,css,spec.ts}
│   │   ├── classification-manager.component.{ts,html,css,spec.ts}
│   │   └── project-sources.component.{ts,html,css,spec.ts} # /organizacao/projetos/:projectId/fontes
│   ├── ingestion/                                    # troca de carregamento direto pelo catálogo
│   ├── search/                                       # idem para filtros
│   ├── ask/                                          # idem para filtros
│   ├── library/                                      # idem para filtros, se expostos
│   └── source-detail/                                # idem para edição
├── layout/authenticated-layout.component.html         # item Organização
└── shared/
    └── metadata-selector/metadata-selector.component.ts # autocomplete de tags
```

**Structure Decision**: `organization/` contém orquestração, formulários e visão de fontes; `MetadataCatalogService` é a única coordenação compartilhada de leituras/invalidações. Nenhum componente de feature chama `HttpClient` diretamente e nenhuma regra de CRUD entra no seletor compartilhado.

## Implementation Approach

### 1. Completar a fronteira HTTP e os tipos

- Adicionar a `knowledge.types.ts` payloads explícitos `CategoryWrite`, `TagWrite`, `ProjectWrite` e `ProjectPatch`; `Project`/`KnowledgeSource` existentes permanecem canônicos.
- Expandir `KnowledgeApiService` com `create/update/deleteCategory`, `create/update/deleteTag`, `create/updateProject`, `archiveProject`, `reactivateProject` e `projectSources`. Manter paths codificados, métodos e respostas exatamente como o contrato.
- Cobrir cada método com `HttpTestingController`, inclusive `status` opcional de projetos e `q`/`limit` de autocomplete.

### 2. Introduzir catálogo reativo de metadados

- Criar `MetadataCatalogService` com signals readonly para categorias, tags, projetos e estado de carga/erro, e métodos de carregar/recarregar cada coleção. Deduplicar carga concorrente e preservar dados válidos durante retry.
- Aplicar a resposta canônica de create/update/delete ao catálogo em vez de fazer reload global. Após archive/reactivate, substituir o projeto e expor `activeProjects` como derivado.
- Migrar Busca, Pergunte, Ingestão, Biblioteca e detalhe para obter opções do catálogo. Todos devem reagir a mudanças; seleções removidas devem ser revisadas, mas não enviadas silenciosamente como outra alteração.

### 3. Criar rota e gestão de categorias/tags

- Registrar `/organizacao` no `AuthenticatedLayoutComponent` e incluir item no menu apenas com a rota implementada.
- Criar `OrganizationPageComponent` com navegação semântica para Categorias, Tags e Projetos. Cada seção representa carga, erro/retry, vazio e sucesso sem misturar estados.
- Criar `ClassificationManagerComponent` reutilizável com lista, formulário explícito de criar/editar, validação local, anúncio de sucesso e `ConfirmDialogComponent` para exclusão. A confirmação somente chama DELETE no evento `confirm`.
- Mapear conflitos de nomes a correção do rascunho e `409` de exclusão a “item em uso; reclassifique as fontes antes de remover”; conservar a lista/catálogo em todos os erros.

### 4. Adicionar autocomplete de tags nos formulários consumidores

- Evoluir `MetadataSelectorComponent` com um campo de tags acessível (`combobox`/`listbox`), chips removíveis por teclado e chamadas a `tagAutocomplete` após uma consulta útil e debounce curto.
- Usar `switchMap` e limpar sugestões quando a consulta muda, não tiver texto ou o controle for destruído; filtrar IDs já selecionados e manter seleção manual mesmo se uma sugestão falhar.
- Migrar Ingestão e detalhe de fonte; revisar Busca/Pergunte quando expõem seleção de tags, preservando seus contratos de filtros e sem criar tags implicitamente.

### 5. Implementar gestão e ciclo de vida de projetos

- Na seção Projetos, carregar a visão ativa por padrão e alternar de forma acessível entre `active` e `archived`; mostrar status, descrição, datas e ações compatíveis com o estado.
- Criar/editar em formulário com PATCH mínimo (não enviar corpo vazio); bloquear controles durante mutação e preservar rascunho em erro.
- Arquivar/reativar somente após confirmação contextual. Em sucesso, atualizar o catálogo, mover o item de visão conforme status e anunciar resultado. Projeto arquivado fica ausente de `activeProjects`, mas continua apresentável quando vier associado a uma fonte.

### 6. Listar fontes de projeto e garantir regressão

- Registrar a rota filha `/organizacao/projetos/:projectId/fontes` para `ProjectSourcesComponent`; carregar `projectSources(id)` e mostrar lista semântica de título, tipo, URI e chips, estado vazio e retry. Cada item aponta para `/sources/:sourceId`.
- Testar desde o serviço até as telas: catálogo sem reload, CRUD e conflitos, confirmação, transições ativo/arquivado, fontes, autocomplete/cancelamento e regressão dos consumidores.
- Validar teclado/foco/ARIA, layout em 320 px, 768 px e desktop; executar o [quickstart](quickstart.md).

## Data Model / API Implications

- Sem migração, código Python, endpoint, contrato OpenAPI, MCP ou alteração de `doc/API.md`.
- O catálogo apenas espelha `Category`, `Tag` e `Project` existentes; os rascunhos e sugestões locais estão em [data-model.md](data-model.md).
- `GET /projects?status=active` é a fonte da visão ativa; o cache pode carregar ambas as visões e deve aplicar respostas de estado sem inventar transições.
- `GET /tags/autocomplete` é usado para sugestão; `GET /tags` ainda é usado pela tela de gestão/catálogo. Nenhuma sugestão cria tag automaticamente.

## Test Strategy

- **Core**: métodos CRUD/projetos/fontes e parâmetros HTTP; sinais do catálogo, atualização canônica, derivação de ativos e retry.
- **Organization**: criação, edição, cancelamento/confirmação de exclusão, conflitos, status, fontes e estados vazio/erro.
- **Shared/consumers**: autocomplete com teclado, debounce, resposta obsoleta, seleção única e atualização observável em Ingestão, detalhe e filtros existentes.
- **Acessibilidade/manual**: landmarks, labels, diálogo/foco, combobox, regiões de status e responsividade em 320 px/768 px/desktop.
- **Quality gate**: `npm run typecheck`, `npm test -- --watch=false`, `npm run build` em `frontend/`.

## Risk Notes

- O backend informa apenas `409`, não a contagem de fontes em uso; a UI deve explicar a ação necessária sem inventar números ou detalhes.
- Mudanças concorrentes podem produzir `404`/`409`; nunca remover/substituir o estado local antes de sucesso e sempre manter rascunhos recuperáveis.
- Arquivar um projeto não remove associações; esconder projetos arquivados em detalhes históricos apagaria contexto e viola o contrato.
- Autocomplete é uma otimização de descoberta, não validação de integridade; o backend permanece a fonte final para IDs e conflitos.

## Complexity Tracking

Nenhuma violação da constituição identificada.
