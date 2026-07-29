# Implementation Plan: Backup e Restauração Administrativos

**Branch**: `022-backup-restore-admin` | **Date**: 2026-07-29 | **Spec**: `spec.md`

## Summary

Adicionar endpoints administrativos protegidos para download de dump PostgreSQL e restauração confirmada que substitui a base, com backup de segurança prévio. Criar tela Angular de operações e incluir `postgresql-client` na imagem de backend.

## Technical Context

**Language/Version**: Python 3.13, Angular/TypeScript

**Dependencies**: FastAPI, Pydantic v2, PostgreSQL/pgvector, Angular HttpClient

**Storage**: PostgreSQL; artefatos temporários em diretório privado do backend durante a operação

**Testing**: pytest com processos PostgreSQL simulados; Vitest/TypeScript para a tela

**Constraints**: operação serializada, confirmação literal, backup prévio obrigatório, sem segredos em logs, upload máximo de 1 GB

## Constitution Check

Passa: rotas ficam finas, subprocessos ficam no serviço, contratos tipados, testes cobrem a operação destrutiva e documentação é atualizada.

## Project Structure

```text
backend/app/
├── api/routes/operations.py
├── schemas/operations.py
└── services/backup.py
frontend/src/app/
├── features/operations/
└── core/knowledge-api.service.ts
tests/test_backup_restore_admin.py
```

**Structure Decision**: manter o serviço de backup existente como fronteira para processos PostgreSQL; expor uma rota administrativa sob o prefixo autenticado existente e uma tela exclusiva de operações.

## Risk Notes

- A restauração substitui dados: confirmação e backup prévio são invariantes de serviço, não apenas de UI.
- O container precisa do `pg_dump`, `pg_restore` e `psql` compatíveis com PostgreSQL 16.
- A execução real exige credenciais com permissões de dump/restauração; falhas são retornadas de forma sanitizada.
