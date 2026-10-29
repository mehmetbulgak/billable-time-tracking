from typing import Any

from django.db import transaction
from django.dispatch import receiver

from apps.billing.models import Invoice
from apps.billing.signals import invoice_issued
from apps.billing.tasks import send_invoice_email


@receiver(invoice_issued, dispatch_uid="billing.queue_invoice_email")
def queue_invoice_email(sender: type[Invoice], invoice: Invoice, **kwargs: Any) -> None:
    invoice_id = invoice.pk
    transaction.on_commit(lambda: send_invoice_email.delay(invoice_id), robust=True)
