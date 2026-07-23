from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Project
from ..repositories.projects import get_project as get_project_record
from ..repositories.projects import get_project_by_normalized_name
from ..repositories.projects import list_project_sources as list_project_source_records
from ..repositories.projects import list_projects as list_project_records
from ..repositories.projects import list_projects_by_ids
from ..repositories.projects import serialize_project

PROJECT_STATUS_ACTIVE = "active"
PROJECT_STATUS_ARCHIVED = "archived"
PROJECT_STATUSES = {PROJECT_STATUS_ACTIVE, PROJECT_STATUS_ARCHIVED}


class ProjectNotFoundError(ValueError):
    pass


class ProjectConflictError(ValueError):
    pass


class ProjectStatusError(ValueError):
    pass


def normalize_project_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def validate_project_status(status: str) -> str:
    if status not in PROJECT_STATUSES:
        raise ProjectStatusError(f"Invalid project status: {status}.")
    return status


async def get_project(session: AsyncSession, project_id: int) -> Project:
    project = await get_project_record(session, project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project {project_id} does not exist.")
    return project


async def get_projects(session: AsyncSession, project_ids: list[int]) -> list[Project]:
    projects = await list_projects_by_ids(session, project_ids)
    projects_by_id = {project.id: project for project in projects}
    missing_ids = [
        project_id for project_id in project_ids if project_id not in projects_by_id
    ]
    if missing_ids:
        raise ProjectNotFoundError(f"Project {missing_ids[0]} does not exist.")
    return [projects_by_id[project_id] for project_id in project_ids]


async def list_projects(
    session: AsyncSession, status: str | None = None
) -> list[dict[str, object]]:
    if status is not None:
        validate_project_status(status)
    return await list_project_records(session, status=status)


async def list_project_sources(
    session: AsyncSession, project_id: int
) -> list[dict[str, object]]:
    await get_project(session, project_id)
    return await list_project_source_records(session, project_id)


async def create_project(
    session: AsyncSession,
    name: str,
    description: str | None = None,
) -> Project:
    normalized_name = normalize_project_name(name)
    if not normalized_name:
        raise ValueError("Project name must not be empty.")
    if await get_project_by_normalized_name(session, normalized_name) is not None:
        raise ProjectConflictError(f"Project '{normalized_name}' already exists.")

    project = Project(
        name=normalized_name,
        normalized_name=normalized_name,
        description=normalize_project_description(description),
        status=PROJECT_STATUS_ACTIVE,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def update_project(
    session: AsyncSession,
    project_id: int,
    name: str | None = None,
    description: str | None = None,
) -> Project:
    project = await get_project(session, project_id)
    if name is not None:
        normalized_name = normalize_project_name(name)
        if not normalized_name:
            raise ValueError("Project name must not be empty.")
        existing = await get_project_by_normalized_name(session, normalized_name)
        if existing is not None and existing.id != project.id:
            raise ProjectConflictError(f"Project '{normalized_name}' already exists.")
        project.name = normalized_name
        project.normalized_name = normalized_name
    if description is not None:
        project.description = normalize_project_description(description)
    await session.commit()
    await session.refresh(project)
    return project


async def archive_project(session: AsyncSession, project_id: int) -> Project:
    return await set_project_status(session, project_id, PROJECT_STATUS_ARCHIVED)


async def reactivate_project(session: AsyncSession, project_id: int) -> Project:
    return await set_project_status(session, project_id, PROJECT_STATUS_ACTIVE)


async def set_project_status(
    session: AsyncSession, project_id: int, status: str
) -> Project:
    project = await get_project(session, project_id)
    project.status = validate_project_status(status)
    await session.commit()
    await session.refresh(project)
    return project


def normalize_project_description(description: str | None) -> str | None:
    if description is None:
        return None
    cleaned = description.strip()
    return cleaned or None


def project_to_dict(project: Project) -> dict[str, object]:
    return serialize_project(project)
