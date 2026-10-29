from django.db import transaction

from apps.accounts.models import Role, User
from apps.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from apps.organizations.models import Organization


def _lock_actor(*, organization_id: int, actor: User) -> User:
    Organization.objects.select_for_update().get(pk=organization_id)
    actor = User.objects.get(pk=actor.pk)
    if actor.organization_id != organization_id:
        raise NotFoundError("Organization not found.")
    if not actor.is_manager:
        raise ForbiddenError("Only owners and managers can manage members.")
    return actor


def _ensure_can_assign_role(*, actor: User, role: str) -> None:
    if role == Role.OWNER and not actor.is_owner:
        raise ForbiddenError("Only owners can grant the owner role.", code="owner_role_required")


def _ensure_other_active_owner_exists(member: User) -> None:
    other_owners = User.objects.filter(
        organization=member.organization,
        role=Role.OWNER,
        is_active=True,
    ).exclude(pk=member.pk)
    if not other_owners.exists():
        raise ConflictError(
            "An organization must keep at least one active owner.",
            code="last_owner",
        )


@transaction.atomic
def create_member(
    *,
    organization: Organization,
    actor: User,
    email: str,
    first_name: str,
    last_name: str,
    role: str,
    password: str,
) -> User:
    actor = _lock_actor(organization_id=organization.pk, actor=actor)
    _ensure_can_assign_role(actor=actor, role=role)
    if User.objects.filter(email__iexact=email).exists():
        raise ConflictError("A user with this email already exists.", code="email_taken")
    return User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        organization=organization,
        role=role,
    )


@transaction.atomic
def update_member(
    *,
    member: User,
    actor: User,
    first_name: str | None = None,
    last_name: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> User:
    if member.organization_id is None or member.organization_id != actor.organization_id:
        raise NotFoundError("Member not found.")
    actor = _lock_actor(organization_id=member.organization_id, actor=actor)
    member = User.objects.select_for_update().get(pk=member.pk)
    if member.is_owner and not actor.is_owner:
        raise ForbiddenError("Only owners can modify another owner.", code="owner_role_required")

    is_self = member.pk == actor.pk
    if role is not None and role != member.role:
        if is_self:
            raise ForbiddenError("You cannot change your own role.", code="self_role_change")
        _ensure_can_assign_role(actor=actor, role=role)
        if member.is_owner:
            _ensure_other_active_owner_exists(member)
        member.role = role

    if is_active is not None and is_active != member.is_active:
        if is_self:
            raise ForbiddenError("You cannot deactivate yourself.", code="self_deactivation")
        if not is_active and member.is_owner:
            _ensure_other_active_owner_exists(member)
        member.is_active = is_active

    if first_name is not None:
        member.first_name = first_name
    if last_name is not None:
        member.last_name = last_name

    member.full_clean()
    member.save()
    return member
