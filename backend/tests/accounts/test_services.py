import pytest

from apps.accounts import services
from apps.accounts.models import Role, User
from apps.core.exceptions import ForbiddenError, NotFoundError


def test_stale_member_cannot_bypass_owner_permissions(manager: User, member: User) -> None:
    User.objects.filter(pk=member.pk).update(role=Role.OWNER)

    with pytest.raises(ForbiddenError, match="Only owners"):
        services.update_member(member=member, actor=manager, first_name="Changed")


def test_profile_updates_do_not_overwrite_new_roles(manager: User, member: User) -> None:
    User.objects.filter(pk=member.pk).update(role=Role.MANAGER)

    updated = services.update_member(member=member, actor=manager, first_name="Revised")

    assert updated.role == Role.MANAGER
    assert updated.first_name == "Revised"


def test_managers_cannot_change_foreign_members(manager: User, outsider: User) -> None:
    with pytest.raises(NotFoundError):
        services.update_member(member=outsider, actor=manager, first_name="Changed")


def test_demoted_managers_cannot_use_stale_permissions(manager: User, member: User) -> None:
    User.objects.filter(pk=manager.pk).update(role=Role.MEMBER)

    with pytest.raises(ForbiddenError, match="manage members"):
        services.update_member(member=member, actor=manager, first_name="Changed")
