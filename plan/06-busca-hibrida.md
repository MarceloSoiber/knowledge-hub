# Plano 06 — Busca híbrida

## Objetivo

Combinar similaridade semântica com busca textual para nomes, códigos, números e termos exatos.

## Implementação

1. Adicionar `tsvector` derivado do conteúdo e índice GIN no PostgreSQL.
2. Escolher configuração textual (`portuguese` ou `simple`) com testes para português e código.
3. Executar busca vetorial e textual com conjuntos candidatos independentes.
4. Combinar rankings com Reciprocal Rank Fusion (RRF), evitando misturar scores de escalas
   diferentes diretamente.
5. Manter filtros de categorias, projetos e tags antes do limite final.
6. Expor opcionalmente o motivo do match para diagnóstico.

## Testes

- Recuperar identificadores exatos, tickers e mensagens de erro.
- Recuperar paráfrases que não compartilham palavras com o documento.
- Não duplicar chunks encontrados pelos dois métodos.
- Comparar qualidade com a busca vetorial anterior.

## Critérios de aceite

- A busca híbrida supera ou iguala a vetorial no conjunto do Plano 12.
- O plano de execução usa os índices esperados.

