# Knowledge Hub

Knowledge Hub is a self-hosted knowledge base for Retrieval-Augmented Generation (RAG). It ingests documents, stores their embeddings in PostgreSQL with `pgvector`, and exposes semantic search and grounded answers through a FastAPI API, an Angular frontend, and a remote MCP server.

Its primary focus is **local LLM usage**. Run an OpenAI-compatible server such as LM Studio on your own infrastructure and Knowledge Hub will use it for chat and embeddings without sending your document content to a hosted model provider. External OpenAI-compatible APIs remain available as an optional fallback.

The project includes a GitLab CI/CD deployment pipeline. A push to the repository's default branch triggers the `deploy` job on a `docker-deploy` GitLab Runner, which validates the Compose configuration, preserves PostgreSQL data, rebuilds the application services, and verifies backend and frontend health checks.

## Components

- `backend/` — FastAPI API, ingestion, semantic search, and LLM answer services.
- `mcp_server/` — MCP server using Streamable HTTP.
- `frontend/` — Angular web interface.
- `docker-compose.yml` — PostgreSQL, backend, frontend, and MCP services.
- `.gitlab-ci.yml` — GitLab CI/CD deployment pipeline.
- `app_config.auth_token` — database-stored Bearer token used to protect the knowledge API and MCP server.

## Requirements

- Docker Engine and Docker Compose v2
- Node.js (for the `npm` scripts)
- Python 3.13 and `uv` (for local backend development)
- An OpenAI-compatible local model server, such as LM Studio, for the default local-LLM workflow

## Configuration

Create a local environment file:

```bash
cp .env.example .env
```

Key settings:

```env
FRONTEND_ORIGIN="http://localhost:8080"
FRONTEND_PORT="8080"

POSTGRES_DSN="postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_hub"

# The default and recommended setup: a local OpenAI-compatible server.
LLM_PROVIDER="local"
LOCAL_LLM_BASE_URL="http://127.0.0.1:1234"
DOCKER_LOCAL_LLM_BASE_URL="http://host.docker.internal:1234"
LOCAL_LLM_MODEL="gemma-4-12b-it"

# Optional external OpenAI-compatible provider.
API_LLM_BASE_URL="https://api.openai.com/v1"
API_LLM_MODEL="gpt-4.1-mini"
API_KEY=""

EMBEDDING_MODEL="text-embedding-nomic-embed-text-v1.5"
EMBEDDING_VERSION="default"
VECTOR_DIM="768"

MCP_HOST="0.0.0.0"
MCP_PORT="8001"
MCP_PUBLIC_URL="http://192.0.2.10:8001"
MCP_PATH="/mcp"
MCP_WRITE_ENABLED="false"
```

When the local model server runs on the Docker host, containers must use `DOCKER_LOCAL_LLM_BASE_URL`; Compose configures `host.docker.internal` on current Linux Docker installations. Ensure the selected embedding model and `VECTOR_DIM` match (for example, `text-embedding-nomic-embed-text-v1.5` uses 768 dimensions).

`MCP_WRITE_ENABLED` grants the MCP token the `knowledge:write` scope when set to `true`. Leave it disabled for a read-only MCP server, and enable it only when `ingest_text` is required.

### Configure the access token

The access token is stored in PostgreSQL under the `app_config.auth_token` key. Do not put it in `.env` or commit it to the repository.

For a local environment:

```bash
uv run set-auth-token --generate
```

With Docker:

```bash
docker compose run --rm backend set-auth-token --generate
```

The command prints the generated token once. Store it only in the MCP client or API client that needs it. To enter a token manually, omit `--generate`. Manually entered tokens must be 32–256 characters and use only letters, numbers, hyphens, and underscores.

To verify that a token exists without revealing it:

```bash
docker exec -it knowledge-hub-postgres psql -U postgres -d knowledge_hub \
  -c "select key, length(value) as token_length, updated_at from app_config;"
```

## Run with Docker

Start the full stack:

```bash
npm run dev:up
```

Other useful commands:

```bash
npm run db:up        # PostgreSQL only
npm run backend:up   # backend only
npm run mcp:up       # MCP server only
npm run db:clear     # permanently removes ingested sources and chunks
```

Default endpoints:

- API: `http://localhost:8000`
- API health check: `http://localhost:8000/health`
- Frontend: `http://localhost:8080`
- Local MCP: `http://localhost:8001/mcp`
- PostgreSQL: `localhost:5432`

Open the frontend and enter the token configured with `set-auth-token`. The optional “stay signed in” setting saves the token in browser storage, so use it only on a trusted device.

## Run locally for development

```bash
uv sync --extra dev
docker compose up -d postgres
uv run backend
```

In separate terminals, start the MCP server and frontend:

```bash
uv run mcp-server

cd frontend
npm install
npm run dev
```

## GitLab deployment

Deployment is managed by [`.gitlab-ci.yml`](.gitlab-ci.yml). The pipeline runs only when a commit reaches the default branch and requires a GitLab Runner tagged `docker-deploy` on the deployment host.

The deployment job:

1. validates `docker compose` configuration;
2. starts and keeps the PostgreSQL service and its persistent volume;
3. recreates the backend, frontend, and MCP containers with a fresh build;
4. waits for health checks and performs final HTTP checks.

Set deployment-specific values as protected GitLab CI/CD variables, especially any secrets and the target model server address. The current pipeline supplies deployment values such as `POSTGRES_DSN`, `DOCKER_LOCAL_LLM_BASE_URL`, and `MCP_PUBLIC_URL`; update them to match your infrastructure before deploying. The runner must be able to reach the local LLM server configured by `DOCKER_LOCAL_LLM_BASE_URL`.

The production database is deliberately preserved between deploys. Do not use the local Docker daemon as a substitute for the configured GitLab Runner or production environment.

## Knowledge API

When an access token has been configured, include it in every protected request:

```text
Authorization: Bearer <your-token>
```

For examples, keep the token in the current shell only:

```bash
export KNOWLEDGE_HUB_TOKEN="paste-your-token-here"
```

List categories:

```bash
curl -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  http://localhost:8000/api/v1/knowledge/categories
```

Create a category:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/categories \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"documents"}'
```

Ingest a file:

```bash
curl -F "file=@./document.pdf" \
  -F "category_ids=1" \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  http://localhost:8000/api/v1/knowledge/uploads
```

Ingest text:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/texts \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Meeting notes","category_ids":[1],"content":"Text to add to the knowledge base."}'
```

Search semantically:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What does this document say?","limit":5}'
```

Ask for an LLM-grounded answer using retrieved chunks:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/answer \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Summarize the document","limit":5}'
```

List document sources:

```bash
curl -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  http://localhost:8000/api/v1/knowledge/sources
```

## MCP access

The MCP endpoint uses Streamable HTTP:

```text
http://<host-or-ip>:8001/mcp
```

Configure an MCP client with `streamable-http`, the endpoint above, and the Bearer token. For example:

```json
{
  "mcpServers": {
    "knowledge-hub": {
      "type": "streamable-http",
      "url": "http://<host-or-ip>:8001/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

Available MCP tools:

| Tool | Purpose |
| --- | --- |
| `health` | Checks whether the MCP server responds. |
| `search` | Searches ingested chunks by semantic similarity. |
| `sources` | Lists available documents and sources. |
| `categories` | Lists available category IDs and names. |
| `ingest_text` | Persists a confirmed text note; requires `MCP_WRITE_ENABLED=true` and `knowledge:write`. |

`ingest_text` writes persistent knowledge. Agents must obtain the user's explicit confirmation of the exact text before calling it; it must not be used to automatically archive conversations. Use `categories` first to obtain valid IDs for `category_ids`.

The MCP resource `config://workspace-overview` returns a concise summary of the frontend, backend, database, MCP server, and LLM configuration.

To rotate a token, run `set-auth-token --generate` again. Backend and MCP validate the token from the database, so no secret needs to be committed or embedded in the deployment configuration.

## Tests and quality

```bash
uv run pytest -q
npm run quality
```

Run layer-specific checks when needed:

```bash
npm run backend:quality
npm run frontend:quality
```

## Troubleshooting

```bash
docker compose ps                         # inspect running services
docker compose stop backend               # stop the Docker backend
curl http://localhost:8000/health         # check the API
curl -i http://localhost:8001/mcp         # check MCP publication
```

A `401 Unauthorized` response from MCP is expected when the Bearer header is missing or does not match `app_config.auth_token`.
