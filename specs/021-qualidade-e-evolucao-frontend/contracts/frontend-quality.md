# Contract: Qualidade e segurança do frontend

## Fronteira HTTP e sessão

| Regra | Contrato verificável |
| --- | --- |
| Header Bearer | Apenas requisições cujo caminho começa com `/api/v1/knowledge/` recebem `Authorization: Bearer <token>` quando há sessão. |
| `401` protegido | `AuthService.logout()` limpa token/memória/persistência e o roteador navega para `/login`. |
| `401` não protegido | Não limpa a sessão do Knowledge Hub. |
| Corpo de erro | Nunca é interpolado como HTML; a mensagem vem de mapeamento local ou regra de domínio segura. |
| Retorno após login | Aceita rota iniciada por uma única `/`, rejeita `//` e `/login`; fallback é `/inicio`. |

## Matriz mínima de testes

| Área | Unitário/HTTP | Componente |
| --- | --- | --- |
| Core | AuthService, guard, auth/unauthorized interceptors, `toApiError`, `KnowledgeApiService` | N/A |
| Login | validação de token, retorno seguro e erro | checking, erro, sucesso |
| Ingestão | upload/texto, metadados, duplicidade e validação | loading, validação, duplicidade, sucesso, indisponibilidade |
| Busca e Pergunte | payloads, filtros e mensagens seguras | loading, vazio, sucesso, erro, citações quando aplicável |
| Biblioteca/detalhe | list/detail, PATCH/DELETE confirmado | loading, vazio, filtro, edição, confirmação, erro |
| Organização | CRUD, conflito, archive/reactivate confirmados | loading, vazio, sucesso, conflito, erro |
| Dashboard | quatro leituras e ordem local | loading, parcial, vazio, erro/retry, atalhos |

## Evoluções fora desta entrega

Nenhum endpoint novo é consumido nesta feature. As propostas de API em [data-model.md](../data-model.md) exigem uma especificação própria com OpenAPI, autorização, paginação/consistência e atualização de `doc/API.md` antes de implementação no cliente.
