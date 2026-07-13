# Plano 08 — Projetos

## Objetivo

Agrupar conhecimento por projeto e permitir que um documento seja reutilizado em mais de um
contexto sem duplicação.

## Modelo proposto

- `projects`: `id`, `name`, `description`, `status`, `created_at` e `updated_at`.
- `document_source_projects`: relação muitos-para-muitos.
- Projeto é opcional; conhecimento geral continua sem associação.

## Implementação

1. Criar CRUD de projetos e associações com fontes.
2. Adicionar filtro por `project_ids` na busca e no MCP.
3. Criar listagem das fontes de um projeto.
4. Manter categorias como assunto e projeto como contexto de trabalho.
5. Definir arquivamento de projeto sem excluir seu conhecimento.

## Testes

- Uma fonte pode participar de vários projetos.
- Arquivar projeto não remove fonte nem chunks.
- Filtros de projeto e categoria funcionam em conjunto.
- Projetos inexistentes são rejeitados sem gravação parcial.

## Critérios de aceite

- A IA consegue restringir uma consulta ao projeto atual.
- Conhecimento compartilhado não precisa ser cadastrado novamente.

