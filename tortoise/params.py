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


ExceptionHandler = t.Callable[[CliException], t.NoReturn]


def _exception_handler(exc: CliException) -> t.NoReturn:
    """Default exception handler."""
    raise exc


class ParamsParser:
    """Argv parser."""
    def __init__(self,
                 params: list[Param],
                 function: t.Optional[t.Callable[..., t.Any]] = None,
                 exception_handler: ExceptionHandler = _exception_handler):
        self.params = params
        self.function = function
        self.exception_handler = exception_handler

        self.rename = Renamer(params)
        self.options = {}
        self.arguments = {}

        for param in params:
            for optarg in param.optargs:
                if optarg.startswith("-"):
                    self.options[optarg] = param
                else:
                    self.arguments[optarg] = param

    def expand(self, prefix: str) -> str:
        """Expand prefix to long option.

        Return prefix if it's a short option and it exists.
        Otherwise, raise UnknownOption.
        Also raise error if the prefix is ambiguous.
        """
        if not prefix.startswith("--"):
            if prefix in self.options:
                return prefix
            raise UnknownOption(prefix)

        candidates = [o for o in self.options if o.startswith(prefix)]
        if len(candidates) != 1:
            raise UnknownOption(prefix)
        return candidates[0]

    def parse_opt(self,
                  prefix: str,
                  args: t.Sequence[str],
                  ) -> tuple[str, t.Any, list[str]]:
        """Parse option.

        Return expanded option name, parsed value and unparsed tokens."""
        assert prefix.startswith("-")
        name = self.expand(prefix)
        param = self.options.get(name)
        if param is None:
            raise UnknownOption(name)
        parse = param.parse

        deque = collections.deque(args)
        value = parse(deque).value
        return (name, value, list(deque))

    def __call__(self, argv: t.Sequence[str]) -> dict[str, t.Any]:
        """Parse options and arguments from argv.

        Parse argv in two passes.
        1. Parse options.
        2. Parse arguments.

        Note: parsers may throw CantParse.
        Long option expansion may raise UnknownOption.
        """
        try:
            return self._call(argv)
        except CliException as exc:
            self.exception_handler(exc)

    def _call(self, argv: t.Sequence[str]) -> dict[str, t.Any]:
        """__call__ implementation.

        Does not handle exceptions.
        """
        args, opts = partition(argv)
        optargs = []

        for opt in opts:
            if opt[0].startswith("-") and not opt[0].startswith("--"):
                for short in opt[0][1:]:
                    name, value, unused = self.parse_opt(f"-{short}", opt[1:])
                    optargs.append((name, value))
                    args.extend(unused)
                continue
            name, value, unused = self.parse_opt(opt[0], opt[1:])
            optargs.append((name, value))
            args.extend(unused)

        deque = collections.deque(args)
        for name, param in self.arguments.items():
            optargs.append((name, param.parse(deque).value))

        if deque:
            raise UnknownOption(deque[0])

        renamed = self.rename(optargs)
        if not self.function:
            return renamed
        return check_arguments(renamed, self.function)


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
    def __init__(self, params: list[Param]):
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
