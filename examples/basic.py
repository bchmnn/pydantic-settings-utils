from pydantic_settings_utils import (
    EXAMPLE_CONFIG_COMMANDS,
    ConfigWithConfigFileField,
    Duration,
)

BaseConfig = ConfigWithConfigFileField.factory("myapp")


class Config(BaseConfig):
    host: str = "localhost"
    port: int = 8080

    duration: Duration


EXAMPLE_CONFIG = Config(duration="1d2h", **EXAMPLE_CONFIG_COMMANDS)  # type: ignore
example_config_cb = lambda c: EXAMPLE_CONFIG.model_dump_yaml(
    quiet=c.suppress_yaml_warning
)

config = Config.init(example_config_cb=example_config_cb)

print(config.model_dump_json(indent=2))
