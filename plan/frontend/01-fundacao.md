# 01 — Fundação da aplicação

## Resultado esperado

Uma área autenticada navegável, com serviços tipados e padrões visuais reutilizáveis para os demais módulos.

## Escopo

- Configurar Angular Router e separar rota pública de login das rotas autenticadas.
- Criar layout autenticado com barra lateral, cabeçalho, estado da sessão e desconexão.
- Criar guard baseado em `AuthService`; ao receber 401, limpar sessão e redirecionar ao login.
- Criar `KnowledgeApiService` para centralizar chamadas HTTP e tratamento de erros.
- Definir tipos TypeScript para categoria, tag, projeto, fonte, chunk, busca e resposta RAG.
- Criar componentes compartilhados: carregamento, erro, estado vazio, diálogo de confirmação e seleção de metadados.
- Definir estilos globais, foco visível, contraste, navegação por teclado e feedback por ARIA.

## Arquivos previstos

```text
frontend/src/app/
├── core/              # auth, interceptor, guard e cliente da API
├── layout/            # navegação e casca autenticada
├── shared/            # tipos e componentes reutilizáveis
├── features/
└── app.routes.ts
```

## Critérios de aceite

- Uma pessoa autenticada acessa as rotas privadas e consegue desconectar.
- Uma sessão ausente ou inválida retorna ao login sem expor o token.
- Estados de loading, erro e vazio têm texto compreensível e semântica acessível.
- `npm run typecheck` e `npm run build` passam em `frontend/`.

## Dependências e riscos

- Depende somente do fluxo de autenticação existente.
- Não duplicar chamadas de autenticação em cada tela; o guard e o serviço devem ser a fonte de verdade.
