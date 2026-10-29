from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing import services as billing_services
from apps.clients.models import Client
from apps.core.periods import MonthPeriod
from apps.organizations.models import Organization
from apps.projects.models import Project
from tests.factories import (
    ISTANBUL,
    ClientFactory,
    ContractFactory,
    ProjectFactory,
    TimeEntryFactory,
)

ClientFor = Callable[[User], APIClient]


@pytest.fixture
def client(organization: Organization) -> Client:
    client = ClientFactory(organization=organization, name="Lumen")
    ContractFactory(client=client, retainer=True)
    return client


@pytest.fixture
def project(client: Client) -> Project:
    return ProjectFactory(client=client)


@pytest.fixture
def internal_project(organization: Organization) -> Project:
    return ProjectFactory(client__organization=organization, is_billable=False)


def track(user: User, project: Project, day: int, hours: float, *, billable: bool = True) -> None:
    start = datetime(2026, 3, day, 9, 0, tzinfo=ISTANBUL)
    TimeEntryFactory(
        user=user,
        project=project,
        started_at=start,
        ended_at=start + timedelta(hours=hours),
        is_billable=billable,
    )


@pytest.fixture
def march_time(member: User, manager: User, project: Project, internal_project: Project) -> None:
    track(member, project, 2, 6)
    track(member, internal_project, 3, 2, billable=False)
    track(manager, project, 2, 2)


@pytest.mark.usefixtures("march_time")
def test_overview_summarizes_hours_revenue_and_team(client_for: ClientFor, manager: User) -> None:
    response = client_for(manager).get("/api/v1/reports/overview/", {"period": "2026-03"})

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["period"] == "2026-03"
    assert data["hours"] == {
        "tracked_hours": "10.00",
        "billable_hours": "8.00",
        "non_billable_hours": "2.00",
        "billable_ratio": "80.00",
    }
    assert data["unbilled_hours"] == "8.00"
    assert len(data["daily"]) == 31
    assert data["daily"][1] == {
        "day": "2026-03-02",
        "billable_hours": "8.00",
        "non_billable_hours": "0.00",
    }
    assert [member["tracked_hours"] for member in data["members"]] == ["8.00", "2.00"]
    assert data["revenue"] == []


@pytest.mark.usefixtures("march_time")
def test_overview_reports_revenue_per_currency(
    client_for: ClientFor,
    manager: User,
    client: Client,
) -> None:
    invoice = billing_services.generate_invoice(client=client, period=MonthPeriod(2026, 3))
    billing_services.issue_invoice(invoice=invoice)

    response = client_for(manager).get("/api/v1/reports/overview/", {"period": "2026-03"})

    assert response.data["revenue"] == [
        {
            "currency": "USD",
            "draft": "0.00",
            "invoiced": "2000.00",
            "paid": "0.00",
            "outstanding": "2000.00",
        },
    ]
    assert response.data["unbilled_hours"] == "0.00"


@pytest.mark.usefixtures("march_time")
def test_retainer_report_projects_usage_before_invoicing(
    client_for: ClientFor,
    manager: User,
) -> None:
    response = client_for(manager).get("/api/v1/reports/retainers/", {"period": "2026-03"})

    [usage] = response.data["retainers"]
    assert usage["client_name"] == "Lumen"
    assert usage["included_hours"] == "20.00"
    assert usage["used_hours"] == "8.00"
    assert usage["remaining_hours"] == "12.00"
    assert usage["utilization"] == "40.00"
    assert usage["invoice_id"] is None


@pytest.mark.usefixtures("march_time")
def test_retainer_report_uses_the_invoice_once_generated(
    client_for: ClientFor,
    manager: User,
    client: Client,
) -> None:
    invoice = billing_services.generate_invoice(client=client, period=MonthPeriod(2026, 3))

    response = client_for(manager).get("/api/v1/reports/retainers/", {"period": "2026-03"})

    [usage] = response.data["retainers"]
    assert usage["used_hours"] == "8.00"
    assert usage["invoice_id"] == invoice.pk
    assert usage["invoice_status"] == "draft"


@pytest.mark.usefixtures("march_time")
def test_my_time_only_includes_the_current_user(client_for: ClientFor, member: User) -> None:
    response = client_for(member).get("/api/v1/reports/my-time/", {"period": "2026-03"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["hours"]["tracked_hours"] == "8.00"
    assert response.data["hours"]["billable_hours"] == "6.00"
    assert len(response.data["projects"]) == 2


def test_manager_reports_are_forbidden_for_members(client_for: ClientFor, member: User) -> None:
    api = client_for(member)

    assert api.get("/api/v1/reports/overview/").status_code == status.HTTP_403_FORBIDDEN
    assert api.get("/api/v1/reports/retainers/").status_code == status.HTTP_403_FORBIDDEN


def test_invalid_period_is_rejected(client_for: ClientFor, manager: User) -> None:
    response = client_for(manager).get("/api/v1/reports/overview/", {"period": "2026-3"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "period" in response.data
