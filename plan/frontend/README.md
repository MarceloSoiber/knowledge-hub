# Plano do frontend — Knowledge Hub

**Status:** proposta inicial · **Data:** 2026-07-23 · **Escopo:** interface Angular

## Visão geral

O Knowledge Hub já possui uma API para ingestão, busca semântica, respostas RAG e organização de fontes. O frontend atual, porém, está restrito à autenticação por Bearer token. Este diretório organiza a evolução da interface em entregas pequenas e independentes, para que o produto ganhe valor sem exigir uma grande reescrita ou mudanças prematuras no backend.

Ao final do primeiro corte, uma pessoa autenticada deverá conseguir adicionar conhecimento, encontrá-lo por busca, fazer perguntas à base e conferir as fontes que sustentam cada resposta.

## Objetivos

- Disponibilizar busca semântica com filtros por categorias, tags e projetos.
- Permitir perguntas em linguagem natural com resposta e fontes auditáveis.
- Permitir ingestão de arquivos e textos com metadados.
- Oferecer biblioteca para consultar e manter fontes existentes.
- Organizar o acervo por categorias, tags e projetos.
- Manter a interface simples, responsiva, acessível e segura no uso do token.

## Princípios de implementação

- **Aproveitar a API existente:** as fases propostas usam endpoints já publicados sob `/api/v1/knowledge`.
- **Construir primeiro os fundamentos:** rotas, autenticação, cliente HTTP tipado e componentes compartilhados precedem telas de negócio.
- **Feedback claro:** carregamento, resultado vazio, validação e falhas da API devem ter mensagens que indiquem o próximo passo.
- **Segurança por padrão:** nunca exibir ou registrar o Bearer token; conteúdo recuperado é dado não confiável e deve ser renderizado como texto.
- **Acessibilidade e responsividade desde o início:** HTML semântico, foco visível, teclado, ARIA e telas utilizáveis em celular e desktop.
- **Escopo progressivo:** implementar apenas o necessário para cada fase e adiar evoluções de API até haver necessidade real.

## Como usar este plano

Cada arquivo abaixo descreve uma entrega: resultado esperado, escopo, endpoints, dependências, riscos e critérios de aceite. A numeração indica a ordem recomendada, não necessariamente uma obrigação de conclusão integral antes do começo da seguinte fase.

Antes de iniciar uma fase, valide o arquivo correspondente e transforme-o em uma especificação e tarefas executáveis no fluxo Spec Kit, caso a implementação seja aprovada.

| Fase | Entrega | Propósito | Situação |
| --- | --- | --- | --- |
| 01 | [Fundação](01-fundacao.md) | Criar a base de navegação, autenticação e integração HTTP. | Planejada |
| 02 | [Busca inteligente](02-busca.md) | Encontrar trechos relevantes e abrir suas fontes. | Planejada |
| 03 | [Pergunte à base](03-pergunte-a-base.md) | Consultar o RAG e auditar a resposta pelas fontes. | Planejada |
| 04 | [Ingestão](04-ingestao.md) | Adicionar textos e arquivos com metadados. | Planejada |
| 05 | [Biblioteca](05-biblioteca.md) | Consultar, editar e excluir fontes. | Planejada |
| 06 | [Organização](06-organizacao.md) | Manter categorias, tags e projetos. | Planejada |
| 07 | [Dashboard](07-dashboard.md) | Oferecer visão inicial do acervo e atalhos. | Planejada |
| 08 | [Qualidade e evolução](08-qualidade-e-evolucao.md) | Estabelecer critérios de qualidade e melhorias posteriores. | Contínua |

## Roteiro recomendado

### Primeiro corte de valor

1. Implementar a [Fundação](01-fundacao.md).
2. Implementar [Busca](02-busca.md) e [Ingestão](04-ingestao.md).
3. Implementar [Pergunte à base](03-pergunte-a-base.md).
4. Integrar a [Biblioteca](05-biblioteca.md) para abrir e manter as fontes resultantes.

Esse corte já atende ao fluxo completo: inserir conhecimento → localizar conteúdo → perguntar → verificar a origem.

### Consolidação do produto

5. Implementar [Organização](06-organizacao.md) para reduzir dependência de administração externa de metadados.
6. Implementar [Dashboard](07-dashboard.md) quando as ações principais já existirem e puderem ser resumidas de forma útil.
7. Aplicar continuamente as práticas de [Qualidade e evolução](08-qualidade-e-evolucao.md).

## Dependências entre fases

```text
01 Fundação
 ├── 02 Busca ─────────────┐
 ├── 03 Pergunte à base    │
 ├── 04 Ingestão ──────────┼── 05 Biblioteca
 └── 06 Organização ───────┘

07 Dashboard reutiliza a fundação e fica mais útil após busca e ingestão.
08 Qualidade acompanha todas as fases.
```

- A **Fundação** é pré-requisito técnico para todas as telas.
- **Busca**, **Pergunte à base**, **Ingestão** e **Organização** podem avançar em paralelo após a fundação, desde que compartilhem os mesmos tipos e componentes de metadados.
- A **Biblioteca** integra os fluxos de busca e ingestão, por isso é recomendada logo após eles.
- O **Dashboard** não bloqueia nenhum fluxo essencial e deve ficar para quando houver dados e ações suficientes para resumir.

## Mapa de capacidades e API atual

| Capacidade | Fase | Endpoints existentes |
| --- | --- | --- |
| Validar sessão e carregar metadados | 01 | `GET /categories` |
| Buscar conhecimento | 02 | `POST /search`, `GET /categories`, `GET /tags`, `GET /tags/autocomplete`, `GET /projects` |
| Gerar resposta RAG | 03 | `POST /answer` |
| Ingerir arquivo ou texto | 04 | `POST /uploads`, `POST /texts` |
| Consultar e manter fontes | 05 | `GET /sources`, `GET/PATCH/DELETE /sources/{source_id}` |
| Manter classificações | 06 | CRUD de `categories`, `tags` e `projects`; arquivar/reativar projetos |
| Resumir o acervo | 07 | Listagens de fontes, categorias, tags e projetos |

Todos os caminhos da tabela são relativos a `/api/v1/knowledge`.

## Limites do escopo atual

Este plano não inclui:

- colaboração em tempo real, usuários múltiplos ou permissões por papel;
- alteração de contratos REST, regras de negócio do backend ou ferramentas MCP;
- persistência de conversas, histórico compartilhado ou telemetria de uso;
- métricas RAG, configuração de modelos, reindexação ou operações de infraestrutura;
- paginação, estatísticas agregadas e progresso assíncrono de ingestão — evoluções que dependem de API adicional.

## Decisões de segurança e experiência

- O token só será salvo em `localStorage` se a pessoa marcar a opção de manter a sessão.
- Respostas `401` encerram a sessão local e retornam ao login.
- Exclusões de fontes, categorias e tags, além do arquivamento de projetos, exigem confirmação explícita.
- A interface deve distinguir, quando possível, erros de validação, duplicidade, indisponibilidade da API, erro de embeddings/LLM e conteúdo sensível bloqueado.
- Sem endpoint de progresso, a ingestão mostrará processamento em andamento sem estimativa percentual enganosa.

## Qualidade mínima por entrega

- Tipos TypeScript estritos e chamadas HTTP centralizadas.
- Testes para serviços, guard, formulários e estados críticos de componentes.
- Verificação manual de navegação por teclado, leitor de tela e layout móvel.
- Execução de `npm run typecheck` e `npm run build` no diretório `frontend/` antes de considerar uma fase concluída.

## Próximo passo

A implementação deve começar pela [Fase 01 — Fundação](01-fundacao.md). Após sua validação, crie uma especificação e uma lista de tarefas específicas para a fase antes de alterar código.
