# Research: Biblioteca e manutenção de fontes

## Decision: Reutilizar os contratos HTTP existentes no cliente

**Rationale**: `GET /sources`, `GET/PATCH/DELETE /sources/{source_id}` já existem no backend e usam UUID público. `KnowledgeApiService` e os tipos de leitura já concentram o cliente HTTP; adicionar os métodos tipados de atualização e exclusão preserva essa fronteira.

**Alternatives considered**:

- Chamar `HttpClient` diretamente nos componentes: rejeitado por duplicar URL, serialização e tratamento de resposta.
- Criar endpoints específicos de frontend: rejeitado, pois não acrescentaria capacidade ao contrato atual.

## Decision: Aplicar pesquisa e filtros em memória sobre a listagem

**Rationale**: O endpoint atual não aceita filtros. O escopo exige busca *local* por título e filtros visuais; normalizar texto para minúsculas sem diacríticos e comparar IDs das associações atende ao requisito sem alterar API.

**Alternatives considered**:

- Estender `GET /sources` com query params: fora de escopo e exigiria mudança/documentação de API.
- Filtrar somente o texto renderizado: rejeitado por não ser tipado e ser frágil para metadados.

## Decision: Manter `/sources/:sourceId` como detalhe único e adicionar `/biblioteca` como listagem

**Rationale**: Busca e ingestão já apontam para o detalhe por UUID. Evoluir o componente existente evita rotas duplicadas e garante que a fonte aberta em qualquer fluxo tenha as mesmas ações de manutenção.

**Alternatives considered**:

- Criar um segundo detalhe sob `/biblioteca/:id`: rejeitado por duplicar UI e criar URLs concorrentes.
- Colocar edição diretamente em cada item da lista: rejeitado por esconder conteúdo e tornar exclusão menos segura.

## Decision: PATCH mínimo a partir de um baseline imutável

**Rationale**: O schema exige ao menos um campo e associações opcionais têm semântica importante: `undefined` preserva, array vazio remove todas. Comparar o rascunho com a resposta inicial permite enviar somente mudanças intencionais e impede PATCH vazio.

**Alternatives considered**:

- Enviar todos os campos sempre: aumenta risco de sobrescrever dados alterados e não separa mudanças de metadados/conteúdo.
- Enviar um PATCH por controle: gera requisições parciais e estados intermediários difíceis de recuperar.

## Decision: Avisar sobre reprocessamento no formulário, não com uma segunda confirmação obrigatória

**Rationale**: A edição de conteúdo precisa informar claramente o custo/efeito, mas o plano só exige confirmação explícita para exclusão. Um aviso persistente que aparece ao detectar diferença no conteúdo mantém o fluxo objetivo e acessível.

**Alternatives considered**:

- Diálogo extra ao salvar conteúdo: adiciona atrito sem ser requisito.
- Omitir o aviso: não atende à transparência exigida.

## Decision: Usar `ConfirmDialogComponent` para exclusão e somente enviar `confirm=true` no evento confirm

**Rationale**: O componente compartilhado já oferece diálogo modal, Escape e foco inicial seguro. O estado `deleteDialogOpen` é a barreira entre o clique inicial e a única chamada DELETE.

**Alternatives considered**:

- `window.confirm`: não fornece experiência/semântica consistente nem é testável de forma equivalente.
- Enviar DELETE antes do diálogo: viola a garantia de confirmação explícita.
