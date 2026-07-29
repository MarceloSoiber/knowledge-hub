# Tasks: Backup e Restauração Administrativos

**Input**: `specs/022-backup-restore-admin/spec.md` e `plan.md`

## Phase 1: Fundação

- [ ] T001 Adicionar `postgresql-client-16` (ou cliente compatível) ao `Dockerfile`.
- [ ] T002 Criar contratos Pydantic e serviço seguro de subprocessos em `backend/app/schemas/operations.py` e `backend/app/services/backup.py`.
- [ ] T003 Criar testes de serviço em `tests/test_backup_restore_admin.py` para confirmação, serialização e falha de backup prévio.

## Phase 2: User Story 1 - Download do backup

- [ ] T004 [US1] Criar `GET /api/v1/operations/backup` em `backend/app/api/routes/operations.py` e registrar no app.
- [ ] T005 [US1] Adicionar método tipado de download em `frontend/src/app/core/knowledge-api.service.ts`.
- [ ] T006 [US1] Criar tela de operações e rota Angular com estado de geração/download.

## Phase 3: User Story 2 - Restauração confirmada

- [ ] T007 [US2] Criar `POST /api/v1/operations/restore` multipart com arquivo e confirmação no endpoint.
- [ ] T008 [US2] Implementar backup de segurança, validação de dump e restauração limpa serializada no serviço.
- [ ] T009 [US2] Adicionar formulário de upload, confirmação literal, aviso destrutivo e estado de resultado na tela Angular.

## Phase 4: Documentação e validação

- [ ] T010 Atualizar `doc/API.md` e `doc/OPERATIONS.md`.
- [ ] T011 Executar pytest relevante e `npm run lint`; registrar qualquer limitação de ambiente.
