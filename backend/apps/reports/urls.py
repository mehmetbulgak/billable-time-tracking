from django.urls import path

from apps.reports.views import MyTimeView, OverviewView, RetainerReportView

urlpatterns = [
    path("reports/overview/", OverviewView.as_view(), name="report-overview"),
    path("reports/retainers/", RetainerReportView.as_view(), name="report-retainers"),
    path("reports/my-time/", MyTimeView.as_view(), name="report-my-time"),
]
