import sys
from collections.abc import Callable

import pytest
from pydantic import ValidationError
from pydantic_settings import CliSubCommand, get_subcommand

from pydantic_settings_utils import (
    ConfigBase,
    ConfigWithConfigFileField,
    CurrentConfigCommand,
    ExampleConfigCommand,
    StandaloneConfig,
    WithRelaxedSubcommands,
)


class ChildConfigShape(ConfigWithConfigFileField):
    test: str


class ParentConfigShape(ConfigBase):
    subcommand: CliSubCommand[ChildConfigShape]


type ChildConfigT = type[ChildConfigShape]
type ParentConfigT = type[ParentConfigShape]
type ExampleCallback = Callable[[ExampleConfigCommand], str]


@pytest.fixture
def BaseConfig():
    return ConfigWithConfigFileField.factory("command", "subcommand")


@pytest.fixture
def ChildConfig(BaseConfig: type[ConfigWithConfigFileField]):
    class Config(BaseConfig):
        test: str

    return Config


@pytest.fixture
def example_callback(ChildConfig: ChildConfigT):
    return lambda c: ChildConfig(
        test="example",
        **{
            "current-config": CurrentConfigCommand(**{}),  # noqa: PIE804
            "example-config": ExampleConfigCommand(**{}),  # noqa: PIE804
        },
    ).model_dump_yaml(quiet=c.suppress_yaml_warning)


@pytest.fixture
def ParentConfig(ChildConfig: ChildConfigT):
    class Config(ConfigBase):
        subcommand: CliSubCommand[ChildConfig]

    return WithRelaxedSubcommands(Config)


def test_raises(
    monkeypatch: pytest.MonkeyPatch,
    ChildConfig: ChildConfigT,
    example_callback: ExampleCallback,
):
    monkeypatch.setattr(sys, "argv", ["command"])

    with pytest.raises(ValidationError):
        ChildConfig.init(example_config_cb=example_callback)


def test_example_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    ChildConfig: ChildConfigT,
    example_callback: ExampleCallback,
):
    monkeypatch.setattr(sys, "argv", ["command", "example-config"])

    with pytest.raises(SystemExit):
        ChildConfig.init(example_config_cb=example_callback)

    captured = capsys.readouterr()
    assert captured.out == "---\ntest: example\n\n"


def test_current_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    ChildConfig: ChildConfigT,
    example_callback: ExampleCallback,
):
    monkeypatch.setattr(sys, "argv", ["command", "--test", "value", "current-config"])

    with pytest.raises(SystemExit):
        ChildConfig.init(example_config_cb=example_callback)

    captured = capsys.readouterr()
    assert captured.out == "---\ntest: value\n\n"


def test_parent_config(
    monkeypatch: pytest.MonkeyPatch,
    ParentConfig: ParentConfigT,
    ChildConfig: ChildConfigT,
):
    monkeypatch.setattr(sys, "argv", ["command", "subcommand"])

    config = StandaloneConfig(ParentConfig).load(ignore_subcommand_help_flags=True)
    match get_subcommand(config):
        case ChildConfig():
            assert True
        case _:
            assert False


def test_parent_raises(
    monkeypatch: pytest.MonkeyPatch,
    ParentConfig: ParentConfigT,
    ChildConfig: ChildConfigT,
    example_callback: ExampleCallback,
):
    monkeypatch.setattr(sys, "argv", ["command", "subcommand"])

    config = StandaloneConfig(ParentConfig).load(ignore_subcommand_help_flags=True)
    match get_subcommand(config):
        case ChildConfig():
            with pytest.raises(ValidationError):
                ChildConfig.init(example_config_cb=example_callback)
        case _:
            assert False


def test_parent_example_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    ParentConfig: ParentConfigT,
    ChildConfig: ChildConfigT,
    example_callback: ExampleCallback,
):
    monkeypatch.setattr(sys, "argv", ["command", "subcommand", "example-config"])

    config = StandaloneConfig(ParentConfig).load(ignore_subcommand_help_flags=True)
    match get_subcommand(config):
        case ChildConfig():
            with pytest.raises(SystemExit):
                ChildConfig.init(example_config_cb=example_callback)

            captured = capsys.readouterr()
            assert captured.out == "---\ntest: example\n\n"
        case _:
            assert False


def test_parent_current_config(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    ParentConfig: ParentConfigT,
    ChildConfig: ChildConfigT,
    example_callback: ExampleCallback,
):
    monkeypatch.setattr(
        sys, "argv", ["command", "subcommand", "--test", "value", "current-config"]
    )

    config = StandaloneConfig(ParentConfig).load(ignore_subcommand_help_flags=True)
    match get_subcommand(config):
        case ChildConfig():
            with pytest.raises(SystemExit):
                ChildConfig.init(example_config_cb=example_callback)

            captured = capsys.readouterr()
            assert captured.out == "---\ntest: value\n\n"
        case _:
            assert False
