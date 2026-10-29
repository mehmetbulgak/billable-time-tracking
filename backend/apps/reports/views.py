from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.context import request_organization, request_user
from apps.core.periods import MonthPeriod
from apps.core.permissions import IsManager, IsOrganizationMember
from apps.organizations.models import Organization
from apps.reports import selectors
from apps.reports.serializers import (
    MyTimeSerializer,
    OverviewSerializer,
    RetainerReportSerializer,
)
from apps.timetracking.models import TimeEntry

PERIOD_PARAMETER = OpenApiParameter(
    "period",
    OpenApiTypes.STR,
    description="Month in YYYY-MM format. Defaults to the current month.",
)


def _period(request: Request, organization: Organization) -> MonthPeriod:
    raw = request.query_params.get("period")
    if not raw:
        return MonthPeriod.containing(timezone.localdate(timezone=organization.tzinfo))
    try:
        return MonthPeriod.parse(raw)
    except ValueError as error:
        raise ValidationError({"period": str(error)}) from error


class OverviewView(APIView):
    permission_classes = (IsOrganizationMember, IsManager)

    @extend_schema(parameters=[PERIOD_PARAMETER], responses=OverviewSerializer)
    def get(self, request: Request) -> Response:
        organization = request_organization(request)
        period = _period(request, organization)
        entries = selectors.period_entries(organization, period)
        payload = {
            "period": str(period),
            "hours": selectors.hours_breakdown(entries),
            "unbilled_hours": selectors.unbilled_hours(organization),
            "active_timers": TimeEntry.objects.running().filter(organization=organization).count(),
            "revenue": selectors.revenue_by_currency(organization, period),
            "daily": selectors.daily_hours(entries, organization, period),
            "members": selectors.hours_by_member(entries),
            "clients": selectors.hours_by_client(entries),
        }
        return Response(OverviewSerializer(payload).data)


class RetainerReportView(APIView):
    permission_classes = (IsOrganizationMember, IsManager)

    @extend_schema(parameters=[PERIOD_PARAMETER], responses=RetainerReportSerializer)
    def get(self, request: Request) -> Response:
        organization = request_organization(request)
        period = _period(request, organization)
        payload = {
            "period": str(period),
            "retainers": selectors.retainer_usage(organization, period),
        }
        return Response(RetainerReportSerializer(payload).data)


class MyTimeView(APIView):
    @extend_schema(parameters=[PERIOD_PARAMETER], responses=MyTimeSerializer)
    def get(self, request: Request) -> Response:
        organization = request_organization(request)
        period = _period(request, organization)
        entries = selectors.period_entries(organization, period, user=request_user(request))
        payload = {
            "period": str(period),
            "hours": selectors.hours_breakdown(entries),
            "daily": selectors.daily_hours(entries, organization, period),
            "projects": selectors.hours_by_project(entries),
        }
        return Response(MyTimeSerializer(payload).data)
