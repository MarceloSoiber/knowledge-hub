# Contract: Dashboard no frontend

Todos os caminhos são relativos a `/api/v1/knowledge`, autenticados pelos interceptores existentes e acessados exclusivamente por `KnowledgeApiService`.

| Necessidade | Método e caminho | Uso no Dashboard |
| --- | --- | --- |
| Fontes | `GET /sources` | Contagem e lista local de recentes. |
| Categorias | `GET /categories` | Contagem. |
| Tags | `GET /tags` | Contagem. |
| Projetos | `GET /projects` | Contagens derivadas de ativos e arquivados. |

Não são adicionados parâmetros, payloads, endpoints ou schemas. As requisições são independentes: uma falha em qualquer uma delas apresenta erro recuperável apenas no cartão ou seção correspondente.

## Regras de apresentação

- A lista de recentes é derivada no cliente por `created_at` decrescente; `updated_at` é fallback; itens sem data válida vêm ao fim.
- A lista mostra no máximo cinco fontes e cada item usa `/sources/{source_id}` para abrir o detalhe já canônico.
- Os atalhos usam as rotas privadas existentes: `/busca`, `/perguntar` e `/ingestao`.
- A resposta de erro é tratada como estado seguro da UI, nunca renderizada como HTML.

## Erros visíveis

| Situação | Comportamento |
| --- | --- |
| Falha de fontes | Não mostrar contagem inventada nem recentes; exibir retry da seção. |
| Falha de metadados | Mostrar erro/retry somente no cartão afetado; dados restantes e atalhos continuam disponíveis. |
| Listas vazias | Mostrar `0`; para fontes, orientar a primeira ingestão. |
| `401` | Permitir que o interceptor existente trate a sessão. |
