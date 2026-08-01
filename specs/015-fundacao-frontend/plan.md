# Implementation Plan: Fundação do Frontend

**Branch**: `015-fundacao-frontend` | **Date**: 2026-07-24 | **Spec**: `specs/015-fundacao-frontend/spec.md`

**Input**: Feature specification from `/specs/015-fundacao-frontend/spec.md`

## Summary

Transformar o frontend Angular, hoje concentrado em um único componente de login, em uma fundação navegável e autenticada. A implementação preservará o `AuthService` existente como fonte de verdade, introduzirá Router, guard e interceptor de resposta 401, separará login do layout privado, centralizará a API do Knowledge Hub em serviço tipado e entregará componentes reutilizáveis e estilos acessíveis para as próximas fases.

As telas de negócio continuam fora do escopo. A única rota privada de conteúdo desta entrega será `/inicio`, uma página inicial de preparação para o acervo; a barra lateral só apresentará destinos já implementados, evitando rotas quebradas.

## Technical Context

**Language/Version**: TypeScript 6.0, Angular 22.0

**Primary Dependencies**: Angular standalone components, Angular Router, `HttpClient`, RxJS

**Storage**: `localStorage` opcional para o Bearer token; demais dados continuam no backend PostgreSQL + pgvector por meio da API REST existente

**Testing**: Angular unit tests com `HttpTestingController` e testes de guard/componentes; `npm run typecheck`, `npm run build`

**Target Platform**: Navegadores modernos em desktop e mobile; Vite/Angular build servido pelo Nginx do frontend

**Project Type**: Aplicação web Angular consumindo API FastAPI

**Performance Goals**: Navegação local sem requisições redundantes de autenticação; nenhuma meta de backend alterada; layout utilizável a partir de 320 px

**Constraints**: Tipagem estrita; token nunca renderizado ou registrado; chamadas de `/api/v1/knowledge` centralizadas; resposta 401 encerra a sessão; conteúdo vindo da API tratado como texto; estilos compartilhados centralizados em `src/styles.css`

**Scale/Scope**: Rotas e shell autenticado, autenticação e erros HTTP, contratos da API, cinco componentes compartilhados, testes e estilos. Sem novas telas de negócio, alteração de API ou migração de banco.

## Constitution Check

- **Code Quality**: Passa. O plano separa core (sessão/API), layout, shared e features; os contratos deixam de estar dispersos em componentes.
- **Testing Standards**: Passa com ação necessária. O projeto ainda não possui alvo/dependências de testes frontend; a implementação deve configurá-los antes dos testes de serviço, guard e componentes.
- **User Experience Consistency**: Passa. Foco visível, ARIA, feedback imediato, semântica e responsividade são requisitos explícitos dos componentes e do shell.
- **Performance Requirements**: Passa. A inicialização valida no máximo a sessão persistida e as telas futuras reutilizarão `KnowledgeApiService`.
- **Technology Stack**: Passa. Mantém Angular/Vite/TypeScript no cliente e os contratos FastAPI existentes no servidor, sem alterar backend.
- **Documentation**: Passa. `doc/API.md` já documenta autenticação e contratos consumidos; nenhuma mudança de comportamento da API é planejada.

## Project Structure

### Documentation (this feature)

```text
specs/015-fundacao-frontend/
├── spec.md
├── plan.md
└── tasks.md            # Criado na próxima etapa /speckit.tasks
```

### Source Code (repository root)

```text
frontend/
├── package.json
├── angular.json
└── src/
    ├── app/
    │   ├── app.config.ts
    │   ├── app.routes.ts
    │   ├── app.component.ts
    │   ├── core/
    │   │   ├── api-error.ts
    │   │   ├── auth.interceptor.ts
    │   │   ├── auth.service.ts
    │   │   ├── auth.guard.ts
    │   │   ├── unauthorized.interceptor.ts
    │   │   ├── knowledge-api.service.ts
    │   │   └── knowledge.types.ts
    │   ├── layout/
    │   │   ├── authenticated-layout.component.ts
    │   │   └── authenticated-layout.component.html/css
    │   ├── shared/
    │   │   ├── loading-state/
    │   │   ├── error-state/
    │   │   ├── empty-state/
    │   │   ├── confirm-dialog/
    │   │   └── metadata-selector/
    │   └── features/
    │       ├── login/
    │       └── home/
    └── styles.css
```

**Structure Decision**: `core` guarda serviços singleton, tipos e infraestrutura HTTP; `layout` contém apenas a casca de rotas privadas; `shared` contém componentes sem regra de negócio; `features` contém login e a página inicial. Os estilos de tokens, foco, tipografia e utilitários globais ficam em `src/styles.css`; estilos estruturais específicos permanecem junto aos componentes.

## Implementation Details

### 1. Router e composição da aplicação

- Criar `app.routes.ts` com `/login` pública e uma árvore privada sob `AuthenticatedLayoutComponent`.
- Definir `/inicio` como rota filha privada, redirecionar a raiz para a rota apropriada e tratar curingas sem expor conteúdo privado.
- Converter `AppComponent` em host mínimo de `RouterOutlet`; o formulário atual deixa de decidir qual layout renderizar.
- Registrar `provideRouter(...)` em `app.config.ts`, com restauração de rolagem e configuração de navegação coerente com SPA.
- A página inicial deve ser uma tela simples de boas-vindas/estado vazio que explica que as ações de acervo chegarão nas próximas fases. Não criar rotas nem botões para Busca, Pergunte, Ingestão, Biblioteca ou Organização nesta entrega.

### 2. Sessão, guard e tratamento de 401

- Manter `AuthService` como único dono de token, status, persistência e logout; expor consultas mínimas para o guard sem duplicar validações por rota.
- Ajustar a inicialização para que a aplicação/guard aguarde a restauração da sessão persistida antes de decidir a rota privada. A validação continua usando `GET /knowledge/categories` via a camada de API.
- Criar `authGuard` funcional para permitir rotas privadas somente com sessão autenticada e redirecionar sessões ausentes/invalidas para `/login`, preservando a URL de retorno somente quando não carregar dados sensíveis.
- Manter o interceptor atual responsável apenas por anexar `Authorization: Bearer ...` às chamadas sob `/api/v1/knowledge/`.
- Criar interceptor de resposta separado para detectar `HttpErrorResponse` 401: chamar `AuthService.logout()` e navegar a `/login` de forma idempotente. Falhas de login e 401 concorrentes não devem provocar loops de navegação nem expor o token.
- Extrair a UI atual de autenticação para `features/login`, usando `AuthService` e rota de retorno segura; remover a confirmação de "conectado" que hoje ocupa a mesma página de login.

### 3. Contratos e `KnowledgeApiService`

- Criar `knowledge.types.ts` a partir dos schemas e contratos de `backend/app/schemas/knowledge.py` e `doc/API.md`: `Category`, `Tag`, `Project`, `KnowledgeSource`, `KnowledgeSourceDetail`, `KnowledgeChunk`, localização, filtros, `KnowledgeSearchRequest/Response`, `KnowledgeAnswerRequest/Response`, payloads de texto/arquivo e resposta de ingestão.
- Representar campos opcionais, datas ISO e `metadata` de maneira explícita; usar `sourceId` no TypeScript mapeando o campo wire `source_id` diretamente ou escolher uma convenção única documentada no serviço. Não transformar dados livremente em cada componente.
- Criar `KnowledgeApiService` com URL-base privada e métodos tipados para categorias, tags, projetos, fontes, busca, resposta RAG e ingestão. Esta fase pode expor os métodos mesmo sem telas consumidoras, pois eles formam o contrato estável das próximas fases.
- Criar `ApiError` normalizado que classifica 0/rede, 400/422 de validação, 401, 403, 404, 409, 413, 429, 502 e 503. Somente detalhes seguros retornados pela API devem chegar à UI; fallback genérico para payload inesperado.
- Não alterar endpoints, autenticação de backend, schemas Python nem `doc/API.md` nesta entrega.

### 4. Layout autenticado e navegação

- Implementar `AuthenticatedLayoutComponent` com landmark `header`, `nav`, `main` e `router-outlet`, nome acessível para a navegação e indicação da rota ativa.
- Exibir marca do produto, rota atual e botão de desconexão. O layout não mostra token, nem mesmo mascarado.
- Construir barra lateral responsiva: visível/operável em desktop, recolhível em telas estreitas, com botão de menu rotulado, Escape para fechar e foco devolvido ao acionador.
- Nesta fase, a navegação contém apenas Início. Preparar uma definição de itens de navegação local para extensões futuras, sem publicar destinos ausentes.

### 5. Componentes compartilhados e acessibilidade

- Criar `LoadingStateComponent` com texto configurável, indicador não dependente apenas de cor e `aria-live`/`aria-busy` adequados.
- Criar `ErrorStateComponent` com título, mensagem segura, `role="alert"` quando a falha exigir anúncio imediato e callback/botão opcional de nova tentativa.
- Criar `EmptyStateComponent` com título, descrição e slot/ação opcional para orientar o próximo passo.
- Criar `ConfirmDialogComponent` reutilizável com título, explicação, rótulos explícitos para cancelar/confirmar, foco inicial seguro, armadilha de foco enquanto aberto e fechamento por Escape sem confirmar. Operações futuras decidem quando invocá-lo.
- Criar `MetadataSelectorComponent` controlado por inputs/outputs para seleção múltipla de categorias obrigatórias, tags e projetos opcionais. Deve suportar labels, mensagens de erro, teclado e estados de carregamento; autocomplete de tags fica para a fase de Busca/Organização.
- Definir tokens CSS para cores, espaçamentos, bordas, estados de foco, feedback e breakpoints; aplicar `:focus-visible`, contraste adequado e `prefers-reduced-motion`. Evitar renderização de HTML remoto em todos os componentes.

### 6. Testes e verificação

- Adicionar configuração e script de teste Angular compatíveis com a versão atual do CLI antes de escrever specs. Usar `HttpTestingController` para validar URL, método, payload, headers e normalização de erros em `KnowledgeApiService`.
- Testar `AuthService` para token ausente, token válido lembrado ou temporário, token inválido e logout; não afirmar nem registrar valor do token em asserções de UI.
- Testar o guard para sessão autenticada, ausente, em restauração e inválida; testar o interceptor 401 para limpeza e redirecionamento idempotente.
- Testar componentes compartilhados para conteúdo acessível, interação de teclado, confirmação/cancelamento e seleção de metadados; testar layout em árvore de rotas para landmarks, link ativo e desconexão.
- Executar `npm run typecheck`, testes frontend configurados e `npm run build` em `frontend/`. Fazer verificação manual com teclado, leitor de tela e larguras de 320 px, 768 px e desktop.

## Data Model / API Implications

- Não há migração ou alteração do modelo PostgreSQL, FastAPI ou MCP.
- O frontend passa a espelhar os contratos existentes dos schemas Python em tipos TypeScript. O mapeamento é somente de cliente e deve permanecer compatível com nomes JSON `snake_case` da API, salvo adaptador único dentro de `KnowledgeApiService`.
- A validação de sessão continua consumindo `GET /api/v1/knowledge/categories`; todas as demais chamadas são preparadas no serviço para fases posteriores, não disparadas automaticamente.
- O interceptor de 401 muda apenas o comportamento local do navegador: invalida a sessão e redireciona ao login. Outros erros continuam disponíveis para os componentes via `ApiError`.
- Não há mudança em OpenAPI ou `doc/API.md` porque nenhum contrato HTTP do servidor muda.

## Test Strategy

- **Unitário — core**: autenticação, guard, interceptors, normalização de `ApiError` e `KnowledgeApiService` com `HttpTestingController`.
- **Unitário — shared**: loading, erro, vazio, diálogo e seletor de metadados, incluindo ARIA e teclado.
- **Integração de rotas**: login → retorno seguro → shell autenticado → logout; acesso direto a URL privada; resposta 401 durante rota privada.
- **Regressão visual/manual**: login, shell e diálogo em mobile/desktop; navegação somente por teclado; foco ao abrir/fechar menu e diálogo.
- **Quality gate**: `npm run typecheck`, comando de testes configurado e `npm run build` no diretório `frontend/`.

## Risk Notes

- O token em `localStorage` é uma decisão existente e opcional, mas permanece vulnerável a XSS; esta fase reduz exposição visual e de logs, não substitui o modelo por cookie HttpOnly.
- Um interceptor 401 mal coordenado com a validação inicial pode causar múltiplos redirects ou estado inconsistente. O tratamento deve ser idempotente e o guard deve aguardar a inicialização.
- O backend pode retornar detalhes de erro variados; a normalização precisa usar texto genérico quando o payload não for seguro ou previsível.
- O seletor de metadados é deliberadamente genérico. Antecipar autocomplete, criação inline ou cache global aumentaria o escopo e deve ficar para as fases de Busca e Organização.
- Adicionar navegação para funcionalidades futuras antes das respectivas rotas prejudica a entrega; o layout deve ser extensível, mas somente Início será acionável agora.

## Complexity Tracking

No constitution violations identified.
