from typing import Any

from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.context import request_organization
from apps.billing.domain.types import BillingModel, LineItem
from apps.billing.models import Contract, Invoice, InvoiceLine
from apps.billing.services import InvoicePreview
from apps.clients.models import Client
from apps.clients.serializers import ClientSummarySerializer
from apps.core.choices import choices_for
from apps.core.fields import HoursFromMinutesField
from apps.core.periods import MonthPeriod
from apps.core.serializers import OrganizationScopedPrimaryKeyRelatedField


class ContractSerializer(serializers.ModelSerializer[Contract]):
    client = OrganizationScopedPrimaryKeyRelatedField(queryset=Client.objects.all())
    client_name = serializers.CharField(source="client.name", read_only=True)
    billing_model = serializers.ChoiceField(choices=choices_for(BillingModel))
    has_invoices = serializers.BooleanField(read_only=True)

    class Meta:
        model = Contract
        fields = (
            "id",
            "client",
            "client_name",
            "billing_model",
            "starts_on",
            "ends_on",
            "hourly_rate",
            "monthly_fee",
            "included_hours",
            "overage_rate",
            "rollover_cap_hours",
            "rounding_increment_minutes",
            "has_invoices",
            "created_at",
        )
        read_only_fields = ("id", "client_name", "has_invoices", "created_at")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        starts_on = attrs.get("starts_on", getattr(self.instance, "starts_on", None))
        ends_on = attrs.get("ends_on", getattr(self.instance, "ends_on", None))
        if starts_on and ends_on and ends_on < starts_on:
            raise serializers.ValidationError(
                {"ends_on": "The end date must be on or after the start date."},
            )
        return attrs


class InvoiceLineSerializer(serializers.ModelSerializer[InvoiceLine]):
    class Meta:
        model = InvoiceLine
        fields = ("id", "position", "kind", "description", "quantity", "unit_price", "amount")
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer[Invoice]):
    client = ClientSummarySerializer(read_only=True)
    billing_model = serializers.CharField(source="contract.billing_model", read_only=True)
    billable_hours = HoursFromMinutesField(source="billable_minutes")
    time_entry_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Invoice
        fields: tuple[str, ...] = (
            "id",
            "number",
            "status",
            "client",
            "billing_model",
            "period_start",
            "period_end",
            "currency",
            "subtotal",
            "tax_amount",
            "total",
            "billable_hours",
            "time_entry_count",
            "issue_date",
            "due_date",
            "created_at",
        )
        read_only_fields: tuple[str, ...] = fields


class InvoiceDetailSerializer(InvoiceSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    tracked_hours = HoursFromMinutesField(source="tracked_minutes")
    included_hours = HoursFromMinutesField(source="included_minutes")
    unused_included_hours = HoursFromMinutesField(source="included_minutes_unused")
    rollover_hours_available = HoursFromMinutesField(source="rollover_minutes_available")
    rollover_hours_applied = HoursFromMinutesField(source="rollover_minutes_applied")
    overage_hours = HoursFromMinutesField(source="overage_minutes")

    class Meta(InvoiceSerializer.Meta):
        fields = (
            *InvoiceSerializer.Meta.fields,
            "tax_rate",
            "lines",
            "tracked_hours",
            "included_hours",
            "unused_included_hours",
            "rollover_hours_available",
            "rollover_hours_applied",
            "overage_hours",
            "issued_at",
            "paid_at",
            "voided_at",
        )
        read_only_fields = fields


@extend_schema_field(OpenApiTypes.STR)
class PeriodField(serializers.Field[MonthPeriod, str, str, Any]):
    default_error_messages = {"invalid": "Use the YYYY-MM format."}

    def to_internal_value(self, data: Any) -> MonthPeriod:
        if not isinstance(data, str):
            self.fail("invalid")
        try:
            return MonthPeriod.parse(data.strip())
        except ValueError as error:
            raise serializers.ValidationError(str(error)) from error

    def to_representation(self, value: MonthPeriod) -> str:
        return str(value)


class InvoicePeriodSerializer(serializers.Serializer[Invoice]):
    client = OrganizationScopedPrimaryKeyRelatedField(queryset=Client.objects.all())
    period = PeriodField()

    def validate_period(self, period: MonthPeriod) -> MonthPeriod:
        organization = request_organization(self.context["request"])
        today = timezone.localdate(timezone=organization.tzinfo)
        if period > MonthPeriod.containing(today):
            raise serializers.ValidationError("Future periods cannot be invoiced.")
        return period


class InvoiceMarkPaidSerializer(serializers.Serializer[Invoice]):
    paid_at = serializers.DateTimeField(required=False)


class LineItemSerializer(serializers.Serializer[LineItem]):
    kind = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class InvoicePreviewSerializer(serializers.Serializer[InvoicePreview]):
    lines = LineItemSerializer(source="result.lines", many=True, read_only=True)
    subtotal = serializers.DecimalField(
        source="result.subtotal",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    tracked_hours = HoursFromMinutesField(source="result.tracked_minutes")
    billable_hours = HoursFromMinutesField(source="result.billable_minutes")
    included_hours = HoursFromMinutesField(source="result.included_minutes")
    rollover_hours_available = HoursFromMinutesField(source="result.rollover_minutes_available")
    overage_hours = HoursFromMinutesField(source="result.overage_minutes")
    is_empty = serializers.BooleanField(source="result.is_empty", read_only=True)
    replaces_draft = serializers.IntegerField(
        source="replaces_draft_id",
        allow_null=True,
        read_only=True,
    )
