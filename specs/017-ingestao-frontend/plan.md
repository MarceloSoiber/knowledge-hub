# Implementation Plan: Ingestão de Conhecimento no Frontend

**Branch**: `feature/frontend-ingestao` | **Date**: 2026-07-27 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `/specs/017-ingestao-frontend/spec.md`

## Summary

Entregar uma rota Angular autenticada para ingerir arquivos e textos com categorias obrigatórias e tags/projetos opcionais. A feature reutilizará autenticação, `KnowledgeApiService`, tipos e seletor compartilhado já existentes; enviará apenas `POST /uploads`, `POST /texts` e os `GET`s de metadados. Cada aba manterá rascunho e estado próprios em memória, exibirá processamento indeterminado e tratará sucesso, duplicidade e falhas sem alterar backend, banco, MCP ou contratos REST.

## Technical Context

**Language/Version**: TypeScript 6, Angular 22, HTML e CSS.

**Primary Dependencies**: Angular standalone components, Router, Forms/Reactive Forms conforme padrão consolidado, HttpClient, RxJS; `KnowledgeApiService`, `MetadataSelectorComponent` e componentes de estado compartilhados.

**Storage**: Sem persistência nova. Arquivo, texto, metadados selecionados, resultados e erros vivem em memória da rota; o conteúdo persistente continua em PostgreSQL + pgvector pelo backend.

**Testing**: Testes unitários Angular para serialização `FormData`/JSON, validações, estados pendentes e tratamento de respostas; `npm run typecheck`, `npm test -- --watch=false` e `npm run build`.

**Target Platform**: Navegadores modernos desktop e mobile; frontend Angular servido pelo Nginx existente.

**Project Type**: Aplicação web Angular consumindo API FastAPI existente.

**Performance Goals**: Nenhuma requisição duplicada por formulário durante processamento; carregamento único de metadados por entrada na rota, com recarga explícita após falha; nenhuma barra de progresso fictícia.

**Constraints**: Formatos `.txt`, `.md`, `.pdf` até 10 MB; texto e título válidos; categorias obrigatórias; conteúdo remoto como texto; controles por teclado, feedback ARIA e viewport mínimo de 320 px; não persistir rascunhos nem vazar token/detalhes internos.

**Scale/Scope**: Uma rota protegida, dois formulários, estado transitório, adaptação mínima de componentes compartilhados e testes frontend. Sem upload em lote, progresso real, alteração de API ou persistência de rascunhos.

## Constitution Check

### Pre-design gate

- **Type safety**: PASS — payloads e respostas já são tipados em `core/knowledge.types.ts`; estados de abas e resposta de duplicidade terão tipos explícitos.
- **Architecture**: PASS — HTTP permanece em `KnowledgeApiService`; a feature fica em `features/ingestion/`; backend, rotas FastAPI e serviços não mudam.
- **Testing/quality**: PASS — plano exige cobertura de serialização e fluxos críticos, além de typecheck, testes e build.
- **UX/accessibility**: PASS — campos semânticos, labels, `fieldset`, foco visível, regiões ARIA, mensagens acionáveis e responsividade são requisitos explícitos.
- **Performance**: PASS — não altera embedding/banco; bloqueio de duplicidade e indicador indeterminado respeitam o contrato disponível.
- **Documentation**: PASS — a API não muda; contrato local documenta consumo existente, sem necessidade de atualizar `doc/API.md`.

### Post-design re-check

PASS. Os contratos em [`contracts/frontend-ingestion.md`](contracts/frontend-ingestion.md) usam somente endpoints e payloads publicados; não há violação que exija rastreamento de complexidade.

## Project Structure

### Documentation (this feature)

```text
specs/017-ingestao-frontend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── frontend-ingestion.md
```

### Source Code (repository root)

```text
frontend/
└── src/
    ├── app/
    │   ├── app.routes.ts                         # registra /ingestao no shell protegido
    │   ├── core/
    │   │   ├── knowledge-api.service.ts           # reutilizar upload/ingestText/metadata
    │   │   └── knowledge.types.ts                 # reutilizar contratos existentes
    │   ├── features/
    │   │   └── ingestion/
    │   │       ├── ingestion-page.component.ts
    │   │       ├── ingestion-page.component.html
    │   │       ├── ingestion-page.component.css
    │   │       └── ingestion-page.component.spec.ts
    │   └── shared/
    │       ├── loading-state/
    │       ├── error-state/
    │       └── metadata-selector/                # reutilizar; adaptar só se necessário
    └── styles.css                                 # somente tokens/ajustes globais necessários
```

**Structure Decision**: Isolar a orquestração e os rascunhos em `features/ingestion/`. `core/` continua sendo o limite exclusivo para HTTP e contratos; `shared/` segue sem regra de negócio de ingestão. Não introduzir biblioteca de estado ou serviços de persistência.

## Implementation Approach

### 1. Rota, navegação e esqueleto da feature

- Adicionar a rota protegida `/ingestao` abaixo de `AuthenticatedLayoutComponent` e a entrada correspondente na navegação somente junto da página implementada.
- Criar componente standalone de ingestão com duas abas semânticas (`tablist`, `tab`, `tabpanel`), estado ativo e foco/teclado conforme o padrão Angular já usado.
- Manter estado de arquivo e texto independente para que alternar de aba não descarte o outro rascunho; não persistir nenhum deles fora da vida da rota.

### 2. Carregamento e seleção de metadados

- Carregar categorias, tags e projetos por `forkJoin` usando apenas `KnowledgeApiService`; exibir `LoadingStateComponent` enquanto necessário e `ErrorStateComponent` com ação de recarga em caso de falha.
- Aplicar o `MetadataSelectorComponent` aos dois formulários, passando seleção, estado de carregamento/erro e `categoriesRequired=true`.
- Confirmar que o seletor emite IDs numéricos, únicos e que o erro de categoria obrigatória seja associado ao `fieldset` da aba. Adaptar o shared somente para essa necessidade geral e sem criar fluxo de mutação de metadados.

### 3. Formulário de arquivo e validação prévia

- Implementar campo de arquivo rotulado, resumo de tipos aceitos e limite de 10 MB. Validar presença, extensão sem distinção de maiúsculas e `File.size` antes de chamar a API.
- Validar a seleção de ao menos uma categoria. Exibir erros próximos aos controles e com associação ARIA; manter tags e projetos opcionais.
- No envio válido, chamar `api.upload(file, categoryIds, tagIds, projectIds)`. Confiar no `FormData` do serviço e não definir `Content-Type` manualmente.
- Durante a chamada, armazenar estado `submitting`, desabilitar seleção/submit desse fluxo e anunciar "Processando arquivo e gerando embeddings" como progresso indeterminado. Não criar porcentagem, polling ou cancelamento.

### 4. Formulário de texto e validação prévia

- Implementar título e `textarea` com labels, contagem/limite útil para 255 caracteres e erro local para valores vazios após `trim`; reutilizar a mesma regra de categoria.
- Montar `KnowledgeTextIngestRequest` com `title`/`content` normalizados e omitir arrays opcionais vazios. Chamar `api.ingestText(payload)`.
- No processamento, bloquear apenas controles e reenvio da aba de texto, anunciando o mesmo estado indeterminado. Não enviar novamente se o estado já for `submitting`.

### 5. Resultado e recuperação de erro

- Reutilizar `KnowledgeUploadResponse` para uma confirmação acessível que mostra título, UUID público e chunks; oferecer `RouterLink` a `/sources/:sourceId`.
- Após `201`, limpar apenas o rascunho que originou o resultado e conservar a confirmação até a próxima ação relevante. Limpar a seleção visual do arquivo com abordagem compatível com o navegador.
- Criar adaptador de erro local, inspirado nas features de busca/pergunta, que converte `400`, `404`, `413`, `422`, `502` e `503` em mensagens locais seguras. Preservar rascunho em todos esses casos.
- Para `409`, ler unicamente `HttpErrorResponse.error.detail.existing_source_id`, validar UUID e apresentar uma ação para `/sources/:sourceId`. Se ausente, mostrar duplicidade sem link. Não usar texto cru do backend nem oferecer sobrescrita.
- Deixar `401` sob responsabilidade do interceptor existente; não duplicar logout/redirecionamento na feature.

### 6. Testes e verificação

- Cobrir `KnowledgeApiService` com `HttpTestingController`: `upload` envia `FormData` com arquivo e campos repetidos corretos; `ingestText` envia JSON e omite arrays vazios quando aplicável.
- Cobrir a feature para abas/rascunhos independentes, campos obrigatórios, extensão/tamanho de arquivo, bloqueio de reenvio, carregamento/recarregamento de metadados e limpeza somente após sucesso.
- Simular `201`, `409` com e sem `existing_source_id`, `400`, `404`, `413`, `422`, `502` e `503`; conferir mensagens seguras, link válido somente na duplicidade estruturada e preservação de dados.
- Verificar semântica/ARIA, operação por teclado das abas e dos controles, além de responsividade manual em 320 px, 768 px e desktop.
- Executar os comandos de qualidade definidos no quickstart e revisar que nenhuma mudança de backend ou `doc/API.md` seja necessária.

## Data Model / API Implications

- Não há alteração de PostgreSQL, pgvector, FastAPI, MCP, OpenAPI ou migração.
- O cliente já define `KnowledgeTextIngestRequest` e `KnowledgeUploadResponse`; a feature introduz apenas tipos locais de rascunho/estado, documentados em [`data-model.md`](data-model.md).
- Arquivos seguem `multipart/form-data` com IDs repetidos; texto segue JSON. A autenticação Bearer é aplicada pelos interceptores existentes.
- `409` possui o contrato estruturado `detail.existing_source_id`, usado exclusivamente para link da fonte existente. Outras mensagens de detalhe não são apresentadas diretamente.
- Como não há mudança de comportamento da API, `doc/API.md` não requer atualização nesta entrega.

## Test Strategy

- **Unitário — core**: serialização de `FormData` e JSON pelo cliente HTTP, mantendo URLs e payloads do contrato.
- **Unitário — feature**: validações locais, transições de estado por aba, envio único, normalização de erro, duplicidade e limpeza pós-sucesso.
- **Integração de rota**: acesso autenticado a `/ingestao`, carregamento de metadados, envio e navegação a `/sources/:sourceId`.
- **Acessibilidade/manual**: tabs, labels, regiões de status/alerta, foco e layout em 320 px/768 px/desktop.
- **Quality gate**: `npm run typecheck`, `npm test -- --watch=false` e `npm run build` em `frontend/`.

## Risk Notes

- A validação de `File.type` é inconsistente entre navegadores; a extensão publicada é a validação local confiável, e o backend continua sendo a decisão final sobre formato e conteúdo extraído.
- Browsers podem limpar um `<input type="file">` após interação/programação; preservar arquivo após falha deve ser feito quando possível, com mensagem clara se uma nova escolha for exigida.
- A resposta de erro pode variar no proxy/camada HTTP. O link de duplicidade só pode existir quando o campo estruturado de UUID estiver presente e for válido.
- A geração de embeddings pode demorar ou falhar; sem endpoint de progresso, qualquer porcentagem seria enganosa. O estado indeterminado e o bloqueio de reenvio mitigam duplicidade sem prometer duração.
- Uma recarga de metadados pode invalidar seleções removidas no servidor; a UI deve manter o rascunho e permitir revisão, enquanto o backend garante integridade no envio.

## Complexity Tracking

Nenhuma violação da constituição a justificar.
