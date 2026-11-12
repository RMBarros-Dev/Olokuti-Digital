from . import base as base_settings
from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only-secret-key"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
MIDDLEWARE = [
    middleware
    for middleware in base_settings.MIDDLEWARE
    if middleware != "whitenoise.middleware.WhiteNoiseMiddleware"
]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
