"""CLInterface paramater descriptor."""

import textwrap
import typing as t

from . import combinators as comb
from .exceptions import CLError


class InvalidOption(CLError):
    """Invalid option (e.g. contains '=' or ' ')."""


class UnknownOption(CLError):
    """Unrecognized option."""


Resolver = t.Callable[[t.Any, t.Any], t.Any]


class Param:  # pylint: disable=too-few-public-methods,too-many-arguments
    """CLI parameter descriptor."""
    def __init__(self,
                 name: str,
                 optargs: t.Optional[list[str]] = None,
                 parse: comb.Parser = comb.One(str),
                 resolve: Resolver = lambda _, b: b,
                 description: t.Optional[str] = None,
                 arg_description: t.Optional[str] = None):
        if optargs is None:
            optargs = [name]
        if description is not None:
            description = textwrap.dedent(description.strip())

        for optarg in optargs:
            if "=" in optarg or any(c.isspace() for c in optarg):
                raise InvalidOption(optarg)

        self.name = name
        self.optargs = optargs
        self.parse = parse
        self.resolve = resolve
        self.description = description
        self.arg_description = arg_description

    def is_option(self) -> bool:
        """Check if Param is an option."""
        return all(p.startswith("-") for p in self.optargs)
