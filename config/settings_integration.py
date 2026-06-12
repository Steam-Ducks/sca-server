"""
Django settings para testes de INTEGRAÇÃO.

Diferente do settings_test.py (SQLite + sem sca_data), este módulo usa
PostgreSQL real e mantém sca_data registrado — permitindo que os modelos
silver/gold/audit sejam criados e consultados sem mocks.

Como usar localmente:
    # 1. Suba o banco
    docker run -d -e POSTGRES_DB=test_db -e POSTGRES_USER=test_user \
      -e POSTGRES_PASSWORD=test_password -p 5432:5432 postgres:16-alpine

    # 2. Crie os schemas
    PGPASSWORD=test_password psql -h localhost -U test_user -d test_db \
      -c "CREATE SCHEMA IF NOT EXISTS silver;
          CREATE SCHEMA IF NOT EXISTS gold;
          CREATE SCHEMA IF NOT EXISTS audit;"

    # 3. Rode as migrations
    python manage.py migrate --settings=config.settings_integration

    # 4. Rode os testes
    pytest --ds=config.settings_integration -m integration --reuse-db -v
"""

import os

from config.settings import *  # noqa: F401,F403

# ── PostgreSQL — banco real ───────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "test_db"),
        "USER": os.environ.get("DB_USER", "test_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "test_password"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        # TEST.NAME aponta para o mesmo banco já criado pelo CI.
        # Combinado com --reuse-db, o pytest reutiliza o banco existente
        # (com schemas + tabelas criados pelos steps anteriores do workflow).
        "TEST": {
            "NAME": os.environ.get("DB_NAME", "test_db"),
        },
    }
}

# ── sca_data: mantido — PostgreSQL suporta os schemas silver.* ───────────────
# (settings_test.py remove sca_data porque SQLite não suporta esses schemas)
INSTALLED_APPS = [app for app in INSTALLED_APPS]  # noqa: F405
