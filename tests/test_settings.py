import importlib
import os
from pathlib import Path

import pytest

from config.settings.base import BASE_DIR, database_from_url
from config.settings.validators import validate_production_configuration


def _valid_prod_env():
    return {
        "DJANGO_SECRET_KEY": "a-very-strong-random-production-secret-key-0123456789",
        "DATABASE_URL": "postgresql://olokuti:StrongPass2026!@db.example.test:5432/olokuti",
        "DJANGO_ALLOWED_HOSTS": "olokuti.example.com",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "https://olokuti.example.com",
        "DJANGO_EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "EMAIL_HOST": "smtp.sendgrid.net",
        "EMAIL_USE_TLS": "true",
        "DEFAULT_FROM_EMAIL": "no-reply@olokuti.example.com",
    }


def test_postgresql_url_is_parsed_with_escaped_credentials_and_options():
    database = database_from_url(
        "postgresql://catalog:p%40ss%21@db.example.test:5433/olokuti?sslmode=require"
    )

    assert database["ENGINE"] == "django.db.backends.postgresql"
    assert database["NAME"] == "olokuti"
    assert database["USER"] == "catalog"
    assert database["PASSWORD"] == "p@ss!"
    assert database["HOST"] == "db.example.test"
    assert database["PORT"] == "5433"
    assert database["OPTIONS"] == {"sslmode": "require"}


def test_sqlite_relative_url_resolves_inside_base_dir():
    database = database_from_url("sqlite:///db.sqlite3")

    assert database["ENGINE"] == "django.db.backends.sqlite3"
    assert database["NAME"] == str(BASE_DIR / "db.sqlite3")


def test_sqlite_memory_and_invalid_database_url():
    assert database_from_url("sqlite:///:memory:")["NAME"] == ":memory:"
    with pytest.raises(ValueError, match="postgresql:// or sqlite://"):
        database_from_url("mysql://user:pass@localhost/db")


def test_supabase_transaction_pooler_disables_server_side_cursors():
    database = database_from_url(
        "postgresql://olokuti_app.ref:secret@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true"
    )

    assert database["USER"] == "olokuti_app.ref"
    assert database["PORT"] == "6543"
    assert database["OPTIONS"] == {"sslmode": "require"}
    assert database["CONN_MAX_AGE"] == 0
    assert database["DISABLE_SERVER_SIDE_CURSORS"] is True


def test_production_validator_accepts_valid_env():
    cfg = validate_production_configuration(_valid_prod_env())
    assert "olokuti.example.com" in cfg["ALLOWED_HOSTS"]
    assert "healthcheck.railway.app" in cfg["ALLOWED_HOSTS"]
    assert cfg["CSRF_TRUSTED_ORIGINS"] == ["https://olokuti.example.com"]
    assert cfg["SECURE_HSTS_SECONDS"] == 31536000


@pytest.mark.parametrize(
    ("overrides", "error_fragment"),
    [
        ({"DJANGO_DEBUG": "true"}, "DJANGO_DEBUG=true"),
        ({"DJANGO_SECRET_KEY": ""}, "DJANGO_SECRET_KEY"),
        ({"DJANGO_SECRET_KEY": "development-only-change-me"}, "DJANGO_SECRET_KEY"),
        ({"DJANGO_SECRET_KEY": "django-insecure-short"}, "DJANGO_SECRET_KEY"),
        ({"DATABASE_URL": ""}, "PostgreSQL DATABASE_URL"),
        ({"DATABASE_URL": "sqlite:///db.sqlite3"}, "PostgreSQL DATABASE_URL"),
        ({"DATABASE_URL": "postgresql://u:change-me@h:5432/db"}, "non-placeholder"),
        ({"DJANGO_ALLOWED_HOSTS": ""}, "DJANGO_ALLOWED_HOSTS"),
        ({"DJANGO_ALLOWED_HOSTS": "*"}, "wildcard"),
        ({"DJANGO_CSRF_TRUSTED_ORIGINS": ""}, "DJANGO_CSRF_TRUSTED_ORIGINS"),
        ({"DJANGO_CSRF_TRUSTED_ORIGINS": "http://insecure.example.com"}, "https://"),
        ({"DJANGO_HSTS_SECONDS": "60"}, "at least 300"),
        (
            {"DJANGO_EMAIL_BACKEND": "django.core.mail.backends.console.EmailBackend"},
            "console, dummy",
        ),
        ({"EMAIL_HOST": ""}, "EMAIL_HOST"),
        ({"EMAIL_HOST": "smtp.example.com"}, "EMAIL_HOST"),
        ({"EMAIL_USE_TLS": "false", "EMAIL_USE_SSL": "false"}, "EMAIL_USE_TLS or EMAIL_USE_SSL"),
        ({"DEFAULT_FROM_EMAIL": "no-reply@olokuti.local"}, "non-local DEFAULT_FROM_EMAIL"),
    ],
)
def test_production_validator_rejects_insecure_configs(overrides, error_fragment):
    env = _valid_prod_env()
    env.update(overrides)
    with pytest.raises(ValueError, match=error_fragment):
        validate_production_configuration(env)


def test_wsgi_and_asgi_default_to_production_settings():
    wsgi_src = (Path(BASE_DIR) / "config" / "wsgi.py").read_text(encoding="utf-8")
    asgi_src = (Path(BASE_DIR) / "config" / "asgi.py").read_text(encoding="utf-8")
    assert (
        'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")' in wsgi_src
    )
    assert (
        'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")' in asgi_src
    )


def test_production_module_import_enforces_validation(monkeypatch):
    for key, val in _valid_prod_env().items():
        monkeypatch.setenv(key, val)
    monkeypatch.setenv("DJANGO_TRUST_PROXY_SSL_HEADER", "true")
    monkeypatch.delenv("DJANGO_DEBUG", raising=False)

    prod_mod = importlib.import_module("config.settings.production")
    importlib.reload(prod_mod)
    assert prod_mod.DEBUG is False
    assert prod_mod.SESSION_COOKIE_SECURE is True
    assert prod_mod.CSRF_COOKIE_SECURE is True
    assert prod_mod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")

    monkeypatch.setenv("DJANGO_SECRET_KEY", "weak")
    with pytest.raises(ValueError, match="DJANGO_SECRET_KEY"):
        importlib.reload(prod_mod)
    # Restore valid state after reload failure
    os.environ["DJANGO_SECRET_KEY"] = _valid_prod_env()["DJANGO_SECRET_KEY"]
    importlib.reload(prod_mod)


def test_health_check_with_db_query(client, db):
    response = client.get("/health?db=1")
    assert response.status_code == 200
    assert response.content == b"ok"
