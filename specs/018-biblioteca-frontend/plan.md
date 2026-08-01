# Implementation Plan: Biblioteca e manutenção de fontes

**Branch**: `018-biblioteca-frontend` | **Date**: 2026-07-27 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `plan/frontend/05-biblioteca.md`

## Summary

Entregar uma Biblioteca Angular privada para consultar o acervo já ingerido, com busca por título e filtros locais de metadados. A rota listará fontes pela API já existente; o detalhe canônico em `/sources/:sourceId` será ampliado para exibir todos os campos, editar título/conteúdo/associações e excluir por um diálogo explícito. A camada `KnowledgeApiService` continuará como único ponto de HTTP e ganhará os contratos de PATCH/DELETE. Não haverá mudança em FastAPI, banco, MCP ou documentação pública da API.

## Technical Context

**Language/Version**: TypeScript 6.0, Angular 22.0; Python/FastAPI somente como contrato existente

**Primary Dependencies**: Angular standalone components, Angular Router, `HttpClient`, RxJS; componentes compartilhados `LoadingState`, `ErrorState`, `EmptyState`, `ConfirmDialog` e `MetadataSelector`

**Storage**: Estado efêmero no cliente; PostgreSQL + pgvector permanecem no backend existente

**Testing**: Angular unit tests com `HttpTestingController` e testes de componentes; `npm run typecheck`, `npm test -- --watch=false`, `npm run build`

**Target Platform**: Navegadores modernos desktop e mobile, frontend Angular/Nginx

**Project Type**: Aplicação web Angular consumindo API FastAPI

**Performance Goals**: Uma requisição de listagem por entrada/recarregamento explícito; busca e filtros sem chamadas adicionais; endpoints sob 1 segundo em condições normais conforme constituição

**Constraints**: Tipagem estrita, UUID público, PATCH mínimo, exclusão somente após confirmação, conteúdo e mensagens remotas como texto, interface usável a partir de 320 px, sem expor token

**Scale/Scope**: Duas rotas privadas (Biblioteca e detalhe existente), expansão pequena do serviço/tipos, reutilização de shared e testes; sem paginação, filtros server-side, backend ou persistência de rascunhos

## Constitution Check

### Pre-design gate

- **Code Quality**: PASS — HTTP e tipos permanecem em `core`; fluxo de Biblioteca fica em `features/library`; o detalhe existente concentra a manutenção individual.
- **Testing Standards**: PASS — o plano exige testes de serviço, filtros, edição, exclusão e caminhos de erro, além dos comandos de qualidade existentes.
- **User Experience Consistency**: PASS — usa estados compartilhados, HTML semântico, ARIA, teclado, foco do diálogo e layout responsivo.
- **Performance Requirements**: PASS — filtros são intencionalmente locais; nenhuma mudança afeta geração de embeddings ou busca vetorial além de consumir o PATCH existente.
- **Technology Stack**: PASS — mantém Angular/TypeScript no cliente e FastAPI/SQLAlchemy/pgvector como contratos inalterados.
- **Documentation**: PASS — nenhum endpoint novo ou comportamento de servidor é criado; o contrato de consumo local está em [`contracts/frontend-library.md`](contracts/frontend-library.md).

### Post-design re-check

PASS. O design em [`data-model.md`](data-model.md) e [`contracts/frontend-library.md`](contracts/frontend-library.md) usa exclusivamente endpoints e schemas já publicados. Não há violação que requeira rastreamento de complexidade.

## Project Structure

### Documentation (this feature)

```text
specs/018-biblioteca-frontend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── frontend-library.md
```

### Source Code (repository root)

```text
frontend/
└── src/
    └── app/
        ├── app.routes.ts                         # adiciona /biblioteca
        ├── core/
        │   ├── knowledge-api.service.ts           # list/detail/patch/delete tipados
        │   ├── knowledge.types.ts                 # payload de PATCH e tipos reutilizados
        │   └── knowledge-api.service.spec.ts      # contratos HTTP
        ├── layout/
        │   ├── authenticated-layout.component.ts  # item de navegação Biblioteca
        │   └── app-shell.component.*              # somente se o menu estiver ali composto
        ├── features/
        │   ├── library/
        │   │   ├── library-page.component.ts
        │   │   ├── library-page.component.html
        │   │   ├── library-page.component.css
        │   │   └── library-page.component.spec.ts
        │   └── source-detail/
        │       ├── source-detail.component.ts
        │       ├── source-detail.component.html
        │       ├── source-detail.component.css
        │       └── source-detail.component.spec.ts
        └── shared/
            ├── confirm-dialog/                   # reutilizar sem alterar, salvo lacuna genérica descoberta
            ├── error-state/
            ├── loading-state/
            ├── empty-state/
            └── metadata-selector/
```

**Structure Decision**: `library/` controla a coleção e seus filtros locais. `source-detail/` permanece a única tela de fonte por UUID, compartilhada com Busca/Ingestão e responsável pelo rascunho, PATCH e DELETE. `core/` conserva URLs, serialização e contratos; componentes em `shared/` não recebem regras de domínio.

## Implementation Approach

### 1. Consolidar o contrato cliente de fontes

- Acrescentar `KnowledgeSourcePatchRequest` em `knowledge.types.ts`, com somente os nomes wire `snake_case` aceitos pela API e campos opcionais explícitos.
- Adicionar `updateSource(sourceId, payload)` com `PATCH` JSON e `deleteSource(sourceId)` com `HttpParams({ confirm: "true" })` ou equivalente que gere exatamente `?confirm=true`.
- Manter `sources()` e `source()` como leitura; não introduzir mapeamento duplicado de `source_id`/UUID nos componentes.
- Cobrir no spec do serviço método, URL codificada, payload mínimo, query de confirmação e resposta `204` vazia.

### 2. Criar a rota e a página Biblioteca

- Registrar `/biblioteca` sob o `AuthenticatedLayoutComponent`, com título de documento; adicionar o item Biblioteca ao menu autenticado apenas junto da rota implementada.
- Criar `LibraryPageComponent` standalone. No carregamento, chamar somente `api.sources()` e renderizar `LoadingStateComponent`, `ErrorStateComponent` com recarregamento, `EmptyStateComponent` ou lista semântica conforme o resultado.
- Exibir em cada item link para `/sources/:sourceId`, título, tipo, URI/origem e chips de categoria/tag/projeto. Não carregar conteúdo de cada fonte na lista.
- Carregar categorias/tags/projetos somente se necessário para construir opções de filtro. Preferir derivar opções únicas da própria lista para manter a promessa de uma requisição de listagem; documentar no componente que filtros abrangem metadados existentes no resultado.

### 3. Implementar busca e filtros em memória

- Usar um controle rotulado de busca por título e grupos de seleção para categorias, tags e projetos. Seleções devem conter IDs únicos e positivos.
- Normalizar consulta e título com `normalize("NFD")`, remoção de diacríticos e lowercase. Uma fonte passa em um grupo quando contém todos os IDs selecionados naquele grupo; todos os grupos devem passar.
- Derivar `filteredSources` sem mutar `sources`. Exibir contagem e um estado vazio específico para “nenhuma fonte encontrada”, com ação de limpar filtros; a lista original vazia deve manter orientação distinta.
- Não adicionar debounce, cache global, paginação ou parâmetros de consulta HTTP; a funcionalidade é local por requisito.

### 4. Evoluir o detalhe para consulta e edição segura

- Ampliar a tela existente para carregar `KnowledgeSourceDetail` e renderizar conteúdo como texto, tipo, URI/origem segura, hash, datas formatadas e todas as associações. Substituir mensagens ad hoc pelos shared states quando isso não prejudicar o detalhe.
- Disponibilizar modo de edição explícito, com formulário de título, conteúdo e `MetadataSelectorComponent`. Carregar categorias, tags e projetos para as opções de edição em paralelo e tratar sua falha sem perder o detalhe já carregado.
- Criar snapshot de baseline e rascunho isolado. Validar título e conteúdo após `trim`; comparar conjuntos de IDs e valores normalizados para montar apenas campos alterados. Bloquear salvar e informar “sem alterações” se nenhum campo mudou.
- Mostrar um aviso persistente, associado ao `textarea`, somente quando o conteúdo divergir do baseline: salvar recriará chunks e embeddings. Durante PATCH, desabilitar controles, anunciar processamento e evitar reenvio.
- Em `200`, substituir fonte/baseline/rascunho pela resposta, sair do estado pendente e anunciar sucesso. Em erro, preservar rascunho e aplicar mensagens seguras: revisão para 400/422, retorno/recarregamento para 404, fonte existente opcional para 409 com UUID validado, e nova tentativa para 502/503.

### 5. Integrar exclusão confirmada e atualização de lista

- Adicionar ação destrutiva visível apenas no detalhe. O primeiro clique abre `ConfirmDialogComponent` com linguagem inequívoca de permanência; cancelar e Escape fecham sem efeito.
- Conectar somente o evento `confirm` a `api.deleteSource(sourceId)`. Enquanto a chamada estiver pendente, desabilitar ações do diálogo/detalhe e manter anúncio de processamento.
- Em `204`, navegar para `/biblioteca` com um sinal de atualização transitório apropriado (por exemplo estado de navegação) ou recarregar a lista na entrada; não manter item excluído em memória. O plano prefere recarga controlada na rota para que a listagem represente o servidor.
- Em erro, fechar/bloquear adequadamente o estado pendente, manter a fonte visível e apresentar próximo passo. Nunca pressupor sucesso sem `204`.

### 6. Testes, acessibilidade e regressão

- Testar a Biblioteca para uma única carga inicial, normalização de acentos/case, combinação de filtros, limpar filtros, lista vazia e erro/retry.
- Testar detalhe para GET, exibição completa, baseline/PATCH mínimo, nenhum PATCH sem mudança, alerta de reprocessamento, sucesso imediato e preservação de rascunho em 400/422/404/409/502/503.
- Testar exclusão para abrir/cancelar/Escape sem DELETE, confirmação com `confirm=true`, `204` com navegação/atualização e recuperação de falha.
- Verificar labels, landmarks, `aria-live` para estados, foco do diálogo, ordem de tabulação e contraste/responsividade em 320 px, 768 px e desktop. Executar os comandos de [`quickstart.md`](quickstart.md).

## Data Model / API Implications

- Sem migração, alteração de SQLAlchemy, serviço FastAPI, rota Python, MCP ou OpenAPI. O backend já implementa UUID público, PATCH mínimo e confirmação da exclusão.
- Novo tipo TypeScript: `KnowledgeSourcePatchRequest`, espelho de `backend/app/schemas/knowledge.py`; `KnowledgeSource` e `KnowledgeSourceDetail` existentes são reutilizados.
- `GET /sources` permanece sem filtros. Busca/filtros são inteiramente locais sobre os campos retornados.
- `PATCH /sources/{source_id}` pode disparar reindexação somente quando `content` está presente/modificado; a interface comunica isso, mas não tenta estimar progresso.
- `DELETE /sources/{source_id}?confirm=true` retorna `204`; autenticação continua sendo responsabilidade dos interceptores existentes.
- Não há alteração de contrato HTTP, portanto `doc/API.md` não requer atualização nesta entrega.

## Test Strategy

- **Unitário — core**: URL, corpo e query do serviço de fontes via `HttpTestingController`.
- **Unitário — Biblioteca**: carregamento único, filtro derivado, normalização da busca, estados vazio/erro e links.
- **Unitário — detalhe**: dados carregados, validação, comparador de rascunho, PATCH, mensagens de erro e aviso de reprocessamento.
- **Integração de rota**: Biblioteca → detalhe → editar/excluir → Biblioteca atualizada; entrada no detalhe a partir de Busca/Ingestão continua funcional.
- **Acessibilidade/manual**: navegação por teclado, diálogo, leitores de tela/ARIA, 320 px, 768 px e desktop.
- **Quality gate**: `npm run typecheck`, `npm test -- --watch=false`, `npm run build` em `frontend/`.

## Risk Notes

- A lista em memória pode crescer além do confortável para o navegador; o escopo atual não inclui paginação ou pesquisa server-side, devendo reavaliar antes de ampliar o acervo significativamente.
- A semântica de array vazio no PATCH remove associações. O comparador de baseline e a seleção controlada são essenciais para não remover metadados por engano.
- Reprocessamento depende de provedores externos e pode falhar após edição de conteúdo; a UI deve preservar o rascunho e evitar prometer prazo/progresso.
- Uma fonte pode ser removida ou alterada em outra sessão. Respostas `404`/`409` não devem ser mascaradas como sucesso nem sobrescritas no cliente.
- O `ConfirmDialogComponent` atual já cobre Escape e foco, mas testes devem confirmar que ações pendentes não permitem dupla exclusão e que foco retorna de forma coerente ao fechar.

## Complexity Tracking

No constitution violations identified.
