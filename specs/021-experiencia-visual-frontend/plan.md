# Implementation Plan: Experiência visual e usabilidade do frontend

**Branch**: `021-experiencia-visual-frontend` | **Date**: 2026-07-28 | **Spec**: [`spec.md`](spec.md)

**Input**: Planejamento para tornar o frontend mais bonito e intuitivo.

## Summary

Evoluir a aplicação Angular para uma experiência visual coesa e mais simples de operar, sem tocar em backend ou contratos. A entrega começa pela consolidação de design tokens e primitives CSS, reforça o shell autenticado como orientação do produto e migra os fluxos existentes em lotes: descoberta (Início/Busca/Pergunte), execução (Ingestão/Biblioteca) e manutenção (Organização/Detalhe). A prioridade é legibilidade, hierarquia de ação, estados explícitos, acessibilidade e responsividade, não ornamentação.

## Technical Context

**Language/Version**: TypeScript 6.0, Angular 22.0, CSS nativo  
**Primary Dependencies**: Angular standalone components, Router/RouterLink/RouterLinkActive, Forms, componentes compartilhados existentes; sem nova dependência  
**Storage**: Preferência de tema em `localStorage`; estado efêmero existente e PostgreSQL + pgvector inalterados  
**Testing**: Vitest/TestBed; `npm run typecheck`, `npm test -- --watch=false`, `npm run build`  
**Target Platform**: Navegadores modernos em mobile, tablet e desktop; app Angular servida por Nginx  
**Project Type**: Aplicação web Angular consumindo API FastAPI existente  
**Performance Goals**: Não adicionar requisições, bloqueios de rota ou assets pesados; interação de menu e feedback percebidos imediatamente  
**Constraints**: 320 px a desktop, sem rolagem horizontal indevida, HTML semântico, teclado, foco visível, redução de movimento, sem mudanças de API/autenticação  
**Scale/Scope**: Shell autenticado, tokens globais, componentes compartilhados e sete superfícies de UI; migração incremental sem reescrita de recursos

## Constitution Check

### Pre-design gate

- **Code quality**: PASS — a lógica de domínio e HTTP permanece em serviços/componentes atuais; a mudança se limita a composição e estilo de frontend tipado.
- **Testing standards**: PASS — o plano prevê testes de shell, estados e regressões dos componentes alterados, além dos gates Angular exigidos.
- **UX/accessibility**: PASS — o objetivo central atende simplicidade, responsividade, feedback claro, semântica e ARIA previstos pela constituição.
- **Performance**: PASS — não há endpoints ou bibliotecas novas; CSS e componentes compartilhados reduzem duplicação sem criar custo de rede.
- **Technology/documentation**: PASS — continua Angular/TypeScript e não altera API, portanto `doc/API.md` não muda.

### Post-design re-check

PASS. Os [tokens e padrões](data-model.md), o [contrato de interação](contracts/frontend-experience.md) e o [guia de validação](quickstart.md) preservam as fronteiras da aplicação e não introduzem dados, dependências ou contratos novos.

## Project Structure

### Documentation (this feature)

```text
specs/021-experiencia-visual-frontend/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── frontend-experience.md
```

### Source Code (repository root)

```text
frontend/src/
├── styles.css                                      # tokens, reset e primitives globais
└── app/
    ├── layout/
    │   └── authenticated-layout.component.*        # salto, navegação e menu responsivo
    ├── shared/
    │   ├── loading-state/
    │   ├── empty-state/
    │   ├── error-state/
    │   ├── confirm-dialog/
    │   └── metadata-selector/                      # contratos visuais compartilhados
    └── features/
        ├── home/
        ├── search/
        ├── ask/
        ├── ingestion/
        ├── library/
        ├── organization/
        └── source-detail/                          # composição de cada fluxo
```

**Structure Decision**: centralizar somente tokens e primitives realmente compartilhados em `styles.css` e `shared/`; manter o layout e os detalhes de cada jornada na feature correspondente. Não será criado store, camada de negócio, biblioteca de UI externa ou duplicação de chamadas HTTP.

## Implementation Approach

### 1. Estabelecer a fundação visual

- Ampliar `frontend/src/styles.css` para incluir tokens semânticos completos: superfícies, texto, estados, foco, tipografia, espaçamento, largura de leitura, raios e elevação; eliminar valores repetidos gradualmente.
- Definir primitives CSS consistentes para página, cabeçalho, botão, cartão/painel, campo/formulário, chip, aviso e links, documentadas pelo [modelo de design](data-model.md).
- Garantir contraste, `:focus-visible`, estados `disabled`, áreas de toque adequadas e `prefers-reduced-motion`; não usar cor como indicador exclusivo.
- Adicionar tokens de tema escuro e `ThemeService` pequeno, iniciado no bootstrap, que aplica a preferência no elemento raiz; usar a preferência do sistema somente quando ainda não houver escolha manual.
- Refinar `LoadingState`, `EmptyState`, `ErrorState`, `ConfirmDialog` e `MetadataSelector` quando um contrato semântico ou visual já for compartilhado. Não abstrair CSS que só aparece em uma tela.

### 2. Tornar a navegação uma orientação confiável

- Ajustar `authenticated-layout.component.*` para incluir link de salto, `aria-current` no destino ativo e rótulos/agrupamentos mais claros para os seis destinos privados.
- Preservar a sidebar no desktop e aperfeiçoar a gaveta móvel: controle de estado, backdrop, Escape, restauração de foco e transição reduzida conforme o [contrato](contracts/frontend-experience.md).
- Diferenciar marca, contexto de navegação e ação de encerrar sessão sem criar uma segunda rota ou alterar guard/autenticação.
- Oferecer no topo um botão com estado e nome acessíveis para alternar tema claro/escuro, com a preferência persistida localmente.
- Criar/atualizar testes do layout para links, rota ativa, ciclo abrir-fechar e foco de menu.

### 3. Migrar os fluxos de descoberta e consulta

- Aplicar cabeçalho e ações de Dashboard, Busca e Pergunte à base aos primitives novos; manter métricas, atalhos, pesquisa, histórico, filtros e tipos já existentes.
- Em Busca e Pergunte, tornar a consulta a ação dominante e colocar filtros avançados em bloco visual secundário, preservando seus rótulos, autocomplete, chips e operação por teclado.
- Padronizar cartões de resultados/respostas/fontes e a apresentação de score, metadados, citações e feedbacks; texto remoto continua interpolado como texto.

### 4. Migrar os fluxos de execução e manutenção

- Reestruturar visualmente Ingestão para tornar modo, dados necessários, envio e retorno de sucesso fáceis de escanear, preservando validações, tabs e os dois caminhos de ingestão.
- Melhorar Biblioteca e Detalhe de fonte com filtros legíveis, listas de alta densidade mas escaneáveis, metadados consistentes e ação contextual sem mudar endpoints.
- Melhorar Organização para distinguir navegação entre categorias/tags/projetos, criação/edição, ações secundárias e ações perigosas; confirmar que diálogos existentes continuam explícitos e acessíveis.

### 5. Validar consistência e evitar regressões

- Acrescentar testes direcionados onde comportamento foi tocado: navegação móvel, foco, estados de feedback e rendering das ações/links principais. Preservar os testes de regra e HTTP existentes.
- Revisar todos os breakpoints em 320 px, 768 px e 1440 px: sem overflow, controles proporcionais, leitura confortável e ordem de conteúdo lógica.
- Auditar landmarks, `h1` único, labels, contrastes, foco e redução de movimento usando o [quickstart](quickstart.md).
- Executar os quality gates no diretório `frontend/`.

## Data Model / API Implications

- Não há migração, schema, endpoint FastAPI, contrato OpenAPI, MCP, autenticação ou mudança em `doc/API.md`; a única persistência nova é a preferência visual local `knowledge-hub.theme`.
- [data-model.md](data-model.md) define apenas tokens, padrões de apresentação e estado efêmero do menu.
- As rotas atuais e as regras de interação estão preservadas em [frontend-experience.md](contracts/frontend-experience.md).

## Test Strategy

- **Layout**: links, item ativo, link de salto, menu em mobile, Escape/backdrop, foco e alternância de tema.
- **Shared**: semântica e variantes de estados carregando/vazio/erro/sucesso, com `prefers-reduced-motion` coberto por revisão de CSS.
- **Features**: renderização de ação principal, filtros/chips, mensagens e confirmações nas telas alteradas; regras de negócio e HTTP continuam nos testes atuais.
- **Manual/a11y**: roteiro de teclado, leitor de tela, contraste e três viewports documentado em [quickstart.md](quickstart.md).
- **Quality gate**: `npm run typecheck`, `npm test -- --watch=false`, `npm run build`.

## Rollout Order

1. Fundação visual e shell autenticado — entrega navegável e validável isoladamente.
2. Início, Busca e Pergunte à base — maior impacto na descoberta e consulta de conhecimento.
3. Ingestão e Biblioteca — melhora o ciclo adicionar → conferir material.
4. Organização e Detalhe — consolida as tarefas administrativas e a leitura de contexto.
5. Auditoria transversal e ajustes de regressão — somente após os padrões estarem aplicados nas telas.

## Risk Notes

- Uma migração visual ampla pode alterar seletores usados pelos testes. Cada lote deve atualizar testes junto da tela e manter comportamento/rotas intactos.
- Abstrair cedo demais pode criar componentes difíceis de customizar. Promover a `shared/` apenas padrões usados por mais de uma superfície ou com comportamento acessível complexo.
- Efeitos visuais ou ícones sem texto podem reduzir acessibilidade. Preferir texto claro; ícones são suplementares e decorativos quando redundantes.
- Não confundir modernização da aparência com alteração de prioridade de produto: nenhuma nova API ou fluxo é necessário para a primeira versão.

## Complexity Tracking

Nenhuma violação da constituição identificada.
