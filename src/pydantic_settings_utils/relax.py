import types
import typing

from pydantic.fields import ModelPrivateAttr
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings, CliSubCommand
from pydantic_settings.sources.types import _CliSubCommand

from pydantic_settings_utils.util import pydantic_field_is_optional

if typing.TYPE_CHECKING:
    from pydantic_settings_utils.config import ConfigWithConfigFileField


def RelaxedConfig[T: ConfigWithConfigFileField](cls: type[T]) -> type[T]:
    """
    Creates new class from input class with all fields
    being optional and initialized to None.

    class A:
        a: str

    becomes

    class Relaxed_A:
        a: str | None = None

    """
    new_cls_dict: dict[typing.Any, typing.Any] = {
        "__annotations__": {},
        "_RELAXED": ModelPrivateAttr(True),
        "_QUIET": ModelPrivateAttr(True),
    }
    for key, field in cls.model_fields.items():
        if not field.annotation:
            continue

        if _CliSubCommand in field.metadata:
            continue

        if pydantic_field_is_optional(field):
            if field.default == PydanticUndefined:
                new_cls_dict["__annotations__"][key] = field.rebuild_annotation()
                new_cls_dict[key] = None
            continue

        new_cls_dict["__annotations__"][key] = field.rebuild_annotation() | None
        new_cls_dict[key] = None

    newclass = type(
        f"Relaxed_{cls.__name__}",
        (cls,),
        new_cls_dict,
    )

    return typing.cast(type[T], newclass)


def WithRelaxedSubcommands[T: BaseSettings](cls: type[T]) -> type[T]:
    new_annotations = {}
    for key, field in cls.model_fields.items():
        if _CliSubCommand in field.metadata and (
            typing.get_origin(field.annotation) == typing.Union
            or typing.get_origin(field.annotation) == types.UnionType
        ):
            new_annotations[key] = CliSubCommand[
                RelaxedConfig(typing.get_args(field.annotation)[0])
            ]

    newclass = type(
        f"Relaxed_{cls.__name__}", (cls,), {"__annotations__": new_annotations}
    )

    return typing.cast(type[T], newclass)
