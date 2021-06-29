"""Genbu paramater descriptor."""

import textwrap
import typing as t

from . import combinators as comb


class InvalidOption(ValueError):
    """Invalid option (e.g. contains '=' or ' ')."""
    def __init__(self, option: str):
        super().__init__(option)
        self.option = option


Aggregator = t.Callable[[t.Sequence[t.Any]], t.Any]


def default_aggregator(values: t.Sequence[t.Any]) -> t.Any:
    """Return last element of values."""
    return values[-1]


class Param:  # pylint: disable=too-many-arguments
    """CLI parameter descriptor."""
    def __init__(self,
                 dest: str,
                 optargs: t.Optional[t.List[str]] = None,
                 parser: comb.Parser = comb.One(str),
                 aggregator: Aggregator = default_aggregator,
                 description: t.Optional[str] = None,
                 arg_description: t.Optional[str] = None):
        if optargs is None:
            optargs = [dest]
        if description is not None:
            description = textwrap.dedent(description.strip())

        for optarg in optargs:
            if "=" in optarg or any(c.isspace() for c in optarg):
                raise InvalidOption(optarg)

        self.dest = dest
        self.optargs = optargs
        self.parser = parser
        self.aggregator = aggregator
        self.description = description
        self.arg_description = arg_description

    def __eq__(self, other: object) -> bool:
        return self.dest == other.dest if isinstance(other, Param) else False

    def __hash__(self) -> int:
        return hash(self.dest)

    def is_option(self) -> bool:
        """Check if Param is an option."""
        return all(p.startswith("-") for p in self.optargs)
