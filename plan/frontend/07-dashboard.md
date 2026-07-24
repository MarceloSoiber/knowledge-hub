# 07 — Dashboard

## Resultado esperado

Uma visão inicial do acervo e atalhos para as ações de maior valor.

## Escopo

- Cartões: total de fontes, categorias, tags, projetos ativos e arquivados.
- Lista de fontes recentes, ordenada no cliente enquanto a API não oferecer ordenação.
- Atalhos para busca, pergunta e ingestão.
- Estado vazio com chamada para a primeira ingestão.

## Endpoints

- `GET /knowledge/sources`
- `GET /knowledge/categories`
- `GET /knowledge/tags`
- `GET /knowledge/projects`

## Critérios de aceite

- Contagens correspondem às listagens carregadas.
- Uma base vazia não mostra cartões quebrados e indica a próxima ação.
- O dashboard não bloqueia a navegação enquanto dados secundários carregam.

## Dependência

Requer fundação. É mais valioso depois de busca e ingestão estarem prontas.
