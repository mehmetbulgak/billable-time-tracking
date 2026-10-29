from django.contrib import admin

from apps.projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "client", "is_billable", "is_archived")
    list_filter = ("organization", "is_billable", "is_archived")
    search_fields = ("code", "name", "client__name")
    list_select_related = ("client",)
