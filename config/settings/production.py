import os

from . import base as base_settings
from .base import *  # noqa: F403, F405

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
if not os.environ.get("DATABASE_URL") or "change-me" in base_settings.DATABASE_URL.lower():
    raise ValueError("Set a production DATABASE_URL with a non-placeholder credential")
if not base_settings.DATABASE_URL.startswith(
    ("postgres://", "postgresql://", "postgresql+psycopg://")
):
    raise ValueError("Production requires a PostgreSQL DATABASE_URL")
if not os.environ.get("DJANGO_ALLOWED_HOSTS"):
    raise ValueError("Set DJANGO_ALLOWED_HOSTS for production")
if "*" in base_settings.ALLOWED_HOSTS:
    raise ValueError("Production DJANGO_ALLOWED_HOSTS must not contain a wildcard")
if not os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS"):
    raise ValueError("Set DJANGO_CSRF_TRUSTED_ORIGINS for production")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend" and not base_settings.EMAIL_HOST:
    raise ValueError("Set EMAIL_HOST for production SMTP password-reset email")
if os.environ.get("DJANGO_TRUST_PROXY_SSL_HEADER", "false").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
