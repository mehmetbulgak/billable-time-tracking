import secrets

from config.settings.base import *

SECRET_KEY = secrets.token_urlsafe(64)
