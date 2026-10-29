from typing import Self

from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import OrganizationOwnedModel

hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Use a hex color such as #3F51B5.",
)

project_code_validator = RegexValidator(
    regex=r"^[A-Z0-9][A-Z0-9-]{1,11}$",
    message="Use 2-12 uppercase letters, digits or dashes.",
)


class ProjectQuerySet(models.QuerySet["Project"]):
    def active(self) -> Self:
        return self.filter(is_archived=False, client__is_archived=False)


class Project(OrganizationOwnedModel):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="projects",
    )
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=12, validators=[project_code_validator])
    color = models.CharField(max_length=7, default="#3F51B5", validators=[hex_color_validator])
    is_billable = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ("client__name", "name")
        constraints = (
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="projects_unique_code_per_organization",
            ),
            models.UniqueConstraint(
                fields=("client", "name"),
                name="projects_unique_name_per_client",
            ),
        )

    def __str__(self) -> str:
        return f"{self.code} · {self.name}"
