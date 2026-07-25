# Implementation Plan: Busca Inteligente no Frontend

**Branch**: `feature/frontend-busca-inteligente` | **Date**: 2026-07-25 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `/specs/015-busca-inteligente-frontend/spec.md`

## Summary

Entregar uma rota Angular autenticada para pesquisar conhecimento, aplicar filtros de categoria/tag/projeto, limite e score mínimo, e abrir a fonte de cada chunk retornado. A implementação reutiliza o `KnowledgeApiService`, tipos e componentes compartilhados da Fase 01; consome exclusivamente os endpoints REST existentes e não altera backend, banco ou MCP.

## Technical Context

**Language/Version**: TypeScript 6, Angular 22, HTML e CSS.

**Primary Dependencies**: Angular standalone components, Router, Reactive Forms, HttpClient e RxJS; componentes e cliente HTTP definidos pela Fase 01.

**Storage**: Nenhum; formulário e resultados permanecem em memória da feature.

**Testing**: Testes unitários Angular para o cliente HTTP, mapeamento de request, formulário e estados críticos; `npm run typecheck` e `npm run build` em `frontend/`.

**Target Platform**: Navegadores modernos em desktop e mobile; frontend estático servido por Nginx.

**Project Type**: Aplicação web Angular com API FastAPI existente.

**Performance Goals**: Não adicionar latência de backend; debounce de autocomplete para limitar chamadas; a busca deve refletir o tempo de resposta existente da API (meta normal de até 1 s).

**Constraints**: Não expor token ou conteúdo como HTML; controles operáveis por teclado; viewport mínimo de 320 px; `limit` 1–50 e `min_score` 0–1; sem mudança de contrato REST.

**Scale/Scope**: Uma rota e componentes de busca; cinco endpoints já publicados; sem persistência de histórico, paginação ou mutação de metadados.

## Constitution Check

### Pre-design gate

- **Type safety**: PASS — contratos serão tipos TypeScript estritos no cliente HTTP compartilhado e na feature.
- **Architecture**: PASS — chamadas HTTP continuam em `core/`; componentes de apresentação e feature ficam isolados.
- **UX/accessibility**: PASS — HTML semântico, foco, ARIA, feedback de estados e layout responsivo são requisitos explícitos.
- **Security**: PASS — usa interceptor da fundação; nenhuma mensagem, log ou renderização pode revelar token ou confiar em HTML recebido.
- **Testing/quality**: PASS — tarefas incluem testes críticos e os comandos obrigatórios de tipo/build.
- **Performance**: PASS — autocomplete com debounce; a feature não altera a pesquisa vetorial ou banco.

### Post-design re-check

PASS. O contrato em [`contracts/frontend-search.md`](contracts/frontend-search.md) confirma que todos os requisitos são atendidos pelos endpoints existentes. Não há violação que exija justificativa de complexidade.

## Project Structure

### Documentation (this feature)

```text
specs/015-busca-inteligente-frontend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── frontend-search.md
└── tasks.md
```

### Source Code (repository root)

```text
frontend/src/app/
├── core/
│   └── knowledge-api.service.ts       # criado pela Fase 01; contratos e chamadas HTTP
├── shared/
│   ├── models/knowledge.models.ts     # criado pela Fase 01; tipos de domínio
│   └── components/                    # loading, error, empty e metadata selector
├── features/
│   └── search/
│       ├── search-page.component.ts
│       ├── search-page.component.html
│       └── search-page.component.css    # formulário, filtros e lista nesta primeira entrega
├── features/source-detail/
│   ├── source-detail.component.ts
│   ├── source-detail.component.html
│   └── source-detail.component.css
└── app.routes.ts                      # criado pela Fase 01; rota protegida

frontend/src/app/features/search/
└── *.spec.ts                          # testes unitários da feature
```

**Structure Decision**: Usar o layout Angular proposto pela Fase 01. Nesta primeira entrega, formulário, filtros e lista permanecem no componente de página para manter o estado local coeso; o cliente centralizado em `core/` preserva autenticação, tipagem e o tratamento HTTP uniforme. O detalhe mínimo da fonte é incluído para cumprir o fluxo de abertura por `source_id` público.

## Implementation Approach

1. Confirmar e completar os contratos públicos do cliente HTTP e dos tipos de domínio trazidos pela fundação.
2. Registrar a rota privada e construir a página de busca com formulário reativo e estado local explícito.
3. Adicionar filtros reutilizando o seletor de metadados; aplicar autocomplete de tags com debounce, cancelamento e seleção pelo teclado.
4. Renderizar resultados, localização, chips e link de fonte por `source_id`; manter score nulo distinguível de zero.
5. Acrescentar estados de carregamento, vazio, validação e erro seguro, seguidos de diagnóstico opt-in.
6. Cobrir fluxos críticos com testes e validar manualmente teclado e viewport móvel.

## API and Data Model Implications

- O request da busca segue [`contracts/frontend-search.md`](contracts/frontend-search.md): campos ausentes não são serializados, evitando enviar arrays vazios ou `min_score` nulo desnecessariamente.
- Categorias, tags e projetos são somente leitura. Tags são sugeridas pelo endpoint de autocomplete; não há criação implícita.
- Resultado usa `source_id` público para navegação e não expõe o ID interno do chunk como identificador de fonte.
- A rota de detalhe poderá ser inicialmente uma rota reservada, pois a tela de fonte pertence à Fase 05; seu contrato de parâmetro deve ser definido já na fundação.

## Test Strategy

- **Cliente HTTP**: serialização de filtros, omissão de valores não definidos e mapeamento de resposta incluindo score nulo e motivos opcionais.
- **Formulário**: consulta vazia, limites inválidos, score inválido, prevenção de envio duplicado e preservação de valores após erro.
- **Filtros**: remoção de chips, autocomplete com debounce e escolha de tag existente.
- **Página de resultados**: campos de resultado, link por UUID público, loading, vazio, `422`/`404` e indisponibilidade `502`/`503`.
- **Manual**: navegação por teclado, anúncios de estado e viewport de 320 px.
- **Build gate**: executar `npm run typecheck` e `npm run build` em `frontend/`.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| A Fase 01 ainda não está implementada | Bloquear início de código até que rota, guard, tipos e cliente centralizado existam; manter estas tarefas dependentes dela. |
| A tela de detalhe pertence à Fase 05 | Definir agora o parâmetro `sourceId` e integrar o link à rota reservada; validar o conteúdo detalhado quando a Fase 05 for entregue. |
| Resultados textuais sem score vetorial | Tratar `null` como valor indisponível, sem converter para zero. |
| Metadados tornam o formulário denso em mobile | Usar seletores recolhíveis, chips removíveis e testes de viewport mínimo. |
| Erros de embeddings podem conter detalhes internos | Fazer mapeamento por status e não renderizar corpo de erro cru. |

## Complexity Tracking

Nenhuma violação constitucional ou complexidade adicional a justificar.
