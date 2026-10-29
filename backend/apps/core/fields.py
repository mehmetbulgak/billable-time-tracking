from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.money import minutes_to_hours


@extend_schema_field(OpenApiTypes.DECIMAL)
class HoursFromMinutesField(serializers.Field[int, str, str, Any]):
    def __init__(self, **kwargs: Any) -> None:
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, value: int) -> str:
        return str(minutes_to_hours(value))
