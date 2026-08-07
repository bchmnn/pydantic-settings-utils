import types
import typing

from pydantic.fields import FieldInfo


def pydantic_field_is_optional(field: FieldInfo):
    return (
        typing.get_origin(field.annotation) in [typing.Union, types.UnionType]
    ) and len(
        set(typing.get_args(field.annotation)).intersection(
            [typing.Optional, types.NoneType]
        )
    ) > 0
