from django.contrib import admin

from apps.billing.models import Contract, Invoice, InvoiceLine


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("client", "billing_model", "starts_on", "ends_on", "monthly_fee", "hourly_rate")
    list_filter = ("organization", "billing_model")
    search_fields = ("client__name",)
    list_select_related = ("client",)


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    readonly_fields = ("position", "kind", "description", "quantity", "unit_price", "amount")
    can_delete = False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "client", "status", "period_start", "total", "currency")
    list_filter = ("organization", "status", "currency")
    search_fields = ("number", "client__name")
    list_select_related = ("client",)
    inlines = (InvoiceLineInline,)
    readonly_fields = ("number", "subtotal", "tax_amount", "total", "issued_at", "paid_at")
