from config.settings.base import BASE_DIR, database_from_url


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


def test_supabase_transaction_pooler_disables_server_side_cursors():
    database = database_from_url(
        "postgresql://olokuti_app.ref:secret@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true"
    )

    assert database["USER"] == "olokuti_app.ref"
    assert database["PORT"] == "6543"
    assert database["OPTIONS"] == {"sslmode": "require"}
    assert database["CONN_MAX_AGE"] == 0
    assert database["DISABLE_SERVER_SIDE_CURSORS"] is True


