# Research: Organização do acervo no frontend

## Decision: concentrar leituras e invalidações em um catálogo compartilhado leve

**Rationale**: Categorias, tags e projetos são usados por Busca, Pergunte à base, Ingestão, Biblioteca e detalhe. Um serviço `MetadataCatalogService` baseado em signals mantém o HTTP em `KnowledgeApiService`, fornece os valores atuais aos componentes e aplica diretamente as respostas de mutação, sem reload global.

**Alternatives considered**:

- Cada feature recarregar seus metadados após toda mutação: rejeitado por chamadas duplicadas, telas desatualizadas e por não cumprir atualização de controles já montados.
- Adicionar NgRx/biblioteca externa: rejeitado; o estado é pequeno, efêmero e não requer persistência ou fluxo global complexo.

## Decision: reutilizar um componente genérico de manutenção para categorias e tags

**Rationale**: ambos têm o mesmo contrato de nome e ciclo listar/criar/renomear/excluir. O componente recebe rótulos e callbacks tipados; `OrganizationPageComponent` concentra as regras de organização e `core` mantém HTTP.

**Alternatives considered**:

- Duplicar componentes de categoria e tag: rejeitado por duplicar diálogo, validação e mapeamento de erros.
- Misturar CRUD no `MetadataSelectorComponent`: rejeitado; o seletor deve continuar focado em escolha de metadados.

## Decision: evoluir o seletor compartilhado com autocomplete de tags

**Rationale**: ingestão e detalhe já consomem o seletor. Debounce curto, `switchMap`, mínimo de caracteres e comparação da consulta evitam requests excessivos e respostas fora de ordem; sugestões complementam, não substituem, tags já selecionadas.

**Alternatives considered**:

- Filtrar somente a lista carregada: não garante o endpoint de autocomplete exigido e degrada para catálogos maiores.
- Criar um autocomplete em cada formulário: rejeitado por inconsistência e repetição.

## Decision: tratar arquivamento como transição imediata do catálogo

**Rationale**: `POST /archive` e `/reactivate` devolvem o projeto canônico. Substituí-lo no catálogo e derivar `activeProjects` garante que seletores ativos não mostrem itens arquivados, sem ocultar a associação histórica retornada nas fontes.

**Alternatives considered**:

- Remover localmente antes da resposta: rejeitado; falha deixaria a UI divergente do servidor.
- Recarregar toda a aplicação: rejeitado por ser desnecessário e prejudicar rascunhos.
