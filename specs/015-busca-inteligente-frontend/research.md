# Research: Busca Inteligente no Frontend

## Decision: reutilizar os contratos REST existentes

**Rationale**: `POST /api/v1/knowledge/search` já recebe texto, limite, filtros de categoria/tag/projeto, score mínimo e diagnóstico opcional. As listagens e autocomplete necessários também já existem. A entrega é uma consumidora Angular desses contratos.

**Alternatives considered**:

- Criar endpoint agregado de filtros: rejeitado; aumenta backend sem necessidade e conflita com o princípio de aproveitar a API existente.
- Filtrar resultados somente no navegador: rejeitado; mudaria a semântica dos filtros e transferiria dados irrelevantes para o cliente.

## Decision: manter a tela como feature Angular, com estado e chamadas no serviço tipado

**Rationale**: A fundação prevista separa `core/`, `shared/` e `features/`. O serviço centralizado mantém autenticação, tratamento HTTP e contratos consistentes; o componente de feature coordena apenas formulário e estado de apresentação.

**Alternatives considered**:

- Fazer `HttpClient` diretamente no componente: rejeitado por duplicar lógica e contrariar a dependência explícita da Fase 01.
- Introduzir uma biblioteca global de estado: rejeitado; o estado desta tela é local e não justifica nova dependência.

## Decision: autocomplete de tags sob demanda, com debounce e cancelamento

**Rationale**: Tags podem crescer em quantidade. `GET /tags/autocomplete?q=&limit=` foi fornecido para sugestão por prefixo. Um fluxo RxJS com debounce, normalização do texto e troca para a requisição mais recente reduz chamadas e evita sugestão obsoleta.

**Alternatives considered**:

- Carregar todas as tags para filtrar no cliente: rejeitado por escalabilidade e por deixar de usar o endpoint dedicado.
- Consultar a cada tecla sem debounce: rejeitado por tráfego excessivo e pior experiência.

## Decision: diagnóstico é opt-in e não altera o significado do score

**Rationale**: `include_match_reasons` é opcional e `score` pode ser nulo em resultados textuais. A UI exibirá score apenas quando presente e motivos apenas quando a pessoa habilitar o diagnóstico e a API os devolver.

**Alternatives considered**:

- Sempre solicitar e renderizar motivos: rejeitado porque acrescenta ruído ao fluxo principal.
- Converter score nulo em zero: rejeitado porque zero comunica uma medida inexistente, não um resultado textual relevante.

## Decision: mensagens de erro por classe HTTP, sem conteúdo interno

**Rationale**: O plano de frontend exige orientação para filtro inválido, recurso inexistente e indisponibilidade de embeddings. A aplicação pode mapear `422` para revisão dos filtros, `404` para recarregar metadados, e `502`/`503` para tentar novamente ou acionar suporte, sem mostrar corpo cru da resposta.

**Alternatives considered**:

- Mostrar o detalhe devolvido pela API: rejeitado; pode revelar informação não apropriada e não é uma mensagem estável para usuários.
- Usar uma única mensagem genérica: rejeitado; não orienta a próxima ação.
