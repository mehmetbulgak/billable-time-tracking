import django_filters

from apps.billing.models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    period_from = django_filters.DateFilter(field_name="period_start", lookup_expr="gte")
    period_to = django_filters.DateFilter(field_name="period_start", lookup_expr="lte")

    class Meta:
        model = Invoice
        fields = ("status", "client")
