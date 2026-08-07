# pydantic-settings-utils

## Usage

```python
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
```

```sh
$ uv run examples/basic.py -h
usage: basic.py [-h] [-c str] [-v] [--host str] [--port int]
                [--duration timedelta]
                {current-config,example-config} ...

options:
  -h, --help            show this help message and exit
  -c, --config str      path to config file (.y[a]ml). Defaults to
                        /home/example/.config/myapp/config.y[a]ml or
                        /etc/myapp/config.y[a]ml if unspecified. (default:
                        None)
  -v, --verbose
  --host str            (default: localhost)
  --port int            (default: 8080)
  --duration timedelta  (required)

subcommands:
  {current-config,example-config}
    current-config
    example-config
```

### Subcommand: example-config

```sh
$ uv run examples/basic.py example-config
---
host: localhost
port: 8080
duration: 1d2h

```

### Subcommand: current-config

```sh
$ uv run examples/basic.py --duration 1d current-config
---
host: localhost
port: 8080
duration: 1d

```

### YAML config file

```sh
$ cat examples/basic.yaml
---
host: example.com
port: 1024
duration: 1d

$ uv run examples/basic.py -c examples/basic.yaml current-config
---
host: example.com
port: 1024
duration: 1d

```

### Subprograms

```python
from pydantic_settings import CliSubCommand, get_subcommand

from pydantic_settings_utils import (
    EXAMPLE_CONFIG_COMMANDS,
    ConfigBase,
    ConfigWithConfigFileField,
    Duration,
    StandaloneConfig,
    WithRelaxedSubcommands,
)

BaseSubprogramConfig = ConfigWithConfigFileField.factory("mysubprogram")


class SubprogramConfig(BaseSubprogramConfig):
    host: str = "localhost"
    port: int = 8080

    duration: Duration


class Config(ConfigBase):
    subprogram: CliSubCommand[SubprogramConfig]


EXAMPLE_SUBPROGRAM_CONFIG = SubprogramConfig(duration="1d2h", **EXAMPLE_CONFIG_COMMANDS)  # type: ignore
example_config_cb = lambda c: EXAMPLE_SUBPROGRAM_CONFIG.model_dump_yaml(
    quiet=c.suppress_yaml_warning
)


def subprogram(config: SubprogramConfig | None = None):
    config = SubprogramConfig.init(config, example_config_cb=example_config_cb)
    print(config.model_dump_json(indent=2))


config = StandaloneConfig(WithRelaxedSubcommands(Config)).load(
    ignore_subcommand_help_flags=True
)
match get_subcommand(config):
    case SubprogramConfig() as c:
        subprogram(c)
```

```sh
$ uv run examples/subprogram.py -h
usage: subprogram.py [-h] {subprogram} ...

options:
  -h, --help    show this help message and exit

subcommands:
  {subprogram}
    subprogram

$ uv run examples/subprogram.py subprogram -h
usage: subprogram.py [-h] [-c str] [-v] [--host str] [--port int]
                     [--duration timedelta]
                     {current-config,example-config} ...

...
```

## Development

Enable git hooks to format staged code and generate README pre-commit:

```sh
git config core.hooksPath .githooks
```
