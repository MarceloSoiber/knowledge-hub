# Feature Specification: Biblioteca e manutenção de fontes

**Feature Branch**: `018-biblioteca-frontend`  
**Created**: 2026-07-27  
**Status**: Draft  
**Input**: Plano `plan/frontend/05-biblioteca.md`

## User Scenarios & Testing

### User Story 1 - Consultar o acervo (Priority: P1)

Um usuário autenticado abre a Biblioteca, encontra uma fonte por título ou pelos metadados já carregados e abre seu detalhe completo.

**Why this priority**: A consulta é a base para confirmar o que já foi ingerido e iniciar qualquer manutenção com segurança.

**Independent Test**: Com fontes de tipos e metadados distintos, filtrar localmente a lista e abrir uma fonte retorna o conteúdo e os metadados correspondentes.

**Acceptance Scenarios**:

1. **Given** fontes já ingeridas, **When** o usuário acessa `/biblioteca`, **Then** vê uma lista de fontes com título, tipo, origem e metadados.
2. **Given** a lista carregada, **When** informa um trecho do título ou aplica filtros de metadados, **Then** a lista mostra somente as fontes que atendem a todos os critérios, sem nova chamada à API.
3. **Given** uma fonte exibida, **When** o usuário abre seu detalhe, **Then** vê conteúdo, origem, tipo, datas e associações corretas.

---

### User Story 2 - Editar uma fonte (Priority: P2)

Um usuário corrige título, conteúdo ou associações suportadas de uma fonte e recebe feedback claro sobre o resultado e sobre o reprocessamento de conteúdo.

**Why this priority**: Corrigir material desatualizado evita reingestão manual e mantém o acervo confiável.

**Independent Test**: Abrir uma fonte, editar um campo válido e confirmar que o detalhe mostra a resposta retornada por `PATCH` imediatamente.

**Acceptance Scenarios**:

1. **Given** o formulário de detalhe, **When** o usuário muda somente título e/ou associações e salva, **Then** a tela atualiza com a resposta bem-sucedida sem indicar novo processamento de conteúdo.
2. **Given** o formulário de detalhe, **When** o usuário modifica o conteúdo, **Then** recebe aviso antes do envio de que chunks e embeddings serão gerados novamente.
3. **Given** a API retorna conflito de conteúdo duplicado ou erro de validação, **When** o envio termina, **Then** o rascunho é preservado e a tela informa um próximo passo seguro.

---

### User Story 3 - Excluir uma fonte com confirmação (Priority: P3)

Um usuário remove definitivamente uma fonte apenas após confirmar explicitamente a operação.

**Why this priority**: Exclusão é irreversível e não pode ocorrer por clique acidental.

**Independent Test**: Abrir o diálogo, cancelar e confirmar que nenhuma chamada DELETE é feita; confirmar e verificar `DELETE` com `confirm=true`, retorno à Biblioteca e lista atualizada.

**Acceptance Scenarios**:

1. **Given** uma fonte aberta, **When** o usuário escolhe excluir, **Then** um diálogo explica que a operação é definitiva e apresenta ações distintas de cancelar e confirmar.
2. **Given** o diálogo aberto, **When** o usuário cancela ou pressiona Escape, **Then** a fonte permanece intacta e nenhuma exclusão é enviada.
3. **Given** o diálogo aberto, **When** o usuário confirma, **Then** o cliente envia `confirm=true` e, após `204`, retorna à Biblioteca sem a fonte excluída.

### Edge Cases

- Lista vazia, busca sem resultados, falha de carregamento e fonte removida em outra sessão têm estados orientados ao próximo passo.
- Uma URL com UUID inválido, uma fonte inexistente ou uma resposta `404` durante salvar/excluir não deve deixar a tela em carregamento nem sugerir que a operação foi concluída.
- Se nenhum campo for alterado, salvar não envia `PATCH` vazio e explica que não há alterações pendentes.
- Filtros de categorias, tags e projetos são inclusivos dentro de cada grupo e cumulativos entre grupos; a pesquisa de título não diferencia maiúsculas/minúsculas nem acentos.
- Enquanto salvar ou excluir está em curso, os controles que poderiam reenviar ou modificar a mesma fonte ficam bloqueados.

## Requirements

### Functional Requirements

- **FR-001**: O sistema DEVE disponibilizar uma rota privada de Biblioteca e uma entrada navegável no shell autenticado.
- **FR-002**: A Biblioteca DEVE carregar `GET /knowledge/sources` uma vez por entrada/recarga explícita e exibir título, tipo, origem e associações de cada fonte.
- **FR-003**: A Biblioteca DEVE pesquisar localmente por título e filtrar localmente por categorias, tags e projetos, sem reenviar filtros ao backend.
- **FR-004**: O detalhe DEVE obter a fonte por UUID via `GET /knowledge/sources/{source_id}` e exibir conteúdo, URI/origem, tipo, hash e datas quando disponíveis, além das associações.
- **FR-005**: O formulário DEVE permitir alterar apenas `title`, `content`, `category_ids`, `tag_ids` e `project_ids`, montando um `PATCH` somente com campos efetivamente alterados.
- **FR-006**: Antes de enviar alteração de conteúdo, a interface DEVE avisar de forma acessível que o conteúdo será reprocessado e terá embeddings recriados.
- **FR-007**: Após `PATCH` bem-sucedido, a interface DEVE usar a resposta como novo estado canônico, limpar o estado de edição pendente e refletir as alterações imediatamente.
- **FR-008**: A exclusão DEVE exigir confirmação por diálogo e DEVE enviar `DELETE /knowledge/sources/{source_id}?confirm=true` somente após a confirmação explícita.
- **FR-009**: Após exclusão bem-sucedida, a interface DEVE retornar à Biblioteca e atualizar/remover a fonte da lista visível.
- **FR-010**: A interface DEVE mapear `400/422`, `404`, `409`, `502` e `503` a mensagens seguras e acionáveis; detalhes remotos não devem ser renderizados como HTML.
- **FR-011**: Estados de carregamento, vazio, erro, sucesso, diálogo e controles devem ser acessíveis por teclado e leitores de tela em viewport de 320 px ou maior.

### Key Entities

- **Fonte listada**: projeção local de `KnowledgeSource`, usada para busca e filtros em memória.
- **Fonte detalhada**: `KnowledgeSourceDetail` canônica retornada pela API, contendo conteúdo e todos os metadados exibidos.
- **Rascunho de edição**: valores editáveis e baseline da fonte detalhada usados para calcular um PATCH mínimo.
- **Estado de Biblioteca**: consulta local, filtros selecionados, carga da lista e resultado filtrado; não é persistido fora da rota.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Testes automatizados demonstram que busca e filtros alteram a lista sem nova requisição HTTP após o carregamento inicial.
- **SC-002**: Testes automatizados demonstram que um `PATCH` bem-sucedido atualiza o detalhe sem recarregar a página e que PATCH vazio não é enviado.
- **SC-003**: Testes automatizados demonstram que DELETE não ocorre ao cancelar/Escape e inclui `confirm=true` após confirmação.
- **SC-004**: Em verificação manual, Biblioteca, detalhe, edição e exclusão são utilizáveis somente por teclado em 320 px, 768 px e desktop.

## Assumptions

- A API existente e documentada é a fonte de verdade; não há alteração de backend, migração ou endpoint novo nesta feature.
- "Filtros visuais de metadados" usa as associações já retornadas pela listagem e não inclui criação/edição de categorias, tags ou projetos.
- "Origem" é representada pela URI publicada pela API; URIs são apresentadas como texto/link seguro, sem interpretar conteúdo remoto.
- A lista é suficientemente pequena para filtragem em memória nesta fase; paginação e pesquisa server-side ficam fora de escopo.
- O componente de detalhe já usado por Busca será evoluído para servir Busca, Ingestão e Biblioteca, preservando `/sources/:sourceId` como rota canônica.

## Out of Scope

- Criação, arquivamento ou exclusão de categorias, tags e projetos.
- Upload, ingestão, reindexação manual, progresso real de embeddings, histórico/versionamento ou desfazer exclusão.
- Paginação, ordenação avançada, filtros enviados ao servidor ou pesquisa de conteúdo integral.
- Alterações nos contratos FastAPI, MCP, PostgreSQL, autenticação ou `doc/API.md`.
