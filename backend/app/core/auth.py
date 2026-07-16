from secrets import compare_digest

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session
from ..services.config import get_auth_token


bearer_scheme = HTTPBearer(auto_error=False)


def is_valid_token(provided_token: str, expected_token: str) -> bool:
    if not expected_token:
        return True
    return compare_digest(provided_token, expected_token)


async def require_auth_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> None:
    expected_token = await get_auth_token(session)
    if not expected_token:
        raise_token_error()

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise_token_error()

    if not is_valid_token(credentials.credentials, expected_token):
        raise_token_error()


def raise_token_error() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
