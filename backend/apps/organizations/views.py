from rest_framework import generics

from apps.accounts.context import request_organization
from apps.core.permissions import IsManagerOrReadOnly, IsOrganizationMember, ProtectDemoAccounts
from apps.organizations.models import Organization
from apps.organizations.serializers import OrganizationSerializer


class CurrentOrganizationView(generics.RetrieveUpdateAPIView[Organization]):
    serializer_class = OrganizationSerializer
    permission_classes = (IsOrganizationMember, IsManagerOrReadOnly, ProtectDemoAccounts)
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self) -> Organization:
        return request_organization(self.request)
