from config.settings.base import *

SECRET_KEY = "test-secret-key-for-the-billable-test-suite"
DEBUG = False
AUTH_THROTTLING_ENABLED = False
WEBSOCKET_ALLOWED_ORIGINS = ["http://testserver"]
ALLOWED_HOSTS = ["testserver", "localhost"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = ()
LOGGING = {**LOGGING, "root": {"handlers": ["console"], "level": "WARNING"}}
