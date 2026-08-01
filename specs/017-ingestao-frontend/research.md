# Research: Ingestão de Conhecimento no Frontend

## Decision: reutilizar o cliente HTTP e os contratos já existentes

**Rationale**: `KnowledgeApiService` já expõe `upload`, `ingestText`, `categories`, `tags` e `projects`, e `knowledge.types.ts` já define os payloads e `KnowledgeUploadResponse`. A feature deve coordenar formulário e apresentação, sem duplicar URLs, serialização ou tipos.

**Alternatives considered**:

- Chamar `HttpClient` diretamente no componente: rejeitado; fragmenta tratamento de autenticação e manutenção do contrato.
- Criar endpoint agregador específico para a tela: rejeitado; os dois endpoints existentes já satisfazem o fluxo.

## Decision: validar localmente apenas limites públicos e manter o backend como autoridade

**Rationale**: A API documenta `.txt`, `.md`, `.pdf` e 10 MB, além das regras de título, texto e IDs. Validar esses limites dá resposta imediata; o backend ainda trata conteúdo extraído vazio, MIME inesperado, metadados obsoletos e limite definitivo.

**Alternatives considered**:

- Não validar no navegador: rejeitado; causaria requisições evitáveis e feedback tardio.
- Reproduzir parsing/OCR ou validar conteúdo de PDF no cliente: rejeitado; diverge do processamento do servidor e amplia o escopo.

## Decision: formulário por aba com estado independente em memória

**Rationale**: Arquivo e texto possuem campos e serializações distintas. Estados separados evitam que uma resposta limpe ou bloqueie o outro fluxo e preservam rascunhos ao alternar de aba, sem persistir arquivos ou conteúdo após reload.

**Alternatives considered**:

- Um único formulário polimórfico: rejeitado; aumenta condicionais e torna validação e preservação de campos mais frágeis.
- Persistir rascunhos em storage: rejeitado; não foi solicitado e pode reter conteúdo sensível localmente.

## Decision: processamento indeterminado e bloqueio apenas do fluxo enviado

**Rationale**: A API responde somente depois de extrair, dividir, gerar embeddings e gravar; ela não publica percentuais. O botão e controles da aba submetida ficam bloqueados para prevenir duplicidade, enquanto a mensagem ARIA explica o processamento. Não haverá porcentagem simulada.

**Alternatives considered**:

- Barra de progresso estimada: rejeitada; seria enganosa.
- Permitir reenvio enquanto a chamada está pendente: rejeitado; pode criar concorrência e mensagens ambíguas.

## Decision: reconhecer duplicidade pelo contrato estruturado de 409

**Rationale**: O backend devolve `409` com `detail.message` e `detail.existing_source_id`. O cliente deve extrair somente esse UUID e construir `/sources/:sourceId`; ausência ou formato inesperado do campo resulta em mensagem de duplicidade sem link.

**Alternatives considered**:

- Usar texto do erro para extrair um ID: rejeitado; é frágil e pode expor detalhe interno.
- Sobrescrever/mesclar a fonte existente: rejeitado; contraria o escopo e requer confirmação/contrato de atualização.

## Decision: reutilizar seletor de metadados com adaptação mínima para erro por formulário

**Rationale**: O `MetadataSelectorComponent` já recebe listas, seleção, obrigatoriedade, carregamento, desabilitação e erro. A feature deve passar o estado de cada aba e manter labels/contexto apropriados, ajustando o compartilhado apenas se necessário para associar erro de categorias ao formulário.

**Alternatives considered**:

- Duplicar três selects por aba: rejeitado; cria divergência de acessibilidade e manutenção.
- Criar tags/projetos inline: rejeitado; está fora do escopo e amplia mutações.
