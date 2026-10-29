import django_filters

from apps.timetracking.models import TimeEntry


class TimeEntryFilter(django_filters.FilterSet):
    started_after = django_filters.IsoDateTimeFilter(field_name="started_at", lookup_expr="gte")
    started_before = django_filters.IsoDateTimeFilter(field_name="started_at", lookup_expr="lt")
    client = django_filters.NumberFilter(field_name="project__client")
    is_running = django_filters.BooleanFilter(field_name="ended_at", lookup_expr="isnull")
    is_invoiced = django_filters.BooleanFilter(
        field_name="invoice",
        lookup_expr="isnull",
        exclude=True,
    )

    class Meta:
        model = TimeEntry
        fields = ("user", "project", "is_billable")
