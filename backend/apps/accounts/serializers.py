from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
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
    email = serializers.EmailField(max_length=254)
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80)
    role = serializers.ChoiceField(choices=Role.choices, default=Role.MEMBER)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=1024)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = User(
            email=attrs["email"], first_name=attrs["first_name"], last_name=attrs["last_name"]
        )
        try:
            validate_password(attrs["password"], user=user)
        except ValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from error
        return attrs


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
