# Knowledge Hub

Knowledge Hub is a self-hosted knowledge base for private, document-grounded AI
workflows. It ingests files and notes, stores vector embeddings in PostgreSQL
with `pgvector`, retrieves the most relevant passages, and can produce grounded
answers through a **local LLM**. It also exposes the knowledge base through a
remote MCP server and an Angular web application.

The project is local-first by design: documents, embeddings, and inference can
remain on infrastructure you control. Cloud models are optional and are only
used when explicitly configured.

## What is included

| Component | Purpose | Default address |
| --- | --- | --- |
| Angular frontend | Browser interface for search, ingestion, library management, and operations. | `http://localhost:8080` |
| FastAPI backend | REST API, ingestion pipeline, semantic search, RAG answers, and authentication. | `http://localhost:8000` |
| PostgreSQL + pgvector | Persistent documents, chunks, metadata, token configuration, and vectors. | `localhost:15432` |
| MCP server | Streamable HTTP tools for AI clients and agents. | `http://localhost:8001/mcp` |
| Local model server | OpenAI-compatible chat and embedding endpoint, such as LM Studio or Ollama. | `http://127.0.0.1:1234` |

## Architecture

```text
Browser / MCP client
        │ Bearer token
        ▼
Frontend ───────► FastAPI API ───────► PostgreSQL + pgvector
                        │                        ▲
                        │ embeddings / retrieval  │
                        ▼                        │
             Local OpenAI-compatible LLM ────────┘
             (LM Studio, Ollama, or equivalent)
```

The backend splits incoming content into chunks, creates embeddings, and saves
them in PostgreSQL. A search retrieves similar chunks. The answer endpoint uses
those retrieved chunks as context for the configured chat model.

## Requirements

- Docker Engine and Docker Compose v2 (`docker compose`)
- Node.js and npm (for frontend development and project scripts)
- Python 3.13 and [uv](https://docs.astral.sh/uv/) (for local backend work)
- A local server with an OpenAI-compatible API for chat and embeddings

For the default configuration, use a model server at port `1234`. The model
server must provide a chat-completions endpoint and an embeddings endpoint.

## Quick start with Docker

1. Create your local configuration:

   ```bash
   cp .env.example .env
   ```

2. Start the full stack:

   ```bash
   npm run dev:up
   ```

3. Create an API/MCP access token:

   ```bash
   docker compose run --rm backend set-auth-token --generate
   ```

   Save the printed value in a password manager. It is shown once.

4. Open `http://localhost:8080`, then sign in with that token.

5. Verify the API:

   ```bash
   curl http://localhost:8000/health
   ```

Useful service commands:

```bash
npm run db:up          # PostgreSQL only
npm run backend:up     # backend and required dependencies
npm run frontend:up    # frontend
npm run mcp:up         # MCP server
docker compose ps      # running services and health status
docker compose logs -f backend
```

`npm run db:clear` permanently removes all knowledge sources and chunks. Do not
use it for normal maintenance.

## Local LLM configuration

Local inference is the default. No cloud API key is required when
`LLM_PROVIDER=local`.

```env
LLM_PROVIDER="local"
LOCAL_LLM_BASE_URL="http://127.0.0.1:1234"
DOCKER_LOCAL_LLM_BASE_URL="http://host.docker.internal:1234"
LOCAL_LLM_MODEL="gemma-4-12b-it"

EMBEDDING_MODEL="text-embedding-nomic-embed-text-v1.5"
EMBEDDING_VERSION="default"
VECTOR_DIM="768"
```

`LOCAL_LLM_BASE_URL` is used when running the backend directly on the host.
`DOCKER_LOCAL_LLM_BASE_URL` is used by Docker containers. On Linux, Compose
maps `host.docker.internal` to the host gateway.

### AI settings portal

After signing in, open **Settings** from the user menu to manage the AI
provider, endpoints, model IDs, and embedding model. Values saved there take
precedence over the corresponding environment variables for new requests; the
environment remains the fallback for any setting that has not been saved.

`DOCKER_LOCAL_LLM_BASE_URL` remains a Docker Compose boot-time setting. It is
used to set the backend's initial `LOCAL_LLM_BASE_URL` and is not managed by
the portal.

When storing an API key through the portal, set `CONFIG_ENCRYPTION_KEY` to one
stable Fernet key in the backend environment. Generate it once:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Keep the generated key secret and unchanged. Without it, local-model settings
continue to work, but the portal cannot save an API key; changing it prevents
the application from decrypting API keys previously stored in PostgreSQL.

### LM Studio

1. Load a chat model and an embedding model in LM Studio.
2. Start its local server with OpenAI-compatible endpoints enabled.
3. Set the actual model IDs displayed by LM Studio in `LOCAL_LLM_MODEL` and
   `EMBEDDING_MODEL`.
4. Keep the embedding dimensionality aligned with `VECTOR_DIM`. The default
   Nomic embedding model uses 768 dimensions.

### Ollama

Ollama can be used when its OpenAI-compatible `/v1` API and the selected chat
and embedding models are available. Point the base URL at the host reachable by
the backend (for example, `http://host.docker.internal:11434/v1` from Docker)
and set model names accordingly. Verify both chat and embedding requests before
ingesting production documents.

### Changing the embedding model

Changing `EMBEDDING_MODEL`, `EMBEDDING_VERSION`, or `VECTOR_DIM` does not make
old vectors compatible with the new model. Reindex the stored knowledge before
depending on search results from the new configuration. Use a new
`EMBEDDING_VERSION` to make the change explicit.

## Environment configuration

Copy `.env.example` and adjust only what your environment requires.

| Variable | Description |
| --- | --- |
| `FRONTEND_ORIGIN` | Allowed frontend origin for the API, e.g. `http://localhost:8080`. |
| `FRONTEND_PORT` / `BACKEND_PORT` | Host ports exposed by Docker Compose. |
| `POSTGRES_DSN` | Async PostgreSQL connection string used by backend and MCP. |
| `POSTGRES_HOST_PORT` | Host port mapped to PostgreSQL; local default is `15432`. |
| `LLM_PROVIDER` | `local` for local inference; set another value only when intentionally using the API configuration. |
| `LOCAL_LLM_*` / `DOCKER_LOCAL_LLM_BASE_URL` | Local model endpoint and chat model name. |
| `API_LLM_BASE_URL`, `API_LLM_MODEL`, `API_KEY` | Optional external OpenAI-compatible provider configuration. Keep `API_KEY` out of Git. |
| `CONFIG_ENCRYPTION_KEY` | Stable Fernet key used only to encrypt an API key saved through the Settings portal. Keep it secret and do not rotate it while a saved API key is needed. |
| `EMBEDDING_MODEL`, `EMBEDDING_VERSION`, `VECTOR_DIM` | Embedding identity and vector size. |
| `MCP_HOST`, `MCP_PORT`, `MCP_PUBLIC_URL`, `MCP_PATH` | MCP listener and public Streamable HTTP URL. |
| `MCP_WRITE_ENABLED` | Enables MCP text ingestion only when set to `true`; default is read-only. |

Do not commit `.env` with real credentials, encryption keys, or production
addresses. The access token is not an environment variable: it is stored in the
`app_config` table in PostgreSQL.

## Authentication

All protected API and MCP calls use:

```text
Authorization: Bearer <token>
```

Create or rotate the token locally:

```bash
uv run set-auth-token --generate
# or, with Docker
docker compose run --rm backend set-auth-token --generate
```

For manual entry, omit `--generate`. Tokens must be 32–256 characters and may
contain letters, numbers, hyphens, and underscores. To verify that a token is
configured without exposing it:

```bash
docker compose exec postgres psql -U postgres -d knowledge_hub \
  -c "select key, length(value) as token_length, updated_at from app_config;"
```

## API usage

Set a shell-only token variable:

```bash
export KNOWLEDGE_HUB_TOKEN="replace-with-your-token"
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

Ingest a text note:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/texts \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Architecture decision","category_ids":[1],"content":"Use local inference by default."}'
```

Search the knowledge base:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"How is local inference configured?","limit":5}'
```

Ask a grounded question:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/answer \
  -H "Authorization: Bearer $KNOWLEDGE_HUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Summarize the architecture decision","limit":5}'
```

The interactive API schema is available at `http://localhost:8000/docs` while
the backend is running.

## MCP server

The MCP endpoint uses Streamable HTTP:

```text
http://localhost:8001/mcp
```

Example client configuration:

```json
{
  "mcpServers": {
    "knowledge-hub": {
      "type": "streamable-http",
      "url": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer <token>"
      }
    }
  }
}
```

Available MCP tools include `health`, `search`, `sources`, `source`,
`categories`, `tags`, `projects`, `project_sources`, `tag_autocomplete`, and
`ingest_text`. The `ingest_text` tool persists knowledge and is disabled by
default. Enable it only when needed:

```env
MCP_WRITE_ENABLED="true"
```

Agents must obtain explicit user confirmation before persisting content through
`ingest_text`.

## Local development

Backend:

```bash
uv sync --extra dev
docker compose up -d postgres
uv run backend
```

MCP server:

```bash
uv run mcp-server
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Run checks:

```bash
uv run pytest -q
npm run backend:quality
npm run frontend:quality
npm run quality
```

## GitLab CI/CD: development and production deployment

For a reusable, step-by-step SSH and GitLab-variable setup for this and future
projects, see [GitLab CI/CD: deploy seguro por SSH](docs/GITLAB_CI_SSH_DEPLOY.md).

The repository contains two deployment jobs in `.gitlab-ci.yml`, both run by a
GitLab runner tagged `docker-deploy`:

- `deploy_develop` runs only for the `develop` branch and deploys to the
  development VM.
- `deploy_master` runs only for the `master` branch and deploys to the
  production Master VM.

The runner connects to each target through SSH; Docker Compose runs **on the
target VM**, not on the GitLab runner. The deployment VM must have Docker
Engine and the Compose plugin installed, while the runner needs SSH, `ssh-keygen`
and `base64` available. Do not configure either job to use an arbitrary shared
runner without the required protected SSH credentials.

### What the pipeline does

1. Validates the Compose file with `docker compose config --quiet`.
2. Preserves the PostgreSQL data volume and waits for PostgreSQL health.
3. Stops and removes stale backend, frontend, and MCP containers.
4. Rebuilds and force-recreates backend, frontend, and MCP one service at a
   time.
5. Waits for repeated backend and frontend health checks.
6. Performs final HTTP checks from inside the backend and frontend containers.

The deployed container names are `knowledge-hub-postgres`,
`knowledge-hub-backend`, `knowledge-hub-frontend`, and `knowledge-hub-mcp`.

### Required target VM setup

For each deployment VM, configure:

- Docker Engine and `docker compose` available to the SSH user.
- permission for that user to manage Docker.
- a checkout at `$DEPLOY_ROOT/$CI_PROJECT_NAME`, with `origin` pointing to this
  GitLab project.
- an untracked, environment-specific `.env` file in that checkout.
- network access from containers to the local LLM endpoint.
- firewall rules allowing only the intended ports: backend `8000`, frontend
  `8080`, MCP `8001`, and optionally PostgreSQL `5432`.

The Master VM is `192.168.15.128`. Its non-secret deployment values include:

```yaml
POSTGRES_HOST_PORT: "5432"
POSTGRES_DSN: "postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/knowledge_hub"
DOCKER_LOCAL_LLM_BASE_URL: "http://192.168.15.114:1234"
EMBEDDING_VERSION: "default"
MCP_PUBLIC_URL: "http://192.168.15.128:8001"
```

Configure the following protected GitLab CI/CD variables for the Master job:

```text
PROD_HOST=192.168.15.128
PROD_USER=<SSH user on Master>
PROD_DEPLOY_ROOT=<absolute checkout parent directory on Master>
PROD_SSH_PRIVATE_KEY_B64=<base64-encoded private key>
PROD_SSH_KNOWN_HOSTS=<known_hosts file variable>
PROD_ENV_FILE=<production .env file variable>
```

Configure the equivalent `DEV_*` variables for the development job, including
`DEV_ENV_FILE`. The pipeline copies the File variable to the target as `.env`
after checking out the release, so each environment keeps its own configuration.
Use [the environment templates](deploy/env) as a starting point. Keep
credentials and optional cloud-provider settings as masked, protected GitLab
variables; do not commit them to `.gitlab-ci.yml` or `.env`. Typical protected
application variables are `API_KEY`, `API_LLM_BASE_URL`, `API_LLM_MODEL`, and
`CONFIG_ENCRYPTION_KEY` when an external provider is intentionally enabled.

### Deploying through GitLab

1. Ensure the GitLab runner is online and tagged `docker-deploy`.
2. Configure the deployment variables and protected SSH credentials in GitLab.
3. Push the desired change to `develop` for development or `master` for Master.
4. Open **Build → Pipelines** in GitLab and follow the `deploy` job logs.
5. Confirm the final health checks and open the frontend and MCP URLs.

The job uses `resource_group: production`, so GitLab serializes production
deployments and prevents overlapping releases.

### Post-deploy checks

On the deployment host or through the job log:

```bash
docker compose ps
docker compose logs --tail=200 backend
curl http://127.0.0.1:8000/health
```

The PostgreSQL volume is deliberately preserved during deployments. A release
does not create or rotate the application token; use `set-auth-token` only when
you explicitly intend to create or rotate it.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Backend cannot reach the local model | Confirm `DOCKER_LOCAL_LLM_BASE_URL` is reachable from the backend container and that the model server exposes both chat and embeddings. |
| Search errors after a model change | Confirm `VECTOR_DIM` matches the embedding model; reindex with a new `EMBEDDING_VERSION`. |
| `401 Unauthorized` from API or MCP | Create or rotate the token, then send it as a Bearer token. |
| Frontend cannot call the API | Check `FRONTEND_ORIGIN`, backend health, and browser network errors. |
| Port already in use | Run `docker compose ps`, identify the listener, then stop the relevant Compose service. |
| GitLab job does not start | Confirm the `develop` or `master` branch rule, runner availability, and the `docker-deploy` runner tag. |

## Security notes

- Treat documents, embeddings, backups, and the Bearer token as sensitive data.
- Keep local inference local when confidentiality matters.
- Do not commit `.env`, tokens, API keys, database dumps, or backups.
- Leave `MCP_WRITE_ENABLED=false` unless a controlled write workflow is needed.
- Use protected GitLab variables and a protected production runner for deploys.
