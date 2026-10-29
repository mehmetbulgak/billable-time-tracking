import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.billing import services as billing_services
from apps.billing.models import Contract, Invoice
from apps.clients.models import Client
from apps.core.exceptions import DomainError
from apps.core.periods import MonthPeriod
from apps.demo.catalog import (
    CLIENTS,
    DEMO_PASSWORD,
    DEMO_TIMEZONE,
    DESCRIPTIONS,
    MEMBERS,
    DemoClient,
    DemoMember,
)
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.timetracking.models import TimeEntry

ORGANIZATION_SLUG = "northwind"
WORKDAY_START = time(9, 30)
LUNCH_BREAK = timedelta(minutes=45)
MONTHS_OF_HISTORY = 3


@dataclass(slots=True)
class SeedReport:
    members: int = 0
    clients: int = 0
    projects: int = 0
    time_entries: int = 0
    invoices: list[str] = field(default_factory=list)


class DemoSeeder:
    def __init__(self, *, now: datetime | None = None, seed: int = 42) -> None:
        self._now = now or timezone.now()
        self._random = random.Random(seed)
        self._report = SeedReport()

    def run(self, *, reset: bool) -> SeedReport:
        if reset:
            self.reset()
        with transaction.atomic():
            organization = self._create_organization()
            members = self._create_members(organization)
            projects = self._create_clients_and_projects(organization)
            self._create_time_entries(organization, members, projects)
        self._create_invoices(organization)
        with transaction.atomic():
            self._start_running_timers(organization, members, projects)
        return self._report

    @staticmethod
    def reset() -> None:
        organization = Organization.objects.filter(slug=ORGANIZATION_SLUG).first()
        if organization is None:
            return
        with transaction.atomic():
            TimeEntry.objects.filter(organization=organization).delete()
            Invoice.objects.filter(organization=organization).delete()
            Contract.objects.filter(organization=organization).delete()
            Project.objects.filter(organization=organization).delete()
            Client.objects.filter(organization=organization).delete()
            User.objects.filter(organization=organization).delete()
            organization.delete()

    def _create_organization(self) -> Organization:
        return Organization.objects.create(
            name="Northwind Studio",
            slug=ORGANIZATION_SLUG,
            timezone=str(DEMO_TIMEZONE),
            default_currency="USD",
            default_payment_terms_days=14,
            invoice_prefix="NWS",
        )

    def _create_members(self, organization: Organization) -> dict[str, User]:
        members = {}
        for spec in MEMBERS:
            is_owner = spec.role == Role.OWNER
            members[spec.email] = User.objects.create_user(
                email=spec.email,
                password=DEMO_PASSWORD,
                first_name=spec.first_name,
                last_name=spec.last_name,
                organization=organization,
                role=spec.role,
                is_staff=is_owner,
                is_superuser=is_owner,
            )
        self._report.members = len(members)
        return members

    def _create_clients_and_projects(self, organization: Organization) -> dict[str, Project]:
        contracts_start = self._history_start().previous().first_day
        projects: dict[str, Project] = {}
        for spec in CLIENTS:
            client = Client.objects.create(
                organization=organization,
                name=spec.name,
                contact_name=spec.contact_name,
                email=spec.email,
                currency=spec.currency,
                tax_rate=spec.tax_rate,
            )
            for project_spec in spec.projects:
                projects[project_spec.code] = Project.objects.create(
                    organization=organization,
                    client=client,
                    name=project_spec.name,
                    code=project_spec.code,
                    color=project_spec.color,
                    is_billable=project_spec.is_billable,
                )
            if spec.contract is not None:
                Contract.objects.create(
                    organization=organization,
                    client=client,
                    starts_on=contracts_start,
                    billing_model=spec.contract.billing_model,
                    rounding_increment_minutes=spec.contract.rounding_increment_minutes,
                    hourly_rate=spec.contract.hourly_rate,
                    monthly_fee=spec.contract.monthly_fee,
                    included_hours=spec.contract.included_hours,
                    overage_rate=spec.contract.overage_rate,
                    rollover_cap_hours=spec.contract.rollover_cap_hours,
                )
        self._report.clients = len(CLIENTS)
        self._report.projects = len(projects)
        return projects

    def _local_today(self) -> date:
        return timezone.localdate(self._now, timezone=DEMO_TIMEZONE)

    def _history_start(self) -> MonthPeriod:
        period = MonthPeriod.containing(self._local_today())
        for _ in range(MONTHS_OF_HISTORY):
            period = period.previous()
        return period

    @staticmethod
    def _client_weight(client: DemoClient, member: DemoMember, period: MonthPeriod) -> float:
        focus_bonus = 3.0 if client.key in member.focus else 1.0
        monthly_swing = 0.6 + 0.8 * random.Random(f"{client.key}-{period}").random()
        return client.weight * focus_bonus * monthly_swing

    def _pick_project(self, member: DemoMember, period: MonthPeriod) -> str:
        clients = list(CLIENTS)
        weights = [self._client_weight(client, member, period) for client in clients]
        client = self._random.choices(clients, weights=weights, k=1)[0]
        return self._random.choice(client.projects).code

    def _workdays(self) -> list[date]:
        start = self._history_start().first_day
        end = self._local_today()
        days = (start + timedelta(days=offset) for offset in range((end - start).days + 1))
        return [day for day in days if day.weekday() < 5]

    def _create_time_entries(
        self,
        organization: Organization,
        members: dict[str, User],
        projects: dict[str, Project],
    ) -> None:
        cutoff = self._now - timedelta(hours=2)
        entries = []
        for day in self._workdays():
            period = MonthPeriod.containing(day)
            for spec in MEMBERS:
                cursor = datetime.combine(day, WORKDAY_START, tzinfo=DEMO_TIMEZONE)
                cursor += timedelta(minutes=self._random.randint(-20, 25))
                remaining = timedelta(hours=self._random.uniform(*spec.daily_hours))
                took_lunch = False
                while remaining > timedelta(minutes=20):
                    block = min(remaining, timedelta(minutes=self._random.randint(35, 170)))
                    ended_at = cursor + block
                    if ended_at > cutoff:
                        break
                    code = self._pick_project(spec, period)
                    entries.append(
                        TimeEntry(
                            organization=organization,
                            user=members[spec.email],
                            project=projects[code],
                            description=self._random.choice(DESCRIPTIONS[code]),
                            started_at=cursor,
                            ended_at=ended_at,
                            is_billable=projects[code].is_billable,
                        ),
                    )
                    remaining -= block
                    cursor = ended_at + timedelta(minutes=self._random.randint(5, 20))
                    if not took_lunch and cursor.hour >= 12:
                        cursor += LUNCH_BREAK
                        took_lunch = True
        TimeEntry.objects.bulk_create(entries, batch_size=500)
        self._report.time_entries = len(entries)

    def _create_invoices(self, organization: Organization) -> None:
        current = MonthPeriod.containing(self._local_today())
        last_month = current.previous()
        period = self._history_start()
        while period < current:
            summary = billing_services.generate_drafts_for_period(
                organization=organization,
                period=period,
            )
            if period < last_month:
                self._issue_and_settle(
                    summary.created, period, settle=period < last_month.previous()
                )
            self._report.invoices.extend(
                f"{period}: {invoice.client.name} ({invoice.status})"
                for invoice in Invoice.objects.filter(pk__in=summary.created).select_related(
                    "client"
                )
            )
            period = period.next()

    def _issue_and_settle(
        self, invoice_ids: list[int], period: MonthPeriod, *, settle: bool
    ) -> None:
        issue_date = period.next().first_day + timedelta(days=1)
        issued_at = datetime.combine(issue_date, time(10, 0), tzinfo=DEMO_TIMEZONE)
        for invoice in Invoice.objects.filter(pk__in=invoice_ids).order_by("client__name"):
            try:
                issued = billing_services.issue_invoice(
                    invoice=invoice,
                    issue_date=issue_date,
                    now=issued_at,
                )
            except DomainError:
                continue
            if settle:
                billing_services.mark_invoice_paid(
                    invoice=issued,
                    paid_at=issued_at + timedelta(days=self._random.randint(5, 13)),
                )

    def _start_running_timers(
        self,
        organization: Organization,
        members: dict[str, User],
        projects: dict[str, Project],
    ) -> None:
        running = (
            ("elif@northwind.test", "LUM-BR", "Packaging mockups", 74),
            ("mert@northwind.test", "ATL-APP", "Payments screen", 38),
        )
        for email, code, description, minutes_ago in running:
            TimeEntry.objects.create(
                organization=organization,
                user=members[email],
                project=projects[code],
                description=description,
                started_at=self._now - timedelta(minutes=minutes_ago),
                is_billable=True,
            )
