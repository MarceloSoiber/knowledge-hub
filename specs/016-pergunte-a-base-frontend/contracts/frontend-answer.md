# Contract: Frontend Answer Integration

## API base

Todos os caminhos são relativos a `/api/v1/knowledge` e passam pelo interceptor de autenticação da fundação.

## Metadados para filtros

| Necessidade | Método e caminho | Uso na interface |
| --- | --- | --- |
| Categorias | `GET /categories` | Carregamento inicial do seletor. |
| Projetos | `GET /projects` | Carregamento inicial do seletor; exibir status retornado. |
| Sugestões de tags | `GET /tags/autocomplete?q={texto}&limit=10` | Autocomplete após debounce; somente itens retornados podem ser selecionados. |

## Pergunta RAG

`POST /answer`

### Request

```json
{
  "query": "Quais decisões foram tomadas para os contratos?",
  "limit": 5,
  "category_ids": [2],
  "tag_ids": [5],
  "project_ids": [3],
  "min_score": 0.35,
  "include_match_reasons": true
}
```

`query` é obrigatório. Campos sem valor não devem ser enviados. `limit` deve ser inteiro entre 1 e 20; `min_score`, quando enviado, deve estar entre 0 e 1. IDs são listas não vazias, únicas e positivas. Dentro de cada dimensão a semântica é ANY; entre dimensões, AND.

### Response consumed

```json
{
  "query": "Quais decisões foram tomadas para os contratos?",
  "answer": "Resumo produzido pelo modelo de linguagem.",
  "sources": [
    {
      "id": 30,
      "source_id": "33333333-3333-4333-8333-333333333333",
      "source_title": "contratos.md",
      "content": "Trecho utilizado para produzir a resposta...",
      "score": 0.87,
      "location": {"chunk_index": 2, "page": null, "section": "Prazos", "start_char": 1200, "end_char": 1840},
      "categories": [{"id": 2, "name": "juridico"}],
      "tags": [{"id": 5, "name": "contratos"}],
      "projects": [{"id": 3, "name": "knowledge hub", "status": "active"}]
    }
  ]
}
```

`sources` pode ser vazio. `score` pode ser `null`; `match_reasons` é opcional e não deve ser presumido.

## Navegação e cópia

- Cada cartão de fonte navega a `/sources/:sourceId` usando somente o UUID público `source_id`.
- **Copiar resposta** escreve apenas o valor de `answer` atualmente exibido.
- **Copiar referências** escreve uma representação textual das fontes apresentadas, uma por bloco: título, localização disponível e trecho; não inclui token, URI local, ID interno ou metadados não expostos.
- Ambas as ações devem anunciar êxito ou indisponibilidade da cópia sem registrar o conteúdo.

## Erros tratados pela UI

| Status | Tratamento esperado |
| --- | --- |
| `401` | A fundação encerra a sessão e redireciona para login. |
| `403` | Informar que a resposta foi bloqueada por conteúdo sensível e sugerir reformular/consultar a política, sem detalhe do backend. |
| `422` | Informar que pergunta ou filtros precisam ser revisados e manter formulário. |
| `502`, `503` | Indicar indisponibilidade temporária de embeddings/LLM/API e oferecer nova tentativa, sem detalhes internos. |
