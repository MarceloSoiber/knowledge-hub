# Data Model: Organização do acervo no frontend

Não há tabelas, migrações ou persistência nova. Os estados abaixo vivem no cliente e usam os tipos HTTP existentes.

## MetadataCatalogState

| Campo | Tipo | Regra |
| --- | --- | --- |
| `categories` | `Category[]` | Ordenadas por nome; atualizadas após CRUD. |
| `tags` | `Tag[]` | Ordenadas por nome; atualizadas após CRUD; não são a fonte única das sugestões. |
| `projects` | `Project[]` | Inclui ativos e arquivados quando carregado pela gestão. |
| `activeProjects` | `Project[]` derivado | Somente `status === "active"`; usado para associação nova. |
| `loading/error` | estado por coleção | Permite retry explícito sem apagar valores válidos já exibidos. |

## ClassificationDraft

| Campo | Tipo | Regra |
| --- | --- | --- |
| `id` | `number \| null` | `null` para criação; positivo para edição. |
| `name` | `string` | Obrigatório após `trim`; máximo de 100 caracteres. |
| `kind` | `"category" \| "tag"` | Determina endpoint e textos da interface. |

## ProjectDraft

| Campo | Tipo | Regra |
| --- | --- | --- |
| `id` | `number \| null` | `null` para criação; positivo para edição. |
| `name` | `string` | Obrigatório após `trim`; máximo de 150 caracteres. |
| `description` | `string` | Opcional; vazio normaliza para `null`; máximo de 2000 caracteres. |

## TagAutocompleteState

| Campo | Tipo | Regra |
| --- | --- | --- |
| `query` | `string` | Texto do campo; consulta vazia não chama API. |
| `suggestions` | `Tag[]` | Resultado da última consulta vigente; sem IDs duplicados ou já selecionados. |
| `loading/error` | estado transitório | Cancelar/ignorar resposta anterior ao alterar consulta ou destruir controle. |

## ProjectSourcesState

| Campo | Tipo | Regra |
| --- | --- | --- |
| `project` | `Project` | Projeto canônico aberto. |
| `sources` | `KnowledgeSource[]` | Carregado por `GET /projects/{id}/sources`. |
| `loading/error` | estado transitório | Distingue vazio legítimo, 404 e falha recuperável. |
