from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.billing.models import Invoice, InvoiceStatus
from apps.organizations.models import Organization
from apps.timetracking.models import TimeEntry


@pytest.mark.django_db
def test_seed_demo_builds_a_complete_agency() -> None:
    output = StringIO()

    call_command("seed_demo", stdout=output)

    organization = Organization.objects.get(slug="northwind")
    statuses = set(
        Invoice.objects.filter(organization=organization).values_list("status", flat=True)
    )
    assert statuses == {InvoiceStatus.PAID, InvoiceStatus.ISSUED, InvoiceStatus.DRAFT}
    assert TimeEntry.objects.running().filter(organization=organization).count() == 2
    assert "billable-demo" in output.getvalue()


@pytest.mark.django_db
def test_seed_demo_requires_reset_to_run_twice() -> None:
    call_command("seed_demo", stdout=StringIO())

    with pytest.raises(CommandError):
        call_command("seed_demo", stdout=StringIO())

    call_command("seed_demo", "--reset", stdout=StringIO())
    assert Organization.objects.filter(slug="northwind").count() == 1
