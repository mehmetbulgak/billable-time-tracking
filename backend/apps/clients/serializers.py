from rest_framework import serializers

from apps.accounts.context import request_organization
from apps.clients.models import Client


class ClientSerializer(serializers.ModelSerializer[Client]):
    class Meta:
        model = Client
        fields = (
            "id",
            "name",
            "contact_name",
            "email",
            "currency",
            "tax_rate",
            "payment_terms_days",
            "is_archived",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"currency": {"required": False}}

    def validate_name(self, value: str) -> str:
        organization = request_organization(self.context["request"])
        duplicates = Client.objects.filter(organization=organization, name__iexact=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("A client with this name already exists.")
        return value


class ClientSummarySerializer(serializers.ModelSerializer[Client]):
    class Meta:
        model = Client
        fields = ("id", "name", "currency")
        read_only_fields = fields
