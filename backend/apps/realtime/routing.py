from django.urls import path

from apps.realtime.consumers import OrganizationActivityConsumer

websocket_urlpatterns = [
    path("ws/activity/", OrganizationActivityConsumer.as_asgi()),
]
