# Plano 11 — Índice vetorial HNSW

## Objetivo

Manter a latência da busca aceitável quando a quantidade de chunks crescer.

## Pré-condições

- Modelo, dimensão e operador de distância estabilizados.
- Conjunto de avaliação disponível.
- Volume suficiente para justificar o índice; em bases pequenas, busca exata pode ser melhor.

## Implementação

1. Medir `EXPLAIN (ANALYZE, BUFFERS)` e latência antes da mudança.
2. Criar índice HNSW usando `vector_cosine_ops` de forma compatível com a versão do pgvector.
3. Configurar parâmetros de construção e consulta a partir de medições, não de valores arbitrários.
4. Executar `ANALYZE` e verificar que a consulta realmente utiliza o índice.
5. Documentar custo de memória, tempo de criação e manutenção.

## Testes

- Comparar recall e latência com busca exata.
- Validar filtros por categorias e projetos.
- Medir inserção e reindexação com o índice ativo.

## Critérios de aceite

- Ganho de latência mensurável sem perda de recall acima do limite acordado.
- Migração e rollback do índice estão documentados.

