from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, date, datetime, timedelta

import pytest
import time_machine
from django.core import mail

from apps.accounts.models import User
from apps.billing import services
from apps.billing.models import Invoice, InvoiceStatus
from apps.billing.tasks import generate_monthly_draft_invoices, send_invoice_email
from apps.core.periods import MonthPeriod
from apps.organizations.models import Organization
from apps.timetracking.models import TimeEntry
from apps.timetracking.tasks import stop_stale_timers
from tests.factories import (
    ISTANBUL,
    ClientFactory,
    ContractFactory,
    ProjectFactory,
    TimeEntryFactory,
)

CaptureCallbacks = Callable[..., AbstractContextManager[list[Callable[[], object]]]]


@pytest.fixture
def retainer_client(organization: Organization, member: User) -> None:
    client = ClientFactory(organization=organization)
    ContractFactory(client=client, retainer=True, starts_on=date(2026, 1, 1))
    start = datetime(2026, 3, 10, 10, 0, tzinfo=ISTANBUL)
    TimeEntryFactory(
        user=member,
        project=ProjectFactory(client=client),
        started_at=start,
        ended_at=start + timedelta(hours=3),
    )


@pytest.mark.usefixtures("retainer_client")
def test_monthly_drafts_are_generated_on_the_first_local_day() -> None:
    with time_machine.travel(datetime(2026, 3, 31, 21, 30, tzinfo=UTC), tick=False):
        created = generate_monthly_draft_invoices()

    invoice = Invoice.objects.get()
    assert created == 1
    assert invoice.status == InvoiceStatus.DRAFT
    assert invoice.period_start == date(2026, 3, 1)


@pytest.mark.usefixtures("retainer_client")
def test_monthly_drafts_wait_for_the_local_month_to_end() -> None:
    with time_machine.travel(datetime(2026, 3, 31, 20, 30, tzinfo=UTC), tick=False):
        created = generate_monthly_draft_invoices()

    assert created == 0
    assert not Invoice.objects.exists()


@pytest.mark.usefixtures("retainer_client")
def test_monthly_drafts_are_idempotent() -> None:
    with time_machine.travel(datetime(2026, 4, 1, 6, 0, tzinfo=UTC), tick=False):
        generate_monthly_draft_invoices()
        created_again = generate_monthly_draft_invoices()

    assert created_again == 0
    assert Invoice.objects.count() == 1


def test_invoice_email_is_skipped_for_drafts_and_clients_without_email(
    organization: Organization,
    django_capture_on_commit_callbacks: CaptureCallbacks,
) -> None:
    client = ClientFactory(organization=organization, email="")
    ContractFactory(client=client, fixed_fee=True)
    draft = services.generate_invoice(client=client, period=MonthPeriod(2026, 3))

    assert send_invoice_email(draft.pk) is False

    with django_capture_on_commit_callbacks(execute=True):
        services.issue_invoice(invoice=draft)

    assert mail.outbox == []


def test_stale_timer_task(member: User, organization: Organization) -> None:
    project = ProjectFactory(client__organization=organization)
    TimeEntryFactory(
        user=member,
        project=project,
        started_at=datetime(2026, 3, 1, 9, 0, tzinfo=ISTANBUL),
        ended_at=None,
    )

    with time_machine.travel(datetime(2026, 3, 2, 9, 0, tzinfo=ISTANBUL), tick=False):
        stopped = stop_stale_timers()

    assert stopped == 1
    assert not TimeEntry.objects.running().exists()
