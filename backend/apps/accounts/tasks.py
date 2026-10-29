from celery import shared_task
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import LoginSession


@shared_task
def purge_expired_sessions() -> int:
    call_command("flushexpiredtokens", verbosity=0)
    count, _ = LoginSession.objects.filter(expires_at__lte=timezone.now()).delete()
    return count
