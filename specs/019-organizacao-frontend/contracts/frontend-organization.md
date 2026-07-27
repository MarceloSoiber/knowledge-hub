# Contract: Integração de Organização no frontend

Todos os caminhos são relativos a `/api/v1/knowledge`, autenticados pelos interceptores existentes e acessados exclusivamente por `KnowledgeApiService`.

| Necessidade | Método e caminho | Resposta/uso |
| --- | --- | --- |
| Categorias | `GET/POST /categories`, `PATCH/DELETE /categories/{id}` | `Category`; DELETE retorna `204`. |
| Tags | `GET/POST /tags`, `PATCH/DELETE /tags/{id}` | `Tag`; DELETE retorna `204`. |
| Sugestões de tags | `GET /tags/autocomplete?q={query}&limit={limit}` | `Tag[]`; `q` normalizada pela API. |
| Projetos | `GET /projects?status={active\|archived}`, `POST /projects`, `PATCH /projects/{id}` | `Project` ou `Project[]`. |
| Ciclo de projeto | `POST /projects/{id}/archive`, `POST /projects/{id}/reactivate` | `Project` canônico com novo `status`. |
| Fontes do projeto | `GET /projects/{id}/sources` | `KnowledgeSource[]`; links usam `/sources/{source_id}`. |

## Payloads

```json
{ "name": "documentação" }
```

```json
{ "name": "knowledge hub", "description": "Contexto de desenvolvimento" }
```

`PATCH /projects/{id}` envia somente nome e/ou descrição alterados. Ações de arquivamento/reativação não têm corpo.

## Erros tratados pela UI

| Status | Tratamento |
| --- | --- |
| `400`, `422` | Pedir revisão do campo; preservar rascunho. |
| `404` | Informar que o item não existe mais e oferecer recarga da lista. |
| `409` em criar/editar | Informar nome já existente; preservar rascunho. |
| `409` em DELETE categoria/tag | Informar que o item está em uso, mantê-lo e orientar a reclassificar fontes primeiro. |
| `502`, `503` | Indisponibilidade temporária e nova tentativa; não exibir corpo bruto. |

`401` continua sob responsabilidade do interceptor de autorização. A interface não interpreta mensagens de erro remotas como HTML.
