import logging

from celery import shared_task

from apps.timetracking import services

logger = logging.getLogger(__name__)


@shared_task
def stop_stale_timers() -> int:
    stopped = services.stop_stale_timers()
    if stopped:
        logger.info("Stopped %s stale timers", stopped)
    return stopped
