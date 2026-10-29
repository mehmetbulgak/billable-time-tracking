from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserSummarySerializer
from apps.core.serializers import OrganizationScopedPrimaryKeyRelatedField
from apps.projects.models import Project
from apps.projects.serializers import ProjectSummarySerializer
from apps.timetracking.models import TimeEntry


class TimeEntrySerializer(serializers.ModelSerializer[TimeEntry]):
    user = UserSummarySerializer(read_only=True)
    project = ProjectSummarySerializer(read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    is_running = serializers.BooleanField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    invoice_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = TimeEntry
        fields = (
            "id",
            "user",
            "project",
            "description",
            "started_at",
            "ended_at",
            "duration_seconds",
            "is_billable",
            "is_running",
            "is_locked",
            "invoice_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_duration_seconds(self, entry: TimeEntry) -> int:
        return int(entry.duration_at(timezone.now()).total_seconds())


class TimeEntryCreateSerializer(serializers.Serializer[TimeEntry]):
    project = OrganizationScopedPrimaryKeyRelatedField(
        queryset=Project.objects.select_related("client"),
    )
    description = serializers.CharField(max_length=500, allow_blank=True, default="")
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField()
    is_billable = serializers.BooleanField(allow_null=True, default=None)


class TimeEntryUpdateSerializer(serializers.Serializer[TimeEntry]):
    project = OrganizationScopedPrimaryKeyRelatedField(
        queryset=Project.objects.select_related("client"),
        required=False,
    )
    description = serializers.CharField(max_length=500, allow_blank=True, required=False)
    started_at = serializers.DateTimeField(required=False)
    ended_at = serializers.DateTimeField(required=False)
    is_billable = serializers.BooleanField(required=False)


class TimerStartSerializer(serializers.Serializer[TimeEntry]):
    project = OrganizationScopedPrimaryKeyRelatedField(
        queryset=Project.objects.select_related("client"),
    )
    description = serializers.CharField(max_length=500, allow_blank=True, default="")
    is_billable = serializers.BooleanField(allow_null=True, default=None)
