from typing import Any, cast

from django.db.models import ProtectedError, QuerySet
from django.http import HttpResponse
from django.utils.http import content_disposition_header
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.accounts.context import request_organization
from apps.billing import selectors, services
from apps.billing.exports import invoice_csv
from apps.billing.filters import InvoiceFilter
from apps.billing.models import Contract, Invoice
from apps.billing.serializers import (
    ContractSerializer,
    InvoiceDetailSerializer,
    InvoiceMarkPaidSerializer,
    InvoicePeriodSerializer,
    InvoicePreviewSerializer,
    InvoiceSerializer,
)
from apps.core.exceptions import ConflictError
from apps.core.permissions import IsManager, IsOrganizationMember
from apps.core.views import OrganizationScopedMixin
from apps.timetracking.selectors import with_related

MANAGER_PERMISSIONS = (IsOrganizationMember, IsManager)


class ContractViewSet(OrganizationScopedMixin[Contract], viewsets.ModelViewSet[Contract]):
    queryset = Contract.objects.select_related("client").with_invoice_flag()
    serializer_class = ContractSerializer
    permission_classes = MANAGER_PERMISSIONS
    filterset_fields = ("client", "billing_model")
    ordering_fields = ("starts_on", "created_at")

    def perform_create(self, serializer: BaseSerializer[Contract]) -> None:
        serializer.instance = services.create_contract(
            organization=request_organization(self.request),
            **serializer.validated_data,
        )

    def perform_update(self, serializer: BaseSerializer[Contract]) -> None:
        serializer.instance = services.update_contract(
            contract=cast("Contract", serializer.instance),
            **serializer.validated_data,
        )

    def perform_destroy(self, instance: Contract) -> None:
        try:
            instance.delete()
        except ProtectedError as error:
            raise ConflictError(
                "This contract has invoices and cannot be deleted. Set an end date instead.",
                code="contract_in_use",
            ) from error


class InvoiceViewSet(
    OrganizationScopedMixin[Invoice],
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet[Invoice],
):
    queryset = Invoice.objects.all()
    permission_classes = MANAGER_PERMISSIONS
    filterset_class = InvoiceFilter
    search_fields = ("number", "client__name")
    ordering_fields = ("period_start", "issue_date", "total", "created_at")

    def get_queryset(self) -> QuerySet[Invoice]:
        queryset = super().get_queryset()
        if self.action == "list":
            return selectors.invoices_with_related(queryset)
        return selectors.invoice_detail(queryset)

    def get_serializer_class(self) -> type[BaseSerializer[Invoice]]:
        if self.action == "list":
            return InvoiceSerializer
        return InvoiceDetailSerializer

    def _detail_response(self, invoice: Invoice, status_code: int = status.HTTP_200_OK) -> Response:
        refreshed = selectors.invoice_detail(Invoice.objects.filter(pk=invoice.pk)).get()
        return Response(InvoiceDetailSerializer(refreshed).data, status=status_code)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        services.discard_draft(invoice=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=InvoicePeriodSerializer, responses={201: InvoiceDetailSerializer})
    @action(detail=False, methods=["post"])
    def generate(self, request: Request) -> Response:
        serializer = InvoicePeriodSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        invoice = services.generate_invoice(**serializer.validated_data)
        return self._detail_response(invoice, status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter("client", OpenApiTypes.INT, required=True),
            OpenApiParameter("period", OpenApiTypes.STR, required=True, description="YYYY-MM"),
        ],
        responses={200: InvoicePreviewSerializer},
    )
    @action(detail=False, methods=["get"])
    def preview(self, request: Request) -> Response:
        serializer = InvoicePeriodSerializer(
            data=request.query_params,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        preview = services.preview_invoice(**serializer.validated_data)
        return Response(InvoicePreviewSerializer(preview).data)

    @extend_schema(request=None, responses={200: InvoiceDetailSerializer})
    @action(detail=True, methods=["post"])
    def issue(self, request: Request, pk: str | None = None) -> Response:
        invoice = services.issue_invoice(invoice=self.get_object())
        return self._detail_response(invoice)

    @extend_schema(request=InvoiceMarkPaidSerializer, responses={200: InvoiceDetailSerializer})
    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request: Request, pk: str | None = None) -> Response:
        serializer = InvoiceMarkPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = services.mark_invoice_paid(
            invoice=self.get_object(),
            paid_at=serializer.validated_data.get("paid_at"),
        )
        return self._detail_response(invoice)

    @extend_schema(request=None, responses={200: InvoiceDetailSerializer})
    @action(detail=True, methods=["post"])
    def void(self, request: Request, pk: str | None = None) -> Response:
        invoice = services.void_invoice(invoice=self.get_object())
        return self._detail_response(invoice)

    @extend_schema(
        responses={(200, "text/csv"): OpenApiResponse(response=OpenApiTypes.STR)},
    )
    @action(detail=True, methods=["get"])
    def export(self, request: Request, pk: str | None = None) -> HttpResponse:
        invoice = self.get_object()
        entries = with_related(invoice.time_entries.order_by("started_at"))
        filename = f"{invoice.number or f'draft-{invoice.pk}'}.csv"
        return HttpResponse(
            invoice_csv(invoice, entries),
            content_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": content_disposition_header(True, filename) or "attachment"
            },
        )
