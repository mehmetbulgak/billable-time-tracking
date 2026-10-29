from enum import StrEnum


class ActivityEvent(StrEnum):
    TIMER_STARTED = "timer.started"
    TIMER_STOPPED = "timer.stopped"
    ENTRY_CHANGED = "entry.changed"
    ENTRY_DELETED = "entry.deleted"
    INVOICE_CHANGED = "invoice.changed"
