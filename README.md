# MCP Knowledge Hub

Base inicial de um hub de conhecimento com:

- Frontend simples
- Backend em Python/FastAPI
- PostgreSQL com `pgvector`
- MCP Server via Python SDK
- Abstração para LLM local ou API

## Estrutura

- `frontend/`: interface web simples em React + Vite
- `backend/`: API FastAPI e camada de domínio
- `mcp_server/`: servidor MCP em `stdio`
- `docker-compose.yml`: banco PostgreSQL com `pgvector`

## Como rodar

1. Suba o banco:

```bash
docker compose up -d postgres
```

Se o plugin `docker compose` não estiver instalado, use:

```bash
docker-compose up -d postgres
```

O banco sobe em `localhost:5432` com a extensão `vector` habilitada.

2. Para subir banco e backend via Docker:

```bash
npm run dev:up
```

Ou somente o backend, assumindo o banco ativo:

```bash
npm run backend:up
```

A API sobe em `http://localhost:8000`.

Para usar LM Studio localmente, inicie o server em `http://127.0.0.1:1234`.
Dentro do container, o backend acessa esse server por
`http://host.docker.internal:1234`. O modelo inicial configurado e
`gemma-4-12b`.

Para gerar embeddings localmente, o servidor OpenAI-compatible tambem precisa
responder em `/v1/embeddings` para o modelo definido em `EMBEDDING_MODEL`.
Se o modelo de chat nao suportar embeddings, carregue um modelo de embeddings
no LM Studio e ajuste `EMBEDDING_MODEL`/`VECTOR_DIM`.

3. Instale as dependências Python com `uv`:

```bash
uv sync
```

4. Rode a API localmente, fora do Docker:

```bash
uv run backend
```

### API de conhecimento

Ingestao de arquivo:

```bash
curl -F "file=@./documento.pdf" http://localhost:8000/api/v1/knowledge/uploads
```

Busca semantica:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query":"o que este documento diz?", "limit":5}'
```

Resposta com LLM usando os chunks encontrados:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"resuma o documento", "limit":5}'
```

5. Rode o MCP Server:

```bash
uv run mcp-server
```

6. No frontend:

```bash
cd frontend
npm install
npm run dev
```

## Próximos passos

- conectar ingestão de documentos ao banco
- implementar embeddings e busca semântica
- integrar o backend com o provedor de LLM escolhido
- expor ferramentas do MCP sobre os dados do hub
