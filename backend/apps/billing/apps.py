from importlib import import_module

from django.apps import AppConfig


class BillingConfig(AppConfig):
    name = "apps.billing"
    label = "billing"

    def ready(self) -> None:
        import_module("apps.billing.receivers")
