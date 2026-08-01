# Feature Specification: Fundação do Frontend

**Feature Branch**: `015-fundacao-frontend`

**Created**: 2026-07-24

**Status**: Draft

**Input**: `plan/frontend/01-fundacao.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acessar a área autenticada (Priority: P1)

Uma pessoa informa um token válido no login e chega a uma área privada navegável, com cabeçalho, barra lateral e ação de desconexão.

**Why this priority**: É a porta de entrada segura para todas as telas de negócio planejadas.

**Independent Test**: Informar um token válido, verificar o redirecionamento à área privada e desconectar pelo layout.

**Acceptance Scenarios**:

1. **Given** uma sessão ausente, **When** a pessoa abre uma rota privada, **Then** ela é direcionada a `/login`.
2. **Given** um token validado, **When** a pessoa conclui o login, **Then** ela acessa a rota inicial autenticada com a navegação visível.
3. **Given** uma sessão autenticada, **When** a pessoa seleciona desconectar, **Then** o token é removido da memória e do armazenamento persistente, e ela retorna a `/login`.

---

### User Story 2 - Manter a sessão segura diante de falhas de autorização (Priority: P1)

Uma pessoa que possui sessão expirada ou revogada não continua usando a área privada nem deixa o token exposto na interface.

**Why this priority**: O Bearer token controla o acesso a todo o acervo de conhecimento.

**Independent Test**: Simular uma resposta HTTP 401 em uma chamada protegida e verificar limpeza de sessão e navegação ao login.

**Acceptance Scenarios**:

1. **Given** um token salvo que não é mais aceito, **When** a aplicação restaura a sessão, **Then** ela limpa a sessão e mostra o login com uma mensagem acionável.
2. **Given** uma pessoa em rota privada, **When** uma chamada protegida responde 401, **Then** a aplicação limpa a sessão e redireciona a `/login`.
3. **Given** a tela de login ou o layout privado, **When** a pessoa usa a aplicação, **Then** o valor do token não é exibido nem registrado pela interface.

---

### User Story 3 - Receber feedback acessível em estados comuns (Priority: P2)

Uma pessoa entende quando uma tela está carregando, falhou ou não tem dados, e consegue operar os controles por teclado em desktop ou celular.

**Why this priority**: Esses estados serão reutilizados por busca, ingestão, biblioteca e organização.

**Independent Test**: Renderizar cada componente compartilhado e verificar texto, semântica, foco e acionamento por teclado.

**Acceptance Scenarios**:

1. **Given** uma operação pendente, **When** o estado de carregamento é mostrado, **Then** ele comunica progresso indeterminado de forma acessível.
2. **Given** uma falha recuperável, **When** o estado de erro é mostrado, **Then** a pessoa recebe uma mensagem compreensível e uma ação de nova tentativa quando aplicável.
3. **Given** uma lista sem dados, **When** o estado vazio é mostrado, **Then** ele explica a ausência e indica o próximo passo sem depender apenas de cor ou ícone.

### Edge Cases

- A aplicação é aberta diretamente em uma URL privada antes da restauração da sessão terminar.
- O token salvo é inválido, a API está indisponível ou a API responde 401 após o login.
- Uma rota desconhecida é acessada por pessoa autenticada ou não autenticada.
- A barra lateral é usada em viewport móvel e não pode ocultar a rota atual nem prender o foco.
- A API retorna erro com detalhe ausente, inesperado ou que não deve ser exposto diretamente.
- Um diálogo de confirmação é aberto, fechado por Escape ou cancelado sem executar sua ação destrutiva.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O frontend MUST expor `/login` como rota pública e proteger as rotas autenticadas com um guard que consulta `AuthService` como fonte única do estado de sessão.
- **FR-002**: O frontend MUST restaurar e validar a sessão persistida antes de liberar a navegação privada.
- **FR-003**: O layout autenticado MUST conter cabeçalho, barra lateral responsiva, indicação da rota atual e ação de desconexão.
- **FR-004**: Uma resposta 401 de qualquer chamada protegida MUST limpar a sessão e redirecionar ao login sem duplicar a lógica em telas de negócio.
- **FR-005**: O frontend MUST centralizar chamadas a `/api/v1/knowledge` em `KnowledgeApiService`, incluindo normalização segura de erros HTTP.
- **FR-006**: O frontend MUST definir tipos TypeScript estritos para categorias, tags, projetos, fontes, chunks, busca, resposta RAG e seus filtros/payloads já publicados pela API.
- **FR-007**: O frontend MUST disponibilizar componentes compartilhados para carregamento, erro, estado vazio, confirmação e seleção de metadados (categorias, tags e projetos).
- **FR-008**: O diálogo de confirmação MUST exigir uma ação explícita para confirmar; cancelar, clicar fora quando permitido ou pressionar Escape não pode confirmar a operação.
- **FR-009**: Estilos globais MUST fornecer foco visível, contraste suficiente, HTML semântico, feedback ARIA e comportamento responsivo para os componentes desta fase.
- **FR-010**: A fundação MUST manter as telas de negócio futuras fora do escopo; a navegação inicial não pode levar a rotas inexistentes.
- **FR-011**: O token MUST ser persistido somente quando a pessoa optar por manter a sessão e MUST nunca ser renderizado, incluído em mensagens de erro ou registrado pelo frontend.
- **FR-012**: `npm run typecheck` e `npm run build` MUST concluir com sucesso em `frontend/`.

### Key Entities *(include if feature involves data)*

- **Session**: Estado local de autenticação composto por status, token mantido somente em memória durante uso e preferência de persistência.
- **API Error**: Representação segura e tipada de falhas HTTP para exibição e decisão de fluxo, sem vazar token ou conteúdo sensível.
- **Knowledge Metadata**: Categorias, tags e projetos usados em filtros e formulários das fases posteriores.
- **Knowledge Result**: Contratos de fontes, chunks, busca e resposta RAG retornados pela API existente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das rotas privadas cadastradas redirecionam uma sessão ausente ou inválida para `/login`.
- **SC-002**: 100% das respostas 401 simuladas em chamadas protegidas limpam a sessão e levam ao login.
- **SC-003**: Os cinco componentes compartilhados apresentam texto compreensível e semântica acessível nos testes de componente previstos.
- **SC-004**: A área autenticada e o login permanecem operáveis por teclado e em viewport móvel de 320 px sem rolagem horizontal involuntária.
- **SC-005**: `npm run typecheck` e `npm run build` passam após a entrega.

## Assumptions

- O fluxo atual de validação por `GET /api/v1/knowledge/categories` continua sendo a verificação de token desta fase.
- A API mantém o prefixo `/api/v1/knowledge` e os contratos documentados em `doc/API.md`.
- A rota autenticada inicial será `/inicio`; as telas de busca, pergunta, ingestão, biblioteca e organização serão adicionadas por suas próprias fases, sem links ativos prematuros.
- A persistência opcional continua em `localStorage`, conforme o plano de frontend existente; não há cookies de sessão nem autenticação por usuário nesta fase.
- O backend e sua documentação pública não mudam; esta é uma reorganização e expansão do cliente Angular.
