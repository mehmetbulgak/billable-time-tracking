import apps.timetracking.models
import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("billing", "0001_initial"),
        ("organizations", "0001_initial"),
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TimeEntry",
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
                ("description", models.CharField(blank=True, max_length=500)),
                ("started_at", models.DateTimeField()),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("is_billable", models.BooleanField(default=True)),
                (
                    "invoice",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="time_entries",
                        to="billing.invoice",
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
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="time_entries",
                        to="projects.project",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="time_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "time entries",
                "ordering": ("-started_at",),
                "indexes": [
                    models.Index(
                        fields=["organization", "started_at"],
                        name="time_entries_org_started",
                    ),
                    models.Index(
                        fields=["user", "started_at"], name="time_entries_user_started"
                    ),
                    models.Index(
                        fields=["project", "started_at"],
                        name="time_entries_proj_started",
                    ),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("ended_at__isnull", True),
                            ("ended_at__gt", models.F("started_at")),
                            _connector="OR",
                        ),
                        name="time_entries_end_after_start",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("ended_at__isnull", True)),
                        fields=("user",),
                        name="time_entries_one_running_timer_per_user",
                    ),
                    django.contrib.postgres.constraints.ExclusionConstraint(
                        expressions=(
                            (
                                apps.timetracking.models.TsTzRange(
                                    "started_at",
                                    "ended_at",
                                    django.contrib.postgres.fields.ranges.RangeBoundary(),
                                ),
                                "&&",
                            ),
                            ("user", "="),
                        ),
                        name="time_entries_no_overlap_per_user",
                    ),
                ],
            },
        ),
    ]
