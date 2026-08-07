import argparse
import logging
import sys
import typing
from pathlib import Path

import yaml
from pydantic_settings import PydanticBaseSettingsSource


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
