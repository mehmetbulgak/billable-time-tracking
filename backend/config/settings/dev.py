from config.settings.base import *

DEBUG = True
SECRET_KEY = SECRET_KEY or "dev-insecure-secret-key-change-me"
ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1"]
CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS or ["http://localhost:5173", "http://127.0.0.1:5173"]
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = ()
