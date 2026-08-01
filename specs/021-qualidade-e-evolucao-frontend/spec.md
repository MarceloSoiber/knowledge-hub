# Feature Specification: Qualidade, segurança e evolução do frontend

**Feature Branch**: `021-qualidade-e-evolucao-frontend`  
**Created**: 2026-07-27  
**Status**: Draft  
**Input**: Plano `plan/frontend/08-qualidade-e-evolucao.md`

## User Scenarios & Testing

### User Story 1 - Usar os fluxos críticos com feedback confiável (Priority: P1)

Uma pessoa autenticada consegue buscar e abrir uma fonte, ingerir texto ou arquivo e perguntar à base, recebendo estados distintos de carregamento, vazio, duplicidade, validação e indisponibilidade.

**Why this priority**: Esses fluxos formam o primeiro corte do produto e precisam ser confiáveis antes de expandir funcionalidades.

**Independent Test**: Executar testes de componentes para Busca, Pergunte, Ingestão, Biblioteca/detalhe e Dashboard, simulando respostas HTTP de sucesso, vazio e erro, e validar os estados exibidos.

**Acceptance Scenarios**:

1. **Given** uma resposta bem-sucedida, vazia ou com falha recuperável, **When** a pessoa executa um fluxo crítico, **Then** a interface distingue os estados e oferece a próxima ação aplicável.
2. **Given** uma duplicidade ou validação rejeitada pela API, **When** a ingestão falha, **Then** o rascunho é preservado e a mensagem não expõe detalhe remoto não confiável.
3. **Given** uma operação irreversível ou de transição de status, **When** a pessoa a inicia, **Then** a interface exige confirmação antes de chamar a API.

---

### User Story 2 - Manter a sessão segura (Priority: P1)

Uma pessoa tem sua sessão limpa e é levada ao login quando a API protegida responde `401`, sem que o Bearer token apareça em telas, logs ou mensagens de erro.

**Why this priority**: A credencial permite acesso ao acervo; o tratamento uniforme de sessão reduz exposição e estados inconsistentes.

**Independent Test**: Testar guard, interceptadores e serviço de autenticação com armazenamento simulado, verificando envio somente à API protegida, remoção do token no `401` e redirecionamento ao login.

**Acceptance Scenarios**:

1. **Given** uma chamada à API protegida com sessão válida, **When** o cliente a envia, **Then** o cabeçalho Bearer é incluído apenas para o prefixo protegido.
2. **Given** uma resposta `401` protegida, **When** ela chega ao cliente, **Then** o token persistido e o estado de sessão são limpos e a navegação segue para `/login`.
3. **Given** uma URL de retorno inválida, **When** o login termina, **Then** a navegação usa `/inicio`, sem redirecionamento aberto.

---

### User Story 3 - Acessar a interface em dispositivos e tecnologias assistivas (Priority: P2)

Uma pessoa navega por teclado e leitor de tela pelos estados e ações dos fluxos críticos, em desktop e mobile.

**Why this priority**: Qualidade de produto exige que os mesmos fluxos funcionem fora do caminho visual ideal.

**Independent Test**: Seguir o roteiro manual em 320 px, 768 px e desktop, com teclado e leitor de tela, cobrindo login, busca, pergunta, ingestão, detalhe e dashboard.

**Acceptance Scenarios**:

1. **Given** carregamento, vazio, erro ou sucesso, **When** a pessoa usa leitor de tela, **Then** recebe anúncio sem duplicar ou revelar conteúdo inseguro.
2. **Given** diálogo de confirmação, **When** a pessoa usa teclado, **Then** pode cancelar, confirmar e recuperar foco de modo previsível.
3. **Given** viewport mobile, **When** a pessoa percorre os fluxos críticos, **Then** controles e conteúdo continuam legíveis e operáveis.

### Edge Cases

- Um erro com corpo inesperado, HTML ou token não pode ser mostrado, serializado em mensagem ou usado para renderização.
- `401` em uma requisição fora do prefixo protegido não pode encerrar a sessão do Knowledge Hub.
- Uma execução de testes/build impedida por requisito de versão do Node deve falhar com diagnóstico explícito; não pode ser tratada como suite aprovada.
- Atualizações futuras de API devem ser registradas como proposta versionada e não ser parcialmente implementadas no cliente antes de contrato publicado.

## Requirements

### Functional Requirements

- **FR-001**: O frontend DEVE ter testes unitários para `KnowledgeApiService`, guard, serviço/interceptadores de autenticação, classificação de erros e validações/formulários dos fluxos críticos.
- **FR-002**: Os testes HTTP DEVEM usar `HttpTestingController` para validar método, URL, query, corpo e ausência/presença apropriada de Authorization.
- **FR-003**: Os componentes críticos DEVEM ter cobertura de loading, vazio, erro recuperável, sucesso e confirmação quando aplicável.
- **FR-004**: O cliente DEVE limpar token e sessão diante de `401` de `/api/v1/knowledge/` e redirecionar ao login sem expor a credencial.
- **FR-005**: O cliente DEVE continuar tratando conteúdo e detalhes remotos como texto não confiável; mensagens ao usuário DEVEM ser derivadas de mapas locais seguros.
- **FR-006**: Exclusão de fonte, exclusão de categoria/tag e arquivamento/reativação de projeto DEVEM ser cobertos por testes que confirmem a intenção antes da requisição.
- **FR-007**: A entrega DEVE documentar e executar uma matriz manual para desktop, mobile, teclado e leitor de tela dos fluxos críticos.
- **FR-008**: Antes de entrega, o pipeline local DEVE executar `npm run typecheck`, `npm test -- --watch=false` e `npm run build` em ambiente Node compatível com o Angular CLI definido pelo lockfile.
- **FR-009**: O repositório DEVE manter um roadmap técnico para paginação/ordenação/filtros de fontes, estatísticas, progresso de ingestão, arquivos originais e metadados administráveis, sem implementar essas APIs nesta feature.

### Key Entities

- **Matriz de qualidade**: relação entre fluxo crítico, estados esperados, testes automatizados e verificações manuais.
- **Erro seguro de UI**: classificação local de código HTTP em mensagem e ação segura, sem interpolar o corpo remoto.
- **Estado de sessão**: token transitório/persistido, status de autenticação e rota de retorno validada.
- **Proposta de evolução de API**: capacidade futura, consumidores, contrato mínimo e critério de adoção.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Cada fluxo crítico possui ao menos um teste de componente para sucesso e para seu estado de falha/vazio mais relevante, além de testes de contrato HTTP quando chama API.
- **SC-002**: Testes demonstram que `401` protegido limpa a sessão, redireciona ao login e não adiciona Bearer a URLs não protegidas.
- **SC-003**: O checklist manual é executável e cobre desktop, mobile, teclado e leitor de tela para todos os fluxos do primeiro corte.
- **SC-004**: Typecheck, testes e build passam em uma versão Node suportada; bloqueios de ferramenta são visíveis como falha de qualidade até serem resolvidos.

## Assumptions

- Esta feature fortalece o frontend Angular já existente; não altera comportamento de FastAPI, banco, MCP ou endpoints publicados.
- O requisito atual do Angular CLI é fonte de verdade para a versão mínima de Node; a imagem Docker do frontend é a referência de build reproduzível.
- Cobertura percentual será medida/configurada somente se a ferramenta atual expuser relatório estável; o mínimo inicial é a matriz de caminhos críticos verificável.

## Out of Scope

- Implementar endpoints futuros, mudar esquema OpenAPI, criar monitoramento de produção, telemetria de usuário, SSO ou autorização por papel.
- Persistir Bearer token fora do comportamento de “manter conectado” já documentado, ou registrar token em logs de teste.
