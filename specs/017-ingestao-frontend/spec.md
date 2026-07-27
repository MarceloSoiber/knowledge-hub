# Feature Specification: Ingestão de Conhecimento no Frontend

**Feature Branch**: `feature/frontend-ingestao`  
**Created**: 2026-07-27  
**Status**: Draft  
**Input**: `plan/frontend/04-ingestao.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingerir um arquivo com metadados (Priority: P1)

Uma pessoa autenticada seleciona um arquivo aceito, associa ao menos uma categoria e, opcionalmente, tags e projetos; ao concluir, recebe a confirmação e pode abrir a fonte criada.

**Why this priority**: Arquivos são uma forma central de incluir material já existente no acervo.

**Independent Test**: Selecionar um `.txt`, `.md` ou `.pdf` de até 10 MB, escolher uma categoria e verificar o envio multipart, a confirmação e o link para a fonte retornada.

**Acceptance Scenarios**:

1. **Given** metadados carregados e um arquivo válido, **When** a pessoa envia o formulário com categorias, **Then** a interface chama `POST /api/v1/knowledge/uploads` com `multipart/form-data` e informa título, UUID público e quantidade de chunks criados.
2. **Given** uma ingestão de arquivo concluída, **When** a confirmação é exibida, **Then** a pessoa pode abrir `/sources/:sourceId` usando o UUID público retornado.
3. **Given** um arquivo com extensão não aceita ou maior que 10 MB, **When** ele é escolhido, **Then** a interface informa o erro localmente e não inicia a requisição.

---

### User Story 2 - Adicionar texto com metadados (Priority: P1)

Uma pessoa autenticada informa título, conteúdo e categorias para registrar texto diretamente na base, sem precisar carregar um arquivo.

**Why this priority**: Permite registrar decisões, notas e conteúdo novo de forma imediata.

**Independent Test**: Preencher título, conteúdo não vazio e categoria, enviar e verificar o corpo JSON de `POST /api/v1/knowledge/texts` e a confirmação recebida.

**Acceptance Scenarios**:

1. **Given** a aba de texto, **When** a pessoa preenche título, conteúdo e pelo menos uma categoria, **Then** a interface envia os IDs de categorias, tags e projetos selecionados no contrato JSON existente.
2. **Given** título, conteúdo ou categorias inválidos, **When** a pessoa tenta enviar, **Then** a interface marca os campos relevantes, explica o problema e não chama a API.
3. **Given** uma falha recuperável da API, **When** ela ocorre, **Then** título, conteúdo e metadados permanecem preenchidos para nova tentativa.

---

### User Story 3 - Lidar com processamento, duplicidade e falhas (Priority: P2)

Uma pessoa entende que a ingestão está em processamento sem receber uma falsa estimativa de progresso, evita submissões duplicadas e consegue agir quando o conteúdo já existe ou a infraestrutura falha.

**Why this priority**: Embeddings podem levar tempo e o backend protege a integridade do acervo com detecção de conteúdo duplicado.

**Independent Test**: Simular submissão pendente, `409` com `existing_source_id`, `400`, `404`, `413`, `502` e `503`, confirmando mensagens seguras, bloqueio de reenvio e preservação segura do formulário.

**Acceptance Scenarios**:

1. **Given** uma requisição em curso, **When** a pessoa tenta reenviar ou muda de aba, **Then** o envio correspondente permanece desabilitado e a UI anuncia processamento indeterminado.
2. **Given** a API responde `409` com `existing_source_id`, **When** a falha é exibida, **Then** a interface explica que o conteúdo já existe e oferece link à fonte existente, sem sobrescrevê-la.
3. **Given** a API responde erro de validação, metadado inexistente, arquivo grande ou indisponibilidade de embeddings, **When** a falha é exibida, **Then** a mensagem é acionável, não expõe detalhes internos e mantém os dados quando for seguro fazê-lo.

### Edge Cases

- Arquivo ausente, com extensão em maiúsculas, sem nome ou com tamanho exatamente 10 MB; a validação local segue somente os formatos e limite publicados, e o erro definitivo do servidor continua sendo exibido com segurança.
- Texto composto somente por espaços, título vazio ou maior que 255 caracteres e seleção de categorias vazia não disparam HTTP.
- Categorias, tags ou projetos podem ser removidos entre o carregamento dos metadados e o envio; `404` orienta a recarregar os metadados e mantém os demais valores.
- A resposta de `409` pode não conter `existing_source_id` em um payload inesperado; nesse caso, a UI informa duplicidade sem construir link inválido.
- Trocar de aba preserva os rascunhos locais de arquivo e texto; um sucesso limpa apenas o formulário que foi enviado. O arquivo não é restaurado após recarregar a página.
- Conteúdo, título e mensagens vindas da API são apresentados como texto, nunca como HTML confiável.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O frontend MUST disponibilizar uma rota autenticada de ingestão com abas "Enviar arquivo" e "Adicionar texto".
- **FR-002**: A feature MUST usar exclusivamente `KnowledgeApiService` para carregar categorias, tags e projetos e para chamar os endpoints de ingestão publicados.
- **FR-003**: O envio de arquivo MUST usar `multipart/form-data` com `file` e campos repetidos `category_ids`, `tag_ids` e `project_ids`; categorias MUST conter pelo menos um ID válido.
- **FR-004**: O envio de texto MUST usar JSON com `title`, `content`, `category_ids` e, quando selecionados, `tag_ids` e `project_ids`.
- **FR-005**: Antes do envio, a interface MUST validar arquivo `.txt`, `.md` ou `.pdf` de no máximo 10 MB; título não vazio de até 255 caracteres; conteúdo textual não vazio após `trim`; e ao menos uma categoria.
- **FR-006**: Enquanto cada envio estiver pendente, a feature MUST impedir submissão duplicada e apresentar indicador de processamento indeterminado com feedback acessível.
- **FR-007**: Em sucesso, a interface MUST exibir título, `source_id`, `chunks_created` e um link para `/sources/:sourceId`; somente o formulário concluído pode ser limpo.
- **FR-008**: Em `409`, a interface MUST informar duplicidade e, quando `detail.existing_source_id` for um UUID público válido, oferecer o atalho à fonte existente; nunca deve substituir conteúdo automaticamente.
- **FR-009**: Em erros de validação, metadado inexistente, arquivo grande ou indisponibilidade (`400`, `404`, `413`, `502`, `503`), a interface MUST exibir mensagem segura e acionável e preservar valores quando não houver risco de perder escolha do usuário.
- **FR-010**: A feature MUST oferecer carregamento/erro de metadados com nova tentativa e deixar claro que categorias são obrigatórias, enquanto tags e projetos são opcionais.
- **FR-011**: A implementação MUST manter navegação por teclado, labels associados, foco visível, regiões ARIA para processamento/resultado/erro e layout utilizável em viewport de 320 px.
- **FR-012**: A implementação MUST cobrir serialização dos dois envios, validações, estados pendentes, duplicidade, sucesso e falhas críticas em testes frontend e manter `npm run typecheck`, `npm test -- --watch=false` e `npm run build` aprovados.

### Key Entities

- **IngestionMetadata**: seleção transitória de IDs de categorias obrigatórias, tags e projetos opcionais para cada rascunho.
- **FileIngestionDraft**: arquivo local selecionado e seus metadados; não é persistido no navegador.
- **TextIngestionDraft**: título, conteúdo e metadados informados no formulário de texto; vive enquanto a rota estiver montada.
- **IngestionResult**: retorno público da API com UUID da fonte, título, metadados associados e total de chunks criados.
- **IngestionViewState**: estado de cada aba (`idle`, `validation-error`, `submitting`, `success`, `duplicate`, `request-error`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa autenticada consegue concluir uma ingestão válida de arquivo ou texto e abrir a fonte criada em até cinco interações após acessar a rota.
- **SC-002**: 100% dos campos enviados aos endpoints de arquivo e texto possuem teste de serialização no cliente HTTP.
- **SC-003**: Durante uma requisição pendente, 100% das tentativas de novo envio pela mesma aba não geram uma segunda chamada HTTP.
- **SC-004**: Para `409`, `400`, `404`, `413`, `502` e `503`, a tela mantém dados seguros do formulário e mostra orientação sem detalhes internos; em `409` com UUID, o link da fonte existente é utilizável.
- **SC-005**: Em viewport de 320 px e somente com teclado, abas, campos, seletor de metadados, envio, link de resultado e nova tentativa são operáveis.

## Assumptions

- A fundação Angular, guard, shell autenticado, `KnowledgeApiService`, tipos, componentes de estado e seletor reutilizável de metadados já estão disponíveis.
- A rota da feature será `/ingestao`, e o detalhe de fonte já é acessível em `/sources/:sourceId`.
- Os limites publicados permanecem `.txt`, `.md` e `.pdf`, máximo de 10 MB, título de até 255 caracteres e conteúdo textual não vazio; o backend continua como autoridade final.
- Não haverá progresso granular de upload, chunking ou embeddings na API; a UI mostrará apenas processamento indeterminado.
- Rascunhos não são persistidos em `localStorage` ou enviados automaticamente; trocar de aba preserva somente o estado em memória.

## Out of Scope

- Criar, editar ou excluir categorias, tags, projetos ou fontes dentro desta tela.
- Atualizar, mesclar ou sobrescrever automaticamente uma fonte duplicada.
- Upload em lote, arrastar-e-soltar, pré-visualização/OCR no navegador, barra de progresso real ou cancelamento da requisição.
- Alterar FastAPI, PostgreSQL, embeddings, MCP, limites de arquivo ou contratos REST existentes.
