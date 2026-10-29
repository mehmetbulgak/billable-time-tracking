from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.accounts.session_views import CSRFTokenView, LoginView, LogoutView, RefreshView
from apps.accounts.views import CurrentUserView, MemberViewSet

router = SimpleRouter()
router.register("members", MemberViewSet, basename="member")

urlpatterns = [
    path("auth/csrf/", CSRFTokenView.as_view(), name="csrf-token"),
    path("auth/token/", LoginView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    *router.urls,
]
