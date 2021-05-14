"""Add subcommands."""

import typing as t


Cli = t.Callable[[t.Sequence[str]], dict[str, t.Any]]
Subcommand = t.Tuple[str, ...]


def get_subcommand(argv: t.Sequence[str],
                   subcommands: t.Sequence[Subcommand],
                   ) -> Subcommand:
    """Get subcommand from argv.

    Assume argv does not contain program name.
    Return () if none of the subcommands match.
    """
    for sub in sorted(subcommands, key=len, reverse=True):
        if tuple(argv[:len(sub)]) == sub:
            return sub
    return ()


class InvalidRoute(Exception):
    """Invalid CLI route."""


class Router:
    """Subcommand router."""
    def __init__(self) -> None:
        self.routes: dict[Subcommand, Cli] = {}

    def add(self, *names: str, cli: Cli) -> None:
        """Add CLI route.

        Overwrite route if one already exists.
        """
        self.routes[names] = cli

    def get_optargs(self, argv: t.Sequence[str]) -> dict[str, t.Any]:
        """Return CLI optargs."""
        subcommand = get_subcommand(argv, tuple(self.routes.keys()))
        cli = self.routes.get(subcommand)
        if cli is None:
            raise InvalidRoute

        args = argv[len(subcommand):]
        return cli(args)
