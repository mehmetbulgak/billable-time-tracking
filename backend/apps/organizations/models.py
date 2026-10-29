from zoneinfo import ZoneInfo

from django.db import models

from apps.core.models import Currency, TimeStampedModel
from apps.organizations.validators import validate_timezone


class Organization(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True)
    timezone = models.CharField(
        max_length=64,
        default="Europe/Istanbul",
        validators=[validate_timezone],
    )
    default_currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
    )
    default_payment_terms_days = models.PositiveSmallIntegerField(default=14)
    invoice_prefix = models.CharField(max_length=10, default="INV")
    next_invoice_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)
