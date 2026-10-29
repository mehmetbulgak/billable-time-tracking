from django.urls import path

from apps.organizations.views import CurrentOrganizationView

urlpatterns = [
    path("organization/", CurrentOrganizationView.as_view(), name="current-organization"),
]
