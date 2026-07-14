# Plano 04 — Metadados e citações na busca

## Objetivo

Tornar cada resultado rastreável e útil para citações produzidas pela IA.

## Dados recomendados

- Fonte: título, URI/URL original, tipo, categorias, autor, data de publicação e data de captura.
- Chunk: índice, página, seção, posição inicial/final e metadados estruturados em JSONB.
- Resultado: `chunk_id`, `source_id`, título, categorias, URI, localização, conteúdo e score.

## Implementação

1. Trocar `metadata_json` textual por JSONB ou colunas consultáveis quando apropriado.
2. Preservar página e seção durante extração e chunking.
3. Enriquecer `KnowledgeChunkRead` e as respostas da API/MCP.
4. Ajustar o prompt de resposta para citar título e localização.
5. Não expor caminhos locais ou metadados sensíveis sem necessidade.

## Testes

- Resultados contêm origem mesmo com múltiplas categorias.
- PDF preserva número da página.
- Texto/Markdown preserva seção quando identificável.
- O endpoint `answer` referencia somente fontes realmente recuperadas.

## Critérios de aceite

- Um usuário consegue localizar o documento original a partir de qualquer resultado.
- A tool MCP fornece contexto suficiente para outro LLM produzir citações.

