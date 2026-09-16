# Análise das transcrições — 07 - Ferramentas de IA para Gestão de projetos

## Escopo e integridade

Esta análise foi produzida a partir do acervo local da disciplina, que contém 24 itens audiovisuais: 23 videoaulas em dez módulos e um podcast. A auditoria confirmou 24/24 vídeos e respectivas transcrições VTT/JSON válidos, além de três materiais de apoio (indicação de leitura, material autoral e slides). As transcrições são automáticas e apresentam ruídos de reconhecimento em nomes próprios e termos como Requirements Copilot, WSJF, RICE, Gherkin, Monte Carlo, n8n e OKR; a síntese corrige a terminologia quando o contexto é suficiente.

## Síntese executiva

A disciplina acompanha um caso contínuo de transformação digital da empresa logística fictícia **Conecta Cargas**, cujo projeto **Hautwise** migra a gestão de uma frota de 140 veículos para uma plataforma inteligente. A jornada percorre o ciclo completo de gestão: descobrir e estruturar requisitos, priorizar backlog, planejar capacidade, estimar prazos, monitorar riscos, transformar reuniões em decisões, comunicar status, governar qualidade, automatizar boards e alinhar portfólio a OKRs.

O papel da IA é o de copiloto verificável. Ela transcreve, classifica, calcula, resume e sugere; a pessoa gestora faz curadoria, confronta fontes, explicita incertezas e decide. O fluxo recomendado é:

```text
Dados brutos → contexto e prompt → artefato estruturado → curadoria humana
      → regra/score → decisão comunicável → rastreabilidade → aprendizado
```

O maior valor não está em gerar textos bonitos, mas em converter informação dispersa em artefatos operacionais: épicos, user stories, critérios de aceite, ranking justificável, cronograma adaptável, intervalos de confiança, cockpit de riscos, ata acionável, status report, checklist de compliance, cards sincronizados e scorecard de portfólio.

## Mapa da disciplina

| Módulo | Tema | Entregável principal |
|---|---|---|
| 01 | Planejamento e escopo com IA (Requirements Copilot) | Backlog estruturado a partir de reunião |
| 02 | Priorização inteligente de backlog | Ranking RICE/WSJF calibrado |
| 03 | Cronograma, capacidade e alocação | Plano com dependências, caminho crítico e cenários |
| 04 | Estimativas e previsões | PERT/3 pontos e Monte Carlo com percentis |
| 05 | Riscos e mitigações | Cockpit, métricas de fluxo e ações preventivas |
| 06 | Reuniões turbinadas | Meeting digest, decisões, blockers e cards |
| 07 | Status reports e executive summaries | Narrativas por audiência com audit trail |
| 08 | Governança, compliance e qualidade | Regras como código e checklist dinâmico |
| 09 | Automação de boards e comunicação | Fluxo n8n/Make, cards e sincronização |
| 10 | Portfólio e OKRs com IA | OKRs validados e scorecard de portfólio |
| Podcast | Gestão com IA e automação | Debate sobre adoção, limites e impacto humano |

## Análise módulo a módulo

### 1. Planejamento e escopo

O Requirements Copilot recebe a transcrição de uma reunião com o diretor de operações Carlos e transforma linguagem natural em épicos, histórias de usuário, domínios e critérios de aceite em Gherkin. O módulo enfatiza que metodologia, isoladamente, não resolve ambiguidade de requisitos. O System Prompt define papel, formato de saída, regras de negócio e limites; o ambiente de IA é configurado e validado antes da execução.

A curadoria técnica é apresentada como barreira contra alucinações: conferir nomes, escopo, dependências e evidências da reunião, rejeitar requisitos inventados e devolver dúvidas ao stakeholder. O pipeline recomendado é transcrição bruta → backlog estruturado → revisão → importação no gerenciador.

### 2. Priorização inteligente

Com dezenas de itens e capacidade limitada por sprint, a decisão deixa de ser “o que parece urgente”. RICE combina alcance, impacto, confiança e esforço; WSJF incorpora custo do atraso e duração do trabalho. A IA calcula e explica o ranking, mas não deve esconder premissas ou transformar números arbitrários em verdade.

O backlog real da Hautwise adiciona hardware, restrições e critérios de aceite. A calibração compara o ranking com conhecimento do negócio, identifica outliers e exige checklist de curadoria antes da apresentação ao stakeholder. A qualidade do resultado é proporcional à qualidade dos dados e à calibração contínua.

### 3. Cronograma, capacidade e alocação

Cronogramas estáticos deterioram quando surgem férias, dependências externas, incidentes ou mudanças de escopo. A IA modela dependências como grafo, calcula caminho crítico e explora cenários What If. O Scheduling Prompt recebe contexto do time, capacidade e restrições e produz um plano que pode ser recalculado à medida que a realidade muda.

O aprendizado central é trocar a promessa de uma data fixa por um plano adaptável, explicitando premissas, folgas, gargalos e impacto de cada alteração.

### 4. Estimativas e previsões

O módulo diagnostica viés de otimismo e substitui estimativas pontuais por estimativa de três pontos/PERT e simulação de Monte Carlo. Percentis P50, P85 e P95 comunicam diferentes níveis de confiança e tornam o risco compreensível para públicos técnicos e executivos.

Uma previsão responsável sempre informa intervalo, confiança, dados utilizados, premissas e fatores que podem deslocar a curva. Monte Carlo é ferramenta de comunicação de incerteza, não garantia de prazo.

### 5. Riscos e mitigações

O cockpit acompanha a execução usando métricas de fluxo e detecção de anomalias. Lead time, throughput, WIP e idade dos itens ajudam a detectar desvio antes da crise; MTTD mede a qualidade do monitoramento. A IA identifica sinais no projeto Hautwise, classifica riscos e sugere mitigação.

Alertas precisam de limiares, contexto e ação associada. Sem curadoria, o sistema gera fadiga de alertas, confunde correlação com causa e recomenda ações genéricas. A mitigação deve ter responsável, prazo, condição de sucesso e plano de contingência.

### 6. Reuniões turbinadas

O Meeting Digest transforma voz em texto e texto em artefatos: decisões, ações, blockers e cards. A classificação semântica separa fatos de opiniões e converte compromissos em itens rastreáveis. A ata gerada é comparada com uma ata manual para avaliar omissões, ambiguidades e falsos compromissos.

A automação só é útil quando preserva quem decidiu, o que foi decidido, prazo, responsável e contexto. Participantes devem saber que a reunião é processada e ter oportunidade de corrigir a ata.

### 7. Status reports e sumários executivos

O módulo aplica a pirâmide de audiências: o mesmo estado do projeto exige narrativa diferente para equipe, sponsor e diretoria. O Status Report Prompt produz variantes, distinguindo dados de narrativa e mantendo histórico de decisões e audit trail.

Um sumário executivo eficaz comunica progresso, desvio, impacto, decisão necessária e próximo passo. Não deve maquiar incerteza nem substituir o relatório de evidências; links para backlog, métricas e decisões permitem auditoria.

### 8. Governança, compliance e qualidade

Governança como código transforma regras de processo em verificações executáveis. O arquivo de regras (apresentado como DangerJS/Danger) gera checklists dinâmicos para deploy e valida qualidade, rastreabilidade e conformidade. A IA auxilia na criação do checklist, mas o critério normativo deve vir da organização.

A separação entre recomendação e enforcement é importante: a IA pode explicar uma falha e sugerir correção; o pipeline deve bloquear o que a política classifica como não conforme. Exceções precisam de justificativa, aprovador, validade e registro.

### 9. Automação de boards e comunicação

Ferramentas conectadas por n8n ou Make funcionam como interface entre Jira/Gira, Slack e outros sistemas. A linguagem natural pode criar cards e sincronizar status, reduzindo trabalho manual. O módulo diferencia ferramenta integrada de workflow orquestrado e mostra que o bot precisa de contexto, permissões e formato de saída.

Controles essenciais são idempotência (não criar o mesmo card duas vezes), deduplicação, mapeamento de IDs, tratamento de falhas e logs. Mensagens geradas devem indicar origem e não alterar prioridade ou prazo sem autorização.

### 10. Portfólio e OKRs

O fechamento diferencia **output** (entrega) de **outcome** (resultado), apresenta a anatomia de um OKR e alinha backlog, estratégia e portfólio. O OKR Aligner valida objetivos, identifica lacunas e consolida um scorecard. A IA ajuda a detectar objetivos vagos, métricas ausentes e desalinhamento entre iniciativas.

OKRs não devem ser uma lista de tarefas nem um mecanismo de punição. A cadência operacional precisa revisar evidências, atualizar hipóteses e separar resultado real de atividade executada. O scorecard deve mostrar qualidade da métrica, responsável, período e fonte.

### Podcast — gestão com IA

O podcast amplia a discussão para “gestão com IA”: adoção, automação, agentes e efeitos sobre pessoas não programadoras. A mensagem complementar é que produtividade não elimina responsabilidade. O gestor deve preservar transparência, autonomia, desenvolvimento das pessoas e capacidade de contestar decisões automatizadas.

## Padrões de prompt e agentes extraídos

- Definir papel, objetivo, contexto, fontes permitidas e formato de saída.
- Separar instruções permanentes (System Prompt) dos dados variáveis do projeto.
- Exigir campos estruturados, premissas, confiança e evidências.
- Incluir critérios de recusa: dados insuficientes, conflito de regras ou pedido fora do escopo.
- Versionar prompts, exemplos, schemas e resultados de avaliação.
- Usar agentes especializados (requisitos, backlog, cronograma, riscos, comunicação e OKRs), coordenados por contratos explícitos.

## Riscos e controles

1. **Alucinação de requisito ou decisão:** exigir fonte na transcrição e revisão do responsável.
2. **Viés numérico:** calibrar RICE/WSJF e registrar pesos, confiança e esforço.
3. **Falsa precisão:** comunicar intervalos, percentis e premissas em vez de datas únicas.
4. **Privacidade de reuniões:** consentimento, minimização, retenção e controle de acesso.
5. **Automação indevida de board:** aprovação para mudanças de prioridade, prazo ou responsável.
6. **Prompt injection em documentos:** tratar atas, tickets e anexos como dados não confiáveis.
7. **Drift de regras:** revisão periódica de políticas, prompts e integrações.
8. **Narrativa sem evidência:** manter links, timestamps, audit trail e dados brutos.

## Arquitetura de referência para implantação

```text
Reuniões, backlog, métricas e estratégia
                ↓
Ingestão + normalização + controle de acesso
                ↓
RAG/contexto do projeto + agentes especializados
                ↓
Saída estruturada (schema, score, intervalo, evidências)
                ↓
Curadoria humana + políticas + validações
                ↓
Gerenciadores, Slack, dashboards e relatórios
                ↓
Feedback, métricas de qualidade e base de conhecimento
```

## Indicadores para medir valor

- Tempo de elaboração e taxa de retrabalho de requisitos.
- Concordância do ranking com decisões revisadas e valor entregue.
- Erro de previsão, cobertura P85/P95 e frequência de replanejamento.
- MTTD, lead time, throughput, WIP e percentual de riscos mitigados.
- Decisões e ações capturadas corretamente nas reuniões.
- Change failure rate, violações de compliance e tempo de aprovação.
- Duplicidade de cards, falhas de integração e latência de sincronização.
- Percentual de OKRs com métrica, fonte, responsável e outcome verificável.

## Roteiro de adoção

**Fase 1 — Assistência:** gerar rascunhos de requisitos, atas e sumários sem escrita automática nos sistemas.

**Fase 2 — Estruturação:** schemas, RICE/WSJF, cronograma, Monte Carlo e cockpit com revisão obrigatória.

**Fase 3 — Governança:** políticas como código, RBAC, audit trail, consentimento e versionamento.

**Fase 4 — Integração controlada:** criar cards e sincronizar status por allowlist, com idempotência e aprovação para mutações.

**Fase 5 — Otimização:** medir qualidade, custo, tempo economizado e impacto no outcome; recalibrar prompts e modelos.

## Conclusão

A disciplina ensina uma gestão de projetos orientada por evidências, na qual IA reduz o trabalho mecânico e aumenta a capacidade de explorar cenários. O diferencial é o encadeamento dos artefatos: uma reunião bem curada alimenta backlog; o backlog alimenta priorização e cronograma; execução alimenta riscos e status; governança protege o fluxo; automações conectam ferramentas; OKRs verificam se as entregas produziram resultado. A adoção madura mantém sempre contexto, incerteza, rastreabilidade e decisão humana no circuito.
