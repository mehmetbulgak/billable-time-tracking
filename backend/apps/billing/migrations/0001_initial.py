import apps.billing.models
import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0001_initial"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        BtreeGistExtension(),
        migrations.CreateModel(
            name="Contract",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "billing_model",
                    models.CharField(
                        choices=[
                            ("hourly", "Hourly"),
                            ("retainer", "Retainer"),
                            ("fixed_fee", "Fixed fee"),
                        ],
                        max_length=16,
                    ),
                ),
                ("starts_on", models.DateField()),
                ("ends_on", models.DateField(blank=True, null=True)),
                (
                    "hourly_rate",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=10,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "monthly_fee",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "included_hours",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=7,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "overage_rate",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=10,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "rollover_cap_hours",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=7,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0"))
                        ],
                    ),
                ),
                (
                    "rounding_increment_minutes",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "1 minute"),
                            (6, "6 minutes"),
                            (15, "15 minutes"),
                            (30, "30 minutes"),
                            (60, "1 hour"),
                        ],
                        default=15,
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="contracts",
                        to="clients.client",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="organizations.organization",
                    ),
                ),
            ],
            options={
                "ordering": ("client__name", "-starts_on"),
            },
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("number", models.CharField(blank=True, default="", max_length=32)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("issued", "Issued"),
                            ("paid", "Paid"),
                            ("void", "Void"),
                        ],
                        default="draft",
                        max_length=8,
                    ),
                ),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("currency", models.CharField(max_length=3)),
                (
                    "subtotal",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=12
                    ),
                ),
                (
                    "tax_rate",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=5
                    ),
                ),
                (
                    "tax_amount",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=12
                    ),
                ),
                (
                    "total",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=12
                    ),
                ),
                ("tracked_minutes", models.PositiveIntegerField(default=0)),
                ("billable_minutes", models.PositiveIntegerField(default=0)),
                ("included_minutes", models.PositiveIntegerField(default=0)),
                ("included_minutes_unused", models.PositiveIntegerField(default=0)),
                ("rollover_minutes_available", models.PositiveIntegerField(default=0)),
                ("rollover_minutes_applied", models.PositiveIntegerField(default=0)),
                ("overage_minutes", models.PositiveIntegerField(default=0)),
                ("next_rollover_minutes", models.PositiveIntegerField(default=0)),
                ("issue_date", models.DateField(blank=True, null=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("issued_at", models.DateTimeField(blank=True, null=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("voided_at", models.DateTimeField(blank=True, null=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoices",
                        to="clients.client",
                    ),
                ),
                (
                    "contract",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoices",
                        to="billing.contract",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="organizations.organization",
                    ),
                ),
            ],
            options={
                "ordering": ("-period_start", "client__name"),
            },
        ),
        migrations.CreateModel(
            name="InvoiceLine",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("position", models.PositiveSmallIntegerField()),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("hourly_time", "Hourly time"),
                            ("retainer_fee", "Retainer fee"),
                            ("included_hours", "Included hours"),
                            ("overage", "Overage"),
                            ("fixed_fee", "Fixed fee"),
                        ],
                        max_length=16,
                    ),
                ),
                ("description", models.CharField(max_length=255)),
                ("quantity", models.DecimalField(decimal_places=2, max_digits=10)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="billing.invoice",
                    ),
                ),
            ],
            options={
                "ordering": ("invoice", "position"),
            },
        ),
        migrations.AddConstraint(
            model_name="contract",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("ends_on__isnull", True),
                    ("ends_on__gte", models.F("starts_on")),
                    _connector="OR",
                ),
                name="contracts_end_on_or_after_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="contract",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("billing_model", "hourly"), _negated=True),
                    ("hourly_rate__isnull", False),
                    _connector="OR",
                ),
                name="contracts_hourly_requires_rate",
            ),
        ),
        migrations.AddConstraint(
            model_name="contract",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("billing_model", "retainer"), _negated=True),
                    models.Q(
                        ("included_hours__isnull", False),
                        ("monthly_fee__isnull", False),
                        ("overage_rate__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="contracts_retainer_requires_terms",
            ),
        ),
        migrations.AddConstraint(
            model_name="contract",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("billing_model", "fixed_fee"), _negated=True),
                    ("monthly_fee__isnull", False),
                    _connector="OR",
                ),
                name="contracts_fixed_fee_requires_fee",
            ),
        ),
        migrations.AddConstraint(
            model_name="contract",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=(
                    (
                        apps.billing.models.DateRange(
                            "starts_on",
                            "ends_on",
                            django.contrib.postgres.fields.ranges.RangeBoundary(
                                inclusive_upper=True
                            ),
                        ),
                        "&&",
                    ),
                    ("client", "="),
                ),
                name="contracts_no_overlap_per_client",
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(
                fields=["organization", "status"], name="invoices_org_status"
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(
                fields=["organization", "period_start"], name="invoices_org_period"
            ),
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "void"), _negated=True),
                fields=("client", "period_start"),
                name="invoices_one_active_per_client_period",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(
                condition=models.Q(("number", ""), _negated=True),
                fields=("organization", "number"),
                name="invoices_unique_number_per_organization",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.CheckConstraint(
                condition=models.Q(("period_end__gte", models.F("period_start"))),
                name="invoices_period_end_after_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("number", ""), ("status", "draft")),
                    models.Q(
                        models.Q(("status", "draft"), _negated=True),
                        models.Q(("number", ""), _negated=True),
                    ),
                    _connector="OR",
                ),
                name="invoices_number_assigned_when_issued",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoiceline",
            constraint=models.UniqueConstraint(
                fields=("invoice", "position"), name="invoice_lines_unique_position"
            ),
        ),
    ]
