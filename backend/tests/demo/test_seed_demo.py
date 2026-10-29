from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings

from apps.billing.models import Invoice, InvoiceStatus
from apps.organizations.models import Organization
from apps.timetracking.models import TimeEntry


@pytest.mark.django_db
@override_settings(DEMO_MODE=True)
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
@override_settings(DEMO_MODE=True)
def test_seed_demo_requires_reset_to_run_twice() -> None:
    call_command("seed_demo", stdout=StringIO())

    with pytest.raises(CommandError):
        call_command("seed_demo", stdout=StringIO())

    call_command("seed_demo", "--reset", stdout=StringIO())
    assert Organization.objects.filter(slug="northwind").count() == 1


@pytest.mark.django_db
@override_settings(DEMO_MODE=False, DEBUG=False)
def test_demo_seed_cannot_reset_a_production_database() -> None:
    organization = Organization.objects.create(name="Real agency", slug="northwind")
    with pytest.raises(CommandError):
        call_command("seed_demo", "--reset", stdout=StringIO())
    assert Organization.objects.filter(pk=organization.pk).exists()


@pytest.mark.django_db
@override_settings(DEMO_MODE=True)
def test_demo_accounts_have_no_system_administration_privileges() -> None:
    from apps.accounts.models import User

    call_command("seed_demo", stdout=StringIO())
    assert not User.objects.filter(is_superuser=True).exists()
    assert not User.objects.filter(is_staff=True).exists()
    assert not User.objects.get(role="owner").has_usable_password()
