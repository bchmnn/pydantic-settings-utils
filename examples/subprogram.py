import sys

from pydantic_settings import CliSubCommand, get_subcommand

from pydantic_settings_utils import (
    EXAMPLE_CONFIG_COMMANDS,
    ConfigBase,
    ConfigWithConfigFileField,
    Duration,
    StandaloneConfig,
    WithRelaxedSubcommands,
)
from pydantic_settings_utils.config import ExampleConfigCommand

BaseSubprogramConfig = ConfigWithConfigFileField.factory("mysubprogram")


class SubprogramConfig(BaseSubprogramConfig):
    host: str = "localhost"
    port: int = 8080

    duration: Duration


class Config(ConfigBase):
    subprogram: CliSubCommand[SubprogramConfig]


def example_config_cb(c: ExampleConfigCommand):
    argv = sys.argv
    # we patch sys.argv with an empty config file,
    # so AutomatorConfig does not search and load values
    # from default config files.
    sys.argv = [*sys.argv[:1], "-c", "/dev/null"]
    config = SubprogramConfig(
        duration="1d2h", **EXAMPLE_CONFIG_COMMANDS  # type: ignore
    ).model_dump_yaml(quiet=c.suppress_yaml_warning)
    sys.argv = argv
    return config


def subprogram(config: SubprogramConfig | None = None):
    config = SubprogramConfig.init(config, example_config_cb=example_config_cb)
    print(config.model_dump_json(indent=2))


config = StandaloneConfig(WithRelaxedSubcommands(Config)).load(
    ignore_subcommand_help_flags=True
)
match get_subcommand(config):
    case SubprogramConfig() as c:
        subprogram(c)
