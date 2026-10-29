from collections.abc import Callable
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing.models import Contract, Invoice, InvoiceStatus
from apps.clients.models import Client
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
    return ClientFactory(organization=organization)


@pytest.fixture
def project(client: Client) -> Project:
    return ProjectFactory(client=client)


@pytest.fixture
def retainer(client: Client) -> Contract:
    return ContractFactory(client=client, retainer=True)


@pytest.fixture
def tracked_march(member: User, project: Project, retainer: Contract) -> None:
    start = datetime(2026, 3, 2, 9, 0, tzinfo=ISTANBUL)
    TimeEntryFactory(
        user=member, project=project, started_at=start, ended_at=start + timedelta(hours=22)
    )


def test_members_cannot_access_billing(client_for: ClientFor, member: User) -> None:
    api = client_for(member)

    assert api.get("/api/v1/invoices/").status_code == status.HTTP_403_FORBIDDEN
    assert api.get("/api/v1/contracts/").status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.usefixtures("tracked_march")
def test_preview_does_not_create_an_invoice(
    client_for: ClientFor, manager: User, client: Client
) -> None:
    response = client_for(manager).get(
        "/api/v1/invoices/preview/",
        {"client": client.pk, "period": "2026-03"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["subtotal"] == "2300.00"
    assert response.data["overage_hours"] == "2.00"
    assert [line["kind"] for line in response.data["lines"]] == [
        "retainer_fee",
        "included_hours",
        "overage",
    ]
    assert response.data["is_empty"] is False
    assert response.data["replaces_draft"] is None
    assert not Invoice.objects.exists()


@pytest.mark.usefixtures("tracked_march")
def test_preview_flags_the_draft_it_would_replace(
    client_for: ClientFor, manager: User, client: Client
) -> None:
    api = client_for(manager)
    draft = api.post("/api/v1/invoices/generate/", {"client": client.pk, "period": "2026-03"})

    response = api.get("/api/v1/invoices/preview/", {"client": client.pk, "period": "2026-03"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["replaces_draft"] == draft.data["id"]
    assert response.data["subtotal"] == draft.data["subtotal"]


@pytest.mark.usefixtures("tracked_march")
def test_full_invoice_lifecycle(client_for: ClientFor, manager: User, client: Client) -> None:
    api = client_for(manager)

    generated = api.post("/api/v1/invoices/generate/", {"client": client.pk, "period": "2026-03"})
    assert generated.status_code == status.HTTP_201_CREATED
    assert generated.data["status"] == InvoiceStatus.DRAFT
    assert generated.data["total"] == "2300.00"
    assert generated.data["time_entry_count"] == 1
    invoice_url = f"/api/v1/invoices/{generated.data['id']}/"

    listing = api.get("/api/v1/invoices/", {"status": "draft"})
    assert listing.data["count"] == 1
    assert listing.data["results"][0]["billable_hours"] == "22.00"

    issued = api.post(f"{invoice_url}issue/")
    assert issued.status_code == status.HTTP_200_OK
    assert issued.data["number"].startswith("NWS-")

    export = api.get(f"{invoice_url}export/")
    assert export.status_code == status.HTTP_200_OK
    assert export["Content-Type"].startswith("text/csv")
    assert issued.data["number"] in export.content.decode()

    paid = api.post(f"{invoice_url}mark-paid/")
    assert paid.data["status"] == InvoiceStatus.PAID

    assert api.post(f"{invoice_url}void/").status_code == status.HTTP_409_CONFLICT


@pytest.mark.usefixtures("tracked_march")
def test_drafts_can_be_discarded(client_for: ClientFor, manager: User, client: Client) -> None:
    api = client_for(manager)
    invoice_id = api.post(
        "/api/v1/invoices/generate/",
        {"client": client.pk, "period": "2026-03"},
    ).data["id"]

    response = api.delete(f"/api/v1/invoices/{invoice_id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Invoice.objects.exists()


def test_generate_rejects_future_periods_and_bad_formats(
    client_for: ClientFor,
    manager: User,
    client: Client,
) -> None:
    api = client_for(manager)

    future = api.post("/api/v1/invoices/generate/", {"client": client.pk, "period": "2099-01"})
    malformed = api.post("/api/v1/invoices/generate/", {"client": client.pk, "period": "March"})

    assert future.status_code == status.HTTP_400_BAD_REQUEST
    assert malformed.status_code == status.HTTP_400_BAD_REQUEST
    assert "period" in malformed.data


def test_generate_without_contract_explains_the_problem(
    client_for: ClientFor,
    manager: User,
    client: Client,
) -> None:
    response = client_for(manager).post(
        "/api/v1/invoices/generate/",
        {"client": client.pk, "period": "2026-03"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["code"] == "no_active_contract"


class TestContractsApi:
    def test_create_retainer_contract(
        self, client_for: ClientFor, manager: User, client: Client
    ) -> None:
        response = client_for(manager).post(
            "/api/v1/contracts/",
            {
                "client": client.pk,
                "billing_model": "retainer",
                "starts_on": "2026-01-01",
                "monthly_fee": "3000.00",
                "included_hours": "30.00",
                "overage_rate": "120.00",
                "rollover_cap_hours": "6.00",
                "rounding_increment_minutes": 15,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["client_name"] == client.name
        assert Contract.objects.get().included_hours == Decimal("30.00")

    def test_incomplete_terms_are_a_validation_error(
        self,
        client_for: ClientFor,
        manager: User,
        client: Client,
    ) -> None:
        response = client_for(manager).post(
            "/api/v1/contracts/",
            {"client": client.pk, "billing_model": "hourly", "starts_on": "2026-01-01"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_terms"

    def test_overlapping_contract_is_a_conflict(
        self,
        client_for: ClientFor,
        manager: User,
        client: Client,
        retainer: Contract,
    ) -> None:
        response = client_for(manager).post(
            "/api/v1/contracts/",
            {
                "client": client.pk,
                "billing_model": "hourly",
                "starts_on": "2026-05-01",
                "hourly_rate": "100.00",
            },
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_end_date_cannot_precede_start(
        self, client_for: ClientFor, manager: User, client: Client
    ) -> None:
        response = client_for(manager).post(
            "/api/v1/contracts/",
            {
                "client": client.pk,
                "billing_model": "hourly",
                "starts_on": "2026-05-01",
                "ends_on": "2026-04-01",
                "hourly_rate": "100.00",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ends_on" in response.data

    def test_contracts_with_invoices_cannot_be_deleted(
        self,
        client_for: ClientFor,
        manager: User,
        retainer: Contract,
        client: Client,
        tracked_march: None,
    ) -> None:
        api = client_for(manager)
        assert api.get(f"/api/v1/contracts/{retainer.pk}/").data["has_invoices"] is False
        api.post("/api/v1/invoices/generate/", {"client": client.pk, "period": "2026-03"})

        listed = api.get("/api/v1/contracts/", {"client": client.pk})
        response = api.delete(f"/api/v1/contracts/{retainer.pk}/")

        assert [contract["has_invoices"] for contract in listed.data["results"]] == [True]
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_patch_end_date(self, client_for: ClientFor, manager: User, retainer: Contract) -> None:
        response = client_for(manager).patch(
            f"/api/v1/contracts/{retainer.pk}/",
            {"ends_on": "2026-12-31"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["has_invoices"] is False
        retainer.refresh_from_db()
        assert retainer.ends_on == date(2026, 12, 31)
