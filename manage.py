#!/usr/bin/env python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _resolve_supabase_pooler(env_file: Path) -> None:
    """Automatically switch between aws-0 and aws-1 Supabase pooler if needed."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "aws-0-eu-west-1.pooler.supabase.com" not in db_url:
        return
    try:
        import psycopg

        with psycopg.connect(db_url, connect_timeout=4):
            return
    except Exception as exc:
        if "Tenant or user not found" in str(exc):
            alt_url = db_url.replace(
                "aws-0-eu-west-1.pooler.supabase.com",
                "aws-1-eu-west-1.pooler.supabase.com",
            )
            os.environ["DATABASE_URL"] = alt_url
            if env_file.exists():
                text = env_file.read_text(encoding="utf-8")
                env_file.write_text(
                    text.replace(
                        "aws-0-eu-west-1.pooler.supabase.com",
                        "aws-1-eu-west-1.pooler.supabase.com",
                    ),
                    encoding="utf-8",
                )


if __name__ == "__main__":
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    if len(sys.argv) > 1 and sys.argv[1] in {"runserver", "migrate", "check"}:
        _resolve_supabase_pooler(env_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
