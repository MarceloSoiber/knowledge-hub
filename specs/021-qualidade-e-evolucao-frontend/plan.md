# Implementation Plan: Qualidade, segurança e evolução do frontend

**Branch**: `021-qualidade-e-evolucao-frontend` | **Date**: 2026-07-27 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification based on `plan/frontend/08-qualidade-e-evolucao.md`

## Summary

Elevar a confiabilidade do primeiro corte do frontend Angular por meio de uma matriz de testes de contrato e componentes, cobertura explícita da fronteira de autenticação/`401`, mensagens de erro seguras e uma rotina de validação manual acessível e responsiva. A entrega também documenta contratos mínimos para evoluções de API após o MVP, sem criar endpoints ou código cliente antecipado. O primeiro passo operacional é alinhar o ambiente local à versão Node exigida pelo Angular CLI para tornar teste e build gates reais.

## Technical Context

**Language/Version**: TypeScript 6.0, Angular 22.0; Node `>=22.22.3` para CLI atual; Python/FastAPI somente como contrato existente  
**Primary Dependencies**: Angular TestBed, `HttpTestingController`, Router testing, Vitest, RxJS; `AuthService`, guard e interceptadores atuais  
**Storage**: Estado transitório Angular e `localStorage` somente para token marcado como persistente; PostgreSQL + pgvector inalterados  
**Testing**: `npm run typecheck`, `npm test -- --watch=false`, `npm run build`; testes HTTP e componentes; roteiro manual desktop/mobile/teclado/leitor de tela  
**Target Platform**: Navegadores modernos em desktop/mobile; build Angular/Nginx; ambiente de desenvolvimento e CI com Node suportado  
**Project Type**: Aplicação web Angular consumindo API FastAPI autenticada por Bearer  
**Performance Goals**: Gates executáveis antes de entrega; testes de unidade sem rede; nenhuma regressão nos objetivos atuais de resposta da API  
**Constraints**: Não registrar/exibir token, não renderizar corpo remoto como HTML, preservar fluxos e contratos existentes, sem endpoint novo nesta feature  
**Scale/Scope**: Core de autenticação/erro/HTTP, componentes dos fluxos críticos, documentos de qualidade e roadmap contratual de API

## Constitution Check

### Pre-design gate

- **Code quality**: PASS — a mudança concentra regras transversais em `core`, testes junto ao código e mensagens seguras reutilizáveis; não introduz lógica de backend no frontend.
- **Testing standards**: PASS — explicita cobertura de serviços, contratos HTTP, guard/interceptadores, estados de UI e quality gates; a lacuna de versão Node é tratada como bloqueio, não como aprovação implícita.
- **UX/accessibility**: PASS — fluxo crítico precisa cobrir loading/vazio/erro/sucesso, confirmação para ações irreversíveis, teclado e leitor de tela em breakpoints definidos.
- **Performance**: PASS — testes são isolados e não adicionam requisições de produção nem alteram geração de embeddings, pgvector ou busca.
- **Technology/documentation**: PASS — preserva Angular/FastAPI existentes; evolução de API é documentada, e `doc/API.md` só muda em feature futura que publique contrato.

### Post-design re-check

PASS. O [modelo](data-model.md) introduz somente artefatos locais de qualidade e propostas futuras; o [contrato](contracts/frontend-quality.md) não muda a superfície HTTP atual.

## Project Structure

### Documentation (this feature)

```text
specs/021-qualidade-e-evolucao-frontend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── frontend-quality.md
```

### Source Code (repository root)

```text
frontend/
├── package.json                                      # comandos de qualidade, se houver ajuste mínimo necessário
├── Dockerfile                                        # Node de build reproduzível (referência atual: 24)
└── src/app/
    ├── core/
    │   ├── auth.service.{ts,spec.ts}                 # restauração, login, logout e token persistente
    │   ├── auth.guard.{ts,spec.ts}                   # rota privada e returnUrl
    │   ├── auth.interceptor.{ts,spec.ts}             # escopo de Authorization
    │   ├── unauthorized.interceptor.{ts,spec.ts}     # limpeza/redirecionamento em 401
    │   ├── api-error.{ts,spec.ts}                    # classificação segura de erros
    │   └── knowledge-api.service.{ts,spec.ts}        # contratos HTTP publicados
    ├── features/
    │   ├── login/login.component.spec.ts
    │   ├── search/search-page.component.spec.ts
    │   ├── ask/ask-page.component.spec.ts
    │   ├── ingestion/ingestion-page.component.spec.ts
    │   ├── library/library-page.component.spec.ts
    │   ├── source-detail/source-detail.component.spec.ts
    │   ├── organization/organization-page.component.spec.ts
    │   └── home/home.component.spec.ts
    └── shared/
        └── confirm-dialog/confirm-dialog.component.spec.ts
```

**Structure Decision**: testes permanecem junto dos componentes/serviços que verificam. `core` controla sessão, HTTP e classificação genérica; cada feature mantém apenas mensagens e decisões específicas de domínio. O checklist manual e as propostas de API ficam em `specs/`, não no código de execução.

## Implementation Approach

### 1. Estabelecer gates reproduzíveis e a matriz de cobertura

- Confirmar no `package-lock.json`/Angular CLI a versão Node suportada e padronizar o ambiente de desenvolvimento/CI com Node 24 ou mínimo aceito. A imagem `frontend/Dockerfile` é uma referência, mas o plano não deve mascarar teste local com Docker sem tornar esse caminho documentado.
- Criar/atualizar um documento de matriz de qualidade que associe cada fluxo crítico aos estados UI, contrato HTTP e verificação manual. Usar [frontend-quality.md](contracts/frontend-quality.md) como fonte de revisão.
- Completar testes ausentes primeiro nos pontos transversais (`AuthService`, guard, dois interceptadores e Login), pois eles fundamentam todas as rotas protegidas.

### 2. Testar a fronteira de sessão, token e retorno seguro

- Adicionar `auth.service.spec.ts` com armazenamento simulado: token vazio, restauração, validação remota, “manter conectado”, logout e falha. Nunca colocar token literal em mensagens/expectativas de DOM ou logs.
- Adicionar specs ao guard e interceptadores com `HttpTestingController`/Router testado. Cobrir Bearer somente para `/api/v1/knowledge/`, ausência em outra URL, `401` protegido que limpa e navega, e `401` externo que não afeta sessão.
- Adicionar `login.component.spec.ts` para formulário inválido, estado checking, sucesso, falha e `returnUrl` válido/inválido. Extrair o validador de retorno para função testável se isso evitar teste frágil de componente.

### 3. Consolidar mapeamento de erros seguros e validar contratos HTTP

- Estender `api-error.spec.ts` para todos os códigos mapeados, `status=0`, payloads inesperados e fallback; o corpo da resposta nunca deve compor `message`.
- Revisar features para usar `toApiError` onde a mensagem é genérica. Preservar mapeamentos de domínio que acrescentem ação segura (duplicidade de fonte, 404 de detalhe, conflitos de classificação), mas cobri-los em specs.
- Expandir `knowledge-api.service.spec.ts` para as leituras ainda sem asserção explícita e cada mutação publicada, validando método, URL codificada, query, payload mínimo, 204 vazio e não vazamento de Authorization (que pertence ao interceptor).

### 4. Cobrir estados e formulários dos fluxos críticos

- Completar specs de Login, Busca, Pergunte, Ingestão, Biblioteca, detalhe, Organização e Dashboard. Para cada um, testar sucesso e estados loading/vazio/erro aplicáveis, sem snapshots amplos que escondam intenção.
- Em Ingestão e detalhe, cobrir validação local, preservação de rascunho, duplicidade/409 e indisponibilidade. Em Busca/Pergunte, cobrir filtros/payload e exibição segura de resultados/citações.
- Em Biblioteca e Organização, cobrir confirmação e cancelamento/Escape antes de DELETE, archive ou reactivate; verificar que nenhuma chamada é enviada quando se cancela.
- Adicionar spec de `ConfirmDialogComponent` para semântica modal, foco inicial, Escape/cancelamento, confirmação explícita e bloqueio durante ação pendente quando a API do componente o suportar.

### 5. Executar revisão manual e publicar o roadmap pós-MVP

- Aplicar [quickstart.md](quickstart.md) em 320 px, 768 px e desktop com teclado e leitor de tela; registrar resultados/restrições no PR ou checklist de entrega, sem incluir credenciais.
- Manter propostas futuras em [data-model.md](data-model.md): paginação/ordenação/filtros, agregados, job de ingestão, arquivo original e categorias enriquecidas. Antes de cada uma, abrir nova spec com decisão de autorização, semântica de consistência e atualização de OpenAPI/`doc/API.md`.
- Rodar os três gates definidos e tratar qualquer falha de ferramenta como tarefa bloqueadora, incluindo atualização de Node quando necessário.

## Data Model / API Implications

- Não há alteração de tabelas, migrações, SQLAlchemy, FastAPI, MCP, OpenAPI ou `doc/API.md` nesta entrega.
- `ApiError` e `AuthStatus` existentes são os contratos locais; a feature poderá apenas completar testes e, se necessário, reforçar suas funções sem mudar a API pública.
- As evoluções de servidor são propostas documentadas em [data-model.md](data-model.md), não contratos implementados. Cada uma exige feature própria e atualização de API antes de ser consumida pelo frontend.
- O contrato cliente atual de sessão e qualidade está em [frontend-quality.md](contracts/frontend-quality.md).

## Test Strategy

- **Core**: TestBed/`HttpTestingController` para método/URL/query/corpo, auth service, guard, autenticação e tratamento de `401`; todos os erros mapeados e payload inseguro em `api-error`.
- **Features**: testes focados em loading, vazio, sucesso, erro, validação, duplicidade, confirmação e preservação de rascunho nos fluxos críticos.
- **Shared**: diálogo de confirmação, estados de erro/vazio/loading e seletor de metadados conforme responsabilidades de cada um.
- **Manual/a11y**: foco/ESC em diálogos, labels, landmarks, `aria-live`, contraste, mobile 320 px/768 px/desktop e leitor de tela.
- **Gates**: `node --version`, `npm run typecheck`, `npm test -- --watch=false`, `npm run build`; Node incompatível bloqueia a entrega.

## Risk Notes

- Testes que só afirmam texto podem deixar passar chamadas HTTP incorretas; por isso cada fronteira de API deve usar `HttpTestingController` para método, URL e corpo.
- Centralizar erros demais pode apagar orientação específica de domínio. O mapeamento comum deve ser complemento, não substituição cega de regras de duplicidade/conflito.
- `localStorage` é parte do comportamento já documentado de “manter conectado”; os testes devem garantir remoção no logout/401, mas não tratar isso como proteção contra comprometimento do navegador.
- Não implementar agregados/paginação/progresso fictícios no cliente: eles dependem de semântica de servidor, autorização e contrato versionado.

## Complexity Tracking

Nenhuma violação da constituição identificada.
