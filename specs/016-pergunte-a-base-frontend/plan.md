# Implementation Plan: Pergunte à Base no Frontend

**Branch**: `feature/frontend-pergunte-a-base` | **Date**: 2026-07-27 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `/specs/016-pergunte-a-base-frontend/spec.md`

## Summary

Entregar uma rota Angular autenticada para enviar perguntas ao RAG, restringir o contexto por metadados, exibir a resposta e auditar as fontes usadas. A implementação reutiliza `KnowledgeApiService`, tipos, autenticação e seletores compartilhados já existentes; consome apenas `POST /api/v1/knowledge/answer` e endpoints de metadados, sem mudanças no backend, banco ou MCP. Perguntas e resultados bem-sucedidos ficam apenas em memória da sessão da página.

## Technical Context

**Language/Version**: TypeScript 6, Angular 22, HTML e CSS.

**Primary Dependencies**: Angular standalone components, Router, Forms/Reactive Forms conforme padrão da feature existente, HttpClient, RxJS e Clipboard API; `KnowledgeApiService` e componentes compartilhados da fundação.

**Storage**: Nenhuma persistência nova. Estado de formulário, resultado e histórico vivem somente em memória do frontend.

**Testing**: Testes unitários Angular para cliente HTTP, serialização, formulário, cópia e estados críticos; `npm run typecheck`, `npm run build` e `npm test -- --watch=false` em `frontend/`.

**Target Platform**: Navegadores modernos desktop e mobile; frontend estático servido por Nginx.

**Project Type**: Aplicação web Angular consumindo API FastAPI existente.

**Performance Goals**: Não aumentar a latência do backend; autocomplete de tags com debounce e cancelamento; refletir a meta normal de resposta da API de até 1 s, ressalvado o tempo do LLM.

**Constraints**: Sem HTML confiável de resposta/fontes; controles por teclado e feedback ARIA; viewport mínimo de 320 px; `limit` 1–20 e `min_score` 0–1; cópia sem registrar conteúdo ou token; sem persistência de conversa.

**Scale/Scope**: Uma rota, estado local e componentes de formulário/resposta/fonte; um endpoint de resposta e os endpoints de filtros existentes; sem streaming, paginação ou mutação.

## Constitution Check

### Pre-design gate

- **Type safety**: PASS — contratos existentes em `core/knowledge.types.ts` serão reutilizados e os novos estados locais terão tipos estritos.
- **Architecture**: PASS — chamadas HTTP permanecem no `KnowledgeApiService`; a feature coordena apresentação e formulário, sem lógica de negócio de backend.
- **UX/accessibility**: PASS — HTML semântico, foco visível, ARIA, feedback imediato, cópia confirmada e layout responsivo são requisitos explícitos.
- **Security**: PASS — interceptores existentes mantêm autenticação; conteúdo remoto é exibido como texto e erros/cópia não podem vazar token ou detalhes internos.
- **Testing/quality**: PASS — plano prevê testes críticos e typecheck/build/test; não muda caminhos de serviços FastAPI nem exige cobertura backend.
- **Performance**: PASS — não altera embeddings, busca ou banco; debounce evita chamadas excessivas no autocomplete.

### Post-design re-check

PASS. O contrato em [`contracts/frontend-answer.md`](contracts/frontend-answer.md) já é suportado pelo endpoint existente e pelos tipos compartilhados. Não há violação que exija justificativa de complexidade.

## Project Structure

### Documentation (this feature)

```text
specs/016-pergunte-a-base-frontend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── frontend-answer.md
```

### Source Code (repository root)

```text
frontend/
├── src/app/
│   ├── app.routes.ts                         # rota protegida da pergunta
│   ├── core/
│   │   ├── knowledge-api.service.ts           # cliente tipado reutilizado
│   │   └── knowledge.types.ts                 # contratos de resposta reutilizados
│   ├── features/
│   │   └── ask/                               # componente, template e estilos da feature
│   └── shared/
│       └── metadata-selector/                 # reutilizar/adaptar somente se necessário
└── src/styles.css                             # estilos centralizados compartilhados, se necessário
```

**Structure Decision**: Implementar a tela isolada em `frontend/src/app/features/ask/`; preservar `core/` como limite de HTTP e reutilizar `shared/` para comportamentos já comuns. Não criar biblioteca de estado nem persistência adicional.

## Complexity Tracking

Nenhuma violação da constituição a justificar.
