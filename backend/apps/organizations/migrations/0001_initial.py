import apps.organizations.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organization",
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
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=60, unique=True)),
                (
                    "timezone",
                    models.CharField(
                        default="Europe/Istanbul",
                        max_length=64,
                        validators=[apps.organizations.validators.validate_timezone],
                    ),
                ),
                (
                    "default_currency",
                    models.CharField(
                        choices=[
                            ("USD", "US Dollar"),
                            ("EUR", "Euro"),
                            ("GBP", "British Pound"),
                            ("TRY", "Turkish Lira"),
                        ],
                        default="USD",
                        max_length=3,
                    ),
                ),
                (
                    "default_payment_terms_days",
                    models.PositiveSmallIntegerField(default=14),
                ),
                ("invoice_prefix", models.CharField(default="INV", max_length=10)),
                ("next_invoice_number", models.PositiveIntegerField(default=1)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
    ]
