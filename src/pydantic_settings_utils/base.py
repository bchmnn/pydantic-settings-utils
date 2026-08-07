import sys

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources.types import _CliSubCommand


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
