from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("PUSULA_DJANGO_SECRET_KEY", "development-only-change-me")
DEBUG = os.environ.get("PUSULA_DEBUG", "0") == "1"
ALLOWED_HOSTS = [item for item in os.environ.get("PUSULA_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if item]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "pusula.teams",
    "pusula.mizan",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "pusula.urls"
WSGI_APPLICATION = "pusula.wsgi.application"
ASGI_APPLICATION = "pusula.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PUSULA_DB_NAME", "pusula"),
        "USER": os.environ.get("PUSULA_DB_USER", "pusula"),
        "PASSWORD": os.environ.get("PUSULA_DB_PASSWORD", ""),
        "HOST": os.environ.get("PUSULA_DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("PUSULA_DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

USE_TZ = True
TIME_ZONE = "UTC"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logto is the identity provider. These values describe the expected OIDC/API-resource boundary;
# JWT signature validation is added as a separate acceptance-tested adapter, never hand-rolled here.
LOGTO_ENDPOINT = os.environ.get("PUSULA_LOGTO_ENDPOINT", "")
LOGTO_API_RESOURCE = os.environ.get("PUSULA_LOGTO_API_RESOURCE", "https://pusula.local/api")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
