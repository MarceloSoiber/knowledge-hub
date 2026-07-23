from __future__ import annotations

import pytest

from backend.app.services.backup import (
    RESTORE_REQUIRED_CHECKS,
    assert_schedule_allowed,
    build_backup_command_plan,
    redact_database_url,
)


def test_redact_database_url_hides_password() -> None:
    redacted = redact_database_url(
        "postgresql+asyncpg://postgres:secret@localhost:5432/knowledge_hub"
    )

    assert "secret" not in redacted
    assert "postgres:***@localhost:5432" in redacted


def test_backup_command_plan_contains_restore_checklist_without_secret() -> None:
    plan = build_backup_command_plan(
        database_url="postgresql://user:secret@db:5432/hub",
        backup_path="/backups/hub.dump",
        restore_database="hub_restore",
    )

    rendered = "\n".join(
        [
            plan.backup_command,
            plan.checksum_command,
            plan.encrypt_command,
            *plan.restore_commands,
        ]
    )
    assert "secret" not in rendered
    assert "pg_dump --format=custom" in plan.backup_command
    assert "CREATE EXTENSION IF NOT EXISTS vector" in plan.restore_commands[1]
    assert set(RESTORE_REQUIRED_CHECKS).issubset(set(plan.checklist))
    assert plan.schedule_allowed is False


def test_scheduled_backup_requires_restore_validation() -> None:
    with pytest.raises(ValueError, match="restore test passes"):
        assert_schedule_allowed(False)

    assert_schedule_allowed(True)


def test_backup_plan_allows_schedule_after_validation() -> None:
    plan = build_backup_command_plan(
        database_url="postgresql://user@db/hub",
        backup_path="/backups/hub.dump",
        restore_database="hub_restore",
        restore_validated=True,
    )

    assert plan.schedule_allowed is True
