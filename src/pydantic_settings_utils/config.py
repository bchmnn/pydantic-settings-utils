import sys
import typing
from pathlib import Path

import platformdirs
import yaml
from pydantic import AliasChoices, BaseModel, Field
from pydantic.fields import ModelPrivateAttr
from pydantic.main import IncEx
from pydantic_settings import (
    CliImplicitFlag,
    CliSubCommand,
    CliToggleFlag,
    get_subcommand,
)

from pydantic_settings_utils.base import ConfigBase
from pydantic_settings_utils.relax import RelaxedConfig
from pydantic_settings_utils.sources import YamlConfigSettingsSource
from pydantic_settings_utils.util import StandaloneConfig


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

        if not config or config._QUIET:
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

        return StandaloneConfig(cls).configure(parse_config_quietly=True).load()
