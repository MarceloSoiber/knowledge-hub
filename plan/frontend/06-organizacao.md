# 06 — Organização: categorias, tags e projetos

## Resultado esperado

Manutenção das classificações e agrupamentos usados em todo o acervo.

## Escopo

- Categorias e tags: listar, criar, editar e excluir.
- Tags: usar autocomplete nos formulários que consomem tags.
- Projetos: criar, editar, filtrar por status, arquivar, reativar e abrir suas fontes vinculadas.
- Confirmar exclusões e mostrar por que a API impede remover itens em uso.

## Endpoints

- Categorias: `GET`, `POST`, `PATCH`, `DELETE /knowledge/categories`.
- Tags: `GET`, `POST`, `PATCH`, `DELETE /knowledge/tags`.
- Projetos: `GET`, `POST /knowledge/projects`, `PATCH /knowledge/projects/{id}`, `POST /archive`, `POST /reactivate`, `GET /sources`.

## Critérios de aceite

- Mudanças de metadados ficam disponíveis nos filtros sem recarregar a aplicação inteira.
- Projeto arquivado não é apresentado como ativo e pode ser reativado.
- Tentativa de excluir categoria/tag em uso explica o conflito e preserva os dados.

## Dependência

Requer fundação. Deve disponibilizar componentes e dados para busca, ingestão e biblioteca.
