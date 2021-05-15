"""CLI object."""

import typing as t


Optargs = list[tuple[str, t.Any]]
TParamsParser = t.Callable[[t.Sequence[str]], Optargs]
TRenamer = t.Callable[[Optargs], dict[str, t.Any]]


class Cli:  # pylint: disable=too-few-public-methods
    """Cli object."""
    def __init__(self, params_parser: TParamsParser, renamer: TRenamer):
        self.params_parser = params_parser
        self.renamer = renamer

    def __call__(self, argv: t.Sequence[str]) -> dict[str, t.Any]:
        """Parse command-line options and arguments."""
        return self.renamer(self.params_parser(argv))
