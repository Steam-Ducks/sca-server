import os

# Prevent load_dotenv() in settings.py from overriding DB_HOST when no
# real test database is explicitly configured. setdefault does not touch
# an already-set value, so a CI-provided DB_HOST is still respected.
os.environ.setdefault("DB_HOST", "")

from config.settings import *  # noqa: F401,F403

# Em CI (DB_HOST setado) usa o Postgres herdado do settings.py — testes
# rodam contra a mesma engine de produção, validando migrations e schemas
# silver. Localmente, sem Postgres disponível, cai pra SQLite em memória
# e remove sca_data do app registry (models silver usam tipos Postgres
# incompatíveis com SQLite; seus testes são puramente unit-mocked).
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

if not os.environ.get("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    INSTALLED_APPS = [
        app for app in INSTALLED_APPS if not app.startswith("sca_data")  # noqa: F405
    ]
