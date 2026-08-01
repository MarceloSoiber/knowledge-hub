# Feature Specification: Backup e Restauração Administrativos

**Feature Branch**: `022-backup-restore-admin`

**Created**: 2026-07-29

**Status**: Draft

**Input**: Usuário deseja gerar, baixar e restaurar backups pela interface; a restauração pode substituir a base atual.

## User Scenarios & Testing

### User Story 1 - Baixar um backup da base (Priority: P1)

Um administrador gera e baixa um backup completo do acervo para guardá-lo fora do sistema.

**Independent Test**: Com uma base contendo fontes e metadados, solicitar o backup e validar que o arquivo custom do PostgreSQL é baixado e pode ser listado por `pg_restore --list`.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada, **When** o administrador solicita um backup, **Then** recebe um arquivo `.dump` contendo a base atual.
2. **Given** falha na ferramenta de backup, **When** o administrador solicita o arquivo, **Then** a API não retorna arquivo parcial e fornece erro sanitizado.

---

### User Story 2 - Restaurar e substituir a base (Priority: P2)

Um administrador envia um backup válido e substitui intencionalmente a base atual.

**Independent Test**: Criar uma base A, gerar backup, alterar a base para B, restaurar o backup de A e confirmar que fontes, metadados e busca voltam ao estado A.

**Acceptance Scenarios**:

1. **Given** um arquivo compatível e a confirmação literal `RESTAURAR BASE`, **When** o administrador confirma a restauração, **Then** a API cria um backup de segurança antes de substituir a base.
2. **Given** confirmação ausente ou diferente, **When** o administrador envia o arquivo, **Then** a API rejeita a operação sem alterar a base.
3. **Given** arquivo inválido, grande demais ou incompatível, **When** a restauração é solicitada, **Then** a API falha antes de executar comandos destrutivos.
4. **Given** uma restauração concluída, **When** o administrador retorna à aplicação, **Then** ela informa o resultado e solicita recarregamento da sessão para refletir o banco restaurado.

### Edge Cases

- Falha durante a geração do backup de segurança impede a restauração.
- Apenas arquivos no formato custom do PostgreSQL são aceitos.
- A operação é serializada; uma segunda solicitação recebe conflito enquanto houver backup/restauração em curso.
- Senhas, URLs de banco e conteúdo das fontes não aparecem em mensagens ou logs.

## Requirements

### Functional Requirements

- **FR-001**: A API deve produzir backup no formato custom via `pg_dump` e transmiti-lo para download.
- **FR-002**: A API deve aceitar restauração apenas com arquivo custom válido e confirmação literal `RESTAURAR BASE`.
- **FR-003**: A API deve criar backup de segurança antes de qualquer restauração destrutiva.
- **FR-004**: A API deve executar restauração com limpeza das tabelas existentes e recriar a extensão `vector` quando necessário.
- **FR-005**: A API deve serializar operações administrativas de backup/restauração.
- **FR-006**: A interface deve explicar a substituição da base, exigir confirmação digitada e apresentar estado de processamento/resultado.
- **FR-007**: Comandos e erros não devem expor credenciais, caminhos sensíveis ou conteúdo do acervo.
- **FR-008**: A imagem de backend deve incluir os clientes PostgreSQL necessários.
- **FR-009**: A documentação de API e operações deve cobrir os novos endpoints, limites e recuperação pelo backup de segurança.

## Success Criteria

- **SC-001**: Um administrador autenticado baixa um backup válido sem intervenção de terminal.
- **SC-002**: Restauração confirmada recupera fontes, relações e busca de uma cópia anterior em ambiente de teste.
- **SC-003**: Nenhuma restauração é executada sem confirmação literal e backup de segurança bem-sucedido.
- **SC-004**: Erros de ferramenta são mostrados sem segredos ou conteúdo das fontes.

## Assumptions

- A mesma autenticação Bearer existente protege estas operações; controle de papéis é futuro escopo.
- A primeira versão executa as operações de forma síncrona e limita o tamanho do upload a 1 GB.
- O backup de segurança é preservado no diretório de trabalho temporário da operação e retornado no resultado apenas por identificador, não por conteúdo.
