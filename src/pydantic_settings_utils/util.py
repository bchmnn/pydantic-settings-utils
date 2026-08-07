import types
import typing

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


def pydantic_field_is_optional(field: FieldInfo):
    return (
        typing.get_origin(field.annotation) in [typing.Union, types.UnionType]
    ) and len(
        set(typing.get_args(field.annotation)).intersection(
            [typing.Optional, types.NoneType]
        )
    ) > 0


def StandaloneConfig[T: BaseSettings](cls: type[T]) -> type[T]:
    class _C(cls):
        model_config = SettingsConfigDict(cli_parse_args=True)

    return typing.cast(type[T], _C)
