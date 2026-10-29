from decimal import Decimal

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, override_settings

from apps.billing.exports import _safe_cell, invoice_csv
from apps.core.security import SecurityHeadersMiddleware
from tests.factories import InvoiceFactory, TimeEntryFactory


@pytest.mark.parametrize(
    "value",
    [
        '=HYPERLINK("https://attacker.example")',
        "+SUM(1,2)",
        "-1+2",
        "@SUM(1,2)",
        "\t=1+1",
        "\r=1+1",
        "\n=1+1",
        "  =1+1",
        "\ufeff=1+1",
        "\x00=1+1",
    ],
)
def test_untrusted_csv_cells_cannot_start_a_formula(value: str) -> None:
    assert _safe_cell(value) == f"'{value}"


@pytest.mark.parametrize("value", ["ordinary text", "", Decimal("-10.20"), 123])
def test_safe_csv_values_keep_their_types(value: object) -> None:
    assert _safe_cell(value) == value


@pytest.mark.django_db
def test_csv_escapes_client_line_project_member_and_entry_text() -> None:
    invoice = InvoiceFactory(client__name="=client", number="=number", status="issued")
    invoice.lines.create(
        position=1, description="=line", quantity=1, unit_price=1, amount=1, kind="hourly_time"
    )
    entry = TimeEntryFactory(
        project__name="=project", user__first_name="=member", description="=entry"
    )
    result = invoice_csv(invoice, [entry])
    for value in ("client", "number", "line", "project", "member", "entry"):
        assert f"'={value}" in result


@override_settings(ALLOWED_HOSTS=["testserver"])
def test_production_headers_restrict_browser_capabilities_and_cache() -> None:
    request = RequestFactory().get("/api/v1/auth/me/")
    middleware = SecurityHeadersMiddleware(lambda request: HttpResponse("{}"))
    response = middleware(request)
    assert "script-src 'self'" in response["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response["Content-Security-Policy"]
    assert "object-src 'none'" in response["Content-Security-Policy"]
    assert "no-store" in response["Cache-Control"]
    assert "Cookie" in response["Vary"]
    assert "camera=()" in response["Permissions-Policy"]


@override_settings(ALLOWED_HOSTS=["testserver"])
def test_host_header_is_validated_before_building_a_csp() -> None:
    request: HttpRequest = RequestFactory().get("/", HTTP_HOST="attacker.example")
    middleware = SecurityHeadersMiddleware(lambda request: HttpResponse("sensitive"))
    assert middleware(request).status_code == 400
