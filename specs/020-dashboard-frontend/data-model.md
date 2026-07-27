# Data Model: Dashboard inicial do acervo

Não há tabelas, migrações ou novos modelos FastAPI. Os estados são locais ao componente Angular e derivados das respostas existentes.

## Dados remotos reutilizados

| Tipo | Campos usados |
| --- | --- |
| `KnowledgeSource` | `source_id`, `title`, `source_type`, `uri`, `created_at`, `updated_at`, metadados para o link de detalhe. |
| `Category` | `id`, `name`; a métrica usa o tamanho da lista. |
| `Tag` | `id`, `name`; a métrica usa o tamanho da lista. |
| `Project` | `id`, `status`; as métricas derivam `active` e `archived`. |

## DashboardState

| Campo | Tipo | Regra |
| --- | --- | --- |
| `sources` | `KnowledgeSource[]` | Resultado de `GET /sources`; não mutar ao ordenar. |
| `categories` | `Category[]` | Resultado de `GET /categories`. |
| `tags` | `Tag[]` | Resultado de `GET /tags`. |
| `projects` | `Project[]` | Resultado de `GET /projects`, incluindo ambos os estados. |
| `loadState` | por coleção: `loading`, `ready` ou `error` | Cada coleção tem erro/mensagem e retry próprios. |
| `recentSources` | `KnowledgeSource[]` derivado | Cópia ordenada por `created_at` desc; fallback `updated_at` desc; inválidas/nulas por último; desempate por título e `source_id`; limitada a 5. |
| `metrics` | valor derivado | `sources.length`, `categories.length`, `tags.length`, e filtros exatos de projetos por status. |

Listas vazias em estado `ready` produzem zero. Uma falha não altera uma lista válida anterior; retry substitui dados somente após sucesso.

## Transições

```text
entrada em /inicio
  ├─ fontes: carregando → pronta / erro → retry → pronta
  ├─ categorias: carregando → pronta / erro → retry → pronta
  ├─ tags: carregando → pronta / erro → retry → pronta
  └─ projetos: carregando → pronta / erro → retry → pronta

fontes prontas e vazias → chamada para primeira ingestão
fontes prontas e preenchidas → lista de recentes
```
