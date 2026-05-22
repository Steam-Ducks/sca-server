import os

from config.settings import *  # noqa: F401,F403

# Em CI (DB_HOST setado) usa o Postgres herdado do settings.py — testes
# rodam contra a mesma engine de produção, validando migrations e schemas
# silver. Localmente, sem Postgres disponível, cai pra SQLite em memória
# e remove sca_data do app registry (models silver usam tipos Postgres
# incompatíveis com SQLite; seus testes são puramente unit-mocked).
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
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
