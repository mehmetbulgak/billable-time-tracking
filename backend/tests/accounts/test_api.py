from collections.abc import Callable

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.organizations.models import Organization
from tests.factories import UserFactory

ClientFor = Callable[[User], APIClient]
PASSWORD = "correct-horse-battery"


def test_obtain_tokens_and_read_profile(api_client: APIClient, member: User) -> None:
    tokens = api_client.post(
        "/api/v1/auth/token/",
        {"email": member.email, "password": PASSWORD},
    )
    assert tokens.status_code == status.HTTP_200_OK

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.data['access']}")
    profile = api_client.get("/api/v1/auth/me/")

    assert profile.status_code == status.HTTP_200_OK
    assert profile.data["email"] == member.email
    assert profile.data["is_manager"] is False
    assert profile.data["organization"]["id"] == member.organization_id


def test_refresh_token_rotation(api_client: APIClient, member: User) -> None:
    tokens = api_client.post("/api/v1/auth/token/", {"email": member.email, "password": PASSWORD})

    original = api_client.cookies["billable_refresh"].value
    refreshed = api_client.post("/api/v1/auth/token/refresh/")

    assert refreshed.status_code == status.HTTP_200_OK
    assert {"access", "csrf_token"} == refreshed.data.keys()
    assert api_client.cookies["billable_refresh"].value != original
    assert "refresh" not in tokens.data


def test_wrong_password_is_rejected(api_client: APIClient, member: User) -> None:
    response = api_client.post("/api/v1/auth/token/", {"email": member.email, "password": "nope"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_users_without_organization_are_forbidden(client_for: ClientFor, db: None) -> None:
    orphan = UserFactory(organization=None)

    response = client_for(orphan).get("/api/v1/time-entries/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_profile_name_can_be_updated(client_for: ClientFor, member: User) -> None:
    response = client_for(member).patch("/api/v1/auth/me/", {"first_name": "Elif", "role": "owner"})

    member.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert member.first_name == "Elif"
    assert member.role == Role.MEMBER


class TestMembers:
    def test_members_can_list_their_team_only(
        self,
        client_for: ClientFor,
        member: User,
        manager: User,
        outsider: User,
    ) -> None:
        response = client_for(member).get("/api/v1/members/")

        emails = {row["email"] for row in response.data["results"]}
        assert emails == {member.email, manager.email}

    def test_members_cannot_invite(self, client_for: ClientFor, member: User) -> None:
        response = client_for(member).post(
            "/api/v1/members/",
            {
                "email": "new@example.test",
                "first_name": "N",
                "last_name": "M",
                "password": PASSWORD,
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_managers_can_add_members(
        self,
        client_for: ClientFor,
        manager: User,
        organization: Organization,
    ) -> None:
        response = client_for(manager).post(
            "/api/v1/members/",
            {
                "email": "new@example.test",
                "first_name": "Nur",
                "last_name": "Ak",
                "role": Role.MEMBER,
                "password": PASSWORD,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        created = User.objects.get(email="new@example.test")
        assert created.organization == organization
        assert created.check_password(PASSWORD)

    def test_weak_passwords_are_rejected(self, client_for: ClientFor, manager: User) -> None:
        response = client_for(manager).post(
            "/api/v1/members/",
            {"email": "weak@example.test", "first_name": "W", "last_name": "P", "password": "123"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_duplicate_emails_conflict(
        self, client_for: ClientFor, manager: User, member: User
    ) -> None:
        response = client_for(manager).post(
            "/api/v1/members/",
            {"email": member.email, "first_name": "D", "last_name": "U", "password": PASSWORD},
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_managers_cannot_grant_ownership(self, client_for: ClientFor, manager: User) -> None:
        response = client_for(manager).post(
            "/api/v1/members/",
            {
                "email": "boss@example.test",
                "first_name": "B",
                "last_name": "S",
                "role": Role.OWNER,
                "password": PASSWORD,
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_can_promote_a_member(
        self, client_for: ClientFor, owner: User, member: User
    ) -> None:
        response = client_for(owner).patch(f"/api/v1/members/{member.pk}/", {"role": Role.MANAGER})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == Role.MANAGER

    @pytest.mark.parametrize("payload", [{"role": Role.MEMBER}, {"is_active": False}])
    def test_users_cannot_demote_or_deactivate_themselves(
        self,
        client_for: ClientFor,
        owner: User,
        payload: dict[str, object],
    ) -> None:
        response = client_for(owner).patch(f"/api/v1/members/{owner.pk}/", payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_deactivated_owners_cannot_change_members(
        self,
        client_for: ClientFor,
        owner: User,
        organization: Organization,
    ) -> None:
        second_owner = UserFactory(organization=organization, role=Role.OWNER)
        api = client_for(second_owner)

        assert api.patch(f"/api/v1/members/{owner.pk}/", {"is_active": False}).status_code == 200
        response = client_for(owner).patch(
            f"/api/v1/members/{second_owner.pk}/",
            {"role": Role.MEMBER},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
