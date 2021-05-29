"""Params parser."""

import collections
import inspect
import textwrap
import typing as t

from . import combinators as comb
from .exceptions import CliException
from .forward import MissingArgument, to_args_kwargs


class UnknownOption(CliException):
    """Unrecognized option."""


def partition(argv: t.Sequence[str]) -> tuple[list[str], list[list[str]]]:
    """Partition argv arguments and options.

    Note: the options list may still contain some positional arguments.
    Assume tokens that contain multiple short options don't take args.
    """
    args = []
    opts = []

    deque = collections.deque(argv)
    while deque:
        current = deque.popleft()
        if not current.startswith("-"):
            args.append(current)
        elif not current.startswith("--") and len(current) > 2:
            for opt in current[1:]:
                opts.append([f"--{opt}"])
        else:
            tail = [current]
            while deque and not deque[0].startswith("-"):
                tail.append(deque.popleft())
            opts.append(tail)
    return args, opts


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

        self.name = name
        self.optargs = optargs
        self.parse = parse
        self.resolve = resolve
        self.description = description
        self.arg_description = arg_description

    def is_option(self) -> bool:
        """Check if Param is an option."""
        return all(p.startswith("-") for p in self.optargs)


def rename(optargs: list[tuple[str, t.Any]],
           name: str,
           names: set[str],
           resolve: Resolver,
           ) -> list[tuple[str, t.Any]]:
    """Rename parameters in optargs and resolve name conflicts."""
    renamed = []
    none = object()
    final: t.Any = none
    for param, value in optargs:
        if param in names:
            final = value if final is none else resolve(final, value)
        else:
            renamed.append((param, value))
    if final is not none:
        renamed.append((name, final))
    return renamed


class Renamer:  # pylint: disable=too-few-public-methods
    """Options and arguments renamer."""
    def __init__(self, params: t.Sequence[Param]):
        self.params = params

    def __call__(self, optargs: list[tuple[str, t.Any]]) -> dict[str, t.Any]:
        """Rename parameters and convert into dict."""
        for param in self.params:
            optargs = rename(
                optargs,
                param.name,
                set(param.optargs),
                param.resolve
            )
        return dict(optargs)


def check_arguments(optargs: dict[str, t.Any],
                    function: t.Callable[..., t.Any],
                    ) -> dict[str, t.Any]:
    """Check if optargs contains all args that function needs.

    Return optargs if okay.
    Raise MissingArguments if not.
    """
    args, kwargs = to_args_kwargs(optargs, function)
    sig = inspect.signature(function)
    try:
        sig.bind(*args, **kwargs)
        return optargs
    except TypeError as exc:
        raise MissingArgument from exc
