import argparse
import logging
import sys
import types
import typing
from pathlib import Path

import platformdirs
import yaml
from pydantic import AliasChoices, BaseModel, Field
from pydantic.fields import ModelPrivateAttr
from pydantic.main import IncEx
from pydantic_core import PydanticUndefined
from pydantic_settings import (
    BaseSettings,
    CliImplicitFlag,
    CliSubCommand,
    CliToggleFlag,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    get_subcommand,
)
from pydantic_settings.sources.types import _CliSubCommand

from pydantic_settings_utils.duration import (
    Duration,
    human_time_to_timedelta,
    timedelta_to_human_time,
)
from pydantic_settings_utils.util import pydantic_field_is_optional


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    locations: list[Path]
    quiet: bool

    def __init__(self, settings_cls, locations: list[Path] | None = None, quiet=False):
        super().__init__(settings_cls)
        self.locations = locations or []
        self.quiet = quiet
        self._data = self._load()

    def get_field_value(self, field, field_name: str) -> tuple[typing.Any, str, bool]:
        if field_name in self._data:
            return self._data[field_name], field_name, False
        return None, field_name, False

    def __call__(self) -> dict:
        return self._data

    def _load(self) -> dict:
        config_path, verbose = self._get_cli_arguments()

        logger = logging.getLogger("bchmnn.pydantic-settings-utils")
        logger.setLevel(logging.DEBUG if not self.quiet and verbose else logging.INFO)

        if config_path:
            logger.debug(f"loading {config_path}")
            return self._load_yaml(config_path)

        for path in self.locations:
            if not path.exists():
                logger.debug(f"lookup {path}")
            else:
                logger.debug(f"found {path}")
                return self._load_yaml(path)

        return {}

    def _get_cli_arguments(self) -> tuple[Path | None, bool]:
        class Arguments:
            config: str | None = None
            verbose: bool = False

        p = argparse.ArgumentParser(add_help=False)
        p.add_argument("-c", "--config", dest="config", type=str, required=False)
        p.add_argument("-v", "--verbose", dest="verbose", action="store_true")
        args = p.parse_known_args(sys.argv, namespace=Arguments)[0]
        return (Path(args.config) if args.config else None, args.verbose)

    def _load_yaml(self, path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        cli_avoid_json=True,
        cli_hide_none_type=True,
        cli_kebab_case=True,
        cli_use_class_docs_for_groups=True,
        env_nested_delimiter="__",
    )

    @classmethod
    def has_subcommands(cls):
        for field in cls.model_fields.values():
            if _CliSubCommand in field.metadata:
                return True
        return False

    @classmethod
    def get_subcommands(cls):
        subcommands = []

        for name, field in cls.model_fields.items():
            if _CliSubCommand in field.metadata:
                subcommands.append(name)
        return subcommands

    @classmethod
    def has_help_before_subcommands(cls):
        subcommands = cls.get_subcommands()
        has_help = False
        for arg in sys.argv:
            if arg in ["-h", "--help"]:
                has_help = True
            elif arg in subcommands:
                return has_help
        return has_help

    @classmethod
    def has_help_after_subcommands(cls):
        subcommands = cls.get_subcommands()
        has_help = False
        for arg in reversed(sys.argv):
            if arg in ["-h", "--help"]:
                has_help = True
            elif arg in subcommands:
                return has_help
        return False

    @classmethod
    def load(cls, ignore_subcommand_help_flags=False):
        if not ignore_subcommand_help_flags:
            return cls()

        subcommands = cls.get_subcommands()

        argv = sys.argv

        seen = False
        sys.argv = [
            arg
            for arg in sys.argv
            if not (seen := seen or arg in subcommands) or arg not in ("-h", "--help")
        ]
        config = cls()
        sys.argv = argv
        seen = False
        argv = sys.argv[0:1]
        for arg in sys.argv[1:]:
            if not seen and arg in subcommands:
                seen = True
                continue
            if seen:
                argv.append(arg)
        sys.argv = argv
        return config


class OutputConfigCommand(BaseModel):
    suppress_yaml_warning: CliImplicitFlag[bool] = Field(
        False, description="suppress yamlfix warning", alias="suppress-yaml-warning"
    )


class CurrentConfigCommand(OutputConfigCommand):
    pass


class ExampleConfigCommand(OutputConfigCommand):
    pass


EXAMPLE_CONFIG_COMMANDS = {
    "current-config": CurrentConfigCommand(**{}),  # noqa: PIE804
    "example-config": ExampleConfigCommand(**{}),  # noqa: PIE804
}


class ConfigWithConfigFileField(ConfigBase):
    _DEFAULT_LOCATIONS = ModelPrivateAttr([])
    _QUIET = ModelPrivateAttr(False)
    _RELAXED = ModelPrivateAttr(False)

    config: str | None = Field(
        None,
        validation_alias=AliasChoices("c", "config"),
    )
    verbose: CliToggleFlag[bool] = Field(
        False, validation_alias=AliasChoices("v", "verbose")
    )

    current_config: CliSubCommand[CurrentConfigCommand] = Field(alias="current-config")
    example_config: CliSubCommand[ExampleConfigCommand] = Field(alias="example-config")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(
                settings_cls,
                cls._DEFAULT_LOCATIONS.get_default(),
                cls._QUIET.get_default(),
            ),
            dotenv_settings,
            file_secret_settings,
        )

    @staticmethod
    def factory(
        dirname: str, filename: str = "config"
    ) -> type["ConfigWithConfigFileField"]:
        yaml_extensions = ["yml", "yaml"]
        default_etc_config_files = [
            Path(f"/etc/{dirname}/{filename}.{ext}") for ext in yaml_extensions
        ]
        default_home_config_files = [
            platformdirs.user_config_path(dirname).joinpath(f"{filename}.{ext}")
            for ext in yaml_extensions
        ]
        default_locations = [*default_home_config_files, *default_etc_config_files]

        newclass = type(
            f"ConfigWithConfigFileField_{dirname}_{filename}",
            (ConfigWithConfigFileField,),
            {
                "__annotations__": {
                    "config": str | None,
                },
                "_DEFAULT_LOCATIONS": ModelPrivateAttr(default_locations),
                "config": Field(
                    None,
                    validation_alias=AliasChoices("c", "config"),
                    description=f"path to config file (.y[a]ml). Defaults to {platformdirs.user_config_path(dirname).joinpath(f"{filename}.y[a]ml")} or /etc/{dirname}/{filename}.y[a]ml if unspecified.",
                ),
            },
        )
        return newclass

    @classmethod
    def configure(
        cls, parse_config_quietly=False, args: dict | None = None
    ) -> type[typing.Self]:
        newclass = type(
            f"{cls.__name__}_configured",
            (cls,),
            {"_QUIET": ModelPrivateAttr(parse_config_quietly), **(args or {})},
        )
        return typing.cast(type[typing.Self], newclass)

    def model_dump_yaml(
        self, excluder: typing.Callable[[list[str]], IncEx] | None = None, quiet=True
    ):
        dump = self.model_dump(
            mode="python",
            exclude=(
                excluder(["config", "verbose", "current_config", "example_config"])
                if excluder
                else {"config", "verbose", "current_config", "example_config"}
            ),
        )
        y = yaml.safe_dump(
            dump,
            sort_keys=False,
            allow_unicode=True,
            indent=2,
        )
        try:
            import yamlfix

            return yamlfix.fix_code(y)
        except ModuleNotFoundError:
            if not quiet:
                print(
                    "WARNING: yamlfix not installed",
                    file=sys.stderr,
                )
            return y

    @classmethod
    def init(
        cls,
        config: typing.Self | None = None,
        example_config_cb: typing.Callable[[ExampleConfigCommand], str] | None = None,
    ) -> typing.Self:
        if config and not config._RELAXED:
            return config

        if cls.has_help_before_subcommands() or cls.has_help_after_subcommands():
            StandaloneConfig(cls).load()
            sys.exit(0)

        if not config:
            config = StandaloneConfig(RelaxedConfig(cls)).load()

        match get_subcommand(config, is_required=False):
            case CurrentConfigCommand() as c:
                print(config.model_dump_yaml(quiet=c.suppress_yaml_warning))
                sys.exit(0)
            case ExampleConfigCommand() as c:
                if not example_config_cb:
                    print("Not implemented!", file=sys.stderr)
                    sys.exit(1)
                print(example_config_cb(c))
                sys.exit(0)

        return StandaloneConfig(cls).load()


def StandaloneConfig[T: BaseSettings](cls: type[T]) -> type[T]:
    class _C(cls):
        model_config = SettingsConfigDict(cli_parse_args=True)

    return typing.cast(type[T], _C)


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
