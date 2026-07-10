# MCP Knowledge Hub

Hub de conhecimento com API FastAPI, PostgreSQL + `pgvector`, embeddings, RAG e um servidor MCP remoto para que agentes consultem os documentos ingeridos.

## O Que Tem Aqui

- `backend/`: API FastAPI, rotas de conhecimento e serviços de ingestão, busca semântica e resposta com LLM.
- `mcp_server/`: servidor MCP via Streamable HTTP.
- `frontend/`: interface React + Vite.
- `docker-compose.yml`: serviços de PostgreSQL, backend e MCP.
- `app_config.auth_token`: token Bearer salvo no PostgreSQL para proteger a API de conhecimento e o MCP.

## Requisitos

- Docker e `docker-compose`
- Node.js, para os scripts `npm`
- Python 3.11+
- `uv`, para rodar o backend localmente
- Um servidor OpenAI-compatible para chat e embeddings, como LM Studio, ou uma API externa configurada por `API_KEY`

## Configuração

Crie o `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Principais variáveis:

```env
FRONTEND_ORIGIN="http://localhost:5173"

POSTGRES_DSN="postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_hub"

LLM_PROVIDER="local"
LOCAL_LLM_BASE_URL="http://127.0.0.1:1234"
DOCKER_LOCAL_LLM_BASE_URL="http://host.docker.internal:1234"
LOCAL_LLM_MODEL="gemma-4-12b-it"

API_LLM_BASE_URL="https://api.openai.com/v1"
API_LLM_MODEL="gpt-4.1-mini"
API_KEY=""

EMBEDDING_MODEL="text-embedding-nomic-embed-text-v1.5"
VECTOR_DIM="768"

MCP_HOST="0.0.0.0"
MCP_PORT="8001"
MCP_PUBLIC_URL="http://192.0.2.10:8001"
MCP_PATH="/mcp"
```

### Configurar Token De Acesso

O token de acesso fica salvo no banco, na tabela `app_config`, com a chave `auth_token`. Ele não deve ficar no `.env` nem em arquivos versionados.

Com o ambiente local:

```bash
uv run set-auth-token
```

Para gerar e salvar automaticamente um token forte:

```bash
uv run set-auth-token --generate
```

Com Docker:

```bash
docker-compose run --rm backend set-auth-token
```

Ou gerando o token automaticamente:

```bash
docker-compose run --rm backend set-auth-token --generate
```

Se o servidor tiver Docker, mas não tiver `docker-compose`, execute o comando dentro do container do backend já iniciado:

```bash
docker exec -it mcp-knowledge-hub-backend set-auth-token
```

Para evitar problemas de colagem no terminal, prefira gerar e salvar direto no container:

```bash
docker exec -it mcp-knowledge-hub-backend set-auth-token --generate
```

O comando pede o token de forma interativa:

```text
AUTH_TOKEN:
```

No modo interativo, o token precisa ter entre 32 e 256 caracteres e conter apenas letras, números, hífen e underscore. Isso evita salvar caracteres invisíveis de colagem no banco.

Depois de salvar, use esse valor apenas no cliente/API que vai acessar o sistema. O modo `--generate` imprime o token uma vez no terminal; guarde esse valor no cliente MCP.

Para conferir se o token foi salvo sem exibir o valor:

```bash
docker exec -it mcp-knowledge-hub-postgres psql -U postgres -d knowledge_hub \
  -c "select key, length(value) as token_length, updated_at from app_config;"
```

## Rodando Com Docker

Suba banco, backend e MCP:

```bash
npm run dev:up
```

Subir apenas o banco:

```bash
npm run db:up
```

Subir apenas o backend:

```bash
npm run backend:up
```

Subir apenas o MCP:

```bash
npm run mcp:up
```

URLs padrão:

- API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- MCP local: `http://localhost:8001/mcp`
- MCP na rede: `http://192.0.2.10:8001/mcp`
- PostgreSQL: `localhost:5432`

Se o LM Studio ou outro servidor local estiver rodando no host, o container deve usar `DOCKER_LOCAL_LLM_BASE_URL`. Em Linux moderno, o Compose já configura `host.docker.internal`.

## Rodando Localmente

Instale as dependências:

```bash
uv sync --extra dev
```

Suba o banco:

```bash
docker-compose up -d postgres
```

Rode a API:

```bash
uv run backend
```

Se a porta `8000` estiver ocupada:

```bash
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8002 --reload
```

Rode o MCP:

```bash
uv run mcp-server
```

Rode o frontend:

```bash
cd frontend
npm install
npm run dev
```

## API De Conhecimento

Quando `auth_token` estiver configurado no banco, inclua:

```text
Authorization: Bearer <seu-token>
```

Para testar com `curl`, você pode guardar o token só na sessão atual do terminal:

```bash
export KNOWLEDGE_HUB_TOKEN="cole-o-token-aqui"
```

Ingestão de arquivo:

```bash
curl -F "file=@./documento.pdf" \
  -F "category=financeiro" \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  http://localhost:8000/api/v1/knowledge/uploads
```

Ingestão de texto:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/texts \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "anotacoes-da-reuniao",
    "category": "financeiro",
    "content": "Cole aqui o texto que deve entrar na base de conhecimento."
  }'
```

Busca semântica:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"o que este documento diz?", "limit":5}'
```

Resposta com LLM usando os chunks encontrados:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/answer \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"resuma o documento", "limit":5}'
```

Listar fontes:

```bash
curl -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  http://localhost:8000/api/v1/knowledge/sources
```

## Acesso MCP

O MCP usa Streamable HTTP e fica em:

```text
http://192.0.2.10:8001/mcp
```

Com autenticação:

```text
Authorization: Bearer <seu-token>
```

### Tools MCP

| Tool | Uso | Parâmetros | Retorno |
| --- | --- | --- | --- |
| `health` | Verifica se o servidor MCP está respondendo. | Nenhum. | `{ "status": "ok", "service": "knowledge-hub-mcp" }` |
| `search` | Busca chunks por similaridade semântica nos documentos ingeridos. | `query` obrigatório, `limit` opcional, `category` opcional. | Lista de chunks com `id`, `source_id`, `content` e `score`. |
| `sources` | Lista documentos/fontes disponíveis no hub. | Nenhum. | Lista com `id`, `title`, `category`, `source_type` e `uri`. |

Exemplo de argumentos para `search`:

```json
{
  "query": "quais documentos falam sobre contratos?",
  "limit": 5,
  "category": "juridico"
}
```

O campo `category` pode ser omitido para buscar em todas as categorias:

```json
{
  "query": "resuma os pontos principais do material enviado",
  "limit": 5
}
```

### Resources MCP

| Resource | Uso | Retorno |
| --- | --- | --- |
| `config://workspace-overview` | Mostra um resumo rápido da stack do projeto. | Objeto com `frontend`, `backend`, `database`, `mcp` e `llm`. |

### Configuração Em Cliente MCP

Use a URL `http://192.0.2.10:8001/mcp` e o transporte `streamable-http`. Em clientes que aceitam configuração JSON, a forma costuma ser parecida com:

```json
{
  "mcpServers": {
    "knowledge-hub": {
      "type": "streamable-http",
      "url": "http://192.0.2.10:8001/mcp",
      "headers": {
        "Authorization": "Bearer cole-o-token-aqui"
      }
    }
  }
}
```

Se o cliente estiver em outra máquina da rede, troque o IP de exemplo pelo IP ou DNS da máquina que está rodando o MCP:

```text
http://192.0.2.10:8001/mcp
```

Nesse caso, ajuste também:

```env
MCP_PUBLIC_URL="http://192.0.2.10:8001"
```

### Rotacionar Token

Para trocar o token, rode novamente:

```bash
uv run set-auth-token
```

Ou gere um novo token automaticamente:

```bash
uv run set-auth-token --generate
```

ou, via Docker:

```bash
docker-compose run --rm backend set-auth-token
```

Sem `docker-compose` no servidor:

```bash
docker exec -it mcp-knowledge-hub-backend set-auth-token
docker restart mcp-knowledge-hub-mcp
```

Para gerar e salvar direto no container:

```bash
docker exec -it mcp-knowledge-hub-backend set-auth-token --generate
docker restart mcp-knowledge-hub-mcp
```

O backend e o MCP consultam o banco para validar o Bearer token, então o novo valor passa a valer sem precisar gravar segredo no repositório.

## Testes

```bash
uv run pytest -q
```

## Troubleshooting

Porta `8000` ocupada:

```bash
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8002 --reload
```

Ver containers ativos:

```bash
docker-compose ps
```

Parar backend Docker:

```bash
docker-compose stop backend
```

Validar se a API está viva:

```bash
curl http://localhost:8000/health
```

Validar se o MCP está publicado:

```bash
curl -i http://localhost:8001/mcp
```

Uma resposta `401 Unauthorized` no MCP é esperada quando o header Bearer não foi enviado ou quando o token não bate com `app_config.auth_token`.
