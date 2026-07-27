# Data Model: Biblioteca e manutenção de fontes

Não há mudança de banco nem modelos FastAPI. Os modelos abaixo são estados TypeScript locais, derivados dos contratos existentes.

## Contratos remotos reutilizados

| Tipo | Campos relevantes |
| --- | --- |
| `KnowledgeSource` | `source_id`, `title`, `source_type`, `uri`, `content_hash`, `created_at`, `updated_at`, `categories`, `tags`, `projects` |
| `KnowledgeSourceDetail` | todos de `KnowledgeSource` + `content` |
| `KnowledgeSourcePatchRequest` (novo tipo cliente) | `title?`, `content?`, `category_ids?`, `tag_ids?`, `project_ids?`; pelo menos um campo |

## Estado de Biblioteca

| Campo | Tipo | Regra |
| --- | --- | --- |
| `sources` | `KnowledgeSource[]` | Resultado canônico de `GET /sources`; recarregado somente por ação explícita/retorno após alteração. |
| `titleQuery` | `string` | Comparado com títulos normalizados, sem case/acentos. |
| `selectedCategoryIds` | `number[]` | Uma fonte deve conter todos os IDs selecionados. |
| `selectedTagIds` | `number[]` | Uma fonte deve conter todos os IDs selecionados. |
| `selectedProjectIds` | `number[]` | Uma fonte deve conter todos os IDs selecionados. |
| `loading` / `error` | estado explícito | Não coexistem com sucesso sem representação clara na UI. |

Os filtros são cumulativos entre grupos e inclusivos em cada grupo. A lista filtrada é valor derivado, nunca uma cópia mutável de `sources`.

## Rascunho e PATCH

| Campo | Tipo | Regra |
| --- | --- | --- |
| `title` | `string` | Após `trim`, 1–255 caracteres. |
| `content` | `string` | Após `trim`, não vazio se presente no PATCH. |
| `categoryIds` | `number[]` | Array presente significa substituir todas as categorias; pode ser vazio conforme API. |
| `tagIds` | `number[]` | Array presente significa substituir todas as tags; vazio remove todas. |
| `projectIds` | `number[]` | Array presente significa substituir todos os projetos; vazio remove todos. |
| `baseline` | snapshot de `KnowledgeSourceDetail` | Atualizado exclusivamente após GET/PATCH bem-sucedido. |

O comparador trata IDs como conjuntos: remove duplicatas e não envia PATCH quando só a ordem mudou. Alteração de `content` habilita o aviso de reprocessamento. Um PATCH bem-sucedido substitui baseline e rascunho pela resposta do servidor.

## Transições de estado

```text
detalhe carregando → detalhe pronto → editando → salvando → detalhe pronto
                              │              └→ erro de salvamento (rascunho preservado)
                              └→ diálogo de exclusão → excluindo → navegação para Biblioteca
                                                        └→ erro de exclusão (detalhe pronto)
```

`404` durante GET, PATCH ou DELETE encerra a ação pendente, explica que a fonte não está mais disponível e oferece retorno à Biblioteca. `409` preserva o rascunho e pode fornecer link seguro à fonte já existente quando `existing_source_id` for UUID válido.
