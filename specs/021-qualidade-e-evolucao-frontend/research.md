# Research: Qualidade, segurança e evolução do frontend

## Decision: ampliar testes sobre as fronteiras atuais, não introduzir nova biblioteca de estado ou teste

**Rationale**: Angular já usa TestBed, Vitest e `HttpTestingController`. A qualidade necessária é cobertura consistente de contratos, estados e decisões de segurança, não uma migração de framework.

**Alternatives considered**:

- Adotar Playwright/Cypress imediatamente: adiado; amplia toolchain e depende de estabilizar o gate de Node antes de gerar valor sobre os fluxos unitários existentes.
- Testar apenas por UI manual: rejeitado; regressões de headers, serialização, `401` e mensagens seguras precisam de teste determinístico.

## Decision: centralizar a classificação de erros seguros e migrar consumidores gradualmente

**Rationale**: `api-error.ts` já mapeia status para mensagens locais, enquanto algumas features mantêm mapeamentos próprios. A camada comum deve cobrir o vocabulário genérico, deixando ações de domínio (por exemplo, fonte duplicada) locais e testadas.

**Alternatives considered**:

- Mostrar `detail` da API diretamente: rejeitado por risco de conteúdo não confiável e inconsistência de UX.
- Forçar uma mensagem genérica para todo erro: rejeitado; perde a diferença útil entre validação, indisponibilidade e conflito.

## Decision: tratar a versão Node como quality gate reproduzível

**Rationale**: O CLI atual requer Node 22.22.3 ou superior, enquanto a imagem de build já usa Node 24. A documentação e CI/local devem convergir para uma versão suportada antes de considerar testes/build aprovados.

**Alternatives considered**:

- Ignorar o bloqueio local porque o typecheck passou: rejeitado; não prova compilação Angular nem execução de specs.
- Reduzir a versão do Angular CLI sem análise de compatibilidade: rejeitado; é uma alteração de dependência fora do escopo de qualidade.

## Decision: registrar evolução de API como contrato de roadmap, sem código antecipado

**Rationale**: Paginação, agregados e progresso assíncrono mudam semântica e exigem decisão de backend/OpenAPI. Documentá-los com consumidores e critérios previne acoplamento prematuro no cliente.

**Alternatives considered**:

- Simular paginação/progresso no frontend: rejeitado; cria comportamento que o servidor não garante.
- Deixar a evolução somente em texto livre: rejeitado; não dá subsídio suficiente para a próxima especificação/contrato.
