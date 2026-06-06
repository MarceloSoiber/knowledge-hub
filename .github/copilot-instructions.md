# Copilot Instructions

- Prefira manter lógica de negócio em `backend/app/services` e rotas finas em `backend/app/api/routes`.
- Para o MCP Server, siga a abordagem `FastMCP` do SDK oficial: https://github.com/modelcontextprotocol/python-sdk e https://modelcontextprotocol.io/
- O banco principal é PostgreSQL com `pgvector`.
- O frontend deve continuar simples e focado em status, ingestão e busca.
- Quando adicionar ferramentas MCP, mantenha nomes de ferramentas curtos e orientados ao domínio do hub.