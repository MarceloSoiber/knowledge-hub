import asyncio
from getpass import getpass

from backend.app.db.init import init_db
from backend.app.db.session import SessionLocal
from backend.app.services.config import AUTH_TOKEN_KEY, set_config_value


async def set_auth_token() -> None:
    token = getpass("AUTH_TOKEN: ").strip()
    if not token:
        raise SystemExit("AUTH_TOKEN must not be empty.")

    await init_db()
    async with SessionLocal() as session:
        await set_config_value(session, AUTH_TOKEN_KEY, token)

    print("auth_token saved in app_config.")


def set_auth_token_main() -> None:
    asyncio.run(set_auth_token())
