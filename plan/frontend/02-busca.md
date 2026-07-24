# 02 — Busca inteligente

## Resultado esperado

Uma pessoa consegue encontrar trechos relevantes, filtrar a consulta e abrir a fonte de cada resultado.

## Escopo

- Campo de consulta, limite de resultados, score mínimo e filtros por categoria, tag e projeto.
- Carregar metadados para filtros e usar autocomplete de tags.
- Exibir título da fonte, trecho, score, localização (página/seção quando existir) e chips de metadados.
- Oferecer alternância para motivos de correspondência retornados pela API.
- Linkar cada resultado para o detalhe da fonte.

## Endpoints

- `POST /knowledge/search`
- `GET /knowledge/categories`
- `GET /knowledge/tags`
- `GET /knowledge/tags/autocomplete`
- `GET /knowledge/projects`

## Estados e erros

- Consulta vazia, busca em andamento, nenhum resultado e falha da API.
- Informar filtro inválido ou recurso inexistente sem perder o texto digitado.
- Indicar indisponibilidade de embeddings de forma acionável, sem revelar dados sensíveis.

## Critérios de aceite

- A busca simples retorna resultados e abre o detalhe da fonte.
- Filtros são opcionais e podem ser removidos individualmente.
- A interface permanece navegável por teclado e utilizável em viewport móvel.

## Dependência

Requer a fundação, os tipos de domínio e o cliente HTTP centralizado.
