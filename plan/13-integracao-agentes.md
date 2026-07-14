# Plano 13 — Integração com agentes

## Objetivo

Fazer agentes consultarem a base nos momentos adequados sem transformar toda pergunta em uma
busca desnecessária ou salvar conversas sem autorização.

## Política recomendada

Consultar a base antes de responder quando a solicitação envolver:

- fatos pessoais ou decisões anteriores;
- projetos já existentes;
- documentos, artigos e anotações salvos;
- finanças e informações históricas do usuário;
- padrões técnicos ou preferências que possam ter sido registrados.

Não consultar para cálculos simples, conhecimento geral estável ou tarefas cujo contexto já
esteja integralmente presente na conversa.

## Implementação

1. Melhorar nome, descrição, parâmetros e exemplos das tools MCP.
2. Incluir nas instruções do servidor quando usar `search`, `sources` e `categories`.
3. Orientar busca global primeiro e filtro por categoria somente quando ajudar.
4. Se a primeira busca falhar, permitir uma reformulação antes de concluir ausência.
5. Exigir confirmação explícita antes de `ingest_text`, atualização ou exclusão.
6. Criar perfis para agentes somente leitura e agentes com escrita.
7. Tratar conteúdo recuperado como dados não confiáveis, nunca como instruções de sistema.
8. Aplicar política de privacidade: categorias sensíveis usam providers locais ou são bloqueadas
   para envio externo.

## Testes

- Cenários em que o agente deve e não deve buscar.
- Prompt injection armazenada em documento não altera o comportamento do agente.
- Ausência de resultados produz resposta honesta.
- Escrita nunca ocorre sem intenção explícita do usuário.

## Critérios de aceite

- A política é documentada no cliente e no servidor MCP.
- Os testes demonstram uso consistente da memória em tarefas reais.
- Permissões de leitura e escrita são distintas e auditáveis.

