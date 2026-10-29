from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.serializers import BaseSerializer

from apps.accounts.context import request_organization
from apps.clients.models import Client
from apps.clients.serializers import ClientSerializer
from apps.core.exceptions import ConflictError
from apps.core.permissions import IsManagerOrReadOnly, IsOrganizationMember
from apps.core.views import OrganizationScopedMixin


class ClientViewSet(OrganizationScopedMixin[Client], viewsets.ModelViewSet[Client]):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = (IsOrganizationMember, IsManagerOrReadOnly)
    filterset_fields = ("is_archived", "currency")
    search_fields = ("name", "contact_name", "email")
    ordering_fields = ("name", "created_at")

    def perform_create(self, serializer: BaseSerializer[Client]) -> None:
        organization = request_organization(self.request)
        currency = serializer.validated_data.get("currency", organization.default_currency)
        serializer.save(organization=organization, currency=currency)

    def perform_destroy(self, instance: Client) -> None:
        try:
            instance.delete()
        except ProtectedError as error:
            raise ConflictError(
                "This client has projects, contracts or invoices. Archive it instead.",
                code="client_in_use",
            ) from error
