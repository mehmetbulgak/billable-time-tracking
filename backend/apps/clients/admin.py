from django.contrib import admin

from apps.clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "currency", "tax_rate", "is_archived")
    list_filter = ("organization", "currency", "is_archived")
    search_fields = ("name", "contact_name", "email")
