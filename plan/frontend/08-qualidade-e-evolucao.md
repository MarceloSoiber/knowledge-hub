# 08 — Qualidade, segurança e evolução

## Qualidade contínua

- Cobrir serviços HTTP, guard, erros e validação de formulários com testes unitários.
- Cobrir loading, vazio, erro e sucesso dos fluxos críticos com testes de componentes.
- Usar `HttpTestingController` para validar contratos consumidos pelo frontend.
- Verificar manualmente desktop, mobile, teclado e leitor de tela.
- Antes de cada entrega, executar `npm run typecheck` e `npm run build` em `frontend/`.

## Segurança e UX

- Nunca exibir ou registrar o Bearer token.
- Limpar sessão no 401 e encaminhar ao login.
- Tratar conteúdo recuperado como texto não confiável; não renderizar HTML arbitrário.
- Confirmar exclusões, arquivamento e qualquer operação difícil de reverter.
- Diferenciar erro de configuração, indisponibilidade e validação sempre que a API devolver detalhe seguro.

## Evoluções de API após o MVP

- Paginação, ordenação e filtros no servidor para fontes.
- Estatísticas agregadas para dashboard.
- Status e progresso assíncrono de ingestão.
- Pré-visualização ou download de arquivos originais, se houver armazenamento.
- Descrição e sensibilidade de categorias administráveis na interface.

## Primeiro corte de produto

O primeiro corte estará pronto quando a pessoa autenticada conseguir buscar e abrir uma fonte, ingerir texto/arquivo, perguntar à base com fontes auditáveis e entender como agir diante de base vazia, erro de API ou duplicidade.
