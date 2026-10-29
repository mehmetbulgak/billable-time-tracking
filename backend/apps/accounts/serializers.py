from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import Role, User
from apps.organizations.serializers import OrganizationSerializer


class UserSummarySerializer(serializers.ModelSerializer[User]):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "full_name")
        read_only_fields = fields


class MemberSerializer(serializers.ModelSerializer[User]):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_active",
            "date_joined",
        )
        read_only_fields = fields


class MemberCreateSerializer(serializers.Serializer[User]):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80)
    role = serializers.ChoiceField(choices=Role.choices, default=Role.MEMBER)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value


class MemberUpdateSerializer(serializers.Serializer[User]):
    first_name = serializers.CharField(max_length=80, required=False)
    last_name = serializers.CharField(max_length=80, required=False)
    role = serializers.ChoiceField(choices=Role.choices, required=False)
    is_active = serializers.BooleanField(required=False)


class CurrentUserSerializer(serializers.ModelSerializer[User]):
    full_name = serializers.CharField(read_only=True)
    is_manager = serializers.BooleanField(read_only=True)
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_manager",
            "organization",
        )
        read_only_fields = ("id", "email", "full_name", "role", "is_manager", "organization")
