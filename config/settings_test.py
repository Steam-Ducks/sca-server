from config.settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Remove sca_data do app registry: os models silver usam schemas PostgreSQL
# incompatíveis com SQLite. Os testes de sca_data são pure unit tests (sem
# @pytest.mark.django_db) e não precisam que o app esteja registrado.
INSTALLED_APPS = [
    app for app in INSTALLED_APPS if not app.startswith("sca_data")
]  # noqa: F405
