from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import User

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class IsOrganizationMember(BasePermission):
    message = "You must belong to an organization."

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return isinstance(user, User) and user.is_active and user.organization_id is not None


class ProtectDemoAccounts(BasePermission):
    message = "Account and organization changes are disabled in the public demo."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return not settings.DEMO_MODE or request.method in SAFE_METHODS


class IsManager(BasePermission):
    message = "Only owners and managers can perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return isinstance(user, User) and user.is_manager


class IsManagerOrReadOnly(IsManager):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in SAFE_METHODS or super().has_permission(request, view)
