from datetime import date
from decimal import Decimal
from typing import Self

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeBoundary, RangeOperators
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, F, Func, OuterRef, Q
from django.utils.functional import cached_property

from apps.billing.domain.types import BillingModel, ContractTerms, LineKind
from apps.core.choices import choices_for
from apps.core.models import OrganizationOwnedModel
from apps.core.periods import MonthPeriod

NON_NEGATIVE = MinValueValidator(Decimal("0"))


class DateRange(Func):
    function = "DATERANGE"
    output_field = DateRangeField()


class RoundingIncrement(models.IntegerChoices):
    ONE_MINUTE = 1, "1 minute"
    SIX_MINUTES = 6, "6 minutes"
    FIFTEEN_MINUTES = 15, "15 minutes"
    THIRTY_MINUTES = 30, "30 minutes"
    ONE_HOUR = 60, "1 hour"


class ContractQuerySet(models.QuerySet["Contract"]):
    def overlapping(self, start: date, end: date) -> Self:
        return self.filter(starts_on__lte=end).filter(
            Q(ends_on__isnull=True) | Q(ends_on__gte=start)
        )

    def with_invoice_flag(self) -> Self:
        return self.annotate(
            has_invoices=Exists(Invoice.objects.filter(contract=OuterRef("pk"))),
        )


class Contract(OrganizationOwnedModel):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="contracts",
    )
    billing_model = models.CharField(max_length=16, choices=choices_for(BillingModel))
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[NON_NEGATIVE]
    )
    monthly_fee = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[NON_NEGATIVE]
    )
    included_hours = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True, validators=[NON_NEGATIVE]
    )
    overage_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[NON_NEGATIVE]
    )
    rollover_cap_hours = models.DecimalField(
        max_digits=7, decimal_places=2, default=Decimal("0.00"), validators=[NON_NEGATIVE]
    )
    rounding_increment_minutes = models.PositiveSmallIntegerField(
        choices=RoundingIncrement.choices,
        default=RoundingIncrement.FIFTEEN_MINUTES,
    )

    objects = ContractQuerySet.as_manager()

    class Meta:
        ordering = ("client__name", "-starts_on")
        constraints = (
            models.CheckConstraint(
                condition=Q(ends_on__isnull=True) | Q(ends_on__gte=F("starts_on")),
                name="contracts_end_on_or_after_start",
            ),
            models.CheckConstraint(
                condition=~Q(billing_model=BillingModel.HOURLY.value)
                | Q(hourly_rate__isnull=False),
                name="contracts_hourly_requires_rate",
            ),
            models.CheckConstraint(
                condition=~Q(billing_model=BillingModel.RETAINER.value)
                | Q(
                    monthly_fee__isnull=False,
                    included_hours__isnull=False,
                    overage_rate__isnull=False,
                ),
                name="contracts_retainer_requires_terms",
            ),
            models.CheckConstraint(
                condition=~Q(billing_model=BillingModel.FIXED_FEE.value)
                | Q(monthly_fee__isnull=False),
                name="contracts_fixed_fee_requires_fee",
            ),
            ExclusionConstraint(
                name="contracts_no_overlap_per_client",
                expressions=(
                    (
                        DateRange("starts_on", "ends_on", RangeBoundary(inclusive_upper=True)),
                        RangeOperators.OVERLAPS,
                    ),
                    ("client", RangeOperators.EQUAL),
                ),
            ),
        )

    def __str__(self) -> str:
        return f"{self.client} · {BillingModel(self.billing_model).label} from {self.starts_on}"

    @cached_property
    def has_invoices(self) -> bool:
        return self.invoices.exists()

    def to_terms(self) -> ContractTerms:
        return ContractTerms(
            billing_model=BillingModel(self.billing_model),
            rounding_increment_minutes=self.rounding_increment_minutes,
            hourly_rate=self.hourly_rate,
            monthly_fee=self.monthly_fee,
            included_hours=self.included_hours,
            overage_rate=self.overage_rate,
            rollover_cap_hours=self.rollover_cap_hours,
        )


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    PAID = "paid", "Paid"
    VOID = "void", "Void"


class InvoiceQuerySet(models.QuerySet["Invoice"]):
    def active(self) -> Self:
        return self.exclude(status=InvoiceStatus.VOID)

    def for_period(self, period: MonthPeriod) -> Self:
        return self.filter(period_start=period.first_day)


class Invoice(OrganizationOwnedModel):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name="invoices")
    number = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(
        max_length=8,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
    )
    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(max_length=3)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tracked_minutes = models.PositiveIntegerField(default=0)
    billable_minutes = models.PositiveIntegerField(default=0)
    included_minutes = models.PositiveIntegerField(default=0)
    included_minutes_unused = models.PositiveIntegerField(default=0)
    rollover_minutes_available = models.PositiveIntegerField(default=0)
    rollover_minutes_applied = models.PositiveIntegerField(default=0)
    overage_minutes = models.PositiveIntegerField(default=0)
    next_rollover_minutes = models.PositiveIntegerField(default=0)
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)

    objects = InvoiceQuerySet.as_manager()

    class Meta:
        ordering = ("-period_start", "client__name")
        indexes = (
            models.Index(fields=("organization", "status"), name="invoices_org_status"),
            models.Index(fields=("organization", "period_start"), name="invoices_org_period"),
        )
        constraints = (
            models.UniqueConstraint(
                fields=("client", "period_start"),
                condition=~Q(status=InvoiceStatus.VOID),
                name="invoices_one_active_per_client_period",
            ),
            models.UniqueConstraint(
                fields=("organization", "number"),
                condition=~Q(number=""),
                name="invoices_unique_number_per_organization",
            ),
            models.CheckConstraint(
                condition=Q(period_end__gte=F("period_start")),
                name="invoices_period_end_after_start",
            ),
            models.CheckConstraint(
                condition=Q(status=InvoiceStatus.DRAFT, number="")
                | (~Q(status=InvoiceStatus.DRAFT) & ~Q(number="")),
                name="invoices_number_assigned_when_issued",
            ),
        )

    def __str__(self) -> str:
        return self.number or f"Draft · {self.client} · {self.period}"

    @property
    def period(self) -> MonthPeriod:
        return MonthPeriod.containing(self.period_start)

    @property
    def is_draft(self) -> bool:
        return self.status == InvoiceStatus.DRAFT


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    position = models.PositiveSmallIntegerField()
    kind = models.CharField(max_length=16, choices=choices_for(LineKind))
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ("invoice", "position")
        constraints = (
            models.UniqueConstraint(
                fields=("invoice", "position"),
                name="invoice_lines_unique_position",
            ),
        )

    def __str__(self) -> str:
        return f"{self.invoice} · {self.description}"
