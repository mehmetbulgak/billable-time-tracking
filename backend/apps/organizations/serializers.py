from rest_framework import serializers

from apps.organizations.models import Organization


class OrganizationSerializer(serializers.ModelSerializer[Organization]):
    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
            "timezone",
            "default_currency",
            "default_payment_terms_days",
            "invoice_prefix",
        )
        read_only_fields = ("id", "slug")
