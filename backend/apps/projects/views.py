from django.db.models import ProtectedError, QuerySet
from rest_framework import viewsets

from apps.core.exceptions import ConflictError
from apps.core.permissions import IsManagerOrReadOnly, IsOrganizationMember
from apps.core.views import OrganizationScopedMixin
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer


class ProjectViewSet(OrganizationScopedMixin[Project], viewsets.ModelViewSet[Project]):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsOrganizationMember, IsManagerOrReadOnly)
    filterset_fields = ("client", "is_archived", "is_billable")
    search_fields = ("name", "code", "client__name")
    ordering_fields = ("name", "code", "created_at")

    def get_queryset(self) -> QuerySet[Project]:
        return super().get_queryset().select_related("client")

    def perform_destroy(self, instance: Project) -> None:
        try:
            instance.delete()
        except ProtectedError as error:
            raise ConflictError(
                "This project has tracked time. Archive it instead.",
                code="project_in_use",
            ) from error
