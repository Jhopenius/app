from __future__ import annotations

import os
import subprocess
from pathlib import Path

from vsuet_accounting.config import get_settings


def backup_database(backup_path: str) -> Path:
    settings = get_settings()
    backup_file = Path(backup_path)
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.postgres_password

    subprocess.run(
        [
            "pg_dump",
            "-h",
            settings.postgres_host,
            "-p",
            str(settings.postgres_port),
            "-U",
            settings.postgres_user,
            "--clean",
            "--if-exists",
            "-f",
            str(backup_file),
            settings.postgres_db,
        ],
        check=True,
        env=env,
    )

    return backup_file


def restore_database(backup_path: str) -> None:
    settings = get_settings()
    backup_file = Path(backup_path)

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.postgres_password

    subprocess.run(
        [
            "psql",
            "-h",
            settings.postgres_host,
            "-p",
            str(settings.postgres_port),
            "-U",
            settings.postgres_user,
            "-d",
            settings.postgres_db,
            "-f",
            str(backup_file),
        ],
        check=True,
        env=env,
    )
