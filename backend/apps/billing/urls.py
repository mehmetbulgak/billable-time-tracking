from rest_framework.routers import SimpleRouter

from apps.billing.views import ContractViewSet, InvoiceViewSet

router = SimpleRouter()
router.register("contracts", ContractViewSet, basename="contract")
router.register("invoices", InvoiceViewSet, basename="invoice")

urlpatterns = router.urls
