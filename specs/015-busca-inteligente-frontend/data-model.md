# Data Model: Busca Inteligente no Frontend

Esta feature não cria persistência nem modelos de banco. Os tipos TypeScript espelham apenas contratos públicos já existentes.

## SearchQuery

| Campo | Tipo | Regras |
| --- | --- | --- |
| `query` | `string` | Obrigatório após `trim`; não enviar vazio. |
| `limit` | `number` | Inteiro de 1 a 50; iniciar no padrão da API. |
| `minScore` | `number \| null` | Nulo omite o campo; quando preenchido, de 0 a 1. |
| `categoryIds` | `number[]` | IDs únicos, positivos; semântica ANY dentro da dimensão. |
| `tagIds` | `number[]` | IDs únicos, positivos; semântica ANY dentro da dimensão. |
| `projectIds` | `number[]` | IDs únicos, positivos; semântica ANY dentro da dimensão. |
| `includeMatchReasons` | `boolean` | Enviar `true` apenas quando ativado. |

As dimensões categoria, tag e projeto são combinadas por AND no backend.

## SearchResult

| Campo | Origem | Exibição |
| --- | --- | --- |
| `id` | Chunk interno | Chave de renderização; não exibir como identificador público. |
| `sourceId` | `source_id` | Usado apenas para construir navegação ao detalhe. |
| `sourceTitle` | `source_title` | Título/link da fonte. |
| `content` | `content` | Trecho renderizado como texto. |
| `score` | `score` | Número opcional; nulo significa score vetorial indisponível. |
| `location` | `location` | Exibir página, seção e/ou índice de chunk somente quando existirem. |
| `categories`, `tags`, `projects` | Metadados | Chips somente de leitura. |
| `matchReasons` | `match_reasons` | Lista opcional de `vector` e/ou `text`, exibida só em modo diagnóstico. |

## SearchViewState

| Estado | Dados permitidos | Comportamento |
| --- | --- | --- |
| `idle` | formulário | Sem mensagem de resultado inicial. |
| `loading` | consulta anterior pode permanecer visível | Indicar carregamento e impedir submissão duplicada. |
| `success` | `results` | Renderizar resultados ou estado vazio. |
| `validation-error` | formulário | Mostrar erro local no campo correspondente. |
| `request-error` | formulário e erro seguro | Preservar consulta/filtros e mostrar recuperação. |

## Relações e ciclo de vida

- Uma `SearchQuery` produz uma requisição e uma resposta `SearchResponse` transitória.
- Cada `SearchResult` referencia uma fonte por UUID público, mas não possui edição nesta feature.
- Um `MetadataFilter` referencia uma categoria, tag ou projeto listado pela API e pode ser removido individualmente.
- Nenhum desses estados é salvo entre sessões ou alterado no backend.
