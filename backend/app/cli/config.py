import asyncio
import argparse
import re
import secrets
from getpass import getpass

from backend.app.db.init import init_db
from backend.app.db.session import SessionLocal
from backend.app.services.config import AUTH_TOKEN_KEY, set_config_value


TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,256}$")


def generate_auth_token() -> str:
    return secrets.token_urlsafe(48)


def validate_auth_token(token: str) -> str:
    normalized_token = token.strip()
    if not normalized_token:
        raise ValueError("AUTH_TOKEN must not be empty.")
    if not TOKEN_PATTERN.fullmatch(normalized_token):
        raise ValueError(
            "AUTH_TOKEN must be 32-256 characters and contain only letters, numbers, "
            "hyphen and underscore."
        )
    return normalized_token


async def save_auth_token(token: str) -> None:
    normalized_token = validate_auth_token(token)

    await init_db()
    async with SessionLocal() as session:
        await set_config_value(session, AUTH_TOKEN_KEY, normalized_token)

    print("auth_token saved in app_config.")


async def set_auth_token(generate: bool = False) -> None:
    if generate:
        token = generate_auth_token()
        await save_auth_token(token)
        print(f"generated token: {token}")
        return

    token = getpass("AUTH_TOKEN: ")
    try:
        await save_auth_token(token)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def set_auth_token_main() -> None:
    parser = argparse.ArgumentParser(description="Save the Knowledge Hub auth token.")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate a strong token and save it without prompting.",
    )
    args = parser.parse_args()
    asyncio.run(set_auth_token(generate=args.generate))
