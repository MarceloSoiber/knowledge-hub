from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


RESTORE_REQUIRED_CHECKS = (
    "pgvector extension enabled",
    "source count matches",
    "chunk count matches the chosen embedding strategy",
    "category/tag/project relation counts match",
    "sample search returns expected restored content",
)
RESTORE_CONFIRMATION = "RESTAURAR BASE"
_operation_lock = asyncio.Lock()


class BackupOperationError(RuntimeError): pass


def _connection(database_url: str) -> tuple[str, dict[str, str]]:
    parts = urlsplit(database_url)
    if not parts.hostname or not parts.path: raise BackupOperationError("Configuração do banco incompatível.")
    password = parts.password
    env = os.environ.copy()
    if password: env["PGPASSWORD"] = password
    port = f":{parts.port}" if parts.port else ""
    return f"postgresql://{parts.username or 'postgres'}@{parts.hostname}{port}{parts.path}", env


def _execute(command: list[str], env: dict[str, str]) -> None:
    try:
        result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc: raise BackupOperationError("A operação administrativa não pôde ser concluída.") from exc
    if result.returncode: raise BackupOperationError("A operação no banco falhou. Verifique o backup e tente novamente.")


def _artifact_path(directory: Path) -> Path:
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return directory / f"knowledge-hub-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.dump"


async def create_database_backup(database_url: str, directory: Path) -> Path:
    url, env = _connection(database_url); path = _artifact_path(directory)
    try: await asyncio.to_thread(_execute, ["pg_dump", "--format=custom", "--no-owner", "--file", str(path), url], env)
    except Exception: path.unlink(missing_ok=True); raise
    os.chmod(path, 0o600); return path


async def restore_database_backup(database_url: str, directory: Path, dump_path: Path, confirmation: str) -> Path:
    if confirmation != RESTORE_CONFIRMATION: raise BackupOperationError("Digite RESTAURAR BASE para confirmar a substituição.")
    url, env = _connection(database_url)
    async with _operation_lock:
        await asyncio.to_thread(_execute, ["pg_restore", "--list", str(dump_path)], env)
        safety = await create_database_backup(database_url, directory)
        try: await asyncio.to_thread(_execute, ["pg_restore", "--clean", "--if-exists", "--no-owner", "--dbname", url, str(dump_path)], env)
        except Exception as exc: raise BackupOperationError(f"A restauração falhou; o backup de segurança foi preservado como {safety.name}.") from exc
    return safety


@dataclass(frozen=True)
class BackupCommandPlan:
    backup_command: str
    checksum_command: str
    encrypt_command: str
    restore_commands: list[str]
    schedule_allowed: bool
    checklist: tuple[str, ...]


def redact_database_url(database_url: str) -> str:
    parts = urlsplit(database_url)
    if parts.password is None:
        return database_url
    username = parts.username or ""
    hostname = parts.hostname or ""
    port = f":{parts.port}" if parts.port is not None else ""
    netloc = f"{username}:***@{hostname}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def build_backup_command_plan(
    *,
    database_url: str,
    backup_path: str,
    restore_database: str,
    restore_validated: bool = False,
) -> BackupCommandPlan:
    redacted_url = redact_database_url(database_url)
    return BackupCommandPlan(
        backup_command=(
            f"pg_dump --format=custom --no-owner --file {backup_path!r} {redacted_url!r}"
        ),
        checksum_command=f"sha256sum {backup_path!r} > {backup_path + '.sha256'!r}",
        encrypt_command=f"gpg --symmetric --cipher-algo AES256 {backup_path!r}",
        restore_commands=[
            f"createdb {restore_database!r}",
            f"psql {restore_database!r} -c 'CREATE EXTENSION IF NOT EXISTS vector;'",
            f"pg_restore --no-owner --dbname {restore_database!r} {backup_path!r}",
        ],
        schedule_allowed=restore_validated,
        checklist=RESTORE_REQUIRED_CHECKS,
    )


def assert_schedule_allowed(restore_validated: bool) -> None:
    if not restore_validated:
        raise ValueError("Scheduled backups are blocked until a restore test passes.")
