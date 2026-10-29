from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.billing.models import Invoice


def send_invoice_issued_email(invoice: Invoice) -> bool:
    if not invoice.client.email:
        return False
    context = {
        "invoice": invoice,
        "client": invoice.client,
        "organization": invoice.organization,
        "lines": invoice.lines.all(),
    }
    send_mail(
        subject=f"Invoice {invoice.number} from {invoice.organization.name}",
        message=render_to_string("billing/invoice_issued_email.txt", context),
        from_email=None,
        recipient_list=[invoice.client.email],
    )
    return True
