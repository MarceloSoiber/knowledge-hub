# Research: Dashboard inicial do acervo

## Decision: compor o resumo exclusivamente dos endpoints já publicados

**Rationale**: `sources`, `categories`, `tags` e `projects` já devolvem todos os dados necessários. Mantê-los em `KnowledgeApiService` preserva a camada HTTP estabelecida e evita uma alteração de backend apenas para cinco números e uma pequena lista.

**Alternatives considered**:

- Criar `GET /dashboard` agregado: rejeitado; amplia API, testes e documentação sem necessidade funcional no escopo atual.
- Reaproveitar a lista da Biblioteca como estado global: rejeitado; ela é local à feature e não é uma fonte de verdade compartilhada.

## Decision: carregar cada coleção de forma independente

**Rationale**: O requisito pede que dados secundários não bloqueiem a navegação. Requisições independentes permitem apresentar fontes, métricas e erros/retry por área assim que cada resposta chega.

**Alternatives considered**:

- Um `forkJoin` único para todas as listas: rejeitado; uma falha atrasa ou invalida todo o resumo e dificulta retry localizado.
- Resolver dados na rota: rejeitado; bloquearia a entrada no Dashboard até todas as respostas terminarem.

## Decision: ordenar fontes recentes no cliente por data canônica, com desempate estável

**Rationale**: A API ainda não oferece ordenação. `created_at` representa a entrada no acervo; `updated_at` é fallback razoável. Datas inválidas ficam ao fim e título/UUID tornam o resultado determinístico.

**Alternatives considered**:

- Assumir a ordem retornada pela API: rejeitado; não atende ao plano e pode variar entre execuções.
- Ordenar por `updated_at` sempre: rejeitado; uma edição faria uma fonte antiga parecer recém-ingerida.

## Decision: manter a página inicial e a feature em `features/home`

**Rationale**: A rota `/inicio` e o componente provisório já existem. Evoluí-los evita uma rota paralela e mantém o layout autenticado inalterado.

**Alternatives considered**:

- Criar uma rota `/dashboard`: rejeitado; duplicaria o destino inicial e alteraria desnecessariamente os links existentes.
- Colocar lógica de dados no layout autenticado: rejeitado; o layout deve continuar responsável somente por navegação e sessão.
