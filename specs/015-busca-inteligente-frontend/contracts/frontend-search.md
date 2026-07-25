# Contract: Frontend Search Integration

## API base

Todos os caminhos abaixo são relativos a `/api/v1/knowledge` e passam pelo interceptor de autenticação da fundação.

## Metadados para filtros

| Necessidade | Método e caminho | Uso na interface |
| --- | --- | --- |
| Categorias | `GET /categories` | Carregamento inicial do seletor. |
| Projetos | `GET /projects` | Carregamento inicial do seletor; exibir status retornado. |
| Tags selecionáveis | `GET /tags` | Carregamento inicial quando necessário para filtros já conhecidos. |
| Sugestões de tag | `GET /tags/autocomplete?q={texto}&limit=10` | Busca incremental após debounce; somente itens devolvidos podem ser selecionados. |

## Busca

`POST /search`

### Request

```json
{
  "query": "como configurar o mcp",
  "limit": 10,
  "category_ids": [2],
  "tag_ids": [5],
  "project_ids": [3],
  "min_score": 0.35,
  "include_match_reasons": true
}
```

Campos sem valor não devem ser enviados. `query` é obrigatório; `limit` deve estar entre 1 e 50; `min_score`, quando enviado, deve estar entre 0 e 1.

### Response consumed

```json
{
  "query": "como configurar o mcp",
  "limit": 10,
  "results": [
    {
      "id": 30,
      "source_id": "33333333-3333-4333-8333-333333333333",
      "source_title": "guia-mcp.md",
      "content": "Trecho encontrado...",
      "score": 0.87,
      "location": {"chunk_index": 2, "page": 5, "section": "Instalação"},
      "categories": [{"id": 2, "name": "docs"}],
      "tags": [{"id": 5, "name": "mcp"}],
      "projects": [{"id": 3, "name": "knowledge hub", "status": "active"}],
      "match_reasons": ["vector", "text"]
    }
  ]
}
```

`score` pode ser `null`. `match_reasons` é opcional e nunca é presumido pelo cliente.

## Navegação para fonte

O link de cada resultado usa somente `source_id` como parâmetro de rota. Não usar o `id` interno do chunk, URI ou título como identificador de navegação.

## Erros tratados pela UI

| Status | Tratamento esperado |
| --- | --- |
| `401` | A fundação encerra a sessão e redireciona para login. |
| `404` | Informar que um filtro ou recurso não existe mais e oferecer recarregar metadados. |
| `422` | Informar que consulta ou filtros precisam ser revisados; manter o formulário. |
| `502`, `503` | Indicar indisponibilidade temporária de busca/embeddings e oferecer tentar novamente, sem detalhes internos. |
