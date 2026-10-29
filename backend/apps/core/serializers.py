from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model, QuerySet
from rest_framework import serializers

from apps.accounts.context import request_organization


class OrganizationScopedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField[Model]):
    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        if queryset is None:
            raise ImproperlyConfigured(f"{type(self).__name__} requires a queryset.")
        request = self.context.get("request")
        if request is None:
            return queryset.none()
        return queryset.filter(organization=request_organization(request))
