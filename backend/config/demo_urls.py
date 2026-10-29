"""Same-origin API, live activity and React routes for the public demo."""

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import include, path, re_path

from config.urls import api_v1_patterns


def health(request: HttpRequest) -> JsonResponse:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok", "demo": True})


def frontend(request: HttpRequest) -> HttpResponse:
    response = HttpResponse(
        (settings.BASE_DIR / "frontend_dist" / "index.html").read_bytes(),
        content_type="text/html",
    )
    response["Cache-Control"] = "no-cache"
    return response


urlpatterns = [
    path("healthz", health),
    path("api/v1/", include(api_v1_patterns)),
    re_path(r"^(?!api/|admin/|assets/).*", frontend),
]
