# Data Model: Qualidade, segurança e evolução do frontend

Não há mudança de banco ou modelos FastAPI. Os modelos abaixo definem artefatos de teste e comportamento cliente.

## QualityMatrixEntry

| Campo | Tipo | Regra |
| --- | --- | --- |
| `flow` | `login \| search \| ask \| ingestion \| library \| source-detail \| dashboard \| organization` | Fluxo público verificável. |
| `automatedStates` | conjunto de estados | Inclui sucesso e loading/vazio/erro aplicáveis. |
| `httpContract` | lista de requisições | Método, URL, parâmetros e payload verificados por `HttpTestingController`. |
| `manualChecks` | conjunto de viewport/teclado/leitor | Não substitui os testes automatizados. |
| `risk` | segurança, reversibilidade ou regressão | Determina prioridade de cobertura. |

## Safe UI Error

| Campo | Tipo | Regra |
| --- | --- | --- |
| `kind` | `ApiErrorKind` existente | Classificação local por status HTTP. |
| `status` | `number` | Conservado para decisão lógica/teste; não precisa ser apresentado. |
| `message` | `string` local | Nunca derivada do HTML ou texto bruto de `error.error`. |
| `action` | retry, revisar, login ou nenhuma | Definida pela feature após a classificação genérica. |

## SessionState

| Campo | Tipo | Regra |
| --- | --- | --- |
| `token` | `string \| null` | Somente enviado ao prefixo protegido; nunca exibido/logado. |
| `status` | `checking \| unauthenticated \| authenticated \| error` | Estado já definido por `AuthService`. |
| `rememberToken` | `boolean` | Controla somente a persistência local já existente. |
| `returnUrl` | `string` validada | Aceita apenas caminho local simples, não `//` nem `/login`. |

## API Evolution Proposal

| Capacidade | Contrato mínimo a especificar depois | Consumidor inicial |
| --- | --- | --- |
| Fontes paginadas/ordenadas/filtradas | cursor ou página, ordem explícita, filtros e total opcional | Biblioteca/Dashboard |
| Estatísticas agregadas | resumo autenticado com escopo, tempo de cálculo e ausência de duplicação | Dashboard |
| Ingestão assíncrona | `job_id`, estados, progresso, erro seguro e política de polling | Ingestão |
| Arquivo original | permissão, metadados, URL temporária ou stream e retenção | Detalhe de fonte |
| Categoria enriquecida | descrição, flag de sensibilidade e regras de edição | Organização |
