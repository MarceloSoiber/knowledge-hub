from __future__ import annotations

import argparse
import json

from backend.app.core.settings import get_settings
from backend.app.services.backup import build_backup_command_plan


def backup_main() -> None:
    parser = argparse.ArgumentParser(
        description="Render redacted Knowledge Hub backup and restore commands."
    )
    parser.add_argument("--backup-path", required=True, help="Destination backup artifact path.")
    parser.add_argument(
        "--restore-database",
        required=True,
        help="Empty database name/URL used for restore validation.",
    )
    parser.add_argument(
        "--restore-validated",
        action="store_true",
        help="Mark scheduling examples as allowed because a restore test has passed.",
    )
    args = parser.parse_args()
    plan = build_backup_command_plan(
        database_url=get_settings().postgres_dsn,
        backup_path=args.backup_path,
        restore_database=args.restore_database,
        restore_validated=args.restore_validated,
    )
    print(json.dumps(plan.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    backup_main()
