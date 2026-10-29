from typing import Any

from django.db.models import Model, QuerySet
from rest_framework.generics import GenericAPIView
from rest_framework.serializers import BaseSerializer

from apps.accounts.context import request_organization


class OrganizationScopedMixin[ModelT: Model](GenericAPIView[ModelT]):
    def get_queryset(self) -> QuerySet[ModelT]:
        organization = request_organization(self.request)
        return super().get_queryset().filter(organization=organization)

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        serializer.save(organization=request_organization(self.request))
