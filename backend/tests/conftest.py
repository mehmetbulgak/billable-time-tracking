from collections.abc import Callable

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.organizations.models import Organization
from tests.factories import OrganizationFactory, UserFactory


@pytest.fixture
def organization(db: None) -> Organization:
    return OrganizationFactory(invoice_prefix="NWS", default_payment_terms_days=14)


@pytest.fixture
def owner(organization: Organization) -> User:
    return UserFactory(organization=organization, role=Role.OWNER)


@pytest.fixture
def manager(organization: Organization) -> User:
    return UserFactory(organization=organization, role=Role.MANAGER)


@pytest.fixture
def member(organization: Organization) -> User:
    return UserFactory(organization=organization, role=Role.MEMBER)


@pytest.fixture
def other_member(organization: Organization) -> User:
    return UserFactory(organization=organization, role=Role.MEMBER)


@pytest.fixture
def outsider(db: None) -> User:
    return UserFactory(role=Role.OWNER)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def client_for(api_client: APIClient) -> Callable[[User], APIClient]:
    def authenticate(user: User) -> APIClient:
        api_client.force_authenticate(user=user)
        return api_client

    return authenticate
