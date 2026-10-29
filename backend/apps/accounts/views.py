from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts import services
from apps.accounts.context import request_organization, request_user
from apps.accounts.models import User
from apps.accounts.serializers import (
    CurrentUserSerializer,
    MemberCreateSerializer,
    MemberSerializer,
    MemberUpdateSerializer,
)
from apps.core.permissions import IsManagerOrReadOnly, IsOrganizationMember, ProtectDemoAccounts
from apps.core.views import OrganizationScopedMixin


class CurrentUserView(generics.RetrieveUpdateAPIView[User]):
    serializer_class = CurrentUserSerializer
    http_method_names = ["get", "patch", "head", "options"]
    permission_classes = (IsOrganizationMember, ProtectDemoAccounts)

    def get_object(self) -> User:
        return request_user(self.request)


class MemberViewSet(
    OrganizationScopedMixin[User],
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet[User],
):
    queryset = User.objects.all()
    serializer_class = MemberSerializer
    permission_classes = (IsOrganizationMember, IsManagerOrReadOnly, ProtectDemoAccounts)
    filterset_fields = ("role", "is_active")
    search_fields = ("first_name", "last_name", "email")
    ordering_fields = ("first_name", "last_name", "date_joined")
    http_method_names = ["get", "post", "patch", "head", "options"]

    @extend_schema(request=MemberCreateSerializer, responses={201: MemberSerializer})
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = MemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = services.create_member(
            organization=request_organization(request),
            actor=request_user(request),
            **serializer.validated_data,
        )
        return Response(MemberSerializer(member).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=MemberUpdateSerializer, responses={200: MemberSerializer})
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        member = self.get_object()
        serializer = MemberUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        member = services.update_member(
            member=member,
            actor=request_user(request),
            **serializer.validated_data,
        )
        return Response(MemberSerializer(member).data)
