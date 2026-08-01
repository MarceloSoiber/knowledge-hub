# Research: Experiência visual e usabilidade do frontend

## Decision: evolução incremental com CSS e componentes Angular existentes

**Rationale**: O frontend já usa Angular standalone, CSS local e tokens iniciais em `styles.css`. Consolidar esses ativos evita reescrever telas, mantém o bundle estável e permite validar cada fluxo preservando serviços e contratos atuais.

**Alternatives considered**:

- Adotar uma biblioteca de design completa: descartado porque adiciona dependência, aparência externa e custo de migração antes de estabilizar os padrões do produto.
- Reescrever as telas em uma única entrega: descartado pelo risco de regressões nos fluxos de ingestão, busca e gestão já implementados.

## Decision: navegação lateral persistente em desktop e gaveta acessível no mobile

**Rationale**: As seis áreas privadas representam funções diferentes e recorrentes. A sidebar existente já oferece a estrutura correta; o trabalho deve reforçar agrupamento, estado ativo, foco, rótulos e comportamento da gaveta em telas pequenas.

**Alternatives considered**:

- Navegação somente no topo: descartada porque não escala bem para seis destinos e compete com o conteúdo em telas menores.
- Menu sempre aberto no mobile: descartado porque reduz drasticamente a área útil de formulários e resultados.

## Decision: usar conteúdo e texto como sinal principal, cor como reforço

**Rationale**: Estados operacionais precisam ser compreendidos por pessoas com diferentes percepções visuais e leitores de tela. Rótulos, ícones decorativos opcionais, `role=status`/`role=alert` apropriados e foco preservam essa clareza.

**Alternatives considered**:

- Estados apenas por cor: descartado por acessibilidade e ambiguidade.
- Toast global para todo feedback: descartado; mensagens locais mantêm contexto, são mais fáceis de reler e já se alinham aos componentes compartilhados.

## Decision: migrar por padrões e não por páginas isoladas

**Rationale**: Busca, Pergunte à base e Ingestão repetem controles, cartões e avisos com CSS próprio. Primeiro estabilizar tokens e primitives reduz duplicação e torna o resultado visualmente coeso; depois cada tela somente adapta a composição.

**Alternatives considered**:

- Ajustar somente cores e sombras nas telas: descartado porque não resolve hierarquia, navegação e inconsistências entre controles.
- Criar um componente Angular para todo elemento: descartado; somente primitives com comportamento/semântica compartilhados justificam componente, e regras puramente visuais continuam em CSS centralizado.
