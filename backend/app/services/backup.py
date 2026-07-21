from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


RESTORE_REQUIRED_CHECKS = (
    "pgvector extension enabled",
    "source count matches",
    "chunk count matches the chosen embedding strategy",
    "category/tag/project relation counts match",
    "sample search returns expected restored content",
)


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
