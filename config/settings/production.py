import os

from .base import *  # noqa: F403, F405
from .validators import validate_production_configuration

_prod_cfg = validate_production_configuration(os.environ)

DEBUG = False
SECRET_KEY = _prod_cfg["SECRET_KEY"]
# Railway sends health checks from this hostname; keep application hosts explicit.
ALLOWED_HOSTS = _prod_cfg["ALLOWED_HOSTS"]
CSRF_TRUSTED_ORIGINS = _prod_cfg["CSRF_TRUSTED_ORIGINS"]
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^health/?$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = _prod_cfg["SECURE_HSTS_SECONDS"]
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
EMAIL_BACKEND = _prod_cfg["EMAIL_BACKEND"]
if os.environ.get("DJANGO_TRUST_PROXY_SSL_HEADER", "false").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
