# API do Knowledge Hub

Documentação da API HTTP usada para cadastrar documentos, consultar categorias,
realizar buscas semânticas e gerar respostas com apoio de um LLM.

## Endereços

Por padrão, a API fica disponível em:

```text
http://localhost:8000
```

Documentação interativa gerada pelo FastAPI:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Todos os endpoints de conhecimento usam o prefixo:

```text
/api/v1/knowledge
```

## Autenticação

Quando um token estiver configurado no banco, os endpoints de conhecimento exigem um
token Bearer:

```http
Authorization: Bearer <token>
```

Exemplo para armazenar o token na sessão atual do terminal:

```bash
export KNOWLEDGE_HUB_TOKEN="seu-token"
```

Quando nenhum token estiver configurado, a autenticação fica desabilitada. Os endpoints
`GET /` e `GET /health` são públicos em ambos os casos.

## MCP

O servidor MCP usa o mesmo token Bearer salvo em `app_config.auth_token`.
Por padrão, ele emite apenas o escopo `knowledge:read` para ferramentas de
consulta. Para permitir escrita via MCP, configure:

```env
MCP_WRITE_ENABLED="true"
```

Com escrita ativa, a tool `ingest_text` exige `knowledge:write` e aceita:

```json
{
  "title": "Decisão de arquitetura",
  "content": "Texto confirmado pelo usuário para persistência.",
  "category_ids": [1, 2],
  "tag_ids": [3],
  "project_ids": [4],
  "metadata": {
    "note_type": "decision"
  }
}
```

Resposta:

```json
{
  "source_id": "11111111-1111-4111-8111-111111111111",
  "title": "Decisão de arquitetura",
  "categories": [
    {
      "id": 1,
      "name": "docs"
    }
  ],
  "tags": [
    {
      "id": 3,
      "name": "rag"
    }
  ],
  "projects": [
    {
      "id": 4,
      "name": "mcp knowledge hub",
      "status": "active"
    }
  ],
  "chunks_created": 2
}
```

A tool grava conhecimento persistente. Clientes/agentes devem pedir confirmação
explícita ao usuário antes de chamá-la e não devem usá-la para arquivar conversas
automaticamente. `metadata` aceita apenas `client_id` e `note_type`.

A tool `source(source_id)` consulta uma fonte detalhada por UUID público. O MCP
não expõe ferramentas de atualização ou exclusão de fontes nesta versão.

A tool `search` aceita `query`, `limit`, `category_ids`, `tag_ids`,
`project_ids`, `min_score` e
`include_match_reasons`, retornando o mesmo contrato citável de
`/api/v1/knowledge/search`: UUID público da fonte, título, URI sanitizada,
categorias, tags, projetos, localização do chunk, conteúdo, score e metadados públicos
permitidos. Quando `include_match_reasons=true`, cada resultado pode indicar se
veio de match `vector`, `text` ou ambos.

A busca vetorial usa somente chunks com embeddings gerados pela configuração
ativa (`LLM_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_VERSION` e `VECTOR_DIM`).
Chunks legados sem metadados de embedding ou gerados por outra configuração não
entram nos candidatos vetoriais; eles ainda podem aparecer por busca textual
quando o fluxo híbrido encontrar correspondência, sem `vector` em
`match_reasons`.

Operacoes administrativas de reindexacao, backup e indice HNSW sao expostas por CLI/runbook,
nao por endpoint HTTP nesta versao. Consulte `doc/OPERATIONS.md` para
`reindex-embeddings`, `knowledge-backup`, `knowledge-hnsw`, backup com `pg_dump`, restauracao e
gate de agendamento apos teste real de restore.

As tools `tags()` e `tag_autocomplete(query, limit)` listam tags existentes para
que clientes MCP escolham `tag_ids` validos antes de ingerir ou buscar.
As tools `projects(status)` e `project_sources(project_id)` listam projetos e
fontes associadas para que agentes restrinjam consultas ao contexto atual.

## Resumo dos endpoints

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/` | Identifica a API. |
| `GET` | `/health` | Verifica a saúde da aplicação. |
| `GET` | `/api/v1/knowledge/categories` | Lista as categorias disponíveis. |
| `POST` | `/api/v1/knowledge/categories` | Cria uma categoria. |
| `PATCH` | `/api/v1/knowledge/categories/{id}` | Renomeia uma categoria. |
| `DELETE` | `/api/v1/knowledge/categories/{id}` | Remove uma categoria sem documentos associados. |
| `GET` | `/api/v1/knowledge/projects` | Lista projetos. |
| `POST` | `/api/v1/knowledge/projects` | Cria um projeto. |
| `PATCH` | `/api/v1/knowledge/projects/{id}` | Atualiza nome ou descrição de um projeto. |
| `POST` | `/api/v1/knowledge/projects/{id}/archive` | Arquiva um projeto sem excluir conhecimento. |
| `POST` | `/api/v1/knowledge/projects/{id}/reactivate` | Reativa um projeto arquivado. |
| `GET` | `/api/v1/knowledge/projects/{id}/sources` | Lista fontes associadas a um projeto. |
| `GET` | `/api/v1/knowledge/tags` | Lista as tags disponíveis. |
| `GET` | `/api/v1/knowledge/tags/autocomplete` | Sugere tags por prefixo. |
| `POST` | `/api/v1/knowledge/tags` | Cria uma tag. |
| `PATCH` | `/api/v1/knowledge/tags/{id}` | Renomeia uma tag. |
| `DELETE` | `/api/v1/knowledge/tags/{id}` | Remove uma tag sem documentos associados. |
| `GET` | `/api/v1/knowledge/sources` | Lista os documentos cadastrados. |
| `GET` | `/api/v1/knowledge/sources/{source_id}` | Consulta um documento por UUID público. |
| `PATCH` | `/api/v1/knowledge/sources/{source_id}` | Atualiza título, categorias e/ou conteúdo. |
| `DELETE` | `/api/v1/knowledge/sources/{source_id}?confirm=true` | Exclui definitivamente um documento. |
| `POST` | `/api/v1/knowledge/uploads` | Cadastra um arquivo. |
| `POST` | `/api/v1/knowledge/texts` | Cadastra conteúdo textual. |
| `POST` | `/api/v1/knowledge/search` | Realiza uma busca semântica. |
| `POST` | `/api/v1/knowledge/answer` | Gera uma resposta usando os documentos encontrados. |

## Categorias

Os documentos são associados a uma ou mais categorias por meio de `category_ids`.
Consulte a listagem antes de cadastrar um documento ou aplicar um filtro.

### Listar categorias

```http
GET /api/v1/knowledge/categories
```

Exemplo:

```bash
curl -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  http://localhost:8000/api/v1/knowledge/categories
```

Resposta `200 OK`:

```json
[
  {
    "id": 1,
    "name": "uncategorized"
  },
  {
    "id": 2,
    "name": "financeiro"
  }
]
```

### Criar categoria

```http
POST /api/v1/knowledge/categories
Content-Type: application/json
```

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/categories \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Financeiro"}'
```

Resposta `201 Created`:

```json
{
  "id": 2,
  "name": "financeiro"
}
```

### Renomear categoria

```http
PATCH /api/v1/knowledge/categories/{id}
Content-Type: application/json
```

O nome é normalizado com remoção de espaços externos e letras minúsculas.

### Excluir categoria

```http
DELETE /api/v1/knowledge/categories/{id}
```

Categorias associadas a documentos não podem ser excluídas e retornam `409 Conflict`.

## Tags

Tags são marcadores livres e granulares, como `python`, `postgres`, `imposto` ou
`rag`. Elas complementam categorias, mas não substituem a taxonomia controlada:
categorias seguem sendo obrigatórias no cadastro, enquanto tags são opcionais.

Nomes de tags são normalizados com remoção de espaços externos, letras minúsculas,
colapso de espaços internos e comparação sem acentos. Assim, `PósTgres` e
`postgres` representam a mesma tag.

### Listar tags

```http
GET /api/v1/knowledge/tags
```

Resposta `200 OK`:

```json
[
  {
    "id": 1,
    "name": "postgres"
  }
]
```

### Autocomplete de tags

```http
GET /api/v1/knowledge/tags/autocomplete?q=po&limit=10
```

`limit` deve ficar entre `1` e `50`.

### Criar tag

```http
POST /api/v1/knowledge/tags
Content-Type: application/json
```

```json
{
  "name": "Postgres"
}
```

Resposta `201 Created`:

```json
{
  "id": 1,
  "name": "postgres"
}
```

Nomes equivalentes pela normalização retornam `409 Conflict`.

### Renomear ou excluir tag

```http
PATCH /api/v1/knowledge/tags/{id}
DELETE /api/v1/knowledge/tags/{id}
```

Tags associadas a documentos não podem ser excluídas e retornam `409 Conflict`.

## Projetos

Projetos representam contexto de trabalho. Categorias continuam descrevendo
assunto amplo e tags continuam descrevendo marcadores granulares; projetos
servem para restringir conhecimento ao contexto atual sem duplicar fontes.

Projetos têm status `active` ou `archived`. Arquivar um projeto não remove
fontes, chunks nem associações; apenas marca o contexto como arquivado.

### Listar projetos

```http
GET /api/v1/knowledge/projects?status=active
```

O filtro `status` é opcional. Sem filtro, a API retorna todos os projetos.

### Criar projeto

```http
POST /api/v1/knowledge/projects
Content-Type: application/json
```

```json
{
  "name": "MCP Knowledge Hub",
  "description": "Contexto de desenvolvimento do hub"
}
```

Resposta `201 Created`:

```json
{
  "id": 4,
  "name": "mcp knowledge hub",
  "description": "Contexto de desenvolvimento do hub",
  "status": "active",
  "created_at": "2026-07-20T12:00:00Z",
  "updated_at": "2026-07-20T12:00:00Z"
}
```

### Atualizar, arquivar e reativar projeto

```http
PATCH /api/v1/knowledge/projects/{id}
POST /api/v1/knowledge/projects/{id}/archive
POST /api/v1/knowledge/projects/{id}/reactivate
```

Nomes duplicados retornam `409 Conflict`. Projeto inexistente retorna `404`.

### Listar fontes de um projeto

```http
GET /api/v1/knowledge/projects/{id}/sources
```

Retorna o mesmo contrato de `GET /knowledge/sources`, filtrado pelas fontes
associadas ao projeto.

## Cadastro de conhecimento

O cadastro pode ser feito por arquivo ou por texto. Nos dois casos, o conteúdo é
normalizado, dividido em chunks, convertido em embeddings e armazenado no banco.

### Cadastrar arquivo

```http
POST /api/v1/knowledge/uploads
Content-Type: multipart/form-data
```

Campos:

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `file` | arquivo | sim | Formatos `.txt`, `.md` ou `.pdf`; máximo de 10 MB. |
| `category_ids` | inteiros repetidos | sim | Cada valor deve ser maior que zero, sem duplicatas, e apontar para uma categoria existente. |
| `tag_ids` | inteiros repetidos | não | Cada valor deve ser maior que zero, sem duplicatas, e apontar para uma tag existente. |
| `project_ids` | inteiros repetidos | não | Cada valor deve ser maior que zero, sem duplicatas, e apontar para um projeto existente. |

Exemplo:

```bash
curl -X POST \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -F "file=@./documento.pdf" \
  -F "category_ids=2" \
  -F "category_ids=3" \
  -F "tag_ids=1" \
  -F "project_ids=4" \
  http://localhost:8000/api/v1/knowledge/uploads
```

Resposta `201 Created`:

```json
{
  "source_id": "22222222-2222-4222-8222-222222222222",
  "title": "documento.pdf",
  "categories": [
    {
      "id": 2,
      "name": "financeiro"
    },
    {
      "id": 3,
      "name": "contratos"
    }
  ],
  "tags": [
    {
      "id": 1,
      "name": "postgres"
    }
  ],
  "projects": [
    {
      "id": 4,
      "name": "mcp knowledge hub",
      "status": "active"
    }
  ],
  "chunks_created": 8
}
```

### Cadastrar texto

```http
POST /api/v1/knowledge/texts
Content-Type: application/json
```

Tambem aceita `multipart/form-data` ou `application/x-www-form-urlencoded` com os
mesmos campos. Em formulario, envie `category_ids`, `tag_ids` e `project_ids` como campos
repetidos quando houver mais de um valor.

Corpo da requisição:

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `title` | string | sim | Entre 1 e 255 caracteres após remover espaços externos. |
| `category_ids` | lista de inteiros | sim | Deve conter pelo menos um ID maior que zero, sem duplicatas, e apontar para categorias existentes. |
| `tag_ids` | lista de inteiros | não | Quando informada, deve conter IDs maiores que zero, sem duplicatas, e apontar para tags existentes. |
| `project_ids` | lista de inteiros | não | Quando informada, deve conter IDs maiores que zero, sem duplicatas, e apontar para projetos existentes. |
| `content` | string | sim | Não pode ficar vazio após a normalização. |

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/texts \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ata da reunião",
    "category_ids": [2, 3],
    "tag_ids": [1],
    "project_ids": [4],
    "content": "Este é o conteúdo que será armazenado na base de conhecimento."
  }'
```

Resposta `201 Created`:

```json
{
  "source_id": "33333333-3333-4333-8333-333333333333",
  "title": "Ata da reunião",
  "categories": [
    {
      "id": 2,
      "name": "financeiro"
    },
    {
      "id": 3,
      "name": "contratos"
    }
  ],
  "tags": [
    {
      "id": 1,
      "name": "postgres"
    }
  ],
  "projects": [
    {
      "id": 4,
      "name": "mcp knowledge hub",
      "status": "active"
    }
  ],
  "chunks_created": 1
}
```

Novas ingestões criam novas fontes mesmo quando o título ou `uri` se repetem. Se
o conteúdo canônico normalizado já existir em outra fonte, a API retorna
`409 Conflict` com o UUID público da fonte existente.

## Consulta de conhecimento

### Busca híbrida

```http
POST /api/v1/knowledge/search
Content-Type: application/json
```

Corpo da requisição:

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `query` | string | sim | Não pode ser vazia. |
| `limit` | inteiro | não | Padrão `5`; mínimo `1`; máximo `50`. |
| `category_ids` | lista de inteiros | não | Filtra documentos que pertençam a qualquer uma das categorias informadas. |
| `tag_ids` | lista de inteiros | não | Filtra documentos que tenham qualquer uma das tags informadas. Combina com categorias como outra dimensão obrigatória. |
| `project_ids` | lista de inteiros | não | Filtra documentos associados a qualquer um dos projetos informados. Quando presente, conhecimento geral sem projeto fica fora do resultado. |
| `min_score` | número | não | Override por requisição; mínimo `0.0`; máximo `1.0`. Quando omitido, usa `SEARCH_MIN_SCORE` (`0.35`). |
| `include_match_reasons` | booleano | não | Padrão `false`. Quando `true`, inclui motivos diagnósticos do match por resultado. |

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quais documentos mencionam contratos?",
    "limit": 5,
    "category_ids": [2, 3],
    "tag_ids": [1],
    "project_ids": [4],
    "min_score": 0.35,
    "include_match_reasons": true
  }'
```

Resposta `200 OK`:

```json
{
  "query": "Quais documentos mencionam contratos?",
  "limit": 5,
  "results": [
    {
      "id": 30,
      "source_id": "33333333-3333-4333-8333-333333333333",
      "source_title": "contratos.md",
      "source_type": "upload",
      "uri": "upload:contratos.md",
      "categories": [
        {
          "id": 2,
          "name": "juridico"
        },
        {
          "id": 3,
          "name": "financeiro"
        }
      ],
      "tags": [
        {
          "id": 1,
          "name": "postgres"
        }
      ],
      "projects": [
        {
          "id": 4,
          "name": "mcp knowledge hub",
          "status": "active"
        }
      ],
      "location": {
        "chunk_index": 2,
        "page": null,
        "section": "Prazos",
        "start_char": 1200,
        "end_char": 1840
      },
      "content": "Trecho do documento encontrado...",
      "score": 0.87,
      "metadata": {},
      "match_reasons": ["vector", "text"]
    }
  ]
}
```

Cada resultado usa o UUID publico da fonte em `source_id` e inclui metadados
suficientes para citacao. URIs baseadas em caminhos locais sao sanitizadas antes
de sair da API. A busca combina candidatos por similaridade vetorial e busca
textual PostgreSQL, usando fusao por ranking. Resultados com score vetorial menor
que o limiar efetivo sao removidos; resultados encontrados apenas por texto podem
ter `score: null` e ainda aparecer quando forem relevantes pelo match textual.
Quando nenhum chunk passa, `results` e retornado como lista vazia. O score e um
sinal de similaridade vetorial para ordenacao e calibracao, nao uma probabilidade
nem o score hibrido interno. O valor padrao `SEARCH_MIN_SCORE=0.35` e conservador
e deve ser recalibrado ao trocar o modelo de embeddings ou o dominio do
conhecimento. O campo `match_reasons` so aparece quando solicitado.
Filtros de categorias, tags e projetos são aplicados antes dos limites de candidatos.
Dentro de cada dimensão, a semântica é ANY; entre dimensões, a combinação é AND.
Na etapa vetorial, apenas chunks com `embedding_status=embedded` e lote de
embedding compatível com a configuração ativa participam da similaridade.
Ao trocar `EMBEDDING_MODEL`, `EMBEDDING_VERSION`, `VECTOR_DIM` ou provider,
reindexe os documentos para recuperar cobertura vetorial completa.

### Gerar resposta com LLM

```http
POST /api/v1/knowledge/answer
Content-Type: application/json
```

Corpo da requisição:

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `query` | string | sim | Não pode ser vazia. |
| `limit` | inteiro | não | Padrão `5`; mínimo `1`; máximo `20`. |
| `category_ids` | lista de inteiros | não | Filtra documentos usados na resposta por semântica qualquer categoria. |
| `tag_ids` | lista de inteiros | não | Filtra documentos usados na resposta por semântica qualquer tag. |
| `project_ids` | lista de inteiros | não | Filtra documentos usados na resposta por semântica qualquer projeto. |
| `min_score` | número | não | Override por requisição; mínimo `0.0`; máximo `1.0`. Quando omitido, usa `SEARCH_MIN_SCORE` (`0.35`). |
| `include_match_reasons` | booleano | não | Padrão `false`. Quando `true`, inclui motivos diagnósticos nas fontes recuperadas. |

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/answer \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Resuma os pontos principais dos contratos.",
    "limit": 5,
    "category_ids": [2, 3],
    "tag_ids": [1],
    "project_ids": [4],
    "min_score": 0.35
  }'
```

Resposta `200 OK`:

```json
{
  "query": "Resuma os pontos principais dos contratos.",
  "answer": "Resumo produzido pelo modelo de linguagem...",
  "sources": [
    {
      "id": 30,
      "source_id": "33333333-3333-4333-8333-333333333333",
      "source_title": "contratos.md",
      "source_type": "upload",
      "uri": "upload:contratos.md",
      "categories": [
        {
          "id": 2,
          "name": "juridico"
        }
      ],
      "tags": [
        {
          "id": 1,
          "name": "postgres"
        }
      ],
      "projects": [
        {
          "id": 4,
          "name": "mcp knowledge hub",
          "status": "active"
        }
      ],
      "location": {
        "chunk_index": 2,
        "page": null,
        "section": "Prazos",
        "start_char": 1200,
        "end_char": 1840
      },
      "content": "Trecho utilizado para produzir a resposta...",
      "score": 0.87,
      "metadata": {}
    }
  ]
}
```

O prompt de resposta recebe titulo e localizacao de cada fonte recuperada, e a
lista `sources` contem somente os chunks usados como contexto para o LLM. Quando
nenhuma fonte passa pelo limiar de relevancia, `sources` fica vazia e o modelo
deve declarar que nao encontrou a informacao no contexto fornecido.

### Listar documentos

```http
GET /api/v1/knowledge/sources
```

Exemplo:

```bash
curl -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  http://localhost:8000/api/v1/knowledge/sources
```

Resposta `200 OK`:

```json
[
  {
    "source_id": "22222222-2222-4222-8222-222222222222",
    "title": "documento.pdf",
    "categories": [
      {
        "id": 2,
        "name": "financeiro"
      }
    ],
    "tags": [
      {
        "id": 1,
        "name": "postgres"
      }
    ],
    "projects": [
      {
        "id": 4,
        "name": "mcp knowledge hub",
        "status": "active"
      }
    ],
    "source_type": "upload",
    "uri": "upload:documento.pdf",
    "content_hash": "d2d2d2...",
    "created_at": "2026-07-16T12:00:00Z",
    "updated_at": "2026-07-16T12:00:00Z"
  },
  {
    "source_id": "33333333-3333-4333-8333-333333333333",
    "title": "Ata da reunião",
    "categories": [
      {
        "id": 2,
        "name": "financeiro"
      },
      {
        "id": 3,
        "name": "contratos"
      }
    ],
    "tags": [],
    "projects": [],
    "source_type": "text",
    "uri": "text:Ata da reunião",
    "content_hash": "a1a1a1...",
    "created_at": "2026-07-16T12:05:00Z",
    "updated_at": "2026-07-16T12:05:00Z"
  }
]
```

### Consultar documento

```http
GET /api/v1/knowledge/sources/{source_id}
```

`source_id` é o UUID público retornado na ingestão ou listagem.

Resposta `200 OK`:

```json
{
  "source_id": "33333333-3333-4333-8333-333333333333",
  "title": "Ata da reunião",
  "categories": [
    {
      "id": 2,
      "name": "financeiro"
    }
  ],
  "tags": [
    {
      "id": 1,
      "name": "postgres"
    }
  ],
  "projects": [
    {
      "id": 4,
      "name": "mcp knowledge hub",
      "status": "active"
    }
  ],
  "source_type": "text",
  "uri": "text:Ata da reunião",
  "content_hash": "a1a1a1...",
  "created_at": "2026-07-16T12:05:00Z",
  "updated_at": "2026-07-16T12:05:00Z",
  "content": "Conteúdo canônico normalizado usado para chunking."
}
```

### Atualizar documento

```http
PATCH /api/v1/knowledge/sources/{source_id}
Content-Type: application/json
```

Corpo da requisição:

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `title` | string | não | Entre 1 e 255 caracteres após remover espaços externos. |
| `category_ids` | lista de inteiros | não | Não pode ser vazia quando informada; IDs devem existir. |
| `tag_ids` | lista de inteiros | não | IDs devem existir e não podem repetir. Lista vazia remove todas as tags da fonte. |
| `project_ids` | lista de inteiros | não | IDs devem existir e não podem repetir. Lista vazia remove todos os projetos da fonte. |
| `content` | string | não | Quando informado, não pode ficar vazio após normalização. |

Ao alterar apenas `title`, `category_ids`, `tag_ids` ou `project_ids`, a API não recria
embeddings. Ao alterar `content`, a API recalcula o hash e substitui chunks e
embeddings em uma transação.

### Excluir documento

```http
DELETE /api/v1/knowledge/sources/{source_id}?confirm=true
```

A exclusão é definitiva e remove chunks e associações de categoria, tags e projetos. Sem
`confirm=true`, a API retorna `400 Bad Request`. Faça backup externo antes de
usar esta operação em dados importantes.

## Endpoints públicos

### Identificação da API

```http
GET /
```

Resposta `200 OK`:

```json
{
  "message": "MCP Knowledge Hub API"
}
```

### Health check

```http
GET /health
```

Resposta `200 OK`:

```json
{
  "status": "ok",
  "app_name": "MCP Knowledge Hub",
  "environment": "development"
}
```

## Erros

Os erros seguem o formato padrão do FastAPI:

```json
{
  "detail": "Descrição do erro."
}
```

Principais códigos:

| Código | Situação |
| --- | --- |
| `400 Bad Request` | Arquivo inválido, conteúdo vazio ou falha de ingestão. |
| `401 Unauthorized` | Token Bearer ausente ou inválido quando a autenticação está ativa. |
| `404 Not Found` | A categoria, tag, projeto ou fonte informada não existe. |
| `409 Conflict` | Nome de categoria/tag/projeto duplicado, categoria/tag em uso ou conteúdo duplicado. |
| `413 Content Too Large` | O arquivo enviado ultrapassa 10 MB. |
| `422 Unprocessable Entity` | O corpo ou os parâmetros não atendem ao schema. |
| `502 Bad Gateway` | Falha ao consultar o serviço de embeddings ou o LLM. |
| `503 Service Unavailable` | Embeddings ou LLM não estão configurados corretamente. |

Exemplo de categoria inexistente:

```json
{
  "detail": "Category 999 does not exist."
}
```
