from collections.abc import Callable

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.clients.models import Client
from apps.organizations.models import Organization
from apps.projects.models import Project
from tests.factories import ClientFactory, ProjectFactory, TimeEntryFactory

ClientFor = Callable[[User], APIClient]


class TestOrganization:
    def test_members_can_read_settings(self, client_for: ClientFor, member: User) -> None:
        response = client_for(member).get("/api/v1/organization/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["timezone"] == "Europe/Istanbul"

    def test_members_cannot_change_settings(self, client_for: ClientFor, member: User) -> None:
        response = client_for(member).patch("/api/v1/organization/", {"name": "Hijacked"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_managers_can_change_settings(self, client_for: ClientFor, manager: User) -> None:
        response = client_for(manager).patch(
            "/api/v1/organization/",
            {"timezone": "Europe/Berlin", "default_payment_terms_days": 30},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["timezone"] == "Europe/Berlin"

    def test_unknown_time_zones_are_rejected(self, client_for: ClientFor, manager: User) -> None:
        response = client_for(manager).patch("/api/v1/organization/", {"timezone": "Mars/Base"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestClients:
    def test_currency_defaults_to_the_agency_currency(
        self,
        client_for: ClientFor,
        manager: User,
        organization: Organization,
    ) -> None:
        response = client_for(manager).post("/api/v1/clients/", {"name": "Lumen Coffee"})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["currency"] == organization.default_currency

    def test_names_are_unique_per_agency(
        self,
        client_for: ClientFor,
        manager: User,
        organization: Organization,
    ) -> None:
        ClientFactory(organization=organization, name="Lumen Coffee")
        ClientFactory(name="Atlas")

        api = client_for(manager)

        assert api.post("/api/v1/clients/", {"name": "lumen coffee"}).status_code == 400
        assert api.post("/api/v1/clients/", {"name": "Atlas"}).status_code == 201

    def test_members_can_read_but_not_write(self, client_for: ClientFor, member: User) -> None:
        api = client_for(member)

        assert api.get("/api/v1/clients/").status_code == status.HTTP_200_OK
        assert api.post("/api/v1/clients/", {"name": "X"}).status_code == status.HTTP_403_FORBIDDEN

    def test_clients_in_use_must_be_archived_instead_of_deleted(
        self,
        client_for: ClientFor,
        manager: User,
        organization: Organization,
    ) -> None:
        client = ClientFactory(organization=organization)
        ProjectFactory(client=client)
        api = client_for(manager)

        deleted = api.delete(f"/api/v1/clients/{client.pk}/")
        archived = api.patch(f"/api/v1/clients/{client.pk}/", {"is_archived": True})

        assert deleted.status_code == status.HTTP_409_CONFLICT
        assert archived.data["is_archived"] is True

    def test_unused_clients_can_be_deleted(
        self,
        client_for: ClientFor,
        manager: User,
        organization: Organization,
    ) -> None:
        client = ClientFactory(organization=organization)

        response = client_for(manager).delete(f"/api/v1/clients/{client.pk}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Client.objects.exists()


class TestProjects:
    @pytest.fixture
    def client(self, organization: Organization) -> Client:
        return ClientFactory(organization=organization)

    def test_codes_are_normalized_to_upper_case(
        self,
        client_for: ClientFor,
        manager: User,
        client: Client,
    ) -> None:
        response = client_for(manager).post(
            "/api/v1/projects/",
            {"client": client.pk, "name": "Website", "code": " lum-web "},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["code"] == "LUM-WEB"
        assert response.data["client_name"] == client.name

    @pytest.mark.parametrize("code", ["x", "has space", "TOO-LONG-CODE-1"])
    def test_invalid_codes_are_rejected(
        self,
        client_for: ClientFor,
        manager: User,
        client: Client,
        code: str,
    ) -> None:
        response = client_for(manager).post(
            "/api/v1/projects/",
            {"client": client.pk, "name": "Website", "code": code},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.data

    def test_codes_and_names_must_be_unique(
        self,
        client_for: ClientFor,
        manager: User,
        client: Client,
    ) -> None:
        ProjectFactory(client=client, name="Website", code="LUM-WEB")
        api = client_for(manager)

        same_code = api.post(
            "/api/v1/projects/", {"client": client.pk, "name": "Other", "code": "LUM-WEB"}
        )
        same_name = api.post(
            "/api/v1/projects/", {"client": client.pk, "name": "website", "code": "LUM-2"}
        )

        assert "code" in same_code.data
        assert "name" in same_name.data

    def test_archived_clients_get_no_new_projects(
        self,
        client_for: ClientFor,
        manager: User,
        client: Client,
    ) -> None:
        client.is_archived = True
        client.save()

        response = client_for(manager).post(
            "/api/v1/projects/",
            {"client": client.pk, "name": "Website", "code": "LUM-WEB"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "client" in response.data

    def test_clients_of_other_agencies_cannot_be_used(
        self, client_for: ClientFor, manager: User
    ) -> None:
        foreign_client = ClientFactory()

        response = client_for(manager).post(
            "/api/v1/projects/",
            {"client": foreign_client.pk, "name": "Website", "code": "LUM-WEB"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_projects_with_time_cannot_be_deleted(
        self,
        client_for: ClientFor,
        manager: User,
        client: Client,
    ) -> None:
        project = ProjectFactory(client=client)
        TimeEntryFactory(project=project, user=manager)

        response = client_for(manager).delete(f"/api/v1/projects/{project.pk}/")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert Project.objects.filter(pk=project.pk).exists()

    def test_filter_by_client(self, client_for: ClientFor, member: User, client: Client) -> None:
        wanted = ProjectFactory(client=client)
        ProjectFactory(client__organization=client.organization)

        response = client_for(member).get("/api/v1/projects/", {"client": client.pk})

        assert [project["id"] for project in response.data["results"]] == [wanted.pk]

    def test_tracked_projects_cannot_move_to_another_client(
        self, client_for: ClientFor, manager: User, client: Client
    ) -> None:
        project = ProjectFactory(client=client)
        TimeEntryFactory(project=project, user=manager)
        destination = ClientFactory(organization=client.organization)

        response = client_for(manager).patch(
            f"/api/v1/projects/{project.pk}/", {"client": destination.pk}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        project.refresh_from_db()
        assert project.client_id == client.pk

    def test_unused_projects_can_move_to_another_client(
        self, client_for: ClientFor, manager: User, client: Client
    ) -> None:
        project = ProjectFactory(client=client)
        destination = ClientFactory(organization=client.organization)

        response = client_for(manager).patch(
            f"/api/v1/projects/{project.pk}/", {"client": destination.pk}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["client"] == destination.pk

    def test_unused_projects_cannot_move_to_archived_clients(
        self, client_for: ClientFor, manager: User, client: Client
    ) -> None:
        project = ProjectFactory(client=client)
        destination = ClientFactory(organization=client.organization, is_archived=True)

        response = client_for(manager).patch(
            f"/api/v1/projects/{project.pk}/", {"client": destination.pk}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
