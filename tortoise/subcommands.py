"""Add subcommands."""

import textwrap
import typing as t


Cli = t.Callable[[t.Sequence[str]], dict[str, t.Any]]


class Subcommand:  # pylint: disable=too-few-public-methods
    """CLI subcommand descriptor."""
    def __init__(self,
                 cli: Cli,
                 name: str,
                 description: str):
        self.cli = cli
        self.name = tuple(name.split())
        self.description = textwrap.dedent(description.strip())


class InvalidRoute(Exception):
    """Invalid CLI route."""


def get_subcommand(argv: t.Sequence[str],
                   subcommands: t.Iterable[Subcommand],
                   ) -> Subcommand:
    """Get subcommand from argv.

    Assume argv does not contain program name.
    Raise InvalidRoute if none of the subcommands match.
    """
    for sub in sorted(subcommands, key=lambda s: len(s.name), reverse=True):
        if tuple(argv[:len(sub.name)]) == sub.name:
            return sub
    raise InvalidRoute


class Router:  # pylint: disable=too-few-public-methods
    """Subcommand router."""
    def __init__(self, routes: t.Sequence[Subcommand]):
        self.routes = routes

    def __call__(self,
                 argv: t.Sequence[str],
                 ) -> tuple[Subcommand, dict[str, t.Any]]:
        """Return CLI optargs."""
        subcommand = get_subcommand(argv, self.routes)
        args = argv[len(subcommand.name):]
        return subcommand, subcommand.cli(args)
