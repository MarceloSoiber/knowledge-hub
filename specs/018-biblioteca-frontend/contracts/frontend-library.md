# Contract: Frontend Biblioteca

Todos os caminhos são relativos a `/api/v1/knowledge`, autenticados pelos interceptores e acessados exclusivamente por `KnowledgeApiService`.

## Listagem e detalhe

| Necessidade | Método e caminho | Uso na interface |
| --- | --- | --- |
| Listar acervo | `GET /sources` | Carregar a Biblioteca; pesquisa e filtros ocorrem no cliente. |
| Abrir fonte | `GET /sources/{source_id}` | Exibir conteúdo e preparar baseline de edição. |

`source_id` é UUID público. `GET /sources` retorna metadados sem conteúdo; o detalhe é necessário antes de editar.

## Atualização

`PATCH /sources/{source_id}` recebe JSON com um ou mais dos campos abaixo. Campos ausentes devem permanecer ausentes; o cliente não envia payload vazio.

```json
{
  "title": "Ata revisada",
  "content": "Conteúdo canônico revisado.",
  "category_ids": [2],
  "tag_ids": [5, 8],
  "project_ids": []
}
```

| Campo | Regra do cliente |
| --- | --- |
| `title` | `trim`, 1–255 caracteres; incluir somente se mudou. |
| `content` | `trim`, não vazio; incluir somente se mudou. Alterá-lo recria chunks/embeddings no servidor. |
| `category_ids`, `tag_ids`, `project_ids` | IDs únicos positivos; incluir somente quando a seleção mudou. Array vazio remove todas as associações do grupo. |

Sucesso retorna `200` e um `KnowledgeSourceDetail` completo, que substitui o estado local.

## Exclusão

`DELETE /sources/{source_id}?confirm=true` é enviado somente pelo evento de confirmação do diálogo. Sucesso é `204 No Content`; não há corpo para interpretar. Cancelar, fechar ou pressionar Escape não chama o endpoint.

## Erros visíveis

| Status | Mensagem/ação esperada |
| --- | --- |
| `400`, `422` | Informar para revisar título, conteúdo ou metadados; preservar rascunho. |
| `404` | Informar que a fonte/metadado não existe mais e oferecer retorno/recarregamento. |
| `409` | Informar conteúdo duplicado; se `detail.existing_source_id` for UUID válido, oferecer abrir a fonte existente. |
| `502`, `503` | Informar indisponibilidade temporária durante reprocessamento e permitir tentar novamente. |
| `401` | Deixar o interceptor encerrar a sessão/redirecionar; não duplicar essa regra na feature. |

Corpos de erro são tratados como dados estruturados e nunca como HTML.
