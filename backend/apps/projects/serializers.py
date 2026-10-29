from typing import Any

from rest_framework import serializers

from apps.accounts.context import request_organization
from apps.clients.models import Client
from apps.core.serializers import OrganizationScopedPrimaryKeyRelatedField
from apps.projects.models import Project, project_code_validator


class ProjectSerializer(serializers.ModelSerializer[Project]):
    client = OrganizationScopedPrimaryKeyRelatedField(queryset=Client.objects.all())
    client_name = serializers.CharField(source="client.name", read_only=True)
    code = serializers.CharField(max_length=12)

    class Meta:
        model = Project
        fields = (
            "id",
            "client",
            "client_name",
            "name",
            "code",
            "color",
            "is_billable",
            "is_archived",
            "created_at",
        )
        read_only_fields = ("id", "client_name", "created_at")

    def validate_code(self, value: str) -> str:
        code = value.strip().upper()
        project_code_validator(code)
        organization = request_organization(self.context["request"])
        duplicates = Project.objects.filter(organization=organization, code=code)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("This project code is already in use.")
        return code

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        client = attrs.get("client") or getattr(self.instance, "client", None)
        name: str = attrs.get("name", getattr(self.instance, "name", ""))
        if not isinstance(client, Client):
            raise serializers.ValidationError({"client": "This field is required."})
        if self.instance is None and client.is_archived:
            raise serializers.ValidationError(
                {"client": "Archived clients cannot get new projects."}
            )
        duplicates = Project.objects.filter(client=client, name__iexact=name)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                {"name": "This client already has a project with this name."}
            )
        return attrs


class ProjectSummarySerializer(serializers.ModelSerializer[Project]):
    client_id = serializers.IntegerField(read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = Project
        fields = ("id", "name", "code", "color", "client_id", "client_name")
        read_only_fields = fields
