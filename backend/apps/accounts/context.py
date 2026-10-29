from django.http import HttpRequest
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request

from apps.accounts.models import User
from apps.organizations.models import Organization


def request_user(request: HttpRequest | Request) -> User:
    user = request.user
    if not isinstance(user, User) or not user.is_authenticated:
        raise NotAuthenticated
    return user


def request_organization(request: HttpRequest | Request) -> Organization:
    organization = request_user(request).organization
    if organization is None:
        raise PermissionDenied("You must belong to an organization.")
    return organization
