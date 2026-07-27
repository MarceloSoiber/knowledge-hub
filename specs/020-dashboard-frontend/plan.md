# Implementation Plan: Dashboard inicial do acervo

**Branch**: `020-dashboard-frontend` | **Date**: 2026-07-27 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification based on `plan/frontend/07-dashboard.md`

## Summary

Substituir a página inicial provisória por um Dashboard Angular privado que apresente um resumo do acervo: cinco métricas, até cinco fontes recentes e atalhos para Busca, Pergunte à base e Ingestão. O componente consumirá os quatro endpoints já expostos por `KnowledgeApiService`, carregando cada coleção independentemente para preservar navegação e dados já disponíveis diante de atraso ou falha parcial. Não haverá mudança de API, persistência, autenticação, MCP ou backend.

## Technical Context

**Language/Version**: TypeScript 6.0, Angular 22.0; FastAPI existente somente como contrato  
**Primary Dependencies**: Angular standalone components, Router/RouterLink, `HttpClient` via `KnowledgeApiService`, RxJS; `LoadingState`, `ErrorState` e `EmptyState` compartilhados  
**Storage**: Estado efêmero local do Dashboard; PostgreSQL + pgvector inalterados  
**Testing**: Angular unit tests com Vitest/TestBed e `HttpTestingController`; `npm run typecheck`, `npm test -- --watch=false`, `npm run build`  
**Target Platform**: Navegadores modernos desktop/mobile; Angular servido por Nginx  
**Project Type**: Aplicação web Angular que consome uma API FastAPI  
**Performance Goals**: Até quatro leituras independentes na entrada; cartões apresentam dados assim que disponíveis; no máximo cinco itens recentes; endpoints respondem em até 1 s em condição normal  
**Constraints**: Tipagem estrita, sem bloquear rota/navegação, sem estado global novo, acessível a partir de 320 px, texto remoto nunca como HTML  
**Scale/Scope**: Uma rota existente (`/inicio`), uma feature de tela e testes; sem paginação, agregação no servidor, gráficos ou realtime

## Constitution Check

### Pre-design gate

- **Code quality**: PASS — URLs e contratos permanecem em `core/knowledge-api.service.ts`; apresentação e derivação ficam em `features/home`; o layout autenticado não recebe lógica de acervo.
- **Testing standards**: PASS — o plano cobre HTTP existente quando necessário, métricas, ordenação, vazio, falhas independentes e links, além dos quality gates Angular.
- **UX/accessibility**: PASS — usa seções/links semânticos, estados compartilhados, `aria-live` nos estados e comportamento responsivo com acesso por teclado.
- **Performance**: PASS — carrega apenas coleções publicadas, limita a lista visual e não altera embeddings, pgvector ou busca; chamadas independentes evitam uma barreira global de carregamento.
- **Technology/documentation**: PASS — Angular/TypeScript consome contratos existentes; nenhum endpoint muda, portanto `doc/API.md` não muda.

### Post-design re-check

PASS. O [modelo local](data-model.md) e o [contrato](contracts/frontend-dashboard.md) reutilizam exclusivamente os endpoints existentes e não introduzem complexidade que viole a constituição.

## Project Structure

### Documentation (this feature)

```text
specs/020-dashboard-frontend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── frontend-dashboard.md
```

### Source Code (repository root)

```text
frontend/
└── src/
    └── app/
        ├── core/
        │   ├── knowledge-api.service.ts            # fontes e metadados já tipados
        │   └── knowledge-api.service.spec.ts        # ampliar somente se faltar cobertura de GET
        ├── features/
        │   └── home/
        │       ├── home.component.ts                # orquestração, estado e derivados
        │       ├── home.component.html              # métricas, recentes, atalhos e estados
        │       ├── home.component.css               # grade responsiva e estilos locais
        │       └── home.component.spec.ts           # cenários do Dashboard
        ├── layout/
        │   └── authenticated-layout.component.*     # permanece inalterado, salvo ajuste visual realmente necessário
        └── shared/
            ├── loading-state/
            ├── error-state/
            └── empty-state/
```

**Structure Decision**: a rota `/inicio` e `HomeComponent` existentes evoluem para o Dashboard. O componente é dono do estado efêmero de suas quatro coleções; `KnowledgeApiService` continua sendo o único ponto de HTTP. Não é necessário criar serviço, store ou componente genérico de métricas para uma única tela.

## Implementation Approach

### 1. Confirmar e manter a fronteira HTTP existente

- Reutilizar `KnowledgeApiService.sources()`, `categories()`, `tags()` e `projects()`; não chamar `HttpClient` diretamente de `HomeComponent`.
- Conferir que os tipos `KnowledgeSource`, `Category`, `Tag` e `Project` já cobrem os campos necessários. Não introduzir payloads nem alterar caminhos.
- Se a cobertura atual de `KnowledgeApiService` não validar os quatro GETs, acrescentar testes concisos com `HttpTestingController`; não reestruturar testes não relacionados.

### 2. Transformar a página inicial em Dashboard de carregamento independente

- Substituir o placeholder de `features/home/home.component.ts` por componente standalone com template e CSS externos, preservando a rota e o título `/inicio` existentes.
- Modelar o estado por coleção (`loading`, `error`, `items`) para fontes, categorias, tags e projetos. Disparar as quatro leituras no `ngOnInit` sem resolver de rota e sem `forkJoin` que condicione a página inteira.
- Fornecer métodos de retry por coleção. Antes de cada nova tentativa, limpar apenas o erro correspondente e conservar dados válidos até a resposta de sucesso; falhas não devem zerar uma métrica.
- Usar `ChangeDetectorRef.markForCheck()` se a estratégia de detecção existente o exigir, seguindo o padrão das features atuais.

### 3. Derivar métricas e fontes recentes de forma determinística

- Criar valores derivados para: total de fontes, categorias, tags, projetos ativos e projetos arquivados. Cada métrica usa apenas a lista canônica já carregada, sem contagem inventada durante erro.
- Ordenar uma cópia de `sources`, nunca a lista original: `created_at` válido em ordem decrescente; `updated_at` somente quando não houver `created_at` válido; itens sem data válida ao fim; título normalizado e `source_id` como desempate estável. Limitar o resultado a cinco.
- Extrair o comparador para função pura local/exportável quando isso facilitar o teste de datas nulas, inválidas e empates; manter a regra fora do template.

### 4. Construir a interface, atalhos e estados vazios

- Renderizar cabeçalho da página, uma grade semântica de cartões e uma seção de fontes recentes. Cada cartão/área deve expressar carregamento, valor, falha e retry de forma acessível; não mostrar `0` enquanto o endpoint falhou ou ainda está pendente.
- Exibir fontes recentes com `RouterLink` para `/sources/:sourceId`, título, tipo e data segura; a lista é omitida quando fontes ainda não carregaram ou falharam.
- Quando fontes terminarem vazias, apresentar `EmptyStateComponent` com link/botão para `/ingestao`; metadados vazios permanecem métricas `0` normais.
- Criar três atalhos em links reais para `/busca`, `/perguntar` e `/ingestao`, sempre renderizados e operáveis durante qualquer carregamento. Usar labels claros, foco visível e uma grade que se adapte de uma coluna em 320 px até desktop.

### 5. Cobrir comportamento, acessibilidade e regressões

- Criar `home.component.spec.ts` para verificar as quatro chamadas independentes, as cinco contagens, projeto ativo/arquivado, lista limitada e ordenada, empates/datas inválidas, links e estado vazio.
- Testar falha/retry de fontes e de uma coleção de metadados sem bloquear os atalhos ou invalidar dados das demais áreas. Validar que sucesso vazio é distinto de erro.
- Verificar manualmente landmarks, hierarquia de títulos, regiões de status, teclado, foco, leitor de tela e layouts de 320 px, 768 px e desktop segundo o [quickstart](quickstart.md).
- Executar `npm run typecheck`, `npm test -- --watch=false` e `npm run build` em `frontend/`.

## Data Model / API Implications

- Não há migração, código Python, rota FastAPI, schema Pydantic, MCP, OpenAPI ou alteração de `doc/API.md`.
- O estado local é documentado em [data-model.md](data-model.md); `KnowledgeSource`, `Category`, `Tag` e `Project` existentes continuam canônicos.
- A interface consome os quatro GETs definidos em [frontend-dashboard.md](contracts/frontend-dashboard.md). Não há novo contrato nem parâmetros de consulta.
- A ordenação de recentes é deliberadamente cliente-side enquanto a API não oferece ordenação. O Dashboard não deve inferir ordenação no servidor.

## Test Strategy

- **Core**: somente ampliar testes HTTP caso algum dos quatro GETs ainda não esteja coberto; preservar os contratos existentes.
- **Dashboard unitário**: carga independente, métricas, separação ativo/arquivado, ordenação/fallback/limite de recentes, vazio, falha e retry.
- **Integração de template/rota**: links para detalhe, Busca, Pergunte e Ingestão; atalhos visíveis antes de todas as respostas.
- **Acessibilidade/manual**: HTML semântico, `aria-live`, foco, navegação por teclado, contraste e responsividade em 320 px, 768 px e desktop.
- **Quality gate**: `npm run typecheck`, `npm test -- --watch=false`, `npm run build` em `frontend/`.

## Risk Notes

- Quatro listas completas na entrada podem deixar de ser adequadas para acervos grandes. Antes dessa escala, preferir endpoint agregado/paginação deliberadamente projetados, não esconder o custo no cliente.
- `created_at` pode ser nulo ou inválido em dados legados. O comparador precisa ser puro e determinístico para evitar oscilação visual e testes frágeis.
- Uma falha parcial não pode ser representada como zero, pois isso induz decisão errada sobre o acervo. O estado do cartão precisa distinguir `loading`, `error` e lista vazia bem-sucedida.
- O Dashboard não deve duplicar filtros, detalhe ou manutenção da Biblioteca/Organização; seus links devem conduzir aos fluxos canônicos.

## Complexity Tracking

Nenhuma violação da constituição identificada.
