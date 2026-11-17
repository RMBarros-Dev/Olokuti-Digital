from urllib.parse import unquote, urlparse

INSECURE_SECRET_KEYS = {
    "development-only-change-me",
    "replace-this-with-a-long-random-secret",
    "test-only-secret-key",
    "changeme",
    "secret",
}
INSECURE_EMAIL_BACKENDS = {
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
    "django.core.mail.backends.locmem.EmailBackend",
    "django.core.mail.backends.filebased.EmailBackend",
}
PLACEHOLDER_PASSWORDS = {"", "change-me", "change-this", "password"}


def validate_production_configuration(environ) -> dict:
    """Validate required production environment settings and fail closed on weak defaults."""
    if environ.get("DJANGO_DEBUG", "").strip().lower() == "true":
        raise ValueError("Production cannot run with DJANGO_DEBUG=true")

    secret_key = environ.get("DJANGO_SECRET_KEY", "").strip()
    if (
        not secret_key
        or secret_key.lower() in INSECURE_SECRET_KEYS
        or secret_key.startswith("django-insecure-")
        or len(secret_key) < 32
    ):
        raise ValueError("Set a strong, unique DJANGO_SECRET_KEY (>= 32 chars) for production")

    database_url = environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("Set a production PostgreSQL DATABASE_URL")
    if not database_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        raise ValueError("Production requires a PostgreSQL DATABASE_URL")
    parsed_db = urlparse(database_url)
    db_password = unquote(parsed_db.password or "").strip().lower()
    if db_password in PLACEHOLDER_PASSWORDS or "change-me" in db_password:
        raise ValueError("Set a production DATABASE_URL with a non-placeholder credential")

    raw_hosts = environ.get("DJANGO_ALLOWED_HOSTS", "")
    allowed_hosts = [host.strip() for host in raw_hosts.split(",") if host.strip()]
    if not allowed_hosts:
        raise ValueError("Set DJANGO_ALLOWED_HOSTS for production")
    if "*" in allowed_hosts:
        raise ValueError("Production DJANGO_ALLOWED_HOSTS must not contain a wildcard")

    raw_origins = environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
    csrf_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if not csrf_origins:
        raise ValueError("Set DJANGO_CSRF_TRUSTED_ORIGINS for production")
    if any(not origin.startswith("https://") for origin in csrf_origins):
        raise ValueError("Production DJANGO_CSRF_TRUSTED_ORIGINS must use https:// origins")

    hsts_seconds = int(environ.get("DJANGO_HSTS_SECONDS", "31536000"))
    if hsts_seconds < 300:
        raise ValueError("Production DJANGO_HSTS_SECONDS must be at least 300 seconds")

    email_backend = environ.get(
        "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
    ).strip()
    allow_console_email = (
        environ.get("DJANGO_ALLOW_CONSOLE_EMAIL", "false").strip().lower() == "true"
    )
    if email_backend == "django.core.mail.backends.console.EmailBackend" and allow_console_email:
        pass
    elif not email_backend or email_backend in INSECURE_EMAIL_BACKENDS:
        raise ValueError("Production cannot use a console, dummy, locmem, or file email backend")

    email_host = environ.get("EMAIL_HOST", "").strip()
    if email_backend == "django.core.mail.backends.smtp.EmailBackend":
        if not email_host or email_host == "smtp.example.com":
            raise ValueError("Set a real EMAIL_HOST for production SMTP delivery")
        use_tls = environ.get("EMAIL_USE_TLS", "true").strip().lower() == "true"
        use_ssl = environ.get("EMAIL_USE_SSL", "false").strip().lower() == "true"
        if use_tls and use_ssl:
            raise ValueError("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True")
        if not (use_tls or use_ssl):
            raise ValueError("Production SMTP requires EMAIL_USE_TLS or EMAIL_USE_SSL")
        default_from = environ.get("DEFAULT_FROM_EMAIL", "").strip().lower()
        if not default_from or default_from.endswith(".local"):
            raise ValueError("Set a non-local DEFAULT_FROM_EMAIL for production")

    return {
        "SECRET_KEY": secret_key,
        "ALLOWED_HOSTS": [*allowed_hosts, "healthcheck.railway.app"],
        "CSRF_TRUSTED_ORIGINS": csrf_origins,
        "SECURE_HSTS_SECONDS": hsts_seconds,
        "EMAIL_BACKEND": email_backend,
    }
