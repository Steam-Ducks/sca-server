from config.settings import *  # noqa: F401,F403

DEBUG = False

# Emails impressos no console em vez de enviados
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
