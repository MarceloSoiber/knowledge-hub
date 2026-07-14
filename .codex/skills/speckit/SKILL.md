---
name: speckit
description: Spec Kit workflow for this repository. Use when the user asks to integrate or use GitHub Spec Kit, create or refine specs, generate implementation plans or task lists, implement from specs, analyze spec/plan/task consistency, update the project constitution, or convert feature ideas into files under specs/ and .specify/.
---

# Speckit

## Overview

Use this skill to run a spec-first workflow in this repository while adapting GitHub Spec Kit assets for Codex. Prefer the canonical project files in `.specify/`, `specs/`, `.github/agents/`, and `.github/prompts/`.

## Workflow

1. **Specify**: Turn the user idea into `specs/<feature-id>/spec.md`.
2. **Plan**: Create or update `specs/<feature-id>/plan.md` using `.specify/templates/plan-template.md`.
3. **Tasks**: Create or update `specs/<feature-id>/tasks.md` using `.specify/templates/tasks-template.md`.
4. **Implement**: Make code changes task by task, keeping edits scoped and aligned with the spec.
5. **Analyze**: Check consistency across spec, plan, tasks, constitution, and implementation.

When the user asks for a full flow, run the stages in order and stop for clarification only when a missing decision would materially change the design.

## Repo Conventions

- Keep backend business logic in `backend/app/services`.
- Keep FastAPI routes thin in `backend/app/api/routes`.
- Use PostgreSQL with `pgvector` assumptions for persistence and vector search.
- Use Pydantic v2 schemas in `backend/app/schemas`.
- Keep MCP tools short, domain-oriented, and aligned with the FastMCP SDK approach.
- Keep the frontend simple and focused on status, ingestion, and search.
- Prefer tests under `tests/`; use `.venv/bin/python -m pytest` when verifying Python behavior.
- Update `doc/API.md` when API behavior changes.

## Stage Details

### Specify

- Read `.specify/memory/constitution.md` before drafting requirements.
- Create a feature folder under `specs/` with a stable numeric prefix when one does not exist, such as `002-hybrid-search`.
- Use `.specify/templates/spec-template.md` when available.
- Capture user stories, acceptance criteria, functional requirements, edge cases, and out-of-scope items.
- Do not jump into implementation details unless the spec template asks for them.

### Plan

- Read the spec and constitution first.
- Use `.specify/templates/plan-template.md`.
- Include technical context, affected files, data model/API implications, test strategy, and risk notes.
- Align decisions with this repo's FastAPI, SQLAlchemy, pgvector, MCP, and Vite/TypeScript stack.

### Tasks

- Read spec and plan first.
- Use `.specify/templates/tasks-template.md`.
- Produce ordered, testable tasks with file paths where possible.
- Separate setup, tests, implementation, documentation, and verification.
- Mark dependencies and parallelizable work only when that is genuinely useful.

### Implement

- Read `tasks.md`, then implement in small coherent batches.
- Preserve user changes and avoid unrelated refactors.
- Add or update tests proportionally to the behavior touched.
- Keep documentation changes close to the behavior changed.
- Report any task that cannot be completed and why.

### Analyze

- Compare `spec.md`, `plan.md`, `tasks.md`, `.specify/memory/constitution.md`, and touched code.
- Lead with contradictions, missing requirements, ambiguous tasks, or untested critical paths.
- Prefer concrete file/line references when reviewing existing artifacts.

## Original Spec Kit Assets

Use the GitHub Spec Kit assets in `.github/agents/` and `.github/prompts/` as detailed references when the user explicitly asks for the original GitHub/Copilot flow or when a stage needs more procedural detail.

Common mappings:

- `speckit.specify.agent.md`: detailed specification workflow.
- `speckit.plan.agent.md`: implementation planning.
- `speckit.tasks.agent.md`: task generation.
- `speckit.implement.agent.md`: implementation execution.
- `speckit.analyze.agent.md`: consistency analysis.
- `speckit.constitution.agent.md`: constitution updates.
- `speckit.clarify.agent.md`: requirement clarification.
- `speckit.checklist.agent.md`: checklist generation.
- `speckit.converge.agent.md`: converge scattered artifacts.
- `speckit.taskstoissues.agent.md`: convert tasks to GitHub issues.

Load only the specific agent file needed for the current stage.
