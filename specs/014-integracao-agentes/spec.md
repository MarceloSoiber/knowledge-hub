# Feature Specification: Integracao com Agentes

**Feature Branch**: `014-integracao-agentes`

**Created**: 2026-07-21

**Status**: Implemented

**Input**: User description: "com base no plano plan/13-integracao-agentes.md planeje a implementação"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agente consulta memoria quando ajuda (Priority: P1)

Um agente conectado ao MCP recebe instrucoes claras para consultar o Knowledge Hub quando a pergunta depender de assuntos que possam existir nas categorias cadastradas da base. A politica usa as categorias atuais como inventario dinamico da memoria, em vez de assumir uma lista fixa de dominios como projetos, financas ou decisoes.

**Why this priority**: Sem uma politica explicita de consulta, agentes podem ignorar memoria relevante ou transformar qualquer pergunta em busca desnecessaria.

**Independent Test**: Validar instrucoes e descricoes das tools MCP com categorias simuladas e executar cenarios de decisao que diferenciem perguntas que devem buscar das que nao devem buscar conforme o inventario atual.

**Acceptance Scenarios**:

1. **Given** uma categoria cadastrada que cobre decisoes de projeto, **When** uma pergunta se alinha a esse tema, **Then** a politica orienta consultar `search` antes de responder.
2. **Given** uma pergunta de calculo simples com todo o contexto na conversa, **When** o agente le as instrucoes MCP, **Then** a politica orienta nao consultar a base.
3. **Given** uma busca inicial sem resultados, **When** a pergunta ainda parece depender de memoria, **Then** a politica permite uma reformulacao antes de concluir ausencia.
4. **Given** uma nova categoria cadastrada para um dominio antes desconhecido, **When** uma pergunta se alinha a esse dominio, **Then** a politica considera esse dominio elegivel para busca sem mudanca de codigo.

---

### User Story 2 - Agente usa filtros e fontes de forma adequada (Priority: P2)

Um agente consegue decidir quando usar busca global, `categories`, `sources`, `projects`, `tags` e filtros sem restringir cedo demais o espaco de resultados.

**Why this priority**: A recuperacao correta depende de orientar o agente a buscar globalmente primeiro e so aplicar filtros quando eles aumentam precisao.

**Independent Test**: Inspecionar contratos e executar testes de encaminhamento das tools garantindo que parametros e descricoes preservam filtros opcionais e comportamento global.

**Acceptance Scenarios**:

1. **Given** uma pergunta ampla sobre documentos salvos, **When** o agente escolhe uma tool, **Then** a descricao de `search` favorece uma busca global inicial.
2. **Given** uma pergunta explicitamente limitada a uma categoria ou projeto, **When** o agente escolhe parametros, **Then** `category_ids`, `project_ids` ou `tag_ids` podem ser usados apos descobrir IDs validos.
3. **Given** um resultado citavel, **When** o agente precisa detalhar a fonte, **Then** a politica orienta usar `source(source_id)`.

---

### User Story 3 - Escrita exige intencao explicita e permissao auditavel (Priority: P3)

Um agente somente grava conhecimento persistente quando o usuario pede ou confirma explicitamente a gravacao, e perfis read-only nao conseguem chamar escrita.

**Why this priority**: O sistema lida com memoria pessoal; gravar conversas implicitamente ou permitir escrita ampla quebra confianca e auditabilidade.

**Independent Test**: Executar testes de escopo `knowledge:read` vs `knowledge:write` e de contrato da tool `ingest_text`.

**Acceptance Scenarios**:

1. **Given** `MCP_WRITE_ENABLED=false`, **When** um agente autentica, **Then** recebe somente escopo `knowledge:read`.
2. **Given** um token sem `knowledge:write`, **When** `ingest_text` e chamado, **Then** a operacao e rejeitada antes de chamar servico de ingestao.
3. **Given** uma conversa sem pedido explicito de salvar, **When** o agente le a descricao da tool, **Then** a politica proibe arquivamento automatico.

---

### User Story 4 - Conteudo recuperado nao vira instrucao (Priority: P4)

Um agente trata documentos recuperados como dados nao confiaveis, mesmo quando o texto recuperado contem instrucoes imperativas, prompt injection ou pedidos para ignorar regras.

**Why this priority**: A memoria pode conter documentos externos ou antigos; o RAG precisa evitar que dados recuperados modifiquem comportamento de sistema.

**Independent Test**: Incluir fixture com conteudo malicioso recuperado e verificar que a resposta/contrato preserva o texto como evidencia, nao como instrucao.

**Acceptance Scenarios**:

1. **Given** um documento salvo com "ignore suas instrucoes", **When** ele aparece em `search`, **Then** a politica instrui o agente a tratar o trecho como dado nao confiavel.
2. **Given** um prompt RAG com contexto recuperado, **When** o LLM gera resposta, **Then** as instrucoes do sistema continuam prevalecendo sobre o conteudo recuperado.

---

### User Story 5 - Privacidade bloqueia envio externo de categorias sensiveis (Priority: P5)

O sistema identifica categorias sensiveis e impede, ou exige provedor local para, fluxos que enviariam conteudo sensivel a providers externos.

**Why this priority**: O plano original cita financas e informacoes historicas do usuario; categorias sensiveis exigem politica operacional clara antes de integrar agentes mais autonomos.

**Independent Test**: Configurar uma categoria sensivel e verificar que respostas/embeddings com provider externo sao bloqueados ou retornam erro acionavel.

**Acceptance Scenarios**:

1. **Given** uma categoria marcada como sensivel, **When** um fluxo tentaria enviar seu conteudo a provider externo, **Then** a operacao e bloqueada com mensagem clara.
2. **Given** provider local configurado, **When** a mesma consulta ocorre, **Then** a operacao pode prosseguir respeitando os demais filtros.

### Edge Cases

- Busca inicial sem resultados por consulta especifica demais.
- Categoria, tag ou projeto informado pelo agente nao existe mais.
- Cliente MCP tenta escrever sem escopo de escrita.
- Usuario pede para "lembrar disso" mas nao fornece categoria valida.
- Conteudo recuperado contem prompt injection ou segredo operacional.
- Busca global retorna conteudo de categoria sensivel enquanto provider externo esta ativo.
- Pergunta mistura calculo simples com referencia a uma categoria existente na base.
- Categoria nova e criada depois que o servidor MCP ja esta em execucao.
- Categorias sao genericas demais para inferir se a pergunta depende de memoria.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O servidor MCP MUST expor instrucoes de uso que definam quando agentes devem consultar memoria e quando devem responder sem busca com base no inventario dinamico de categorias.
- **FR-002**: A tool `search` MUST ter nome, descricao, parametros e exemplos/documentacao que orientem busca global inicial e filtros por categoria/tag/projeto somente quando houver ganho de precisao.
- **FR-003**: As tools `categories`, `tags`, `projects`, `sources`, `source` e `project_sources` MUST explicar quando ajudam a preparar, refinar ou decidir uma busca.
- **FR-004**: A politica MUST orientar uma segunda formulacao de busca quando a primeira falhar e a pergunta depender de memoria.
- **FR-005**: A tool `ingest_text` MUST exigir confirmacao explicita do usuario no contrato/documentacao e MUST continuar protegida por `knowledge:write`.
- **FR-006**: O servidor MCP MUST manter perfis distintos read-only e read-write por configuracao auditavel.
- **FR-007**: Conteudo recuperado por busca/source MUST ser documentado e tratado como dado nao confiavel, nunca como instrucao de sistema.
- **FR-008**: O fluxo RAG MUST isolar contexto recuperado das instrucoes do sistema e evitar obedecer comandos contidos nos documentos.
- **FR-009**: O sistema MUST permitir declarar categorias sensiveis por configuracao ou metadado operacional.
- **FR-010**: Quando provider externo estiver ativo, conteudo de categorias sensiveis MUST ser bloqueado para fluxos que enviam texto para fora do ambiente local, salvo configuracao explicita futura fora do escopo MVP.
- **FR-011**: Testes MUST cobrir cenarios em que agentes devem buscar, nao devem buscar, devem reformular, usar categorias dinamicas, e nunca devem escrever sem intencao explicita.
- **FR-012**: `doc/API.md` ou documentacao operacional MUST registrar a politica para clientes MCP e servidores.
- **FR-013**: A politica MUST tratar exemplos como heuristicas ilustrativas, nao como uma lista fechada de dominios pesquisaveis.

### Key Entities *(include if feature involves data)*

- **Agent Memory Policy**: Politica textual e testavel que orienta decisao de busca, uso de categorias dinamicas, filtros, reformulacao e escrita.
- **Category Inventory**: Lista atual de categorias disponiveis usada pelo agente para inferir quais dominios podem existir na memoria.
- **MCP Profile**: Perfil efetivo de conexao MCP com escopos `knowledge:read` e opcionalmente `knowledge:write`.
- **Sensitive Category Policy**: Lista/configuracao que classifica categorias sensiveis e define bloqueio de provider externo.
- **Retrieved Context**: Conteudo retornado por `search` ou `source`, sempre classificado como dado nao confiavel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos cenarios documentados de decisao MCP passam em testes automatizados.
- **SC-002**: Uma tentativa de escrita MCP com perfil read-only falha antes de chamar ingestao.
- **SC-003**: Um documento com prompt injection recuperado nao altera o prompt de sistema nem a politica do agente nos testes RAG/MCP.
- **SC-004**: Categorias sensiveis com provider externo resultam em bloqueio testado e mensagem acionavel.
- **SC-005**: A documentacao MCP descreve quando usar `search`, `sources`, `categories`, `tags`, `projects`, `source` e `ingest_text`.
- **SC-006**: Uma categoria adicionada ao inventario consegue alterar a decisao de buscar nos testes sem alterar codigo de politica.

## Assumptions

- O MVP altera contratos e guardrails do MCP/RAG, sem criar uma nova UI de administracao.
- `MCP_WRITE_ENABLED` continua sendo a chave principal para distinguir perfis read-only e read-write.
- Categorias sensiveis podem ser configuradas por nomes normalizados em settings no MVP, evitando migracao de banco inicial.
- A decisao de buscar usa nomes de categorias existentes no MVP; descricoes de categorias podem ser adicionadas em feature futura para melhorar precisao sem mudar o principio dinamico.
- O bloqueio de privacidade vale para resposta RAG e outros fluxos que enviam conteudo recuperado para provider externo; busca local no banco continua permitida.
- Atualizacao e exclusao via MCP permanecem fora do escopo porque essas tools ainda nao existem.
