# Plano 01 — Categorias muitos-para-muitos

## Objetivo

Permitir que um documento pertença a várias categorias e adicionar gestão básica de
categorias. Este plano substitui `document_sources.category_id` por uma tabela associativa.

## Modelo proposto

- `categories`: `id`, `name`, `created_at` e nome único sem diferenciar maiúsculas.
- `document_source_categories`: `document_source_id`, `category_id` e chave primária composta.
- Exclusão do documento remove associações com `ON DELETE CASCADE`.
- Exclusão de categoria associada deve ser recusada com `409 Conflict`.
- Todo documento deve possuir pelo menos uma categoria no momento do cadastro.

## Contrato

- Upload multipart recebe `category_ids` como lista de inteiros.
- Cadastro textual recebe `category_ids: [1, 2]`.
- Busca e resposta recebem `category_ids` opcionais.
- O filtro inicial usa semântica `ANY`: basta pertencer a uma das categorias informadas.
- Fontes passam a retornar `categories: [{"id": 1, "name": "financas"}]`.
- Criar `POST`, `PATCH` e `DELETE /api/v1/knowledge/categories` e manter o `GET` atual.
- Atualizar as tools `categories`, `search` e `sources` para o novo contrato.

## Implementação

1. Criar o modelo associativo e os relacionamentos ORM.
2. Criar migração idempotente: copiar cada `category_id` atual para a associação, validar
   contagens e somente então remover a coluna antiga.
3. Alterar schemas, serviços, API e MCP para listas de categorias.
4. Evitar duplicação de chunks em consultas com várias categorias usando `EXISTS` ou `DISTINCT`.
5. Normalizar nome de categoria e tratar conflito de unicidade.
6. Atualizar exemplos e documentação.

## Testes

- Migração preserva a categoria de todos os documentos existentes.
- Documento pode ser cadastrado com duas ou mais categorias.
- Lista vazia, IDs repetidos e categoria inexistente são rejeitados.
- Filtro `ANY` não duplica chunks.
- Categoria em uso não pode ser excluída.
- Recadastro atualiza as associações corretamente.

## Critérios de aceite

- Nenhum documento migrado fica sem categoria.
- API, MCP e documentação não expõem mais o campo singular `category_id`.
- Todos os testes passam e a migração pode ser executada mais de uma vez.

