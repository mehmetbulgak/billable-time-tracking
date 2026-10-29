from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from django.core import mail

from apps.accounts.models import User
from apps.billing import services
from apps.billing.models import Contract, Invoice, InvoiceStatus
from apps.clients.models import Client
from apps.core.exceptions import ConflictError, DomainError
from apps.core.periods import MonthPeriod
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.timetracking.models import TimeEntry
from tests.factories import (
    ISTANBUL,
    ClientFactory,
    ContractFactory,
    ProjectFactory,
    TimeEntryFactory,
)

MARCH = MonthPeriod(2026, 3)
CaptureCallbacks = Callable[..., AbstractContextManager[list[Callable[[], object]]]]


@pytest.fixture
def client(organization: Organization) -> Client:
    return ClientFactory(
        organization=organization, tax_rate=Decimal("20.00"), payment_terms_days=30
    )


@pytest.fixture
def project(client: Client) -> Project:
    return ProjectFactory(client=client)


@pytest.fixture
def retainer(client: Client) -> Contract:
    return ContractFactory(client=client, retainer=True)


def track(
    user: User, project: Project, start: datetime, hours: float, **kwargs: object
) -> TimeEntry:
    return TimeEntryFactory(
        user=user,
        project=project,
        started_at=start,
        ended_at=start + timedelta(hours=hours),
        **kwargs,
    )


def at(day: int, hour: int = 9, month: int = 3) -> datetime:
    return datetime(2026, month, day, hour, 0, tzinfo=ISTANBUL)


class TestGenerateInvoice:
    def test_retainer_invoice_with_overage_and_tax(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        entries = [track(member, project, at(day), 5) for day in range(2, 7)]

        invoice = services.generate_invoice(client=client, period=MARCH)

        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.number == ""
        assert invoice.period_start == date(2026, 3, 1)
        assert invoice.period_end == date(2026, 3, 31)
        assert invoice.contract == retainer
        assert invoice.billable_minutes == 25 * 60
        assert invoice.overage_minutes == 5 * 60
        assert [line.amount for line in invoice.lines.all()] == [
            Decimal("2000.00"),
            Decimal("0.00"),
            Decimal("750.00"),
        ]
        assert invoice.subtotal == Decimal("2750.00")
        assert invoice.tax_amount == Decimal("550.00")
        assert invoice.total == Decimal("3300.00")
        assert set(invoice.time_entries.all()) == set(entries)

    def test_only_finished_billable_uninvoiced_entries_of_the_period_count(
        self,
        member: User,
        other_member: User,
        project: Project,
        retainer: Contract,
        client: Client,
        organization: Organization,
    ) -> None:
        included = track(member, project, at(10), 2)
        track(member, project, at(11), 2, is_billable=False)
        track(member, project, at(2, month=4), 2)
        track(member, ProjectFactory(client__organization=organization), at(12), 2)
        TimeEntryFactory(user=other_member, project=project, started_at=at(13), ended_at=None)

        invoice = services.generate_invoice(client=client, period=MARCH)

        assert list(invoice.time_entries.all()) == [included]
        assert invoice.billable_minutes == 120

    def test_period_boundaries_follow_the_agency_time_zone(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        late_march_utc = datetime(2026, 3, 31, 22, 30, tzinfo=ISTANBUL) - timedelta(hours=3)
        april_in_istanbul = datetime(2026, 4, 1, 0, 30, tzinfo=ISTANBUL)
        march_entry = track(member, project, late_march_utc, 0.5)
        track(member, project, april_in_istanbul, 1)

        invoice = services.generate_invoice(client=client, period=MARCH)

        assert list(invoice.time_entries.all()) == [march_entry]

    def test_regenerating_a_draft_replaces_it(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 2)
        first = services.generate_invoice(client=client, period=MARCH)
        track(member, project, at(3), 3)

        second = services.generate_invoice(client=client, period=MARCH)

        assert not Invoice.objects.filter(pk=first.pk).exists()
        assert second.billable_minutes == 5 * 60
        assert second.time_entries.count() == 2

    def test_issued_invoices_cannot_be_regenerated(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 2)
        services.issue_invoice(invoice=services.generate_invoice(client=client, period=MARCH))

        with pytest.raises(ConflictError) as error:
            services.generate_invoice(client=client, period=MARCH)

        assert error.value.code == "invoice_already_issued"

    def test_requires_a_contract_for_the_period(self, client: Client) -> None:
        ContractFactory(client=client, starts_on=date(2026, 4, 1))

        with pytest.raises(DomainError) as error:
            services.generate_invoice(client=client, period=MARCH)

        assert error.value.code == "no_active_contract"

    def test_hourly_contract_without_time_has_nothing_to_invoice(self, client: Client) -> None:
        ContractFactory(client=client)

        with pytest.raises(DomainError) as error:
            services.generate_invoice(client=client, period=MARCH)

        assert error.value.code == "nothing_to_invoice"

    def test_unused_retainer_hours_roll_into_the_next_month(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 12)
        march = services.generate_invoice(client=client, period=MARCH)
        track(member, project, at(2, month=4), 23)

        april = services.generate_invoice(client=client, period=MARCH.next())

        assert march.next_rollover_minutes == 5 * 60
        assert april.rollover_minutes_available == 5 * 60
        assert april.rollover_minutes_applied == 5 * 60
        assert april.overage_minutes == 0
        assert april.subtotal == Decimal("2000.00")

    def test_preview_matches_generation_without_saving(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 21)

        preview = services.calculate_invoice(client=client, period=MARCH)

        assert preview.result.subtotal == Decimal("2150.00")
        assert not Invoice.objects.exists()


class TestPreviewInvoice:
    def test_counts_work_already_on_the_draft_it_would_replace(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 21)
        draft = services.generate_invoice(client=client, period=MARCH)
        track(member, project, at(3), 2)

        preview = services.preview_invoice(client=client, period=MARCH)

        assert preview.replaces_draft_id == draft.pk
        assert preview.result.billable_minutes == 23 * 60
        assert preview.result.subtotal == Decimal("2450.00")
        assert services.generate_invoice(client=client, period=MARCH).subtotal == Decimal(
            "2450.00",
        )

    def test_without_a_draft_nothing_is_replaced(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 4)

        preview = services.preview_invoice(client=client, period=MARCH)

        assert preview.replaces_draft_id is None
        assert not preview.result.is_empty

    def test_issued_periods_cannot_be_previewed(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 4)
        services.issue_invoice(invoice=services.generate_invoice(client=client, period=MARCH))

        with pytest.raises(ConflictError, match="already been issued"):
            services.preview_invoice(client=client, period=MARCH)


class TestInvoiceLifecycle:
    @pytest.fixture
    def draft(self, member: User, project: Project, retainer: Contract, client: Client) -> Invoice:
        track(member, project, at(2), 4)
        return services.generate_invoice(client=client, period=MARCH)

    def test_issuing_assigns_sequential_numbers_and_due_date(
        self,
        draft: Invoice,
        organization: Organization,
        django_capture_on_commit_callbacks: CaptureCallbacks,
    ) -> None:
        other_client = ClientFactory(organization=organization)
        ContractFactory(client=other_client, fixed_fee=True)
        other_draft = services.generate_invoice(client=other_client, period=MARCH)

        with django_capture_on_commit_callbacks(execute=True):
            first = services.issue_invoice(invoice=draft, issue_date=date(2026, 4, 2))
            second = services.issue_invoice(invoice=other_draft, issue_date=date(2026, 4, 2))

        assert first.number == "NWS-2026-0001"
        assert second.number == "NWS-2026-0002"
        assert first.status == InvoiceStatus.ISSUED
        assert first.due_date == date(2026, 5, 2)
        assert [message.subject for message in mail.outbox] == [
            f"Invoice NWS-2026-0001 from {organization.name}",
            f"Invoice NWS-2026-0002 from {organization.name}",
        ]

    def test_only_drafts_can_be_issued(self, draft: Invoice) -> None:
        services.issue_invoice(invoice=draft)

        with pytest.raises(ConflictError):
            services.issue_invoice(invoice=draft)

    def test_paying_an_issued_invoice(self, draft: Invoice) -> None:
        issued = services.issue_invoice(invoice=draft)

        paid = services.mark_invoice_paid(invoice=issued)

        assert paid.status == InvoiceStatus.PAID
        assert paid.paid_at is not None

    def test_drafts_cannot_be_marked_paid(self, draft: Invoice) -> None:
        with pytest.raises(ConflictError):
            services.mark_invoice_paid(invoice=draft)

    def test_voiding_releases_entries_for_a_new_invoice(
        self, draft: Invoice, client: Client
    ) -> None:
        issued = services.issue_invoice(invoice=draft)

        voided = services.void_invoice(invoice=issued)
        replacement = services.generate_invoice(client=client, period=MARCH)

        assert voided.status == InvoiceStatus.VOID
        assert voided.number == issued.number
        assert voided.time_entries.count() == 0
        assert replacement.time_entries.count() == 1

    def test_paid_invoices_cannot_be_voided(self, draft: Invoice) -> None:
        paid = services.mark_invoice_paid(invoice=services.issue_invoice(invoice=draft))

        with pytest.raises(ConflictError):
            services.void_invoice(invoice=paid)

    def test_discarding_a_draft_unlocks_its_entries(self, draft: Invoice) -> None:
        entry_ids = list(draft.time_entries.values_list("pk", flat=True))

        services.discard_draft(invoice=draft)

        assert not Invoice.objects.filter(pk=draft.pk).exists()
        assert TimeEntry.objects.filter(pk__in=entry_ids, invoice__isnull=True).count() == 1


class TestDraftGeneration:
    def test_creates_drafts_for_every_client_with_a_contract(
        self,
        organization: Organization,
        member: User,
    ) -> None:
        retainer_client = ClientFactory(organization=organization)
        ContractFactory(client=retainer_client, retainer=True)
        hourly_client = ClientFactory(organization=organization)
        ContractFactory(client=hourly_client)
        ClientFactory(organization=organization)

        summary = services.generate_drafts_for_period(organization=organization, period=MARCH)

        assert len(summary.created) == 1
        assert (hourly_client.pk, "nothing_to_invoice") in summary.skipped

    def test_existing_invoices_are_left_untouched(
        self,
        organization: Organization,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 2)
        existing = services.generate_invoice(client=client, period=MARCH)

        summary = services.generate_drafts_for_period(organization=organization, period=MARCH)

        assert summary.created == []
        assert (client.pk, "invoice_exists") in summary.skipped
        assert Invoice.objects.get() == existing


class TestContracts:
    def test_overlapping_contracts_are_rejected(
        self, organization: Organization, client: Client
    ) -> None:
        ContractFactory(client=client, starts_on=date(2026, 1, 1), ends_on=date(2026, 6, 30))

        with pytest.raises(ConflictError) as error:
            services.create_contract(
                organization=organization,
                client=client,
                billing_model="hourly",
                starts_on=date(2026, 6, 1),
                hourly_rate=Decimal("90.00"),
            )

        assert error.value.code == "overlapping_contract"

    def test_back_to_back_contracts_are_allowed(
        self, organization: Organization, client: Client
    ) -> None:
        ContractFactory(client=client, starts_on=date(2026, 1, 1), ends_on=date(2026, 5, 31))

        contract = services.create_contract(
            organization=organization,
            client=client,
            billing_model="hourly",
            starts_on=date(2026, 6, 1),
            hourly_rate=Decimal("90.00"),
        )

        assert contract.pk is not None

    def test_incomplete_terms_are_rejected(
        self, organization: Organization, client: Client
    ) -> None:
        with pytest.raises(DomainError) as error:
            services.create_contract(
                organization=organization,
                client=client,
                billing_model="retainer",
                starts_on=date(2026, 1, 1),
                monthly_fee=Decimal("1000.00"),
            )

        assert error.value.code == "invalid_terms"

    def test_terms_are_locked_once_invoices_are_issued(
        self,
        member: User,
        project: Project,
        retainer: Contract,
        client: Client,
    ) -> None:
        track(member, project, at(2), 2)
        services.issue_invoice(invoice=services.generate_invoice(client=client, period=MARCH))

        with pytest.raises(ConflictError):
            services.update_contract(contract=retainer, monthly_fee=Decimal("9999.00"))

        updated = services.update_contract(contract=retainer, ends_on=date(2026, 12, 31))
        assert updated.ends_on == date(2026, 12, 31)
