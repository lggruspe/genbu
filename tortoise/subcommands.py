"""Add subcommands."""

import textwrap
import typing as t

from .exceptions import CliException
from .params import ParamsParser as Cli


class Subcommand:  # pylint: disable=too-few-public-methods
    """CLI subcommand descriptor."""
    def __init__(self,
                 cli: Cli,
                 name: str,
                 description: str):
        self.cli = cli
        self.name = tuple(name.split())
        self.description = textwrap.dedent(description.strip())


class InvalidRoute(CliException):
    """Invalid CLI route."""


class Router:
    """Subcommand router."""
    def __init__(self, routes: t.Sequence[Subcommand]):
        self.routes = routes

    def takes_params(self) -> bool:
        """Check if Router can directly take Params."""
        return any(r.name == () for r in self.routes)

    def has_subcommands(self) -> bool:
        """Check if Router has named subcommands."""
        return any(r.name != () for r in self.routes)

    def get_subcommand(self, argv: t.Sequence[str]) -> Subcommand:
        """Get subcommand from argv.

        Assume argv does not contain program name.
        Raise InvalidRoute if none of the subcommands match.
        """
        routes = sorted(self.routes, key=lambda s: len(s.name), reverse=True)
        for sub in routes:
            if tuple(argv[:len(sub.name)]) == sub.name:
                return sub
        raise InvalidRoute

    def __call__(self,
                 argv: t.Sequence[str],
                 ) -> tuple[Subcommand, dict[str, t.Any]]:
        """Return CLI optargs."""
        subcommand = self.get_subcommand(argv)
        args = argv[len(subcommand.name):]
        return subcommand, subcommand.cli(args)
