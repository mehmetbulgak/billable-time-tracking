from typing import Any

from django.db import IntegrityError, transaction

from apps.billing.domain.types import InvalidTermsError
from apps.billing.models import Contract, InvoiceStatus
from apps.clients.models import Client
from apps.core.db import violated_constraint
from apps.core.exceptions import ConflictError, DomainError
from apps.organizations.models import Organization

CONTRACT_OVERLAP_CONSTRAINT = "contracts_no_overlap_per_client"
IMMUTABLE_CONTRACT_FIELDS = frozenset(
    {
        "client",
        "billing_model",
        "starts_on",
        "hourly_rate",
        "monthly_fee",
        "included_hours",
        "overage_rate",
        "rollover_cap_hours",
        "rounding_increment_minutes",
    },
)


def _save_contract(contract: Contract) -> Contract:
    try:
        contract.to_terms()
    except InvalidTermsError as error:
        raise DomainError(str(error), code="invalid_terms") from error
    contract.full_clean(validate_constraints=False)
    try:
        with transaction.atomic():
            contract.save()
    except IntegrityError as error:
        if violated_constraint(error) != CONTRACT_OVERLAP_CONSTRAINT:
            raise
        raise ConflictError(
            "This contract overlaps another contract of the same client.",
            code="overlapping_contract",
        ) from error
    return contract


def create_contract(*, organization: Organization, **fields: Any) -> Contract:
    client: Client = fields["client"]
    if client.organization_id != organization.pk:
        raise DomainError("Unknown client.", code="unknown_client")
    return _save_contract(Contract(organization=organization, **fields))


def update_contract(*, contract: Contract, **fields: Any) -> Contract:
    has_issued_invoices = contract.invoices.exclude(status=InvoiceStatus.DRAFT).exists()
    changed = {name for name, value in fields.items() if getattr(contract, name) != value}
    if has_issued_invoices and changed & IMMUTABLE_CONTRACT_FIELDS:
        raise ConflictError(
            "Contracts with issued invoices can only change their end date.",
            code="contract_locked",
        )
    for name, value in fields.items():
        setattr(contract, name, value)
    return _save_contract(contract)
