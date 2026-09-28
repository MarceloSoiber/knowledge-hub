# Feature Specification: Configuração de IA pelo portal

**Feature Branch**: `022-configuracao-llm-portal`  
**Created**: 2026-09-02  
**Status**: Draft  
**Input**: "Permitir ajustar pelo portal as configurações de IA mostradas no ambiente: provedor, URLs e modelos local/API, chave de API, modelo de embeddings e dimensão vetorial; reunir o acesso a essa configuração, ao tema e à desconexão em um menu de usuário no canto superior direito."

## User Scenarios & Testing

### User Story 1 - Administrar provedor, endpoints e modelos de IA (Priority: P1)

Uma pessoa autenticada abre Configurações, escolhe o provedor local ou API e ajusta os endpoints e modelos de chat/embeddings ativos, sem editar `.env` nem recriar containers.

**Why this priority**: O IP do serviço local pode mudar; depender de alteração de arquivo e reinicialização interrompe a operação do portal.

**Independent Test**: Com uma configuração inicialmente oriunda do ambiente, salvar um provedor, endpoint e modelo válidos e verificar que a próxima operação usa o destino e modelo selecionados.

**Acceptance Scenarios**:

1. **Given** que não há valor salvo no banco, **When** a pessoa abre Configurações, **Then** visualiza os fallbacks do ambiente e sabe que ainda não foram personalizados no portal.
2. **Given** valores válidos para o provedor escolhido, **When** a pessoa os salva, **Then** eles ficam persistidos e passam a ser usados pelas próximas chamadas de embeddings e respostas.
3. **Given** uma URL inválida, modelo vazio ou provedor sem chave de API configurada, **When** a pessoa tenta salvar, **Then** recebe erro de validação e a configuração ativa não é alterada.

---

### User Story 2 - Proteger a chave de API (Priority: P1)

Uma pessoa autenticada informa ou substitui a chave de API quando seleciona o provedor externo, sem que o segredo volte a aparecer na página, nas respostas da API ou nos logs.

**Why this priority**: Sem uma chave configurável e protegida, a seleção do provedor API não é operacional.

**Independent Test**: Salvar uma chave, recarregar a página e verificar que ela é reportada apenas como configurada; executar uma solicitação no provedor API confirma seu uso sem expô-la.

**Acceptance Scenarios**:

1. **Given** que já existe chave salva, **When** a pessoa consulta Configurações, **Then** vê somente o estado “configurada”, nunca seu conteúdo.
2. **Given** o provedor API selecionado, **When** a pessoa informa uma nova chave não vazia e salva, **Then** o portal confirma a atualização e a chave passa a ser usada pelas próximas requisições.
3. **Given** o provedor API selecionado sem chave efetiva, **When** a pessoa tenta salvar ou operar uma chamada dependente dela, **Then** recebe erro orientado à ação sem revelar segredos.

---

### User Story 3 - Alterar embeddings com segurança (Priority: P1)

Uma pessoa autenticada pode trocar o modelo de embeddings e administrar a dimensão vetorial por um fluxo explícito de manutenção, entendendo quando precisa reindexar a base.

**Why this priority**: Modelo, provedor e dimensão compõem a identidade dos vetores; uma alteração ingênua pode tornar a busca incompatível ou impossibilitar a inicialização.

**Independent Test**: Alterar o modelo de embeddings mantendo a dimensão, verificar aviso de reindexação e iniciar a operação existente; solicitar alteração de dimensão confirma a migração, adapta a coluna e termina com reindexação válida.

**Acceptance Scenarios**:

1. **Given** uma alteração de modelo de embeddings ou provedor, **When** a pessoa revisa e confirma a configuração, **Then** o portal explica que os vetores existentes ficam incompatíveis até a reindexação e oferece o próximo passo seguro.
2. **Given** uma alteração de `VECTOR_DIM`, **When** a pessoa não confirma a operação de manutenção, **Then** a dimensão ativa e a estrutura do banco não são modificadas.
3. **Given** uma alteração de dimensão confirmada, **When** o processo de migração e reindexação termina, **Then** a coluna pgvector, o índice e os embeddings ativos usam a nova dimensão consistente.

---

### User Story 4 - Entender a configuração ativa (Priority: P2)

Uma pessoa autenticada consegue distinguir valores configurados pelo portal dos fallbacks do ambiente e recebe feedback claro de carregamento, sucesso e falha ao administrar o LLM.

**Why this priority**: A transparência evita a impressão de que uma alteração foi salva quando o processo ainda usa outro valor.

**Independent Test**: Abrir a página sem configuração persistida, salvar valores e recarregar; a origem e os valores efetivos são mostrados corretamente em cada estado.

**Acceptance Scenarios**:

1. **Given** a tela de Configurações aberta, **When** os dados estão carregando ou há falha de rede, **Then** a interface apresenta estado acessível e uma ação de recuperação.
2. **Given** uma configuração salva pelo portal, **When** a pessoa retorna à tela, **Then** vê os valores persistidos e a indicação de que substituem o ambiente.

---

### User Story 5 - Usar controles pessoais em um único lugar (Priority: P2)

Uma pessoa autenticada abre o menu de usuário no canto superior direito para alternar o tema, acessar Configurações ou desconectar, sem esses controles competirem com busca e navegação principal.

**Why this priority**: Tema, preferências e sessão pertencem ao mesmo contexto de conta; agrupá-los reduz ruído visual na barra superior e torna a configuração fácil de encontrar.

**Independent Test**: Abrir o menu por mouse e teclado, alternar o tema, navegar para Configurações e sair da sessão, confirmando que cada ação funciona e o menu fecha de forma previsível.

**Acceptance Scenarios**:

1. **Given** uma rota privada aberta, **When** a pessoa aciona o botão de usuário, **Then** vê um menu com a ação de tema, o link Configurações e Desconectar.
2. **Given** o menu aberto, **When** a pessoa pressiona Escape, clica fora, escolhe uma ação ou muda de rota, **Then** o menu fecha e o foco retorna ao botão quando apropriado.
3. **Given** uma pessoa navega por teclado ou leitor de tela, **When** abre o menu, **Then** o botão informa seu estado, os itens têm nomes claros e podem ser alcançados em ordem lógica.

### Edge Cases

- URLs podem ser fornecidas com ou sem o sufixo `/v1`; o cliente preserva o comportamento atual e não duplica esse segmento.
- Espaços antes/depois de URL, modelo, provedor e dimensão são removidos antes de validar e persistir.
- Uma URL sintaticamente válida pode estar indisponível ou apontar para um servidor sem o modelo escolhido; salvar não deve testar nem bloquear pela disponibilidade remota, e os erros da operação posterior continuam retornando como hoje.
- Alterar uma configuração enquanto uma requisição está em andamento não muda essa requisição; a atualização se aplica às novas requisições iniciadas após o salvamento.
- Trocar provedor ou modelo de embeddings torna vetores existentes incompatíveis até reindexação; trocar dimensão exige mudança física da coluna `vector(n)` e reconstrução de índice.
- Trocar para provedor API não pode enviar conteúdo sensível se as políticas atuais o proibirem.
- O menu deve permanecer utilizável em telas pequenas, não ser cortado pela barra superior e não conflitar com o menu lateral de navegação.

## Requirements

### Functional Requirements

- **FR-001**: O sistema DEVE expor, sob autenticação existente, a configuração efetiva e a origem (portal ou ambiente) de `LLM_PROVIDER`, endpoints/modelos local e API, modelo de embeddings e dimensão vetorial, sem retornar segredos.
- **FR-002**: O sistema DEVE permitir atualizar atomicamente o provedor, URLs e modelos aplicáveis, validando `local`/`api`, URL absoluta HTTP(S), modelos não vazios e chave efetiva quando o provedor for API.
- **FR-003**: O sistema DEVE persistir substituições em `app_config`, usando chaves próprias para os valores não secretos e um armazenamento cifrado para a chave de API, com atualização atômica para evitar configuração parcialmente aplicada.
- **FR-004**: Enquanto não existir substituição persistida, o sistema DEVE manter todos os valores do ambiente como fallbacks: `LLM_PROVIDER`, `LOCAL_LLM_*`, `API_LLM_*`, `API_KEY`, `EMBEDDING_MODEL` e `VECTOR_DIM`.
- **FR-005**: Após uma atualização bem-sucedida, novas chamadas de embeddings e de chat DEVEM resolver e usar os valores persistidos; não pode ser necessário reiniciar o processo ou recriar containers, exceto durante a operação explícita de migração de dimensão vetorial.
- **FR-006**: `DOCKER_LOCAL_LLM_BASE_URL` DEVE permanecer somente como mecanismo de inicialização do Docker Compose que alimenta o fallback `LOCAL_LLM_BASE_URL`; o portal não deve editar arquivos `.env`, variáveis de processo ou Docker.
- **FR-007**: O portal DEVE oferecer uma rota privada Configurações com seções Provedor e chat, Embeddings e Manutenção vetorial; campos inativos devem permanecer visíveis apenas quando necessários ao provedor selecionado.
- **FR-008**: A API e a interface NÃO DEVEM expor a chave de API. A chave DEVE ser cifrada em repouso com uma chave mestra fornecida somente ao backend; leitura retorna somente `api_key_configured`.
- **FR-009**: Alteração de modelo/provedor de embeddings DEVE exibir o impacto e encaminhar à reindexação. Alteração de dimensão DEVE exigir confirmação explícita, bloquear novas operações dependentes durante a manutenção e executar migração da coluna pgvector, recriação de índices e reindexação antes de se tornar ativa.
- **FR-010**: A documentação da API DEVE descrever endpoints, precedência portal → ambiente, proteção da chave e a distinção entre `DOCKER_LOCAL_LLM_BASE_URL` e a configuração efetiva de runtime.
- **FR-011**: O cabeçalho autenticado DEVE reunir alternância de tema, acesso à rota Configurações e desconexão em um menu de usuário acionado pelo canto superior direito; esses controles não devem permanecer como botões independentes na barra.
- **FR-012**: O menu de usuário DEVE ser operável por teclado, indicar `aria-expanded`, fechar por Escape, clique externo, navegação e seleção de item, e restaurar foco ao botão de origem quando o fechamento não resultar em navegação.

### Key Entities

- **Configuração operacional de IA**: provedor, endpoints, modelos de chat/embeddings e dimensão que determinam clientes e compatibilidade dos vetores.
- **Entrada `app_config`**: registro chave-valor persistente existente; armazena substituições operacionais e a chave de API cifrada, com data de atualização.
- **Operação de migração vetorial**: manutenção exclusiva para mudança de dimensão, composta por confirmação, bloqueio, adaptação de schema/índices e reindexação.
- **Origem da configuração**: metadado de leitura que informa se o valor efetivo veio do portal ou do ambiente.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Uma pessoa autenticada altera provedor, endpoint e modelos pelo portal e, sem reiniciar a aplicação, a próxima chamada usa os valores ativos correspondentes.
- **SC-002**: Na ausência de registros em `app_config`, todas as operações continuam usando os valores de ambiente, sem regressão nos testes existentes de LLM/embeddings.
- **SC-003**: Nenhum GET, resposta de erro ou log de aplicação contém o valor da chave de API salva.
- **SC-004**: Tentativas de salvar combinação inválida recebem resposta 422 e não modificam nenhum valor ativo.
- **SC-005**: Uma alteração confirmada de dimensão conclui com coluna e índice pgvector na dimensão escolhida e sem embeddings legados considerados compatíveis.

## Assumptions

- O Bearer token já obrigatório para rotas privadas representa o acesso administrativo do portal atual; não há papéis separados nesta entrega.
- Ambos os provedores continuam falando a API compatível com OpenAI usada por `OpenAIEmbeddingClient` e `OpenAICompatibleAnswerClient`.
- A URL informada é a que o processo backend consegue alcançar (por exemplo, IP da rede), não necessariamente a URL visível no navegador do usuário.
- A tabela `app_config` já existente atende ao requisito de persistência; criar outra tabela apenas para os mesmos pares chave-valor seria redundante.
- Tema continua preferência local do navegador; o menu apenas centraliza seu acesso, sem passar a persistir tema no backend.

## Out of Scope

- Descoberta automática de modelos, teste de conectividade, histórico/auditoria por usuário, permissões administrativas granulares ou edição de `.env`/Docker pelo portal.
