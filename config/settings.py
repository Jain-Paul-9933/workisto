"""
Django settings for the home-services marketplace.

Design notes for review:
- We run on ASGI (daphne) from day one so the SAME server handles HTTP and the
  WebSocket chat later. That's why 'daphne' is the FIRST installed app.
- The database engine is the PostGIS backend, not the plain postgres one — that
  is what unlocks geo columns and ST_DWithin queries.
- Everything environment-specific is read from env vars (12-factor style), with
  dev-friendly defaults so a fresh clone still boots.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# --- Core -------------------------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# --- Applications -----------------------------------------------------------
INSTALLED_APPS = [
    "daphne",  # must precede staticfiles so runserver uses the ASGI server
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",  # GeoDjango — spatial fields & queries
    # Third-party
    "rest_framework",
    "corsheaders",
    "channels",
    # Local apps (bounded contexts). More get added as we build them.
    "accounts",
    "catalog",
    "providers",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # keep high in the stack
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# HTTP is handled by wsgi for classic deploys, but we run ASGI in dev+prod.
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --- Database (PostGIS) -----------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("POSTGRES_DB", "homeservices"),
        "USER": os.getenv("POSTGRES_USER", "homeservices"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "homeservices"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}


# --- Custom user ------------------------------------------------------------
# We swap in our own User (email login + role) BEFORE the first migration,
# because changing AUTH_USER_MODEL later is a painful migration.
AUTH_USER_MODEL = "accounts.User"


# --- Channels (WebSocket layer over Redis) ----------------------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [os.getenv("REDIS_URL", "redis://redis:6379/0")]},
    }
}


# --- Celery -----------------------------------------------------------------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
CELERY_TIMEZONE = "UTC"


# --- Caching & sessions -----------------------------------------------------
# Auth is cookie/session based on purpose — see docs/adr/0001-auth.md.
# Sessions use the cached_db backend: reads hit Redis (fast, shared across all
# web instances on Railway) while writes go THROUGH to Postgres, so a Redis
# restart or eviction never silently logs the whole marketplace out. Revocation
# stays instant — logout/ban is just a row delete.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("CACHE_URL", "redis://redis:6379/3"),
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"


# --- DRF --------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# --- CORS (Next.js dev servers) ---------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


# --- Password validation ----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- I18N / TZ --------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True  # store everything in UTC; critical for booking slot correctness


# --- Static -----------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
