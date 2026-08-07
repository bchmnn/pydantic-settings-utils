import re
from datetime import timedelta
from typing import Annotated

from pydantic import PlainSerializer, PlainValidator, WithJsonSchema


def human_time_to_timedelta(s: str) -> timedelta:
    pattern = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")
    match = pattern.fullmatch(s.strip().lower())
    if not match:
        raise ValueError(f"Invalid duration string: {s!r}")
    days, hours, minutes, seconds = (int(x) if x else 0 for x in match.groups())
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def timedelta_to_human_time(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")

    return "".join(parts)


Duration = Annotated[
    timedelta,
    PlainValidator(human_time_to_timedelta, json_schema_input_type=str),
    PlainSerializer(timedelta_to_human_time, return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]
