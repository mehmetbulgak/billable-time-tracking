from collections.abc import Callable
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.timetracking.models import TimeEntry
from tests.factories import ProjectFactory, TimeEntryFactory

ClientFor = Callable[[User], APIClient]


@pytest.fixture
def project(organization: Organization) -> Project:
    return ProjectFactory(client__organization=organization)


def test_requires_authentication(api_client: APIClient) -> None:
    response = api_client.get("/api/v1/time-entries/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_timer_lifecycle(client_for: ClientFor, member: User, project: Project) -> None:
    api = client_for(member)

    assert api.get("/api/v1/time-entries/current/").status_code == status.HTTP_204_NO_CONTENT

    started = api.post(
        "/api/v1/time-entries/start/",
        {"project": project.pk, "description": "Moodboard"},
    )
    assert started.status_code == status.HTTP_201_CREATED
    assert started.data["is_running"] is True
    assert started.data["project"]["id"] == project.pk

    current = api.get("/api/v1/time-entries/current/")
    assert current.data["id"] == started.data["id"]

    stopped = api.post("/api/v1/time-entries/stop/")
    assert stopped.status_code == status.HTTP_200_OK
    assert stopped.data["is_running"] is False

    assert api.post("/api/v1/time-entries/stop/").status_code == status.HTTP_404_NOT_FOUND


def test_members_only_see_their_own_entries(
    client_for: ClientFor,
    member: User,
    other_member: User,
    project: Project,
) -> None:
    own = TimeEntryFactory(user=member, project=project)
    TimeEntryFactory(user=other_member, project=project)

    response = client_for(member).get("/api/v1/time-entries/")

    assert [entry["id"] for entry in response.data["results"]] == [own.pk]


def test_managers_see_the_whole_team(
    client_for: ClientFor,
    manager: User,
    member: User,
    other_member: User,
    project: Project,
) -> None:
    TimeEntryFactory(user=member, project=project)
    TimeEntryFactory(user=other_member, project=project)

    response = client_for(manager).get("/api/v1/time-entries/")

    assert response.data["count"] == 2


def test_entries_of_other_organizations_are_invisible(
    client_for: ClientFor,
    manager: User,
    outsider: User,
) -> None:
    foreign = TimeEntryFactory(user=outsider, project__client__organization=outsider.organization)

    api = client_for(manager)

    assert api.get("/api/v1/time-entries/").data["count"] == 0
    assert api.get(f"/api/v1/time-entries/{foreign.pk}/").status_code == status.HTTP_404_NOT_FOUND


def test_cannot_track_time_on_foreign_projects(client_for: ClientFor, member: User) -> None:
    foreign_project = ProjectFactory()

    response = client_for(member).post(
        "/api/v1/time-entries/start/", {"project": foreign_project.pk}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "project" in response.data


def test_create_update_and_delete_manual_entry(
    client_for: ClientFor,
    member: User,
    project: Project,
) -> None:
    api = client_for(member)
    started_at = timezone.now() - timedelta(hours=3)

    created = api.post(
        "/api/v1/time-entries/",
        {
            "project": project.pk,
            "description": "Client call",
            "started_at": started_at.isoformat(),
            "ended_at": (started_at + timedelta(minutes=90)).isoformat(),
        },
    )
    assert created.status_code == status.HTTP_201_CREATED
    assert created.data["duration_seconds"] == 90 * 60

    entry_url = f"/api/v1/time-entries/{created.data['id']}/"
    updated = api.patch(entry_url, {"description": "Kick-off call", "is_billable": False})
    assert updated.status_code == status.HTTP_200_OK
    assert updated.data["description"] == "Kick-off call"
    assert updated.data["is_billable"] is False

    assert api.delete(entry_url).status_code == status.HTTP_204_NO_CONTENT
    assert not TimeEntry.objects.exists()


def test_overlapping_entries_return_conflict(
    client_for: ClientFor,
    member: User,
    project: Project,
) -> None:
    existing = TimeEntryFactory(user=member, project=project)

    response = client_for(member).post(
        "/api/v1/time-entries/",
        {
            "project": project.pk,
            "started_at": (existing.started_at + timedelta(minutes=15)).isoformat(),
            "ended_at": (existing.ended_at + timedelta(minutes=15)).isoformat(),
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["code"] == "overlapping_entry"


def test_members_cannot_change_colleagues_entries(
    client_for: ClientFor,
    member: User,
    other_member: User,
    project: Project,
) -> None:
    entry = TimeEntryFactory(user=other_member, project=project)

    response = client_for(member).patch(f"/api/v1/time-entries/{entry.pk}/", {"description": "x"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_active_timers_are_visible_to_the_whole_team(
    client_for: ClientFor,
    member: User,
    other_member: User,
    project: Project,
) -> None:
    client_for(other_member).post("/api/v1/time-entries/start/", {"project": project.pk})

    response = client_for(member).get("/api/v1/time-entries/active/")

    assert response.status_code == status.HTTP_200_OK
    assert [entry["user"]["id"] for entry in response.data] == [other_member.pk]


def test_filters_by_date_range_and_invoice_state(
    client_for: ClientFor,
    manager: User,
    project: Project,
) -> None:
    early = TimeEntryFactory(user=manager, project=project)
    late = TimeEntryFactory(user=manager, project=project)
    api = client_for(manager)

    response = api.get(
        "/api/v1/time-entries/",
        {"started_after": late.started_at.isoformat(), "is_invoiced": "false"},
    )

    ids = [entry["id"] for entry in response.data["results"]]
    assert ids == [late.pk]
    assert early.pk not in ids
