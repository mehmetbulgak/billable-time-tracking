from decimal import Decimal
from typing import Self

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import Currency, OrganizationOwnedModel


class ClientQuerySet(models.QuerySet["Client"]):
    def active(self) -> Self:
        return self.filter(is_archived=False)


class Client(OrganizationOwnedModel):
    name = models.CharField(max_length=160)
    contact_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    payment_terms_days = models.PositiveSmallIntegerField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    objects = ClientQuerySet.as_manager()

    class Meta:
        ordering = ("name",)
        constraints = (
            models.UniqueConstraint(
                fields=("organization", "name"),
                name="clients_unique_name_per_organization",
            ),
            models.CheckConstraint(
                condition=Q(tax_rate__gte=0) & Q(tax_rate__lte=100),
                name="clients_tax_rate_between_0_and_100",
            ),
        )

    def __str__(self) -> str:
        return self.name

    @property
    def effective_payment_terms_days(self) -> int:
        if self.payment_terms_days is not None:
            return self.payment_terms_days
        return self.organization.default_payment_terms_days
