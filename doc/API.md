# API do MCP Knowledge Hub

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

## Resumo dos endpoints

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/` | Identifica a API. |
| `GET` | `/health` | Verifica a saúde da aplicação. |
| `GET` | `/api/v1/knowledge/categories` | Lista as categorias disponíveis. |
| `GET` | `/api/v1/knowledge/sources` | Lista os documentos cadastrados. |
| `POST` | `/api/v1/knowledge/uploads` | Cadastra um arquivo. |
| `POST` | `/api/v1/knowledge/texts` | Cadastra conteúdo textual. |
| `POST` | `/api/v1/knowledge/search` | Realiza uma busca semântica. |
| `POST` | `/api/v1/knowledge/answer` | Gera uma resposta usando os documentos encontrados. |

## Categorias

Os documentos são associados a uma categoria por meio de `category_id`. Consulte a
listagem antes de cadastrar um documento ou aplicar um filtro.

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
| `category_id` | inteiro | sim | Deve ser maior que zero e apontar para uma categoria existente. |

Exemplo:

```bash
curl -X POST \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -F "file=@./documento.pdf" \
  -F "category_id=2" \
  http://localhost:8000/api/v1/knowledge/uploads
```

Resposta `201 Created`:

```json
{
  "source_id": 10,
  "title": "documento.pdf",
  "category_id": 2,
  "chunks_created": 8
}
```

### Cadastrar texto

```http
POST /api/v1/knowledge/texts
Content-Type: application/json
```

Corpo da requisição:

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `title` | string | sim | Entre 1 e 255 caracteres após remover espaços externos. |
| `category_id` | inteiro | sim | Deve ser maior que zero e apontar para uma categoria existente. |
| `content` | string | sim | Não pode ficar vazio após a normalização. |

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/texts \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ata da reunião",
    "category_id": 2,
    "content": "Este é o conteúdo que será armazenado na base de conhecimento."
  }'
```

Resposta `201 Created`:

```json
{
  "source_id": 11,
  "title": "Ata da reunião",
  "category_id": 2,
  "chunks_created": 1
}
```

Se uma origem com a mesma identificação já existir, seus chunks anteriores serão
substituídos pelo conteúdo novo.

## Consulta de conhecimento

### Busca semântica

```http
POST /api/v1/knowledge/search
Content-Type: application/json
```

Corpo da requisição:

| Campo | Tipo | Obrigatório | Regras |
| --- | --- | --- | --- |
| `query` | string | sim | Não pode ser vazia. |
| `limit` | inteiro | não | Padrão `5`; mínimo `1`; máximo `50`. |
| `category_id` | inteiro | não | Filtra os documentos por categoria. |

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quais documentos mencionam contratos?",
    "limit": 5,
    "category_id": 2
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
      "source_id": 10,
      "content": "Trecho do documento encontrado...",
      "score": 0.87
    }
  ]
}
```

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
| `category_id` | inteiro | não | Filtra os documentos usados na resposta. |

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/answer \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Resuma os pontos principais dos contratos.",
    "limit": 5,
    "category_id": 2
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
      "source_id": 10,
      "content": "Trecho utilizado para produzir a resposta...",
      "score": 0.87
    }
  ]
}
```

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
    "id": 10,
    "title": "documento.pdf",
    "category_id": 2,
    "source_type": "upload",
    "uri": "upload:financeiro:documento.pdf"
  },
  {
    "id": 11,
    "title": "Ata da reunião",
    "category_id": 2,
    "source_type": "text",
    "uri": "text:financeiro:Ata da reunião"
  }
]
```

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
| `404 Not Found` | O `category_id` informado no cadastro não existe. |
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
