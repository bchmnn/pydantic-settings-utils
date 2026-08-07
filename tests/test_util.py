import typing

import pytest
from pydantic import BaseModel

from pydantic_settings_utils import pydantic_field_is_optional


class ModelShape(BaseModel):
    opt1: typing.Optional[typing.Any]  # noqa: UP045
    opt2: typing.Any | None


type ModelT = type[ModelShape]


@pytest.fixture
def Model():
    class M(BaseModel):
        opt1: typing.Optional[typing.Any]  # noqa: UP045
        opt2: typing.Any | None

    return M


def test_util(Model: ModelT):

    for v in Model.model_fields.values():
        assert pydantic_field_is_optional(v)
