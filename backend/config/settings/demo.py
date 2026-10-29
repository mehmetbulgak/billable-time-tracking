"""Single-container, disposable portfolio demo. Never use for customer data."""

from config.settings.prod import *

ROOT_URLCONF = "config.demo_urls"
DEMO_MODE = True
DATABASES["default"].update(
    NAME="billable",
    USER="app",
    PASSWORD="",
    HOST="/run/postgresql/billable",
    PORT="",
    CONN_MAX_AGE=0,
)
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
if hostname := env.str("RENDER_EXTERNAL_HOSTNAME", default=""):
    ALLOWED_HOSTS.append(hostname)
    CSRF_TRUSTED_ORIGINS = [f"https://{hostname}"]
    WEBSOCKET_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.dummy.EmailBackend"}}
WHITENOISE_ROOT = BASE_DIR / "frontend_dist"

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "NUM_PROXIES": 1,
    "DEFAULT_THROTTLE_RATES": {
        **REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
        "anon": "120/minute",
        "user": "600/minute",
    },
}
