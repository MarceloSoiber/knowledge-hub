# Tasks: Configuração de IA pelo portal

**Input**: `spec.md` e `plan.md`

## Implementation

- [x] T001 Criar a especificação e o plano em `specs/022-configuracao-llm-portal/`.
- [x] T002 Implementar schemas, persistência com fallback e validação em `backend/app/schemas/configuration.py` e `backend/app/services/config.py`.
- [x] T003 Integrar a configuração efetiva às dependências de LLM/embeddings em `backend/app/api/dependencies.py`.
- [x] T004 Criar endpoints autenticados em `backend/app/api/routes/configuration.py` e registrá-los em `backend/app/main.py`.
- [x] T005 Criar tipos e chamadas HTTP em `frontend/src/app/core/knowledge.types.ts` e `frontend/src/app/core/knowledge-api.service.ts`.
- [x] T006 Criar página de configurações e rota privada em `frontend/src/app/features/configuration/` e `frontend/src/app/app.routes.ts`.
- [x] T007 Substituir controles soltos por menu de usuário em `frontend/src/app/layout/authenticated-layout.component.*`.
- [x] T008 Documentar o contrato em `doc/API.md` e atualizar `.env.example`.
- [ ] T009 Adicionar testes de serviço/API e componente, depois executar pytest, typecheck, testes e build. Backend concluído; validação Angular bloqueada pela propriedade root de `frontend/node_modules/@bramus`.

## Deferred safely

- [ ] T010 Implementar a migração assíncrona de `VECTOR_DIM` com bloqueio, alteração de `vector(n)`, reconstrução HNSW e reindexação. A UI/API atual informa o valor ativo e rejeita alteração direta para não corromper a compatibilidade atual.
