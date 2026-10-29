import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0001_initial"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
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
                ("name", models.CharField(max_length=160)),
                (
                    "code",
                    models.CharField(
                        max_length=12,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Use 2-12 uppercase letters, digits or dashes.",
                                regex="^[A-Z0-9][A-Z0-9-]{1,11}$",
                            )
                        ],
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        default="#3F51B5",
                        max_length=7,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Use a hex color such as #3F51B5.",
                                regex="^#[0-9A-Fa-f]{6}$",
                            )
                        ],
                    ),
                ),
                ("is_billable", models.BooleanField(default=True)),
                ("is_archived", models.BooleanField(default=False)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="projects",
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
                "ordering": ("client__name", "name"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("organization", "code"),
                        name="projects_unique_code_per_organization",
                    ),
                    models.UniqueConstraint(
                        fields=("client", "name"),
                        name="projects_unique_name_per_client",
                    ),
                ],
            },
        ),
    ]
