from django.contrib import admin

from apps.organizations.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "timezone", "default_currency", "next_invoice_number")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
