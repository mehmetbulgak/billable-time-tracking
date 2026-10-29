from collections.abc import Callable
from datetime import datetime, timedelta

import pytest

from apps.accounts.models import User
from apps.core.exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.timetracking import services
from apps.timetracking.models import TimeEntry
from tests.factories import ISTANBUL, InvoiceFactory, ProjectFactory, TimeEntryFactory

NOW = datetime(2026, 3, 10, 15, 0, tzinfo=ISTANBUL)


@pytest.fixture
def project(organization: Organization) -> Project:
    return ProjectFactory(client__organization=organization)


class TestTimer:
    def test_start_creates_a_running_entry(self, member: User, project: Project) -> None:
        entry = services.start_timer(
            user=member, project=project, description="Wireframes", now=NOW
        )

        assert entry.is_running
        assert entry.started_at == NOW
        assert entry.is_billable is project.is_billable
        assert entry.organization_id == project.organization_id

    def test_starting_a_new_timer_stops_the_running_one(
        self, member: User, project: Project
    ) -> None:
        first = services.start_timer(user=member, project=project, now=NOW)

        second = services.start_timer(user=member, project=project, now=NOW + timedelta(minutes=30))

        first.refresh_from_db()
        assert first.ended_at == NOW + timedelta(minutes=30)
        assert second.started_at == first.ended_at
        assert TimeEntry.objects.running().filter(user=member).get() == second

    def test_billable_flag_defaults_to_the_project_setting(
        self,
        member: User,
        organization: Organization,
    ) -> None:
        internal = ProjectFactory(client__organization=organization, is_billable=False)

        entry = services.start_timer(user=member, project=internal, now=NOW)

        assert entry.is_billable is False

    def test_stop_ends_the_running_timer(self, member: User, project: Project) -> None:
        services.start_timer(user=member, project=project, now=NOW)

        entry = services.stop_timer(user=member, now=NOW + timedelta(minutes=45))

        assert entry.ended_at == NOW + timedelta(minutes=45)
        assert entry.duration_seconds == 45 * 60

    def test_stop_without_a_running_timer_fails(self, member: User) -> None:
        with pytest.raises(NotFoundError) as error:
            services.stop_timer(user=member, now=NOW)

        assert error.value.code == "no_running_timer"

    def test_archived_projects_cannot_be_tracked(self, member: User, project: Project) -> None:
        project.is_archived = True
        project.save()

        with pytest.raises(DomainError) as error:
            services.start_timer(user=member, project=project, now=NOW)

        assert error.value.code == "project_archived"

    def test_projects_of_other_organizations_are_hidden(self, member: User) -> None:
        foreign_project = ProjectFactory()

        with pytest.raises(NotFoundError):
            services.start_timer(user=member, project=foreign_project, now=NOW)


class TestManualEntries:
    def test_create_entry(self, member: User, project: Project) -> None:
        entry = services.create_entry(
            user=member,
            project=project,
            started_at=NOW - timedelta(hours=2),
            ended_at=NOW - timedelta(hours=1),
            now=NOW,
        )

        assert entry.duration_seconds == 3600

    def test_overlapping_entries_are_rejected_by_the_database(
        self,
        member: User,
        project: Project,
    ) -> None:
        services.create_entry(
            user=member,
            project=project,
            started_at=NOW - timedelta(hours=3),
            ended_at=NOW - timedelta(hours=1),
            now=NOW,
        )

        with pytest.raises(ConflictError) as error:
            services.create_entry(
                user=member,
                project=project,
                started_at=NOW - timedelta(hours=2),
                ended_at=NOW - timedelta(minutes=30),
                now=NOW,
            )

        assert error.value.code == "overlapping_entry"

    def test_adjacent_entries_do_not_overlap(self, member: User, project: Project) -> None:
        boundary = NOW - timedelta(hours=2)
        services.create_entry(
            user=member,
            project=project,
            started_at=boundary - timedelta(hours=1),
            ended_at=boundary,
            now=NOW,
        )

        entry = services.create_entry(
            user=member,
            project=project,
            started_at=boundary,
            ended_at=boundary + timedelta(hours=1),
            now=NOW,
        )

        assert entry.pk is not None

    def test_entries_after_a_running_timer_overlap_it(self, member: User, project: Project) -> None:
        services.start_timer(user=member, project=project, now=NOW - timedelta(hours=2))

        with pytest.raises(ConflictError):
            services.create_entry(
                user=member,
                project=project,
                started_at=NOW - timedelta(hours=1),
                ended_at=NOW - timedelta(minutes=30),
                now=NOW,
            )

    def test_different_users_may_track_the_same_interval(
        self,
        member: User,
        other_member: User,
        project: Project,
    ) -> None:
        for user in (member, other_member):
            services.create_entry(
                user=user,
                project=project,
                started_at=NOW - timedelta(hours=2),
                ended_at=NOW - timedelta(hours=1),
                now=NOW,
            )

        assert TimeEntry.objects.count() == 2

    @pytest.mark.parametrize(
        ("start_offset", "end_offset", "code"),
        [
            (timedelta(hours=-1), timedelta(hours=-2), "invalid_range"),
            (timedelta(hours=-1), timedelta(hours=-1), "invalid_range"),
            (timedelta(hours=1), timedelta(hours=2), "future_entry"),
            (timedelta(hours=-1), timedelta(hours=1), "future_entry"),
        ],
    )
    def test_invalid_ranges_are_rejected(
        self,
        member: User,
        project: Project,
        start_offset: timedelta,
        end_offset: timedelta,
        code: str,
    ) -> None:
        with pytest.raises(DomainError) as error:
            services.create_entry(
                user=member,
                project=project,
                started_at=NOW + start_offset,
                ended_at=NOW + end_offset,
                now=NOW,
            )

        assert error.value.code == code


class TestEditing:
    def test_owner_of_the_entry_can_update_it(self, member: User, project: Project) -> None:
        entry = TimeEntryFactory(user=member, project=project)

        updated = services.update_entry(entry=entry, actor=member, description="Revised", now=NOW)

        assert updated.description == "Revised"

    def test_members_cannot_edit_entries_of_colleagues(
        self,
        member: User,
        other_member: User,
        project: Project,
    ) -> None:
        entry = TimeEntryFactory(user=other_member, project=project)

        with pytest.raises(ForbiddenError):
            services.update_entry(entry=entry, actor=member, description="Nope", now=NOW)

    def test_managers_can_edit_entries_of_their_team(
        self,
        manager: User,
        member: User,
        project: Project,
    ) -> None:
        entry = TimeEntryFactory(user=member, project=project)

        updated = services.update_entry(entry=entry, actor=manager, is_billable=False, now=NOW)

        assert updated.is_billable is False

    def test_invoiced_entries_are_locked(self, member: User, project: Project) -> None:
        entry = TimeEntryFactory(
            user=member, project=project, invoice=InvoiceFactory(client=project.client)
        )

        with pytest.raises(ConflictError) as error:
            services.update_entry(entry=entry, actor=member, description="Changed", now=NOW)
        with pytest.raises(ConflictError):
            services.delete_entry(entry=entry, actor=member)

        assert error.value.code == "entry_locked"

    def test_setting_an_end_time_stops_a_running_entry(
        self, member: User, project: Project
    ) -> None:
        entry = services.start_timer(user=member, project=project, now=NOW - timedelta(hours=1))

        updated = services.update_entry(
            entry=entry,
            actor=member,
            ended_at=NOW - timedelta(minutes=10),
            now=NOW,
        )

        assert not updated.is_running

    @pytest.mark.parametrize("operation", [services.update_entry, services.delete_entry])
    def test_stale_entries_cannot_bypass_invoice_lock(
        self, member: User, project: Project, operation: Callable[..., object]
    ) -> None:
        entry = TimeEntryFactory(user=member, project=project)
        invoice = InvoiceFactory(client=project.client)
        TimeEntry.objects.filter(pk=entry.pk).update(invoice=invoice)

        with pytest.raises(ConflictError, match="can no longer be changed"):
            operation(entry=entry, actor=member)

        entry.refresh_from_db()
        assert entry.invoice_id == invoice.pk

    def test_partial_updates_preserve_changes_made_after_loading(
        self, member: User, project: Project
    ) -> None:
        entry = TimeEntryFactory(user=member, project=project)
        TimeEntry.objects.filter(pk=entry.pk).update(is_billable=False)

        updated = services.update_entry(entry=entry, actor=member, description="Revised", now=NOW)

        assert updated.is_billable is False
        assert updated.description == "Revised"

    def test_managers_cannot_edit_another_organizations_entry(self, manager: User) -> None:
        entry = TimeEntryFactory()

        with pytest.raises(NotFoundError):
            services.update_entry(entry=entry, actor=manager, description="Changed", now=NOW)

    @pytest.mark.parametrize("operation", [services.update_entry, services.delete_entry])
    def test_entries_deleted_since_loading_return_not_found(
        self, member: User, project: Project, operation: Callable[..., object]
    ) -> None:
        entry = TimeEntryFactory(user=member, project=project)
        TimeEntry.objects.filter(pk=entry.pk).delete()

        with pytest.raises(NotFoundError):
            operation(entry=entry, actor=member)

    def test_delete_entry(self, member: User, project: Project) -> None:
        entry = TimeEntryFactory(user=member, project=project)

        services.delete_entry(entry=entry, actor=member)

        assert not TimeEntry.objects.filter(pk=entry.pk).exists()


def test_stale_timers_are_capped_at_the_maximum_duration(member: User, project: Project) -> None:
    stale = services.start_timer(user=member, project=project, now=NOW - timedelta(hours=14))

    stopped = services.stop_stale_timers(now=NOW, max_duration=timedelta(hours=12))

    stale.refresh_from_db()
    assert stopped == 1
    assert stale.ended_at == stale.started_at + timedelta(hours=12)


def test_recent_timers_are_left_running(member: User, project: Project) -> None:
    services.start_timer(user=member, project=project, now=NOW - timedelta(hours=2))

    assert services.stop_stale_timers(now=NOW, max_duration=timedelta(hours=12)) == 0
