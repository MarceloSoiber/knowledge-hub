# Contract: Frontend Ingestion Integration

## API base

Todos os caminhos são relativos a `/api/v1/knowledge`, autenticados pelos interceptores da fundação e chamados por `KnowledgeApiService`.

## Metadados

| Necessidade | Método e caminho | Uso |
| --- | --- | --- |
| Categorias | `GET /categories` | Obrigatórias para ambos os formulários. |
| Tags | `GET /tags` | Opcionais; seleção múltipla. |
| Projetos | `GET /projects` | Opcionais; seleção múltipla. |

As listas são carregadas uma vez ao abrir a feature (ou novamente por ação explícita). IDs selecionados devem ser únicos e positivos.

## Envio de arquivo

`POST /uploads` com `multipart/form-data`.

| Campo | Representação | Regra |
| --- | --- | --- |
| `file` | um `File` | `.txt`, `.md` ou `.pdf`; até 10 MB. |
| `category_ids` | campo repetido | Um ou mais IDs. |
| `tag_ids` | campo repetido opcional | Um ou mais IDs quando selecionados. |
| `project_ids` | campo repetido opcional | Um ou mais IDs quando selecionados. |

Não definir manualmente o cabeçalho `Content-Type`: o navegador deve incluir o boundary do `FormData`.

## Envio de texto

`POST /texts` com JSON.

```json
{
  "title": "Ata da reunião",
  "content": "Decisões registradas durante a reunião.",
  "category_ids": [2, 3],
  "tag_ids": [1],
  "project_ids": [4]
}
```

`title`, `content` e `category_ids` são obrigatórios. Arrays opcionais vazios devem ser omitidos.

## Resposta de sucesso

Ambos os endpoints retornam `201 Created`:

```json
{
  "source_id": "33333333-3333-4333-8333-333333333333",
  "title": "Ata da reunião",
  "categories": [{"id": 2, "name": "financeiro"}],
  "tags": [],
  "projects": [],
  "chunks_created": 1
}
```

A confirmação mostra `title`, `source_id` e `chunks_created`, além do link `/sources/{source_id}`. Nenhum ID interno ou URI local deve ser apresentado.

## Erros tratados pela UI

| Status | Tratamento |
| --- | --- |
| `400` | Informar que arquivo/texto não pôde ser aceito ou está vazio; manter o rascunho. |
| `401` | A fundação encerra a sessão e redireciona ao login. |
| `404` | Informar que algum metadado não existe mais e oferecer recarga das listas. |
| `409` | Extrair `error.detail.existing_source_id`; explicar duplicidade e oferecer link à fonte existente quando o UUID for válido. |
| `413` | Informar que o arquivo excede 10 MB e não reenviar automaticamente. |
| `422` | Informar para revisar campos/metadados; manter o rascunho. |
| `502`, `503` | Informar indisponibilidade temporária de embeddings/serviço e oferecer nova tentativa; não expor configuração ou corpo bruto. |

O backend pode rejeitar entradas que passaram na validação do navegador. A UI não sobrescreve fontes e não interpreta conteúdo ou mensagens remotas como HTML.
