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

2. Instale as dependências Python com `uv`:

```bash
uv sync
```

3. Rode a API:

```bash
uv run backend
```

4. Rode o MCP Server:

```bash
uv run mcp-server
```

5. No frontend:

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