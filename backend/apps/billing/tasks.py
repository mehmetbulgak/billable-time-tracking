import logging

from celery import shared_task
from django.utils import timezone

from apps.billing import services
from apps.billing.models import Invoice
from apps.billing.notifications import send_invoice_issued_email
from apps.core.periods import MonthPeriod
from apps.organizations.models import Organization

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=5)
def send_invoice_email(invoice_id: int) -> bool:
    invoice = (
        Invoice.objects.select_related("client", "organization")
        .prefetch_related("lines")
        .filter(pk=invoice_id)
        .first()
    )
    if invoice is None or not invoice.number:
        return False
    return send_invoice_issued_email(invoice)


@shared_task
def generate_monthly_draft_invoices() -> int:
    created = 0
    now = timezone.now()
    for organization in Organization.objects.all():
        local_today = timezone.localdate(now, timezone=organization.tzinfo)
        if local_today.day != 1:
            continue
        period = MonthPeriod.containing(local_today).previous()
        summary = services.generate_drafts_for_period(organization=organization, period=period)
        created += len(summary.created)
        logger.info(
            "Generated %s draft invoices for %s (%s), skipped %s",
            len(summary.created),
            organization.slug,
            period,
            len(summary.skipped),
        )
    return created
