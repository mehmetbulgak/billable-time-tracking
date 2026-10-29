from enum import StrEnum


def choices_for(enum: type[StrEnum]) -> list[tuple[str, str]]:
    return [(member.value, getattr(member, "label", member.value)) for member in enum]
