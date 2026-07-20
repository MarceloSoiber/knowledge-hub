from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.models import DocumentSource, Project, document_source_projects
from .sources import serialize_source


async def get_project(session: AsyncSession, project_id: int) -> Project | None:
    return await session.get(Project, project_id)


async def get_project_by_normalized_name(
    session: AsyncSession, normalized_name: str
) -> Project | None:
    return await session.scalar(
        select(Project).where(Project.normalized_name == normalized_name)
    )


async def list_projects_by_ids(session: AsyncSession, project_ids: list[int]) -> list[Project]:
    rows = (
        (
            await session.execute(
                select(Project).where(Project.id.in_(project_ids))
            )
        )
        .scalars()
        .all()
    )
    return list(rows)


async def list_projects(
    session: AsyncSession, status: str | None = None
) -> list[dict[str, object]]:
    statement = select(Project).order_by(Project.name)
    if status is not None:
        statement = statement.where(Project.status == status)
    rows = ((await session.execute(statement)).scalars().all())
    return [serialize_project(project) for project in rows]


async def list_project_sources(
    session: AsyncSession, project_id: int
) -> list[dict[str, object]]:
    rows = (
        (
            await session.execute(
                select(DocumentSource)
                .join(
                    document_source_projects,
                    document_source_projects.c.document_source_id == DocumentSource.id,
                )
                .options(
                    selectinload(DocumentSource.categories),
                    selectinload(DocumentSource.tags),
                    selectinload(DocumentSource.projects),
                )
                .where(document_source_projects.c.project_id == project_id)
                .order_by(DocumentSource.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [serialize_source(source) for source in rows]


def serialize_project(project: Project) -> dict[str, object]:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
