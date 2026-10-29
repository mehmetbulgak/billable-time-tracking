from typing import Any

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.context import request_organization, request_user
from apps.core.views import OrganizationScopedMixin
from apps.timetracking import selectors, services
from apps.timetracking.filters import TimeEntryFilter
from apps.timetracking.models import TimeEntry
from apps.timetracking.serializers import (
    TimeEntryCreateSerializer,
    TimeEntrySerializer,
    TimeEntryUpdateSerializer,
    TimerStartSerializer,
)


class TimeEntryViewSet(
    OrganizationScopedMixin[TimeEntry],
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet[TimeEntry],
):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    filterset_class = TimeEntryFilter
    search_fields = ("description", "project__name", "project__code", "project__client__name")
    ordering_fields = ("started_at", "ended_at")
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self) -> QuerySet[TimeEntry]:
        queryset = selectors.with_related(super().get_queryset())
        user = request_user(self.request)
        return queryset if user.is_manager else queryset.filter(user=user)

    @extend_schema(request=TimeEntryCreateSerializer, responses={201: TimeEntrySerializer})
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = TimeEntryCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        entry = services.create_entry(user=request_user(request), **serializer.validated_data)
        return Response(TimeEntrySerializer(entry).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=TimeEntryUpdateSerializer, responses={200: TimeEntrySerializer})
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        entry = self.get_object()
        serializer = TimeEntryUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        entry = services.update_entry(
            entry=entry,
            actor=request_user(request),
            **serializer.validated_data,
        )
        return Response(TimeEntrySerializer(entry).data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        services.delete_entry(entry=self.get_object(), actor=request_user(request))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={
            200: TimeEntrySerializer,
            204: OpenApiResponse(description="No timer is running."),
        },
    )
    @action(detail=False, methods=["get"])
    def current(self, request: Request) -> Response:
        entry = selectors.running_entry_for(request_user(request))
        if entry is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(TimeEntrySerializer(entry).data)

    @extend_schema(request=TimerStartSerializer, responses={201: TimeEntrySerializer})
    @action(detail=False, methods=["post"])
    def start(self, request: Request) -> Response:
        serializer = TimerStartSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        entry = services.start_timer(user=request_user(request), **serializer.validated_data)
        return Response(TimeEntrySerializer(entry).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses={200: TimeEntrySerializer})
    @action(detail=False, methods=["post"])
    def stop(self, request: Request) -> Response:
        entry = services.stop_timer(user=request_user(request))
        return Response(TimeEntrySerializer(entry).data)

    @extend_schema(responses={200: TimeEntrySerializer(many=True)})
    @action(detail=False, methods=["get"], pagination_class=None, filter_backends=())
    def active(self, request: Request) -> Response:
        entries = selectors.active_timers(request_organization(request))
        return Response(TimeEntrySerializer(entries, many=True).data)
