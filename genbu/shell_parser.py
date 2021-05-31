"""Shell parser."""

import collections
import sys
import textwrap
import typing as t

from .exceptions import CliException
from .namespace import Namespace
from .normalize import normalize
from .params import Param, Renamer, UnknownOption, check_arguments


ExceptionHandler = t.Callable[["ShellParser", CliException], t.NoReturn]


def default_exception_handler(cli: "ShellParser",
                              exc: CliException,
                              ) -> t.NoReturn:
    """Default exception handler."""
    name = " ".join(cli.complete_name())
    sys.exit(f"{name}: {exc}")


class ShellParser:  # pylint: disable=R0902,R0913
    """Shell (argv) parser."""
    def __init__(self,
                 name: str,
                 description: str,
                 params: t.Optional[list[Param]] = None,
                 subparsers: t.Optional[t.Sequence["ShellParser"]] = None,

                 exception_handler: ExceptionHandler =
                 default_exception_handler,

                 function: t.Optional[t.Callable[..., t.Any]] = None,
                 ):
        assert not any(c.isspace() for c in name)

        self.name = name
        self.description = textwrap.dedent(description.strip())
        self.params = list(params or ())
        self.subparsers = {s.name: s for s in subparsers or []}
        self.exception_handler = exception_handler
        self.function = function
        self.parent = None

        self.rename = Renamer(params or ())
        self.options = {}
        self.arguments = {}

        for param in params or ():
            for optarg in param.optargs:
                if optarg.startswith("-"):
                    self.options[optarg] = param
                else:
                    self.arguments[optarg] = param

        for sub in self.subparsers.values():
            sub.parent = self

    def complete_name(self) -> tuple[str, ...]:
        """Return complete command name (includes parents)."""
        if self.parent is None:
            return (self.name,)
        return self.parent.complete_name() + (self.name,)

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

    def takes_params(self) -> bool:
        """Check if ShellParser can directly take Params."""
        return bool(self.params)

    def has_subcommands(self) -> bool:
        """Check if ShellParser has named subcommands."""
        return bool(self.subparsers)

    def __call__(self, argv: t.Sequence[str]) -> Namespace:
        """Parse commands, options and arguments from argv.

        Parse argv in three passes.
        0. Parse commands.
        1. Parse options.
        2. Parse arguments.

        Note: parsers may throw CantParse.
        Long option expansion may raise UnknownOption.
        """
        route: list["ShellParser"] = []
        deque = collections.deque(argv)
        try:
            while deque:
                prev = len(route)
                for name, sub in self.subparsers.items():
                    if name == deque[0]:
                        route.append(sub)
                        deque.popleft()
                        break
                if prev == len(route):
                    break

            subparser = route[-1] if route else self
            optargs = self.parse_optargs(subparser, deque)
            return Namespace(optargs, tuple(s.name for s in route) or None)
        except CliException as exc:
            subparser = route[-1] if route else self
            subparser.exception_handler(subparser, exc)

    @staticmethod
    def parse_optargs(subparser: "ShellParser",
                      argv: t.Sequence[str],
                      ) -> dict[str, t.Any]:
        """Parse options and arguments from argv using custom subparser.

        Assume program name and subcommands have been removed.
        """
        normalized = normalize(subparser.params, argv)
        args = normalized.arguments
        opts = normalized.options
        optargs = []

        for opt in opts:
            name, value, unused = subparser.parse_opt(opt[0], opt[1:])
            optargs.append((name, value))
            args.extend(unused)

        deque = collections.deque(args)
        for name, param in subparser.arguments.items():
            optargs.append((name, param.parse(deque).value))

        if deque:
            raise UnknownOption(deque[0])

        renamed = subparser.rename(optargs)
        if not subparser.function:
            return renamed
        return check_arguments(renamed, subparser.function)
