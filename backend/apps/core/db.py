from django.db import IntegrityError


def violated_constraint(error: IntegrityError) -> str | None:
    diagnostics = getattr(error.__cause__, "diag", None)
    constraint_name: str | None = getattr(diagnostics, "constraint_name", None)
    return constraint_name
