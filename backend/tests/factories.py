from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import factory

from apps.accounts.models import Role, User
from apps.billing.domain.types import BillingModel
from apps.billing.models import Contract, Invoice
from apps.clients.models import Client
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.timetracking.models import TimeEntry

ISTANBUL = ZoneInfo("Europe/Istanbul")


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Agency {n}")
    slug = factory.Sequence(lambda n: f"agency-{n}")
    timezone = "Europe/Istanbul"
    default_currency = "USD"
    invoice_prefix = "INV"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.test")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    organization = factory.SubFactory(OrganizationFactory)
    role = Role.MEMBER
    password = factory.django.Password("correct-horse-battery")


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Client {n}")
    email = factory.Sequence(lambda n: f"billing{n}@client.test")
    currency = "USD"
    tax_rate = Decimal("0.00")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    client = factory.SubFactory(ClientFactory)
    organization = factory.SelfAttribute("client.organization")
    name = factory.Sequence(lambda n: f"Project {n}")
    code = factory.Sequence(lambda n: f"PRJ-{n}")
    is_billable = True


class ContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contract

    client = factory.SubFactory(ClientFactory)
    organization = factory.SelfAttribute("client.organization")
    billing_model = BillingModel.HOURLY
    starts_on = date(2026, 1, 1)
    hourly_rate = Decimal("100.00")
    rounding_increment_minutes = 15

    class Params:
        retainer = factory.Trait(
            billing_model=BillingModel.RETAINER,
            hourly_rate=None,
            monthly_fee=Decimal("2000.00"),
            included_hours=Decimal("20.00"),
            overage_rate=Decimal("150.00"),
            rollover_cap_hours=Decimal("5.00"),
        )
        fixed_fee = factory.Trait(
            billing_model=BillingModel.FIXED_FEE,
            hourly_rate=None,
            monthly_fee=Decimal("5000.00"),
        )


class TimeEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimeEntry

    project = factory.SubFactory(ProjectFactory)
    organization = factory.SelfAttribute("project.organization")
    user = factory.SubFactory(UserFactory, organization=factory.SelfAttribute("..organization"))
    description = "Design work"
    started_at = factory.Sequence(
        lambda n: datetime(2026, 3, 2, 9, 0, tzinfo=ISTANBUL) + timedelta(hours=2 * n),
    )
    ended_at = factory.LazyAttribute(lambda entry: entry.started_at + timedelta(hours=1))
    is_billable = True


class InvoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invoice

    client = factory.SubFactory(ClientFactory)
    organization = factory.SelfAttribute("client.organization")
    contract = factory.SubFactory(ContractFactory, client=factory.SelfAttribute("..client"))
    period_start = date(2026, 3, 1)
    period_end = date(2026, 3, 31)
    currency = "USD"
