# Feature Specification: Experiência visual e usabilidade do frontend

**Feature Branch**: `021-experiencia-visual-frontend`  
**Created**: 2026-07-28  
**Status**: Draft  
**Input**: "precisamos deixar o front mais bonito, mais intuitivo. monte um planejamento para melhorar o front"

## User Scenarios & Testing

### User Story 1 - Encontrar o próximo passo (Priority: P1)

Uma pessoa autenticada reconhece onde está, entende as áreas disponíveis e alcança Busca, Pergunte à base, Ingestão, Biblioteca e Organização com uma navegação consistente em desktop e celular.

**Why this priority**: A aplicação já entrega os fluxos principais, mas seu valor depende de eles serem descobertos e acessíveis sem decorar rotas.

**Independent Test**: Em 320 px e desktop, navegar por teclado e por toque entre todas as rotas privadas, confirmando indicação clara da página atual, menu operável e retorno previsível ao conteúdo.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada, **When** a pessoa abre qualquer rota privada, **Then** vê a navegação principal, a área atual e um caminho claro para as ações principais.
2. **Given** uma tela pequena, **When** a pessoa abre e fecha a navegação por botão, backdrop ou Escape, **Then** o menu não encobre permanentemente o conteúdo, mantém foco previsível e permite continuar a navegação.
3. **Given** uma pessoa navega com teclado, **When** ela percorre a página, **Then** consegue pular para o conteúdo e identificar visualmente o foco e o item de navegação atual.

---

### User Story 2 - Compreender e operar cada fluxo (Priority: P1)

Uma pessoa entende de imediato o propósito de cada tela, diferencia ações primárias de secundárias e recebe feedback claro em busca, perguntas, ingestão, biblioteca e organização.

**Why this priority**: Os fluxos existentes são completos, mas controles, cartões, filtros e mensagens hoje usam padrões visuais duplicados e nem sempre têm a mesma hierarquia.

**Independent Test**: Executar uma busca, enviar um texto, filtrar a biblioteca e editar um metadado, verificando títulos, ações principais, estados de carregamento/vazio/erro e confirmação das ações.

**Acceptance Scenarios**:

1. **Given** uma página funcional, **When** ela é renderizada, **Then** título, descrição, ação principal, conteúdo e ações secundárias têm hierarquia visual consistente.
2. **Given** dados carregando, vazios ou indisponíveis, **When** a pessoa abre uma área da aplicação, **Then** recebe uma explicação orientada à ação sem confundir sucesso vazio com falha.
3. **Given** uma ação destrutiva ou irreversível, **When** a pessoa a inicia, **Then** a interface preserva confirmação explícita e a diferencia visualmente das ações comuns.

---

### User Story 3 - Usar a aplicação confortavelmente em qualquer tela (Priority: P2)

Uma pessoa usa os mesmos recursos em celular, tablet ou desktop com texto legível, controles tocáveis e sem rolagem horizontal indevida.

**Why this priority**: O acervo pode ser consultado fora da estação de trabalho; responsividade e legibilidade evitam que o aprimoramento visual prejudique a utilidade.

**Independent Test**: Inspecionar as telas privadas em 320 px, 768 px e 1440 px e concluir os fluxos principais sem zoom obrigatório ou corte de conteúdo.

**Acceptance Scenarios**:

1. **Given** largura de 320 px, **When** a pessoa usa formulários, filtros, listas e cartões, **Then** controles permanecem legíveis, tocáveis e dentro da área visível.
2. **Given** largura de desktop, **When** há espaço disponível, **Then** o layout usa colunas e agrupamentos para facilitar leitura sem dispersar o conteúdo.

### Edge Cases

- Títulos, trechos, URIs e metadados muito longos devem quebrar linha ou truncar com contexto sem causar rolagem horizontal.
- Estados de erro, carregamento e vazio devem caber em telas pequenas e manter o próximo passo disponível.
- A preferência do sistema por redução de movimento deve ser respeitada em menus, feedbacks e quaisquer transições novas.
- A interface deve permanecer utilizável sem cor como único indicador de estado e com contraste suficiente para texto, controles e foco.

## Requirements

### Functional Requirements

- **FR-001**: O sistema DEVE consolidar tokens globais para cores, tipografia, espaçamento, raios, sombras, foco e estados semânticos, usados por todas as telas privadas.
- **FR-002**: O sistema DEVE disponibilizar padrões reutilizáveis de apresentação para cabeçalho de página, botões, cartões, campos, chips, avisos e estados de carregamento, vazio e erro, sem alterar a lógica de negócio existente.
- **FR-003**: O layout autenticado DEVE apresentar navegação para todas as rotas privadas existentes, indicar a rota ativa e incluir um atalho de teclado para o conteúdo principal.
- **FR-004**: A navegação móvel DEVE abrir, fechar e restaurar foco de maneira acessível por botão, backdrop e tecla Escape.
- **FR-005**: As telas Início, Busca, Pergunte à base, Ingestão, Biblioteca, Organização e Detalhe da fonte DEVEM aplicar a mesma hierarquia de conteúdo, escala visual e linguagem de ações.
- **FR-006**: Busca e Pergunte à base DEVEM manter filtros avançados disponíveis sem competir visualmente com a consulta principal; filtros selecionados devem continuar fáceis de revisar e remover.
- **FR-007**: Ingestão, Biblioteca e Organização DEVEM priorizar a tarefa principal da tela e apresentar feedback imediato, acessível e recuperável para sucesso, vazio, validação e falha de rede.
- **FR-008**: Todas as alterações DEVEM funcionar de 320 px a desktop, suportar teclado, foco visível, HTML semântico, nomes acessíveis e `prefers-reduced-motion`.
- **FR-009**: A implementação NÃO DEVE mudar endpoints HTTP, esquemas, persistência, autenticação, regras de negócio, rotas publicadas, MCP ou `doc/API.md`.
- **FR-010**: O sistema DEVE oferecer tema claro e escuro com alternância acessível; a escolha manual fica salva somente no navegador e, na ausência dela, respeita a preferência do sistema.

### Key Entities

- **Design tokens**: valores globais de aparência e espaçamento que mantêm a interface coerente.
- **Padrão de componente**: contrato visual e semântico de elementos reutilizáveis, como botão, cartão e estado de feedback.
- **Contexto de navegação**: relação entre rota ativa, menu e conteúdo principal exibida no shell autenticado.
- **Estado de tarefa**: apresentação de carregamento, sucesso, vazio, validação ou erro de uma operação já existente.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Todas as seis áreas privadas e o detalhe de fonte são alcançáveis pela navegação principal em desktop e em 320 px, com rota ativa identificável.
- **SC-002**: Testes de componentes cobrem menu móvel, links de navegação, ações primárias e os estados críticos introduzidos ou migrados.
- **SC-003**: Verificação manual em 320 px, 768 px e 1440 px não encontra rolagem horizontal involuntária nos fluxos de busca, pergunta, ingestão, biblioteca e organização.
- **SC-004**: Auditoria manual demonstra ordem de foco visível, atalhos semânticos, Escape no menu, contraste adequado e redução de movimento respeitada.
- **SC-005**: `npm run typecheck`, `npm test -- --watch=false` e `npm run build` passam no diretório `frontend/`.

## Assumptions

- O escopo é uma evolução de UX/UI sobre as telas Angular atuais; não inclui rebranding, pesquisa com usuários, telemetria, nova biblioteca de componentes ou novas dependências de ícones.
- O idioma principal continua português (Brasil), com a terminologia atual do produto preservada.
- Ícones, se empregados, serão poucos, decorativos quando redundantes ao texto e implementados sem dependência externa nova.
- A implementação pode ser entregue em lotes, começando pela fundação visual e navegação antes de migrar os fluxos.
- A preferência de tema é específica do navegador, sem sincronização entre dispositivos ou contas.

## Out of Scope

- Redesenhar fluxos de negócio, criar novos recursos, alterar contratos da API ou adicionar métricas/gráficos ao Dashboard.
- Internacionalização, personalização por usuário, onboarding guiado, analytics de comportamento ou testes formais com usuários.
