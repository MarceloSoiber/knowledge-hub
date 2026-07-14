# Plano 07 — Tags

## Objetivo

Adicionar classificação livre e granular sem transformar categorias em uma lista difícil de
administrar.

## Decisão antes de implementar

Categorias e tags serão muitos-para-muitos, mas têm papéis diferentes:

- Categoria: vocabulário controlado e assunto amplo, como `financas` ou `software`.
- Tag: marcador específico e reutilizável, como `python`, `postgres`, `imposto` ou `rag`.

Se as categorias múltiplas já atenderem ao uso real após algumas semanas, este plano pode ser
adiado para evitar complexidade sem benefício.

## Implementação

1. Criar `tags` e `document_source_tags` com chaves e índices únicos.
2. Normalizar nomes e definir política para acentos e maiúsculas.
3. Adicionar CRUD, autocomplete e associação aos documentos.
4. Permitir filtro `ANY` e, se houver caso real, filtro `ALL`.
5. Atualizar API, MCP e documentação.

## Testes e aceite

- Tags repetidas não criam duplicatas.
- Alterar tags não reprocessa embeddings.
- Busca combina tags com categorias sem duplicar chunks.
- O plano só é considerado pronto se houver casos que categorias não resolvem bem.

