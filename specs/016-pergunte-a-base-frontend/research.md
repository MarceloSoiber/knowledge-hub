# Research: Pergunte à Base no Frontend

## Decision: consumir o endpoint de resposta já publicado

**Rationale**: `POST /api/v1/knowledge/answer` aceita pergunta, limite, filtros de categoria/tag/projeto, score mínimo e diagnóstico opcional; devolve texto e os chunks efetivamente usados como fontes. A feature pode ser inteiramente Angular, sem endpoint agregador.

**Alternatives considered**:

- Criar endpoint específico para a tela: rejeitado; duplicaria o contrato de RAG e ampliaria backend sem necessidade.
- Montar resposta no navegador chamando `/search`: rejeitado; exporia decisão de prompt/LLM ao cliente e não atende ao fluxo RAG existente.

## Decision: manter formulário, resultado e histórico como estado local

**Rationale**: O requisito exige histórico apenas durante a sessão. Estado no componente/feature é suficiente, é automaticamente perdido no reload e não introduz risco de retenção de conteúdo ou token.

**Alternatives considered**:

- `localStorage` ou `sessionStorage`: rejeitado; sobreviveriam a reload/navegação e violariam o descarte requerido.
- Biblioteca global de estado: rejeitado; aumenta complexidade para uma feature isolada e não entrega valor adicional.

## Decision: reutilizar o padrão de filtros da busca

**Rationale**: Categorias, projetos e tags usam os mesmos endpoints e a mesma semântica de IDs. O autocomplete de tags com `debounceTime`, `distinctUntilChanged` e `switchMap` reduz chamadas e evita sugestões obsoletas.

**Alternatives considered**:

- Carregar todas as tags e filtrar no cliente: rejeitado; não escala e ignora endpoint dedicado.
- Duplicar seletor e cliente HTTP diretamente no template: rejeitado; fragmenta manutenção e viola o limite de `core/`.

## Decision: tratar resposta sem fontes como sucesso explicitamente rotulado

**Rationale**: O contrato permite `sources: []` quando nenhum chunk passa o limiar, ainda que o LLM devolva uma resposta. A UI precisa preservar essa distinção para não criar falsa auditabilidade.

**Alternatives considered**:

- Converter em erro: rejeitado; a requisição foi aceita e a resposta pode ser útil para indicar ausência de contexto.
- Ocultar a seção de fontes sem explicação: rejeitado; não permite à pessoa identificar que a resposta não tem sustentação recuperada.

## Decision: cópia com Clipboard API e retorno acessível

**Rationale**: `navigator.clipboard.writeText` é a API padrão em contexto seguro. Uma abstração de cópia permite mostrar confirmação via região ARIA e, quando a permissão/API não existir, informar a falha sem alterar o conteúdo exibido ou registrar texto.

**Alternatives considered**:

- Exigir seleção manual do texto: rejeitado; não cumpre a ação explícita de copiar.
- Inserir conteúdo em HTML/Markdown para copiar: rejeitado; amplia superfície de interpretação de dados não confiáveis.

## Decision: mapear falhas por status HTTP sem usar detalhes crus

**Rationale**: O backend devolve `403` para conteúdo sensível bloqueado, `422` para payload inválido e `502`/`503` para falhas de embeddings/LLM ou indisponibilidade. Mensagens por classe dão próximo passo sem vazar detalhes de configuração ou conteúdo.

**Alternatives considered**:

- Exibir `error.detail` diretamente: rejeitado por segurança, instabilidade e experiência pouco acionável.
- Uma única mensagem genérica: rejeitado porque não distingue bloqueio, correção de filtros e indisponibilidade temporária.
