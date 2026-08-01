# Data Model: Pergunte à Base no Frontend

Esta feature não cria persistência, migração ou modelo de banco. Os estados TypeScript apenas organizam o contrato público existente.

## AnswerQuery

| Campo | Tipo | Regras |
| --- | --- | --- |
| `query` | `string` | Obrigatório após `trim`; não enviar vazio. |
| `limit` | `number` | Inteiro entre 1 e 20; iniciar em 5, padrão da API. |
| `minScore` | `number \| null` | `null` omite o campo; quando preenchido, de 0 a 1. |
| `categoryIds` | `number[]` | IDs únicos e positivos; semântica ANY na dimensão. |
| `tagIds` | `number[]` | IDs únicos e positivos; semântica ANY na dimensão. |
| `projectIds` | `number[]` | IDs únicos e positivos; semântica ANY na dimensão. |
| `includeMatchReasons` | `boolean` | Enviar `true` apenas quando habilitado. |

Categorias, tags e projetos são combinados por AND no backend.

## AnswerResult

| Campo | Tipo/origem | Exibição |
| --- | --- | --- |
| `query` | `KnowledgeAnswerResponse.query` | Pergunta normalizada que originou o resultado. |
| `answer` | `KnowledgeAnswerResponse.answer` | Texto simples; nunca interpretar como HTML. |
| `sources` | `KnowledgeAnswerResponse.sources` | Cartões de auditoria; pode ser lista vazia. |
| `createdAt` | estado local | Ordenação somente do histórico em memória; não persistir. |

Cada fonte reutiliza `KnowledgeChunk`: `source_id` para navegação, `source_title`, `content`, `location`, metadados, `score` opcional e `match_reasons` opcional.

## AnswerHistoryEntry

| Campo | Tipo | Regras |
| --- | --- | --- |
| `id` | `string` local | Chave de renderização; nunca é enviada à API. |
| `request` | `AnswerQuery` | Snapshot normalizado da submissão válida. |
| `result` | `AnswerResult` | Somente sucesso; não armazenar erros ou dados de autenticação. |

O histórico é uma lista em memória da rota. É apagado ao destruir/recarregar a aplicação e não usa storage do navegador.

## AnswerViewState

| Estado | Dados permitidos | Comportamento |
| --- | --- | --- |
| `idle` | formulário e histórico eventual | Não mostrar mensagem de resultado inicial. |
| `loading` | formulário e resultado anterior | Desabilitar envio duplicado e anunciar progresso. |
| `success` | resposta e fontes | Mostrar resposta e seção de fontes. |
| `success-without-sources` | resposta, `sources: []` | Explicar ausência de fontes auditáveis. |
| `validation-error` | formulário | Associar erro ao campo inválido sem chamar API. |
| `request-error` | formulário e erro seguro | Preservar valores e oferecer nova tentativa. |
| `copy-feedback` | resposta/referências e mensagem transitória | Anunciar sucesso ou falha da cópia sem mudar resultado. |
