from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from ..db.models import AppConfig


AUTH_TOKEN_KEY = "auth_token"


async def get_config_value(session: AsyncSession, key: str) -> str | None:
    value = await session.scalar(select(AppConfig.value).where(AppConfig.key == key))
    return value.strip() if value else None


async def get_auth_token(session: AsyncSession) -> str:
    token = await get_config_value(session, AUTH_TOKEN_KEY)
    return token or ""


async def set_config_value(session: AsyncSession, key: str, value: str) -> None:
    statement = (
        insert(AppConfig)
        .values(key=key, value=value)
        .on_conflict_do_update(
            index_elements=[AppConfig.key],
            set_={"value": value, "updated_at": func.now()},
        )
    )
    await session.execute(statement)
    await session.commit()
