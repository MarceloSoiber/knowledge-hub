# Data Model: Ingestão de Conhecimento no Frontend

Esta feature não cria tabelas, migrações ou persistência. Os modelos abaixo representam estado local e contratos HTTP existentes.

## IngestionMetadata

| Campo | Tipo | Regras |
| --- | --- | --- |
| `categoryIds` | `number[]` | Obrigatório; lista não vazia de IDs positivos, únicos e presentes nos metadados carregados. |
| `tagIds` | `number[]` | Opcional; IDs positivos e únicos. Omitir no JSON/form-data quando vazio. |
| `projectIds` | `number[]` | Opcional; IDs positivos e únicos. Omitir no JSON/form-data quando vazio. |

## FileIngestionDraft

| Campo | Tipo | Regras |
| --- | --- | --- |
| `file` | `File \| null` | Obrigatório para envio; extensão `.txt`, `.md` ou `.pdf` sem distinção de maiúsculas; tamanho máximo de `10 * 1024 * 1024` bytes. |
| `metadata` | `IngestionMetadata` | Metadados enviados como campos `FormData` repetidos. |

O objeto `File` não é serializado fora do `FormData` e não é persistido. Após sucesso, limpar a seleção conforme restrições do navegador; após falha, manter o arquivo se o controle ainda o suportar, ou explicar quando a plataforma exigir nova seleção.

## TextIngestionDraft

| Campo | Tipo | Regras |
| --- | --- | --- |
| `title` | `string` | Obrigatório após `trim`; no máximo 255 caracteres normalizados. |
| `content` | `string` | Obrigatório após `trim`; apresentado/enviado como texto simples. |
| `metadata` | `IngestionMetadata` | Serializado em `category_ids`, `tag_ids` e `project_ids`. |

## IngestionResult

| Campo | Tipo/origem | Uso na interface |
| --- | --- | --- |
| `source_id` | `KnowledgeUploadResponse.source_id` | UUID público para link `/sources/:sourceId`. |
| `title` | `KnowledgeUploadResponse.title` | Título da confirmação. |
| `chunks_created` | `KnowledgeUploadResponse.chunks_created` | Quantidade de chunks criada. |
| `categories`, `tags`, `projects` | `KnowledgeUploadResponse` | Contexto opcional da confirmação; não é necessário reenviar. |

## IngestionViewState

| Estado | Dados permitidos | Comportamento |
| --- | --- | --- |
| `idle` | rascunho | Pronto para edição e envio. |
| `validation-error` | rascunho, erros por campo | Não chama API; associa mensagem a campo/fieldset. |
| `submitting` | snapshot enviado, rascunho | Exibe processamento indeterminado e bloqueia novo envio no fluxo correspondente. |
| `success` | `IngestionResult` | Mostra confirmação e link; limpa somente o rascunho concluído. |
| `duplicate` | rascunho, `existingSourceId?` | Mostra duplicidade e link somente se o UUID estruturado estiver disponível. |
| `request-error` | rascunho, mensagem segura | Preserva dados para nova tentativa. |

## DuplicateConflict

| Campo | Tipo | Regra |
| --- | --- | --- |
| `existingSourceId` | `string \| null` | Extraído exclusivamente de `HttpErrorResponse.error.detail.existing_source_id`; validar UUID antes de gerar URL. |
| `message` | `string` | Mensagem local segura; não apresentar `detail.message` cru. |
