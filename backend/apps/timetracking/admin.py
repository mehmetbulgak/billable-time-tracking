from django.contrib import admin

from apps.timetracking.models import TimeEntry


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "started_at", "ended_at", "is_billable", "invoice")
    list_filter = ("organization", "is_billable")
    search_fields = ("description", "user__email", "project__name", "project__code")
    list_select_related = ("user", "project", "invoice")
    date_hierarchy = "started_at"
    raw_id_fields = ("user", "project", "invoice")
