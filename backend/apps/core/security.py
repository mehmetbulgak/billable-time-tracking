from collections.abc import Callable

from django.core.exceptions import DisallowedHost
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.cache import patch_vary_headers


def csrf_failure(request: HttpRequest, reason: str = "") -> JsonResponse:
    return JsonResponse(
        {"detail": "CSRF verification failed. Reload the page and try again."}, status=403
    )


class SecurityHeadersMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            host = request.get_host()
        except DisallowedHost:
            return HttpResponseBadRequest("Invalid host.")
        response = self.get_response(request)
        socket_origin = f"{'wss' if request.is_secure() else 'ws'}://{host}"
        response["Content-Security-Policy"] = "; ".join(
            (
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data:",
                "font-src 'self'",
                f"connect-src 'self' {socket_origin}",
                "object-src 'none'",
                "base-uri 'none'",
                "frame-ancestors 'none'",
                "form-action 'self'",
            ),
        )
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        if request.path.startswith("/api/"):
            response["Cache-Control"] = "no-store, private"
            patch_vary_headers(response, ("Authorization", "Cookie"))
        return response
